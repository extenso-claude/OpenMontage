"""qa_drift — the drift guarantee. Every beat anchor must resolve to the VO.

The entire animated-history-map timeline is hung off the voiceover: each beat
declares a `start_anchor` and an `end_anchor` whose `phrase` is looked up in the
Whisper transcript to convert "this beat fires when the narrator says X" into a
concrete timestamp. If a phrase can't be found and the beat carries no numeric
`fallback_absolute_s`, the compiler has NOTHING to anchor to — it would silently
slide the beat to t=0 (or wherever), and the visual drifts off the narration.
That is the documented "anchor NOT_FOUND" bug, and it is a HARD FAIL here
(see memory drift_audit_all_cue_types: "NOT_FOUND on anchor lookup is a HARD
FAIL"). This gate is the load-bearing check that no anchor can sneak through
unresolved.

This MM build tightens the AHM original on two axes:

1. NO FALLBACK LOOPHOLE WHEN VO EXISTS. The AHM gate let *any* anchor pass the
   moment it carried a numeric `fallback_absolute_s` — even on a real VO run,
   where a hand-typed time silently overrides what the narrator actually says
   (the exact drift this gate is supposed to forbid). NEW: when Whisper words
   are present (a real VO run), an anchor that resolves ONLY via fallback (no
   contiguous Whisper-word match in its chapter) is a FAIL — UNLESS it carries
   an explicit `fallback_reason` (schema enum `no_vo_yet_structural_test`), which
   downgrades it to a non-blocking WARN (a deliberately-marked structural stub).
   When NO Whisper words exist at all (a pure structural build, VO not recorded
   yet), the old lenient behavior is kept: a numeric fallback alone pins the beat
   to a time and passes.

2. PER-CHAPTER SCOPING. The AHM gate matched every phrase against the WHOLE
   video's word stream, so a phrase spoken in chapter 7 would "resolve" a beat in
   chapter 1. NEW: each chapter's phrases are matched only against the Whisper
   words that fall inside that chapter's master-time window
   `[vo_start_offset_in_master_s, vo_start_offset_in_master_s + duration_s)`
   (offset defaults to 0; a missing duration widens the window to the rest of the
   transcript so a malformed storyboard never manufactures a failure). A phrase
   must land WITHIN its own chapter to count as resolved.

Rule (fail), per beat, for BOTH start_anchor and end_anchor:
    the anchor.phrase (lowercased, whitespace-split into tokens) must appear as a
    CONTIGUOUS run in the chapter-scoped Whisper word stream (compared against
    lowercased word tokens). If it is NOT found:
      * VO present, no `fallback_reason`            -> FAIL
      * VO present, explicit `fallback_reason`      -> WARN (non-blocking)
      * VO absent (structural), numeric fallback    -> PASS (lenient)
      * VO absent (structural), no fallback         -> FAIL (nothing to anchor)

To compare fairly, both the phrase tokens and the Whisper words are normalized
the same way: lowercased and stripped of leading/trailing punctuation (so
"Washington," in the transcript matches "washington" in the phrase). An empty
anchor (no phrase tokens after normalization) cannot be resolved and follows the
same fallback rules above.

Reads:  <project>/artifacts/storyboard/*.json   (one storyboard per chapter)
        <project>/artifacts/whisper/full.json    (the VO transcript; may be
                                                   absent/empty in a structural
                                                   build)
Shapes (only the fields this gate reads):
    storyboard = {"chapter_id", "duration_s", "vo_start_offset_in_master_s"?,
                  "phases": [
                    {"phase_id", "beats": [
                        {"beat_id",
                         "start_anchor": {"phrase",
                                          "fallback_absolute_s"?,
                                          "fallback_reason"?},
                         "end_anchor":   {...}}, ...]}, ...]}
    whisper    = {"words": [{"word": str, "start": float, "end": float}, ...]}
"""

from __future__ import annotations

import math
from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# Schema-sanctioned reason that legalizes a fallback while a VO already exists
# (midnight_magnates_storyboard.schema.json anchor.fallback_reason enum). Its
# presence downgrades an otherwise-FAIL fallback-only anchor to a WARN.
_FALLBACK_REASONS = frozenset({"no_vo_yet_structural_test"})

# Trim only edge punctuation; keep internal apostrophes/hyphens so contractions
# ("nation's") and hyphenates ("thirty-five") survive identically on both sides.
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
    # bool is an int subclass; a True/False fallback is not a real timestamp.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _contiguous_run(needle: List[str], haystack: List[str]) -> bool:
    """True iff `needle` appears as a contiguous sublist of `haystack`."""
    n, h = len(needle), len(haystack)
    if n == 0 or n > h:
        return False
    first = needle[0]
    for i in range(h - n + 1):
        if haystack[i] != first:
            continue
        if haystack[i:i + n] == needle:
            return True
    return False


def _load_whisper_words(project_dir: Path) -> List[Tuple[str, float]]:
    """Load (normalized_token, start_seconds) pairs in transcript order.

    Returns ``[]`` (NOT an error) when the transcript is absent or carries no
    'words' — that is a pure structural build (VO not recorded yet), and the
    caller switches to the lenient no-VO rules. A transcript that IS present but
    structurally corrupt (a word entry that is not an object, or with no string
    'word') is still a hard input error: that is real damage, not "no VO".

    A word with a missing / non-numeric 'start' is kept but pinned to 0.0 so it
    still participates in matching; the timestamp only governs which chapter
    window it falls into, and 0.0 is the safe "earliest" default.
    """
    path = project_dir / "artifacts" / "whisper" / "full.json"
    if not path.exists():
        return []  # structural build: no VO transcript yet
    data = load_json(path)
    words = data.get("words")
    if not isinstance(words, list) or not words:
        return []  # transcript present but empty -> treat as no-VO (structural)
    tokens: List[Tuple[str, float]] = []
    for w in words:
        if not isinstance(w, dict):
            raise GateInputError("whisper/full.json: a word entry is not an object")
        raw = w.get("word")
        if not isinstance(raw, str):
            raise GateInputError("whisper/full.json: a word entry has no string 'word'")
        t = _norm_token(raw)
        if t:
            start = w.get("start")
            start_s = float(start) if _is_number(start) else 0.0
            tokens.append((t, start_s))
    # All entries normalized away (e.g. all punctuation) -> no usable VO words.
    return tokens


def _load_storyboards(project_dir: Path) -> List[tuple]:
    """Return [(source_name, storyboard_dict), ...]. Raises if none readable."""
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
    out: List[tuple] = []
    for p in paths:
        data = load_json(p)  # GateInputError on unreadable/invalid JSON
        if not isinstance(data, dict):
            raise GateInputError(str(p) + ": storyboard root is not an object")
        out.append((p.name, data))
    return out


def _chapter_label(name: str, data: dict) -> str:
    cid = data.get("chapter_id")
    return str(cid) if isinstance(cid, str) and cid.strip() else name


def _chapter_window(data: dict) -> Tuple[float, float]:
    """Master-time [lo, hi) this chapter's anchors must resolve inside.

    lo = vo_start_offset_in_master_s (default 0.0).
    hi = lo + duration_s, or +inf if duration_s is missing/non-numeric (a
         malformed storyboard widens to the rest of the transcript rather than
         manufacturing a spurious out-of-window failure).
    """
    off = data.get("vo_start_offset_in_master_s")
    lo = float(off) if _is_number(off) else 0.0
    dur = data.get("duration_s")
    hi = lo + float(dur) if _is_number(dur) else math.inf
    return lo, hi


def _scope_words(words: List[Tuple[str, float]], lo: float, hi: float) -> List[str]:
    """Tokens whose start time falls in [lo, hi), in transcript order."""
    return [tok for (tok, s) in words if lo <= s < hi]


def _fallback_reason(anchor: dict):
    """Return the anchor's fallback_reason iff it is a recognized enum value."""
    fr = anchor.get("fallback_reason")
    return fr if isinstance(fr, str) and fr in _FALLBACK_REASONS else None


def _unresolved_finding(
    anchor: dict,
    side: str,
    where: str,
    detail: str,
    vo_present: bool,
) -> List[Finding]:
    """An anchor that could not be matched to a chapter-scoped word. Resolve its
    severity by the fallback rules:

      * VO present + explicit fallback_reason -> WARN (deliberate structural stub)
      * VO present + no fallback_reason       -> FAIL (the closed loophole)
      * VO absent  + numeric fallback         -> PASS (lenient structural build)
      * VO absent  + no fallback              -> FAIL (nothing to anchor at all)
    """
    has_fallback = _is_number(anchor.get("fallback_absolute_s"))
    reason = _fallback_reason(anchor)

    if vo_present:
        if has_fallback and reason is not None:
            return [Finding(
                "warn", "anchor_fallback_structural",
                "{0} {1}; it resolves only via fallback_absolute_s but is marked "
                "fallback_reason={2!r}, so it is allowed as a structural stub "
                "(must be re-anchored to a spoken word before final render)".format(
                    side, detail, reason),
                where=where,
            )]
        if has_fallback:
            return [Finding(
                "fail", "anchor_fallback_without_reason",
                "{0} {1}; it resolves ONLY via fallback_absolute_s with NO "
                "fallback_reason while a real VO transcript exists — a hand-typed "
                "time silently overrides the narration (drift). Anchor it to a "
                "spoken phrase, or mark fallback_reason for a structural "
                "stub".format(side, detail),
                where=where,
            )]
        return [Finding(
            "fail", "anchor_not_found",
            "{0} {1} and has no fallback_absolute_s (drift: the beat has nothing "
            "to anchor to)".format(side, detail),
            where=where,
        )]

    # No VO transcript at all -> structural build. A numeric fallback (with or
    # without reason) legitimately pins the time; only a beat with neither a
    # resolvable phrase nor a fallback has nothing to anchor to.
    if has_fallback:
        return []
    return [Finding(
        "fail", "anchor_unanchored_structural",
        "{0} {1} and carries no fallback_absolute_s; with no VO transcript yet "
        "there is nothing to anchor the beat to (a structural build must pin a "
        "time via fallback_absolute_s)".format(side, detail),
        where=where,
    )]


def _check_anchor(
    anchor: Optional[dict],
    side: str,
    where: str,
    words: List[str],
    vo_present: bool,
) -> List[Finding]:
    """One anchor (start/end) of one beat, matched against the chapter-scoped
    word stream ``words``. Missing anchor -> FAIL; otherwise severity follows the
    fallback rules in `_unresolved_finding`."""
    if not isinstance(anchor, dict):
        return [Finding(
            "fail", "missing_anchor",
            "{0} is missing or not an object; nothing to resolve against the VO".format(side),
            where=where,
        )]

    phrase = anchor.get("phrase")
    phrase_str = phrase if isinstance(phrase, str) else ""
    tokens = _tokenize(phrase_str)

    if not tokens:
        return _unresolved_finding(
            anchor, side, where,
            "has no usable phrase", vo_present)

    if vo_present and _contiguous_run(tokens, words):
        return []  # resolved against this chapter's transcript window

    detail = (
        "phrase {0!r} is NOT FOUND as a contiguous run in this chapter's VO "
        "window".format(phrase_str)
    )
    return _unresolved_finding(anchor, side, where, detail, vo_present)


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    all_words = _load_whisper_words(project_dir)  # [(token, start_s), ...]
    vo_present = bool(all_words)
    storyboards = _load_storyboards(project_dir)

    findings: List[Finding] = []
    for name, data in storyboards:
        chap = _chapter_label(name, data)
        # Scope the word stream to THIS chapter's master-time window so a phrase
        # only counts when spoken inside its own chapter, never elsewhere.
        lo, hi = _chapter_window(data)
        words = _scope_words(all_words, lo, hi) if vo_present else []
        phases = data.get("phases")
        if not isinstance(phases, list):
            findings.append(Finding(
                "fail", "no_phases",
                "storyboard has no 'phases' array; no beats to anchor",
                where=chap,
            ))
            continue
        for pi, phase in enumerate(phases):
            if not isinstance(phase, dict):
                findings.append(Finding(
                    "fail", "malformed_phase", "phase is not an object",
                    where="{0} :: phase[{1}]".format(chap, pi)))
                continue
            phase_id = str(phase.get("phase_id") or "phase[{0}]".format(pi))
            beats = phase.get("beats")
            if not isinstance(beats, list):
                # A phase with no beats array carries nothing to anchor; skip
                # (schema allows an empty/absent beats list to be a no-op here).
                continue
            for bi, beat in enumerate(beats):
                if not isinstance(beat, dict):
                    findings.append(Finding(
                        "fail", "malformed_beat", "beat is not an object",
                        where="{0} :: {1} :: beat[{2}]".format(chap, phase_id, bi)))
                    continue
                beat_id = str(beat.get("beat_id") or "beat[{0}]".format(bi))
                base = "{0} :: {1} :: {2}".format(chap, phase_id, beat_id)
                findings.extend(_check_anchor(
                    beat.get("start_anchor"), "start_anchor", base, words,
                    vo_present))
                findings.extend(_check_anchor(
                    beat.get("end_anchor"), "end_anchor", base, words,
                    vo_present))
    return findings


if __name__ == "__main__":
    run_cli("qa_drift", check)
