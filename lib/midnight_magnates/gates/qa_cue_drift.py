"""qa_cue_drift — the VISUAL twin of qa_audio_drift. Cues land on their word.

The whole timeline hangs off the voiceover. qa_drift proves every BEAT anchor
RESOLVES to the VO; this gate proves every emitted CUE actually FIRES within a
tight, per-kind budget of the word it is reacting to. A face cut, a character
card, a map sprite, an archival clip only reads if it lands on the narrated
beat — a card that pops a second early (or late) is the documented visual-drift
bug (memory drift_audit_all_cue_types: per-cue-type drift budgets, "NOT_FOUND on
anchor lookup is a HARD FAIL").

For every cue in artifacts/cuelist.json we re-derive expected_t from the owning
beat/layer in the storyboard and the VO transcript, NOT from anything the cue
self-reports — so a compiler that stamped the wrong start_s is caught:

  * find the cue's owning beat+layer by its id "<chapter>.<beat>.<prim>.<idx>";
  * the anchor is the LAYER's cue_anchor if present, else the beat's
    start_anchor;
  * resolve anchor.phrase to a contiguous lowercased-token run in the Whisper
    word stream -> the run's first word .start, + anchor.offset_ms/1000;
  * scope that resolution to the chapter's master window
    [vo_start_offset_in_master_s, +duration_s) so a phrase that recurs across
    chapters binds to the occurrence inside THIS chapter (full.json is ONE master
    transcript and the compiler resolves the same scoped way);
  * FAIL `cue_drift_exceeds_budget` when |cue.start_s - expected_t| > BUDGET[kind]
    — both are MASTER-clock seconds, so no per-chapter offset is re-added.

Per-kind budget (seconds): faces/cards must hit the frame (0.4); maps/animations
ease a touch wider (0.5); archival clips are tightest after faces (0.3).

Also load-bearing (independent of the budget math):
  * `over_loose_drift_budget` — layer_action.drift_budget_ms may only TIGHTEN the
    default-for-kind; a value LOOSER than the default is a config error that would
    silently widen the leash, so it is itself a FAIL.
  * `unanchored_intra_beat_action` — the 2nd+ time_distinct layer in a beat with
    NO cue_anchor has nothing of its own to fire on and would inherit the beat
    start, sliding off its narrated moment.
  * `ambiguous_anchor` — a phrase that matches >1 word-run in its resolution scope
    with no occurrence_index / near_s to disambiguate (silent first-occurrence
    binding is banned).

A gate that cannot run must never silently pass:
  * no cuelist.json / whisper/full.json / storyboard dir -> GateInputError;
  * a cue id that maps to no beat/layer                  -> FAIL (unmapped cue);
  * an anchor phrase that resolves to NOTHING            -> FAIL (NOT_FOUND);
  * a cue/anchor missing the numbers needed to verify    -> FAIL.

Reads:  <project>/artifacts/storyboard/*.json   (one storyboard per chapter)
        <project>/artifacts/whisper/full.json    (the VO transcript)
        <project>/artifacts/cuelist.json         (the compiled cues)
Shapes (only the fields this gate reads):
    storyboard = {"chapter_id", "vo_start_offset_in_master_s"?, "phases": [
                    {"phase_id"?, "beats": [
                        {"beat_id",
                         "start_anchor": {"phrase","offset_ms"?,"occurrence_index"?,
                                          "near_s"?,"fallback_absolute_s"?},
                         "layers": [
                            {"primitive","time_distinct"?,"drift_budget_ms"?,
                             "cue_anchor": {"phrase",...}?}, ...]}, ...]}, ...]}
    whisper    = {"words": [{"word": str, "start": float, "end": float}, ...]}
    cuelist    = {"cues": [{"id": "<chapter>.<beat>.<prim>.<idx>",
                            "kind": str, "start_s": float, ...}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# Per-cue-type drift budget in seconds (memory drift_audit_all_cue_types). Faces
# and cards must land on the frame; maps/animations ease a touch wider; archival
# clips are tightest after faces. DEFAULT covers anything unlisted.
DEFAULT_BUDGET_S = 0.5
BUDGET_S: Dict[str, float] = {
    # faces — emotional cuts must hit the word
    "face": 0.4, "face_closeup": 0.4, "face_reaction": 0.4,
    "face_medium": 0.4, "reaction_cut": 0.4,
    # character / info cards
    "character_card": 0.4, "character_card_pop": 0.4, "cards": 0.4,
    # archival clips — tightest after faces
    "clip_archival": 0.3, "clips": 0.3,
    # maps + animations/scenes ease a touch wider (map_* handled by prefix below)
    "animations": 0.5, "scene": 0.5,
}


def _budget_for_kind(kind: str) -> float:
    """Resolve the drift budget for a cue kind (exact, then map_* prefix, then default)."""
    k = (kind or "").strip().lower()
    if k in BUDGET_S:
        return BUDGET_S[k]
    if k.startswith("map_"):  # map_sprite, map_label, ... all 0.5
        return 0.5
    return DEFAULT_BUDGET_S


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
    # bool is an int subclass; a True/False value is not a real number here.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _load_whisper(project_dir: Path) -> List[Tuple[str, float]]:
    """Return [(normalized_token, start_s), ...] in transcript order.

    Each surviving token keeps its own word's ``start`` so a resolved run's first
    word maps back to a real timestamp (same as qa_audio_drift).
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


def _run_starts(needle: List[str], stream: List[Tuple[str, float]]) -> List[float]:
    """First-word .start of EVERY contiguous match of `needle` in `stream`.

    Returns all matches (not just the first) so the caller can detect an
    ambiguous phrase that resolves to more than one place.
    """
    n, h = len(needle), len(stream)
    if n == 0 or n > h:
        return []
    first = needle[0]
    hits: List[float] = []
    for i in range(h - n + 1):
        if stream[i][0] != first:
            continue
        if [tok for tok, _ in stream[i:i + n]] == needle:
            hits.append(stream[i][1])
    return hits


def _scope_stream(stream: List[Tuple[str, float]], lo: float, hi: float
                  ) -> List[Tuple[str, float]]:
    """Restrict the master word stream to a chapter's [lo, hi) master window.

    full.json is ONE master transcript; scoping to the chapter window makes a phrase
    that recurs across chapters resolve to THIS chapter's occurrence (matching the
    compiler). An empty window (mis-set offset/duration — that is qa_master_offset's
    job to catch) falls back to the full stream rather than forcing a spurious
    NOT_FOUND here.
    """
    scoped = [(tok, t) for (tok, t) in stream if lo <= t < hi]
    return scoped or stream


def _load_storyboards(project_dir: Path) -> List[Tuple[str, dict]]:
    """Return [(source_name, storyboard_dict), ...]. Raises if none readable."""
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        raise GateInputError(
            "required input not found: " + str(sb_dir) + " (no storyboard directory)"
        )
    paths = sorted(sb_dir.glob("*.json"))
    if not paths:
        raise GateInputError(
            "no storyboard files in " + str(sb_dir)
            + " (expected one *.json per chapter)"
        )
    out: List[Tuple[str, dict]] = []
    for p in paths:
        data = load_json(p)  # GateInputError on unreadable/invalid JSON
        if not isinstance(data, dict):
            raise GateInputError(str(p) + ": storyboard root is not an object")
        out.append((p.name, data))
    return out


class _BeatIndex:
    """One owning beat for a cue: its anchor source + per-primitive layer list.

    Holds enough to (a) re-derive expected_t for any cue that belongs to this
    beat, and (b) police the intra-beat time_distinct/cue_anchor invariants once,
    regardless of how many cues map back to it.
    """

    __slots__ = ("chapter_label", "beat_id", "vo_offset", "duration",
                 "start_anchor", "layers_by_prim")

    def __init__(self, chapter_label: str, beat_id: str, vo_offset: float,
                 duration: float, start_anchor: Optional[dict]):
        self.chapter_label = chapter_label
        self.beat_id = beat_id
        self.vo_offset = vo_offset
        self.duration = duration  # chapter duration_s -> the master window upper bound
        self.start_anchor = start_anchor
        # primitive -> ordered list of layer dicts sharing that primitive.
        self.layers_by_prim: Dict[str, List[dict]] = {}


def _chapter_label(name: str, data: dict) -> str:
    cid = data.get("chapter_id")
    return str(cid) if isinstance(cid, str) and cid.strip() else name


def _index_beats(storyboards: List[Tuple[str, dict]]
                 ) -> Tuple[Dict[Tuple[str, str], _BeatIndex], List[Finding]]:
    """Build {(chapter_label, beat_id): _BeatIndex} + structural findings.

    Structural findings here are the intra-beat invariants that don't need the
    cuelist at all (unanchored 2nd+ time_distinct action) — they FAIL even if the
    compiler never emitted a cue for that layer.
    """
    index: Dict[Tuple[str, str], _BeatIndex] = {}
    findings: List[Finding] = []
    for name, data in storyboards:
        chap = _chapter_label(name, data)
        vo_offset = data.get("vo_start_offset_in_master_s")
        vo_off = float(vo_offset) if _is_number(vo_offset) else 0.0
        dur = data.get("duration_s")
        dur_f = float(dur) if _is_number(dur) else float("inf")
        phases = data.get("phases")
        if not isinstance(phases, list):
            continue  # qa_drift owns "no phases"; nothing to map here.
        for pi, phase in enumerate(phases):
            if not isinstance(phase, dict):
                continue
            phase_id = str(phase.get("phase_id") or "phase[{0}]".format(pi))
            beats = phase.get("beats")
            if not isinstance(beats, list):
                continue
            for bi, beat in enumerate(beats):
                if not isinstance(beat, dict):
                    continue
                beat_id = str(beat.get("beat_id") or "beat[{0}]".format(bi))
                bidx = _BeatIndex(chap, beat_id, vo_off, dur_f, beat.get("start_anchor"))
                base = "{0} :: {1} :: {2}".format(chap, phase_id, beat_id)

                layers = beat.get("layers")
                if isinstance(layers, list):
                    distinct_seen = 0
                    for li, layer in enumerate(layers):
                        if not isinstance(layer, dict):
                            continue
                        prim = layer.get("primitive")
                        if isinstance(prim, str) and prim:
                            bidx.layers_by_prim.setdefault(prim, []).append(layer)
                        # Intra-beat anchoring invariant: the FIRST time_distinct
                        # action may inherit the beat start, but the 2nd+ MUST
                        # carry its own cue_anchor or it slides off its word.
                        if layer.get("time_distinct") is True:
                            distinct_seen += 1
                            has_cue_anchor = isinstance(
                                layer.get("cue_anchor"), dict)
                            if distinct_seen >= 2 and not has_cue_anchor:
                                findings.append(Finding(
                                    "fail", "unanchored_intra_beat_action",
                                    "time_distinct layer #{0} (primitive {1!r}) is "
                                    "the {2}{3} distinct action in this beat but has "
                                    "no cue_anchor — it would inherit the beat start "
                                    "and drift off its own narrated moment".format(
                                        li, prim, distinct_seen,
                                        _ord_suffix(distinct_seen)),
                                    where=base))
                index[(chap, beat_id)] = bidx
    return index, findings


def _ord_suffix(n: int) -> str:
    if 10 <= (n % 100) <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _parse_cue_id(cid: str) -> Optional[Tuple[str, str, str]]:
    """Split "<chapter>.<beat>.<prim>.<idx>" -> (chapter, beat, primitive).

    The chapter id itself contains no dot (schema pattern ^ch\\d{2}_[a-z0-9_]+$),
    so the first dot ends the chapter; the LAST two dotted fields are prim + idx,
    leaving the middle as the beat id (beat ids may themselves be dotted).
    """
    if not isinstance(cid, str):
        return None
    parts = cid.split(".")
    if len(parts) < 4:
        return None
    chapter = parts[0]
    primitive = parts[-2]
    beat = ".".join(parts[1:-2])
    if not chapter or not beat or not primitive:
        return None
    return chapter, beat, primitive


def _resolve_anchor_time(
    anchor: dict,
    stream: List[Tuple[str, float]],
    where: str,
    side: str,
) -> Tuple[Optional[float], Optional[Finding]]:
    """Resolve an anchor dict to a transcript-local time (pre vo_offset).

    Returns (time, None) on success, (None, Finding) on a blocking failure:
      * empty phrase + no fallback        -> empty_anchor_phrase
      * phrase NOT FOUND + no fallback    -> anchor_not_found
      * phrase matches >1 run + no        -> ambiguous_anchor
        occurrence_index / near_s
    offset_ms is applied to the resolved word time; a numeric fallback_absolute_s
    stands in when the phrase isn't (yet) in the VO.
    """
    offset_ms = anchor.get("offset_ms")
    offset_s = (float(offset_ms) / 1000.0) if _is_number(offset_ms) else 0.0

    phrase = anchor.get("phrase")
    phrase_str = phrase if isinstance(phrase, str) else ""
    tokens = _tokenize(phrase_str)

    fallback = anchor.get("fallback_absolute_s")
    has_fallback = _is_number(fallback)

    if not tokens:
        if has_fallback:
            return float(fallback) + offset_s, None
        return None, Finding(
            "fail", "empty_anchor_phrase",
            "{0} has no usable phrase and no numeric fallback_absolute_s — the cue "
            "cannot be anchored to the VO".format(side),
            where=where)

    hits = _run_starts(tokens, stream)
    if not hits:
        if has_fallback:
            return float(fallback) + offset_s, None
        return None, Finding(
            "fail", "anchor_not_found",
            "{0}.phrase {1!r} is NOT FOUND as a contiguous run in the VO transcript "
            "and has no fallback_absolute_s — the cue has nothing to anchor "
            "to".format(side, phrase_str),
            where=where)

    if len(hits) > 1:
        occ = anchor.get("occurrence_index")
        near = anchor.get("near_s")
        if _is_number(occ):
            idx = int(occ)
            if idx < 0 or idx >= len(hits):
                return None, Finding(
                    "fail", "anchor_occurrence_out_of_range",
                    "{0}.phrase {1!r} has occurrence_index {2} but only {3} "
                    "match(es) exist in scope".format(
                        side, phrase_str, idx, len(hits)),
                    where=where)
            return hits[idx] + offset_s, None
        if _is_number(near):
            chosen = min(hits, key=lambda t: abs(t - float(near)))
            return chosen + offset_s, None
        return None, Finding(
            "fail", "ambiguous_anchor",
            "{0}.phrase {1!r} matches {2} separate runs in the VO transcript but "
            "carries no occurrence_index or near_s to disambiguate (silent "
            "first-occurrence binding is banned)".format(
                side, phrase_str, len(hits)),
            where=where)

    return hits[0] + offset_s, None


def _layer_for_cue(bidx: _BeatIndex, primitive: str, idx: int) -> Optional[dict]:
    """Pick the layer a cue id resolves to: the idx-th layer of that primitive,
    falling back to the first (a single-cue primitive is the common case)."""
    layers = bidx.layers_by_prim.get(primitive)
    if not layers:
        return None
    if 0 <= idx < len(layers):
        return layers[idx]
    return layers[0]


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    stream = _load_whisper(project_dir)
    storyboards = _load_storyboards(project_dir)
    index, findings = _index_beats(storyboards)

    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            findings.append(Finding(
                "fail", "malformed_cue", "cue is not an object",
                where="cue[{0}]".format(i)))
            continue

        cid = cue.get("id")
        cid_str = str(cid) if isinstance(cid, str) and cid else "cue[{0}]".format(i)
        kind = cue.get("kind")
        kind_str = kind if isinstance(kind, str) else ""

        parsed = _parse_cue_id(cid)
        if parsed is None:
            findings.append(Finding(
                "fail", "unparseable_cue_id",
                "cue id {0!r} is not of the form '<chapter>.<beat>.<prim>.<idx>' — "
                "cannot map it back to a beat to verify its drift".format(cid_str),
                where=cid_str))
            continue
        chapter, beat, primitive = parsed
        idx_field = cid.split(".")[-1]
        cue_idx = int(idx_field) if idx_field.isdigit() else 0

        bidx = index.get((chapter, beat))
        if bidx is None:
            findings.append(Finding(
                "fail", "cue_without_beat",
                "cue {0!r} maps to chapter/beat ({1}, {2}) which is not in any "
                "storyboard — an orphan cue cannot be drift-checked".format(
                    cid_str, chapter, beat),
                where=cid_str))
            continue

        # Anchor source: the layer's cue_anchor if present, else the beat start.
        layer = _layer_for_cue(bidx, primitive, cue_idx)
        anchor: Optional[dict] = None
        side = "start_anchor"
        if isinstance(layer, dict) and isinstance(layer.get("cue_anchor"), dict):
            anchor = layer["cue_anchor"]
            side = "cue_anchor"
        elif isinstance(bidx.start_anchor, dict):
            anchor = bidx.start_anchor

        if not isinstance(anchor, dict):
            findings.append(Finding(
                "fail", "no_resolvable_anchor",
                "cue {0!r} has neither a layer cue_anchor nor a beat start_anchor "
                "to resolve an expected time against".format(cid_str),
                where=cid_str))
            continue

        # drift_budget_ms may only TIGHTEN the default-for-kind, never loosen it.
        budget_s = _budget_for_kind(kind_str)
        if isinstance(layer, dict):
            dbm = layer.get("drift_budget_ms")
            if _is_number(dbm):
                override_s = float(dbm) / 1000.0
                if override_s > budget_s + 1e-9:
                    findings.append(Finding(
                        "fail", "over_loose_drift_budget",
                        "drift_budget_ms={0} ({1:.3f}s) is LOOSER than the "
                        "default-for-kind {2!r} budget of {3:.3f}s — a per-cue "
                        "budget may only tighten, never widen the leash".format(
                            int(dbm), override_s, kind_str or "default", budget_s),
                        where=cid_str))
                    # keep evaluating with the (stricter) default so a real drift
                    # still surfaces alongside the config error.
                else:
                    budget_s = override_s

        # Resolve in MASTER time, scoped to THIS chapter's window so a recurring
        # phrase binds to the right occurrence. full.json is master and the scope
        # restricts to the chapter, so the resolved time IS already master — do NOT
        # re-add vo_offset (re-adding it double-counted the offset and made every cue
        # in any chapter past offset 0 fail).
        scoped = _scope_stream(stream, bidx.vo_offset, bidx.vo_offset + bidx.duration)
        expected_t, err = _resolve_anchor_time(anchor, scoped, cid_str, side)
        if err is not None:
            findings.append(err)
            continue

        start_s = cue.get("start_s")
        if not _is_number(start_s):
            findings.append(Finding(
                "fail", "missing_start_s",
                "cue needs a numeric start_s to verify it against its anchor at "
                "{0:.2f}s (master)".format(expected_t),
                where=cid_str))
            continue

        delta = abs(float(start_s) - expected_t)
        if delta > budget_s:
            findings.append(Finding(
                "fail", "cue_drift_exceeds_budget",
                "start_s {0:.2f}s is {1:.2f}s off the {2} at {3:.2f}s (master) — "
                "kind {4!r} budget {5:.2f}s".format(
                    float(start_s), delta, side, expected_t,
                    kind_str or "default", budget_s),
                where=cid_str))

    return findings


if __name__ == "__main__":
    run_cli("qa_cue_drift", check)
