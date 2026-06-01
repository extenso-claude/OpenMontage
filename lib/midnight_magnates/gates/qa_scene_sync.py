"""qa_scene_sync — the 2D/3D scene-graph timeline must reconcile to the VO.

MM RULE 2 makes 2D (flat-segmented noir) and 3D (bird's-eye diorama) co-equal
render modes, chosen per shot. Either way the moving picture is driven by a
scene graph (the diorama/cutout engine emits one per animated beat), and that
graph hangs off the voiceover exactly like every other cue: a key moment in the
animation — the gun raised, the ledger slammed, the face turning — only lands if
it fires on the narrated word it is reacting to.

Two holes the swarm found and this gate closes:

  1) SILENT-SKIP (the legacy bug): qa_physics/qa_render_directive only look at the
     scene graphs that *exist*. A beat tagged animation_tier 2d/3d with NO scene
     graph at all slipped through with at most a soft warn — an animated shot that
     was never actually built (or whose graph was dropped) shipped as a dead hold.
     Here a 2d/3d beat with no matching scene graph is a LOUD `missing_scene_graph`
     fail, not a silent pass ("a gate that cannot run must never silently pass",
     applied to the thing being checked, not just the checker's inputs).

  2) MOMENT DRIFT: a present scene graph must declare scene_t0_master_s (where the
     scene starts on the master timeline) and key_moments (each a local_t into the
     scene + the vo_anchor_phrase it must hit). For each key moment we resolve the
     phrase in Whisper -> word_time, and require
         |scene_t0_master_s + local_t - word_time| <= budget
     budget = 0.5s normally, tightened to 0.4s for a FACE moment (an emotional
     close-up reads as off the instant the expression and the word disagree). A
     phrase that does not resolve is a HARD `anchor_not_found` (the documented
     "NOT_FOUND on anchor lookup is a HARD FAIL", drift_audit_all_cue_types) —
     a key moment with nothing to anchor to is a drift waiting to happen.

Beat<->graph binding: a scene graph claims its beat via an explicit `beat_id`
field (preferred; may also carry `chapter_id` to disambiguate same-named beats
across chapters), or, lacking that, by its filename stem matching the beat_id
(e.g. ``ch01_x.b04_booth.scene_graph.json`` or ``b04_booth.scene_graph.json``).
Only beats whose animation_tier is 2d/3d require a graph; un-tiered / chrome
beats are ignored (RULE 3 — not every beat is an animated scene).

Reads:  <project>/artifacts/diorama/*.scene_graph.json
        <project>/artifacts/storyboard/*.json   (one per chapter)
        <project>/artifacts/whisper/full.json
Shapes (only the fields this gate reads):
    scene_graph = {"scene_t0_master_s": float,
                   "beat_id"?: str, "chapter_id"?: str,
                   "key_moments": [
                       {"local_t": float, "vo_anchor_phrase": str,
                        "face"?: bool, "fallback_absolute_s"?: float}, ...]}
    storyboard  = {"chapter_id", "phases": [
                      {"beats": [
                          {"beat_id", "animation_tier"? ("2d"|"3d"),
                           "emotion_face"?: {...}}, ...]}, ...]}
    whisper     = {"words": [{"word": str, "start": float, "end": float}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# Per-moment drift budget in seconds. A scene's key moment may sit this far from
# the narrated word it reacts to. Faces are tighter: when the expression and the
# word disagree, an emotional close-up reads as wrong almost immediately.
BUDGET_DEFAULT_S = 0.5
BUDGET_FACE_S = 0.4

# Only these tiers declare an animated scene that needs a scene graph.
ANIMATED_TIERS = frozenset({"2d", "3d"})

# Suffix the diorama engine stamps on every scene-graph file.
_GRAPH_SUFFIX = ".scene_graph.json"

# Trim only edge punctuation; keep internal apostrophes/hyphens so contractions
# ("nation's") and hyphenates ("thirty-five") survive identically on both sides.
# Mirrors qa_drift / qa_audio_drift so a phrase resolves the same way everywhere.
_EDGE_PUNCT = ".,!?;:\"'`()[]{}<>—–…“”‘’"


def _norm_token(tok: str) -> str:
    """Lowercase and strip leading/trailing punctuation. May return ''."""
    return tok.lower().strip().strip(_EDGE_PUNCT)


def _tokenize(text: str) -> List[str]:
    """Whitespace-split, normalize each token, drop tokens that normalize away."""
    out: List[str] = []
    for raw in text.split():
        t = _norm_token(raw)
        if t:
            out.append(t)
    return out


def _is_number(v) -> bool:
    # bool is an int subclass; a True/False is not a real time/coordinate.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _load_whisper(project_dir: Path) -> List[Tuple[str, float]]:
    """Return [(normalized_token, start_s), ...] in transcript order.

    Each surviving token keeps its own word's ``start`` so a resolved run's first
    word maps back to a real timestamp (same pattern as qa_audio_drift).
    """
    data = load_json(project_dir / "artifacts" / "whisper" / "full.json")
    words = data.get("words")
    if not isinstance(words, list) or not words:
        raise GateInputError("whisper/full.json has no 'words' array")
    out: List[Tuple[str, float]] = []
    for w in words:
        if not isinstance(w, dict):
            raise GateInputError("whisper/full.json: a word entry is not an object")
        raw = w.get("word")
        if not isinstance(raw, str):
            raise GateInputError("whisper/full.json: a word entry has no string 'word'")
        start = w.get("start")
        if not _is_number(start):
            raise GateInputError(
                "whisper/full.json: word {0!r} has no numeric 'start'".format(raw)
            )
        t = _norm_token(raw)
        if t:
            out.append((t, float(start)))
    if not out:
        raise GateInputError(
            "whisper/full.json: no usable word tokens after normalization"
        )
    return out


def _resolve_run_start(
    needle: List[str], stream: List[Tuple[str, float]]
) -> Optional[float]:
    """First-word .start of the earliest contiguous match of `needle`, else None."""
    n, h = len(needle), len(stream)
    if n == 0 or n > h:
        return None
    first = needle[0]
    for i in range(h - n + 1):
        if stream[i][0] != first:
            continue
        if [tok for tok, _ in stream[i:i + n]] == needle:
            return stream[i][1]
    return None


def _load_storyboard_beats(project_dir: Path) -> List[Tuple[str, str, dict]]:
    """Return [(chapter_id, beat_id, beat_dict), ...] across all storyboards.

    Raises GateInputError if the storyboard dir / files are missing or unreadable
    — a present-but-broken storyboard must never let this gate silently pass.
    """
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        raise GateInputError(
            "required input not found: " + str(sb_dir) + " (no storyboard directory)"
        )
    paths = sorted(sb_dir.glob("*.json"))
    if not paths:
        raise GateInputError(
            "no storyboard files in " + str(sb_dir) + " (expected one *.json per chapter)"
        )

    out: List[Tuple[str, str, dict]] = []
    for p in paths:
        data = load_json(p)  # GateInputError on unreadable/invalid JSON
        if not isinstance(data, dict):
            raise GateInputError(str(p) + ": storyboard root is not an object")
        cid = data.get("chapter_id")
        cid = str(cid) if isinstance(cid, str) and cid.strip() else p.stem
        phases = data.get("phases")
        if not isinstance(phases, list):
            continue
        for phase in phases:
            if not isinstance(phase, dict):
                continue
            beats = phase.get("beats")
            if not isinstance(beats, list):
                continue
            for bi, beat in enumerate(beats):
                if not isinstance(beat, dict):
                    continue
                bid = beat.get("beat_id")
                bid = str(bid) if isinstance(bid, str) and bid.strip() else "beat[{0}]".format(bi)
                out.append((cid, bid, beat))
    return out


def _load_scene_graphs(project_dir: Path) -> List[Tuple[str, dict]]:
    """Return [(filename, graph_dict), ...]. Empty list is allowed (a project
    with no animated beats has no graphs); a present-but-broken graph raises."""
    d = project_dir / "artifacts" / "diorama"
    if not d.is_dir():
        return []
    out: List[Tuple[str, dict]] = []
    for p in sorted(d.glob("*" + _GRAPH_SUFFIX)):
        graph = load_json(p)  # unreadable/invalid -> GateInputError (blocking)
        if not isinstance(graph, dict):
            raise GateInputError(str(p) + ": scene graph root is not an object")
        out.append((p.name, graph))
    return out


def _graph_stem(filename: str) -> str:
    """``ch01_x.b04_booth.scene_graph.json`` -> ``ch01_x.b04_booth``."""
    if filename.endswith(_GRAPH_SUFFIX):
        return filename[: -len(_GRAPH_SUFFIX)]
    return filename


def _index_graphs_by_beat(
    graphs: List[Tuple[str, dict]],
) -> Tuple[Dict[Tuple[str, str], List[Tuple[str, dict]]],
           Dict[str, List[Tuple[str, dict]]]]:
    """Index graphs for beat lookup.

    Returns (by_chapter_beat, by_beat_only):
      * by_chapter_beat[(chapter_id, beat_id)] -> graphs that named BOTH.
      * by_beat_only[beat_id]                  -> graphs keyed on beat_id alone,
        whether the beat_id came from an explicit field or the filename stem.
    A graph that names a beat_id (field) and/or whose stem looks like a beat is
    discoverable; the stem is also matched against the bare beat_id and against
    the ``<chapter>.<beat>`` form.
    """
    by_chapter_beat: Dict[Tuple[str, str], List[Tuple[str, dict]]] = {}
    by_beat_only: Dict[str, List[Tuple[str, dict]]] = {}

    for fname, graph in graphs:
        stem = _graph_stem(fname)
        field_beat = graph.get("beat_id")
        field_beat = field_beat.strip() if isinstance(field_beat, str) and field_beat.strip() else None
        field_chap = graph.get("chapter_id")
        field_chap = field_chap.strip() if isinstance(field_chap, str) and field_chap.strip() else None

        # Candidate beat keys this graph answers to.
        beat_keys = set()
        if field_beat:
            beat_keys.add(field_beat)
        # Filename stem forms: whole stem, and the last dotted segment
        # (so "ch01_x.b04_booth" also answers to "b04_booth").
        if stem:
            beat_keys.add(stem)
            if "." in stem:
                beat_keys.add(stem.rsplit(".", 1)[-1])

        for bk in beat_keys:
            by_beat_only.setdefault(bk, []).append((fname, graph))

        # Chapter-qualified keys (most specific).
        if field_chap and field_beat:
            by_chapter_beat.setdefault((field_chap, field_beat), []).append((fname, graph))
        if "." in stem:
            chap_part, beat_part = stem.split(".", 1)
            # beat_part may itself be dotted; take its last segment as the beat.
            beat_leaf = beat_part.rsplit(".", 1)[-1] if "." in beat_part else beat_part
            if chap_part and beat_leaf:
                by_chapter_beat.setdefault((chap_part, beat_leaf), []).append((fname, graph))

    return by_chapter_beat, by_beat_only


def _graphs_for_beat(
    chapter_id: str,
    beat_id: str,
    by_chapter_beat: Dict[Tuple[str, str], List[Tuple[str, dict]]],
    by_beat_only: Dict[str, List[Tuple[str, dict]]],
) -> List[Tuple[str, dict]]:
    """Best match for a beat: chapter-qualified first, else beat-id alone."""
    qualified = by_chapter_beat.get((chapter_id, beat_id))
    if qualified:
        return qualified
    return by_beat_only.get(beat_id, [])


def _check_graph_moments(
    fname: str,
    graph: dict,
    beat_is_face: bool,
    stream: List[Tuple[str, float]],
    where: str,
) -> List[Finding]:
    """Validate scene_t0 + every key_moment of one already-matched graph."""
    findings: List[Finding] = []

    t0 = graph.get("scene_t0_master_s")
    if not _is_number(t0):
        findings.append(Finding(
            "fail", "missing_scene_t0",
            "scene graph {0!r} has no numeric scene_t0_master_s — its local "
            "moment times cannot be placed on the master VO timeline".format(fname),
            where=where))
        # Without t0 we cannot evaluate any moment for this graph.
        return findings
    t0 = float(t0)

    moments = graph.get("key_moments")
    if not isinstance(moments, list) or not moments:
        findings.append(Finding(
            "fail", "missing_key_moments",
            "scene graph {0!r} declares no key_moments — an animated scene with no "
            "VO-anchored moments cannot be reconciled to the narration".format(fname),
            where=where))
        return findings

    for mi, m in enumerate(moments):
        mwhere = "{0} :: {1}#km{2}".format(where, fname, mi)
        if not isinstance(m, dict):
            findings.append(Finding(
                "fail", "malformed_key_moment",
                "key_moment[{0}] is not an object".format(mi),
                where=mwhere))
            continue

        local_t = m.get("local_t")
        if not _is_number(local_t):
            findings.append(Finding(
                "fail", "missing_key_moments",
                "key_moment[{0}] has no numeric local_t".format(mi),
                where=mwhere))
            continue

        phrase = m.get("vo_anchor_phrase")
        phrase_str = phrase if isinstance(phrase, str) else ""
        tokens = _tokenize(phrase_str)
        is_face = beat_is_face or bool(m.get("face"))
        budget = BUDGET_FACE_S if is_face else BUDGET_DEFAULT_S

        if not tokens:
            findings.append(Finding(
                "fail", "missing_key_moments",
                "key_moment[{0}] has no vo_anchor_phrase — nothing to reconcile its "
                "scene time against the VO".format(mi),
                where=mwhere))
            continue

        word_time = _resolve_run_start(tokens, stream)
        if word_time is None:
            fallback = m.get("fallback_absolute_s")
            if not _is_number(fallback):
                findings.append(Finding(
                    "fail", "anchor_not_found",
                    "key_moment vo_anchor_phrase {0!r} is NOT FOUND as a contiguous "
                    "run in the VO transcript and has no fallback_absolute_s — the "
                    "scene moment has nothing to anchor to".format(phrase_str),
                    where=mwhere))
                continue
            word_time = float(fallback)

        scene_time = t0 + float(local_t)
        delta = abs(scene_time - word_time)
        if delta > budget:
            findings.append(Finding(
                "fail", "scene_moment_drift",
                "scene moment lands at {0:.2f}s (scene_t0 {1:.2f}s + local_t "
                "{2:.2f}s) but its anchor {3!r} is narrated at {4:.2f}s — {5:.2f}s "
                "off ({6}budget {7:.2f}s)".format(
                    scene_time, t0, float(local_t), phrase_str, word_time, delta,
                    "face " if is_face else "", budget),
                where=mwhere))

    return findings


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    stream = _load_whisper(project_dir)
    beats = _load_storyboard_beats(project_dir)
    graphs = _load_scene_graphs(project_dir)
    by_chapter_beat, by_beat_only = _index_graphs_by_beat(graphs)

    findings: List[Finding] = []
    for chapter_id, beat_id, beat in beats:
        tier = beat.get("animation_tier")
        if tier not in ANIMATED_TIERS:
            continue  # not an animated scene -> no scene graph required (RULE 3)

        where = "{0} :: {1}".format(chapter_id, beat_id)
        matched = _graphs_for_beat(chapter_id, beat_id, by_chapter_beat, by_beat_only)

        if not matched:
            # The hole the swarm found: an animated beat with NO scene graph is a
            # LOUD fail (was a silent warn) — the shot was never built / was lost.
            findings.append(Finding(
                "fail", "missing_scene_graph",
                "beat is animation_tier={0!r} but no scene graph claims it (looked "
                "for artifacts/diorama/*{1} with beat_id {2!r} or a matching "
                "filename stem) — an animated 2D/3D shot with no scene graph renders "
                "as a dead hold".format(tier, _GRAPH_SUFFIX, beat_id),
                where=where))
            continue

        beat_is_face = isinstance(beat.get("emotion_face"), dict)
        for fname, graph in matched:
            findings.extend(_check_graph_moments(
                fname, graph, beat_is_face, stream, where))

    return findings


if __name__ == "__main__":
    run_cli("qa_scene_sync", check)
