"""qa_emotion_face_coverage — RULE 4: an emotional beat must show a FACE.

The swarm's "synchrony/enforcement hole": Midnight Magnates is a documentary
about PEOPLE, and the moments that carry the story — the grief, the betrayal,
the realization, the death — only land if the viewer sees a human face at that
beat. A beat that narrates "and then he wept, alone" while the only thing on
screen is an archival panel of a building plays as emotionally dead: the line
that should hit on a close-up plays on cardboard. RULE 4 makes that impossible
to ship: every emotional beat MUST render a face primitive.

The storyboard schema *declares* the contract (a beat with `emotion_face` is
required to contain a face primitive), but that allOf is only enforced by
qa_schema_validate at the ASSETS stage — and ONLY when `emotion_face` is present.
This gate is the load-bearing storyboard-stage enforcer and it is STRICTLY
broader than the schema:

  * STRONG signal — `emotion_face` declared on the beat. This is the explicit
    "this beat is an emotional human face" marker; if it is present the beat MUST
    contain a face primitive. (Same contract the schema declares, enforced here
    one stage earlier, as a blocking gate, so it cannot reach assets unfaced.)
  * WEAK signal — the beat is doing emotional work in WORDS even though nobody
    flagged emotion_face: its `intent` text (always present) OR its resolved VO
    span carries a high-emotion keyword (grief/cried/wept/realized/betrayed/
    alone/death/loss/fear/...). The schema does NOT police this case at all; an
    emotional line with no emotion_face and no face primitive sails straight
    through. Here it is a FAIL.

For any beat hit by EITHER signal, the beat's `layers` MUST contain at least one
face primitive: face_closeup / face_reaction / face_medium / reaction_cut.
Otherwise -> `emotional_beat_without_face` (BLOCKING fail — RULE 4 never warns;
an unfaced emotional beat is a shippable defect, not advice).

VO-span resolution mirrors the compiler / qa_beat_visual_coverage exactly
(start_anchor / end_anchor -> Whisper word time, else fallback_absolute_s; the
beat's VO text is the Whisper words whose start falls in [start, end]). The
transcript is OPTIONAL: with no whisper/full.json the gate still runs on the
emotion_face signal and the always-present `intent` text, so it can never
silently no-op — a gate that cannot run must never silently pass.

Reads:  <project>/artifacts/storyboard/*.json          (REQUIRED — one per chapter)
        <project>/artifacts/whisper/full.json           (OPTIONAL — widens the
                                                          WEAK keyword scan to VO)
Shapes (only the fields this gate reads):
    storyboard = {"chapter_id", "phases": [
                    {"phase_id", "beats": [
                        {"beat_id", "intent"?,
                         "emotion_face"? {...},
                         "start_anchor"? {"phrase", "offset_ms"?,
                                          "fallback_absolute_s"?},
                         "end_anchor"?   {...},
                         "layers": [{"primitive", ...}, ...]}, ...]}, ...]}
    whisper    = {"words": [{"word": str, "start": float, "end": float}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from .. import vocab
from ._contract import Finding, GateInputError, load_json, run_cli

# The face primitives. A beat that shows a human face at an emotional moment must
# render one of these (mirrors the storyboard schema's emotion_face allOf list +
# the layer_action primitive enum's face family). Single source: vocab.FACE_PRIMITIVES
# (== compiler's FACE_PRIMS) — {face_closeup, face_reaction, face_medium, reaction_cut}.
FACE_PRIMITIVES = vocab.FACE_PRIMITIVES

# High-emotion keywords. A beat whose intent/VO carries one is doing emotional
# work that, per RULE 4, must be carried by a face. The task's seed list, lightly
# expanded with their obvious inflections — kept deliberately small + documented
# so the rule is auditable. Matched as whole, case-insensitive substrings against
# normalized (punctuation-stripped) tokens, so "wept," and "Alone." still hit.
EMOTION_KEYWORDS = frozenset({
    "grief", "grieved", "grieving",
    "cried", "crying", "cries",
    "wept", "weeping", "weep",
    "realized", "realised", "realization", "realisation",
    "betrayed", "betrayal",
    "alone", "lonely", "loneliness",
    "death", "died", "dying", "dead",
    "loss", "lost",
    "fear", "feared", "afraid", "terror", "terrified",
})

_EDGE_PUNCT = ".,!?;:\"'`()[]{}<>—–…“”‘’"


def _norm(tok: str) -> str:
    """Lowercase + strip edge punctuation. Mirrors the drift gates' tokenizer."""
    return tok.lower().strip().strip(_EDGE_PUNCT)


def _tokens(text: str) -> List[str]:
    out: List[str] = []
    for raw in text.split():
        t = _norm(raw)
        if t:
            out.append(t)
    return out


def _is_number(v) -> bool:
    # bool is an int subclass; a True/False is not a real timestamp.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _emotion_hit(text: str) -> Optional[str]:
    """Return the first emotion keyword found in ``text`` (token-wise), else None."""
    for tok in _tokens(text):
        if tok in EMOTION_KEYWORDS:
            return tok
    return None


def _whisper_words(project_dir: Path) -> Optional[List[Tuple[str, float]]]:
    """[(word_raw, start_s), ...] or None if there is no transcript yet.

    None means "no VO to scan" (the WEAK signal then runs on intent only); it is
    NOT a silent pass — the emotion_face + intent paths still execute. A whisper
    file that EXISTS but is malformed is a hard GateInputError (it must not be
    treated as 'no transcript').
    """
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
        if not isinstance(raw, str) or not _is_number(start):
            raise GateInputError(
                "whisper/full.json: a word entry lacks string 'word' / numeric 'start'")
        out.append((str(raw), float(start)))
    return out


def _resolve_anchor(anchor, words: Optional[List[Tuple[str, float]]]) -> Optional[float]:
    """Beat-time of an anchor: Whisper phrase time, else fallback_absolute_s, else None.

    Mirrors compiler._resolve_anchor / qa_beat_visual_coverage so the VO span this
    gate scans is exactly the one the compiler renders. Returns None (skip) rather
    than raising on an unresolved anchor — that is qa_drift's failure to report,
    not this gate's.
    """
    if not isinstance(anchor, dict):
        return None
    offset = 0.0
    off_raw = anchor.get("offset_ms", 0)
    if _is_number(off_raw):
        offset = float(off_raw) / 1000.0
    toks = _tokens(str(anchor.get("phrase", "")))
    if toks and words:
        norm_words = [_norm(w) for w, _ in words]
        n = len(toks)
        for i in range(len(norm_words) - n + 1):
            if norm_words[i:i + n] == toks:
                return max(0.0, words[i][1] + offset)
    fb = anchor.get("fallback_absolute_s")
    if _is_number(fb):
        return max(0.0, float(fb) + offset)
    return None


def _beat_vo_text(words: List[Tuple[str, float]], start_s: float, end_s: float) -> str:
    """Whisper words whose start time falls in [start_s, end_s], joined."""
    return " ".join(raw for raw, t in words if start_s <= t <= end_s)


def _has_face_primitive(beat: dict) -> bool:
    layers = beat.get("layers")
    if not isinstance(layers, list):
        return False
    for la in layers:
        if isinstance(la, dict) and la.get("primitive") in FACE_PRIMITIVES:
            return True
    return False


def _storyboards(project_dir: Path) -> List[Tuple[str, dict]]:
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        raise GateInputError(
            "required input not found: " + str(sb_dir) + " (no storyboard directory)")
    paths = sorted(sb_dir.glob("*.json"))
    if not paths:
        raise GateInputError(
            "no storyboard files in " + str(sb_dir) + " (expected one *.json per chapter)")
    out: List[Tuple[str, dict]] = []
    for p in paths:
        data = load_json(p)  # GateInputError on unreadable/invalid JSON
        if not isinstance(data, dict):
            raise GateInputError(str(p) + ": storyboard root is not an object")
        out.append((p.name, data))
    return out


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    storyboards = _storyboards(project_dir)
    words = _whisper_words(project_dir)  # None -> VO scan skipped (intent still runs)

    findings: List[Finding] = []
    for name, sb in storyboards:
        cid = str(sb.get("chapter_id") or name)
        phases = sb.get("phases")
        if not isinstance(phases, list):
            continue
        for ph in phases:
            beats = ph.get("beats") if isinstance(ph, dict) else None
            if not isinstance(beats, list):
                continue
            phase_id = str(ph.get("phase_id") or "phase") if isinstance(ph, dict) else "phase"
            for beat in beats:
                if not isinstance(beat, dict):
                    continue
                bid = str(beat.get("beat_id") or "beat")
                where = "{0} :: {1} :: {2}".format(cid, phase_id, bid)

                # --- Decide whether this beat is "emotional". ---
                # STRONG: an explicit emotion_face marker.
                has_emotion_face = isinstance(beat.get("emotion_face"), dict)

                # WEAK: an emotion keyword in the beat's intent text (always
                # available) or in its resolved VO span (only if whisper exists).
                reason = None
                if has_emotion_face:
                    reason = "declares emotion_face (an emotional human face)"
                else:
                    kw = _emotion_hit(str(beat.get("intent", "")))
                    if kw is not None:
                        reason = "intent carries the emotion keyword {0!r}".format(kw)
                    elif words is not None:
                        s = _resolve_anchor(beat.get("start_anchor"), words)
                        e = _resolve_anchor(beat.get("end_anchor"), words)
                        if s is not None and e is not None and e >= s:
                            vo_kw = _emotion_hit(_beat_vo_text(words, s, e))
                            if vo_kw is not None:
                                reason = "VO carries the emotion keyword {0!r}".format(vo_kw)

                if reason is None:
                    continue  # not an emotional beat — RULE 4 does not apply

                # --- Enforce: an emotional beat MUST render a face primitive. ---
                if not _has_face_primitive(beat):
                    findings.append(Finding(
                        "fail", "emotional_beat_without_face",
                        "emotional beat ({0}) has NO face primitive in its layers — "
                        "RULE 4 requires a face (one of {1}); the emotional moment "
                        "would play on a non-face shot (e.g. panel_archival).".format(
                            reason, "/".join(sorted(FACE_PRIMITIVES))),
                        where=where,
                    ))

    return findings


if __name__ == "__main__":
    run_cli("qa_emotion_face_coverage", check)
