"""qa_beat_visual_coverage — micro-beat coverage + the shot-plan precondition (A10).

Two concerns, one gate:

1. (advisory / WARN) MICRO-BEAT COVERAGE.
   The documented failure mode is a beat that lingers >=3s on a high-intent line
   of narration ("our American Cousin", "the most famous actor in the country",
   "the loudest laugh of the night") while NOTHING happens off the map — the map
   just sits there and the moment that should carry a visual (a comedy ticket, a
   3-image actor sequence) plays as dead air. For every beat whose spoken span is
   >=MIN_BEAT_S seconds AND whose VO carries a high-narrative-intent keyword, but
   whose `layers` contain ZERO off-map visual primitive, we emit a WARN suggesting
   a concrete visual. This is advisory (it never blocks) because the right visual
   is an authoring call — but a silent high-intent beat should always surface.

   A beat's spoken span is resolved exactly the way the compiler resolves it:
   start_anchor / end_anchor -> Whisper word time (or fallback_absolute_s). The VO
   text of the beat is the Whisper words whose start time falls in [start, end].
   If neither anchor resolves we cannot judge the beat and skip it (qa_drift is the
   gate that fails on an unresolved anchor — not this one).

2. (HARD FAIL) qa_shot_plan_exists.
   Before render, the animator MUST emit a shot plan per chapter at
   artifacts/animation_shot_plan/<chapter_id>.md. Every storyboard chapter that
   exists must have a matching, non-empty shot-plan file. A missing/empty plan is a
   FAIL — render cannot proceed off an unplanned chapter.

Reads:  <project>/artifacts/storyboard/*.json
        <project>/artifacts/whisper/full.json            (optional; coverage WARNs
                                                           are skipped if absent)
        <project>/artifacts/animation_shot_plan/<id>.md  (required per chapter)
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from .. import vocab
from ._contract import Finding, GateInputError, load_json, run_cli

# A beat shorter than this is a quick punctuation hit; coverage is only expected
# on beats that actually linger (matches the task's ">= 3s" threshold).
MIN_BEAT_S = 3.0

_EDGE_PUNCT = ".,!?;:\"'`()[]{}<>—–…“”‘’"

# Off-map visual primitives — a beat that "steps off the map" uses one of these.
# Mirrors qa_primitive_utilization's OFF_MAP family (the source of truth for what
# counts as an off-map visual), minus nothing: character cards, panels, dives,
# documents, clips, citations, etymology, concept diagrams. Sourced from the
# single-source vocabulary (identical membership; see lib/midnight_magnates/vocab.py).
OFF_MAP_VISUAL_PRIMS = vocab.OFF_MAP_VISUAL_PRIMS

# High-narrative-intent keywords. When the VO of a lingering beat carries one of
# these, the line is doing dramatic/biographical work that wants a picture, not a
# static map. Grouped only for the suggestion text; matching is a flat OR.
INTENT_SUGGESTIONS: Tuple[Tuple[Tuple[str, ...], str], ...] = (
    (("most famous", "famous actor", "best known", "renowned", "celebrated",
      "household name", "star of"),
     "a 3-image actor/portrait sequence (panel_illustration / character_card) of "
     "the person being introduced"),
    (("loudest laugh", "laughter", "the laugh", "biggest laugh", "roared", "comedy",
      "comedic", "punch line", "punchline", "funniest"),
     "the comedy beat as a panel (e.g. the 'Our American Cousin' ticket / a "
     "playbill panel_archival) so the laugh lands on a visual"),
    (("our american cousin", "the play", "the playbill", "the ticket",
      "the theater program", "the program"),
     "the period playbill / ticket as a panel_archival or document_overlay"),
    (("born", "grew up", "childhood", "as a boy", "as a child", "raised in",
      "the son of", "young"),
     "an archival/illustration panel of the early-life subject (story_dive into a "
     "panel_illustration)"),
    (("letter", "wrote", "diary", "telegram", "the note", "his words",
      "her words", "manifesto"),
     "the document itself as a document_overlay / panel_quote"),
    (("famous", "legendary", "infamous", "notorious", "the greatest",
      "remembered as", "would become"),
     "an off-map portrait / archival panel so the claim has a face"),
)


def _norm(tok: str) -> str:
    return tok.lower().strip().strip(_EDGE_PUNCT)


def _whisper_words(project_dir: Path) -> Optional[List[Tuple[str, float]]]:
    """[(word_lower, start_s), ...] or None if no transcript (coverage is then skipped)."""
    path = project_dir / "artifacts" / "whisper" / "full.json"
    if not path.is_file():
        return None
    data = load_json(path)
    words = data.get("words")
    if not isinstance(words, list) or not words:
        raise GateInputError("whisper/full.json has no 'words' array")
    out: List[Tuple[str, float]] = []
    for w in words:
        if not isinstance(w, dict):
            raise GateInputError("whisper/full.json: a word entry is not an object")
        raw = w.get("word")
        start = w.get("start")
        if not isinstance(raw, str) or not isinstance(start, (int, float)) or isinstance(start, bool):
            raise GateInputError("whisper/full.json: a word entry lacks string 'word' / numeric 'start'")
        out.append((str(raw), float(start)))
    return out


def _resolve_anchor(anchor: Optional[dict], words: List[Tuple[str, float]]) -> Optional[float]:
    """Beat-time of an anchor: Whisper phrase time, else fallback_absolute_s, else None.

    Mirrors compiler._resolve_anchor's resolution order so coverage sees the same
    span the compiler renders, but returns None (skip) instead of raising — an
    unresolved anchor is qa_drift's failure to report, not this gate's.
    """
    if not isinstance(anchor, dict):
        return None
    offset = 0.0
    off_raw = anchor.get("offset_ms", 0)
    if isinstance(off_raw, (int, float)) and not isinstance(off_raw, bool):
        offset = float(off_raw) / 1000.0
    phrase = str(anchor.get("phrase", "")).strip()
    toks = [_norm(t) for t in phrase.split()]
    toks = [t for t in toks if t]
    if toks and words:
        norm_words = [_norm(w) for w, _ in words]
        n = len(toks)
        for i in range(len(norm_words) - n + 1):
            if norm_words[i:i + n] == toks:
                return max(0.0, words[i][1] + offset)
    fb = anchor.get("fallback_absolute_s")
    if isinstance(fb, (int, float)) and not isinstance(fb, bool):
        return max(0.0, float(fb) + offset)
    return None


def _beat_vo_text(words: List[Tuple[str, float]], start_s: float, end_s: float) -> str:
    """Whisper words whose start time falls in [start_s, end_s], joined."""
    return " ".join(raw for raw, t in words if start_s <= t <= end_s)


def _intent_hit(vo_lower: str) -> Optional[str]:
    """Return a suggestion string if the VO carries a high-intent keyword, else None."""
    for keywords, suggestion in INTENT_SUGGESTIONS:
        for kw in keywords:
            if kw in vo_lower:
                return suggestion
    return None


def _has_offmap_visual(beat: dict) -> bool:
    layers = beat.get("layers")
    if not isinstance(layers, list):
        return False
    for la in layers:
        if isinstance(la, dict) and la.get("primitive") in OFF_MAP_VISUAL_PRIMS:
            return True
    return False


def _storyboards(project_dir: Path) -> List[Tuple[str, dict]]:
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        raise GateInputError("required input not found: " + str(sb_dir) + " (no storyboard directory)")
    paths = sorted(sb_dir.glob("*.json"))
    if not paths:
        raise GateInputError("no storyboard files in " + str(sb_dir) + " (expected one *.json per chapter)")
    out: List[Tuple[str, dict]] = []
    for p in paths:
        data = load_json(p)
        if not isinstance(data, dict):
            raise GateInputError(str(p) + ": storyboard root is not an object")
        out.append((p.name, data))
    return out


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    storyboards = _storyboards(project_dir)
    words = _whisper_words(project_dir)  # None -> coverage WARNs skipped
    plan_dir = project_dir / "artifacts" / "animation_shot_plan"

    findings: List[Finding] = []

    for name, sb in storyboards:
        cid = str(sb.get("chapter_id") or name)

        # --- 2) HARD: shot plan must exist + be non-empty for this chapter. ---
        plan = plan_dir / "{0}.md".format(cid)
        if not plan.is_file():
            findings.append(Finding(
                "fail", "missing_shot_plan",
                "no animation shot plan at artifacts/animation_shot_plan/{0}.md — the "
                "animator must emit a shot plan for this chapter before render".format(cid),
                where=cid,
            ))
        else:
            try:
                if not plan.read_text(errors="ignore").strip():
                    findings.append(Finding(
                        "fail", "empty_shot_plan",
                        "animation shot plan artifacts/animation_shot_plan/{0}.md is empty".format(cid),
                        where=cid,
                    ))
            except OSError as exc:
                findings.append(Finding(
                    "fail", "unreadable_shot_plan",
                    "shot plan for {0} could not be read: {1}".format(cid, exc),
                    where=cid,
                ))

        # --- 1) ADVISORY: micro-beat coverage (needs the transcript). ---
        if words is None:
            continue
        phases = sb.get("phases")
        if not isinstance(phases, list):
            continue
        for ph in phases:
            beats = ph.get("beats") if isinstance(ph, dict) else None
            if not isinstance(beats, list):
                continue
            phase_id = str(ph.get("phase_id") or "phase")
            for beat in beats:
                if not isinstance(beat, dict):
                    continue
                start_s = _resolve_anchor(beat.get("start_anchor"), words)
                end_s = _resolve_anchor(beat.get("end_anchor"), words)
                if start_s is None or end_s is None or end_s - start_s < MIN_BEAT_S:
                    continue
                if _has_offmap_visual(beat):
                    continue  # already steps off the map; nothing to suggest
                vo = _beat_vo_text(words, start_s, end_s)
                suggestion = _intent_hit(vo.lower())
                if suggestion is None:
                    continue
                bid = str(beat.get("beat_id") or "beat")
                snippet = (vo[:80] + "…") if len(vo) > 80 else vo
                findings.append(Finding(
                    "warn", "uncovered_high_intent_beat",
                    "beat lingers {0:.1f}s on a high-intent line (VO: \"{1}\") but has NO "
                    "off-map visual — suggest {2}.".format(end_s - start_s, snippet, suggestion),
                    where="{0} :: {1} :: {2}".format(cid, phase_id, bid),
                ))

    return findings


if __name__ == "__main__":
    run_cli("qa_beat_visual_coverage", check)
