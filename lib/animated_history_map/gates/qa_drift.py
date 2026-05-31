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

Rule (fail): for each beat, for BOTH start_anchor and end_anchor —
    the anchor.phrase (lowercased, whitespace-split into tokens) must appear as
    a CONTIGUOUS run in the Whisper word stream (compared against lowercased
    word tokens) OR the anchor must carry a numeric `fallback_absolute_s`.
    A phrase that is NOT found AND has no fallback = FAIL (NOT_FOUND), reporting
    the chapter / beat / anchor side + the missing phrase.

To compare fairly, both the phrase tokens and the Whisper words are normalized
the same way: lowercased and stripped of leading/trailing punctuation (so
"Washington," in the transcript matches "washington" in the phrase). An empty
anchor (no phrase tokens after normalization) cannot be resolved and is a FAIL.

Reads:  <project>/artifacts/storyboard/*.json   (one storyboard per chapter)
        <project>/artifacts/whisper/full.json    (the VO transcript)
Shapes (only the fields this gate reads):
    storyboard = {"chapter_id", "phases": [
                    {"phase_id", "beats": [
                        {"beat_id",
                         "start_anchor": {"phrase", "fallback_absolute_s"?},
                         "end_anchor":   {"phrase", "fallback_absolute_s"?}}, ...]}, ...]}
    whisper    = {"words": [{"word": str, "start": float, "end": float}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

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


def _load_whisper_words(project_dir: Path) -> List[str]:
    data = load_json(project_dir / "artifacts" / "whisper" / "full.json")
    words = data.get("words")
    if not isinstance(words, list) or not words:
        raise GateInputError("whisper/full.json has no 'words' array")
    tokens: List[str] = []
    for w in words:
        if not isinstance(w, dict):
            raise GateInputError("whisper/full.json: a word entry is not an object")
        raw = w.get("word")
        if not isinstance(raw, str):
            raise GateInputError("whisper/full.json: a word entry has no string 'word'")
        t = _norm_token(raw)
        if t:
            tokens.append(t)
    if not tokens:
        raise GateInputError("whisper/full.json: no usable word tokens after normalization")
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


def _check_anchor(
    anchor: Optional[dict],
    side: str,
    where: str,
    words: List[str],
) -> List[Finding]:
    """One anchor (start/end) of one beat. Empty/missing -> FAIL; unresolved -> FAIL."""
    if not isinstance(anchor, dict):
        return [Finding(
            "fail", "missing_anchor",
            "{0} is missing or not an object; nothing to resolve against the VO".format(side),
            where=where,
        )]

    has_fallback = _is_number(anchor.get("fallback_absolute_s"))
    phrase = anchor.get("phrase")
    phrase_str = phrase if isinstance(phrase, str) else ""
    tokens = _tokenize(phrase_str)

    if not tokens:
        # No phrase to look up. A numeric fallback still pins the beat to a time.
        if has_fallback:
            return []
        return [Finding(
            "fail", "empty_anchor_phrase",
            "{0} has no usable phrase and no numeric fallback_absolute_s — "
            "the beat cannot be anchored to the VO".format(side),
            where=where,
        )]

    if _contiguous_run(tokens, words):
        return []  # resolved against the transcript

    if has_fallback:
        return []  # not in the VO, but a hard fallback timestamp is provided

    return [Finding(
        "fail", "anchor_not_found",
        "{0}.phrase {1!r} is NOT FOUND as a contiguous run in the VO transcript "
        "and has no fallback_absolute_s (drift: the beat has nothing to anchor "
        "to)".format(side, phrase_str),
        where=where,
    )]


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    words = _load_whisper_words(project_dir)
    storyboards = _load_storyboards(project_dir)

    findings: List[Finding] = []
    for name, data in storyboards:
        chap = _chapter_label(name, data)
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
                    beat.get("start_anchor"), "start_anchor", base, words))
                findings.extend(_check_anchor(
                    beat.get("end_anchor"), "end_anchor", base, words))
    return findings


if __name__ == "__main__":
    run_cli("qa_drift", check)
