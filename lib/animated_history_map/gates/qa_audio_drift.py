"""qa_audio_drift — sound cues are anchored to the VO and don't drift.

The whole timeline hangs off the voiceover, and sound is no exception: a
sting, a clock tick, a door thud only lands if it fires on the word it's
reacting to. A cue declares an ``anchor_phrase`` (e.g. "raised a pistol") that
is looked up in the Whisper transcript to convert "this SFX fires when the
narrator says X" into a concrete timestamp; ``t_in`` must sit within a tight,
per-category budget of that resolved time. If the phrase can't be found and the
cue carries no numeric ``fallback_absolute_s``, the compiler has NOTHING to
anchor to and the sound slides off the narration — the documented "NOT_FOUND on
anchor lookup is a HARD FAIL" case (memory drift_audit_all_cue_types).

Per-category drift budget (seconds): sfx tolerates almost nothing (accents must
hit the frame), music/ambient are looser beds that can ease in.

Rule (fail):
  * Every cue with category=="sfx" MUST carry an anchor_phrase, else
    `missing_anchor` (an unanchored accent will drift — not policed only for
    music/ambient beds, which may legitimately have no anchor).
  * For ANY cue that HAS an anchor_phrase: resolve it as a contiguous
    lowercased-token run in the Whisper word stream -> expected_t = the run's
    first word .start. If the phrase is NOT found AND there's no numeric
    fallback_absolute_s -> `anchor_not_found` (NOT_FOUND, hard fail). If not
    found but a numeric fallback_absolute_s is present -> expected_t =
    fallback_absolute_s.
  * Then if abs(t_in - expected_t) > budget[category] -> `drift_exceeds_budget`
    (reports the delta + the budget).
  * music/ambient cues WITHOUT an anchor_phrase are fine (not policed).

Reads:  <project>/artifacts/sound_cuelist.json
        <project>/artifacts/whisper/full.json
Shapes (only the fields this gate reads):
    sound_cuelist = {"cues": [
        {"id", "category" ("music"|"sfx"|"ambient"), "asset",
         "t_in", "t_out", "anchor_phrase"?, "fallback_absolute_s"?}, ...]}
    whisper       = {"words": [{"word": str, "start": float, "end": float}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# Per-category drift budget in seconds. SFX accents must land on the frame;
# music/ambient beds may ease in, so they get a looser leash.
BUDGET = {"sfx": 0.15, "music": 0.5, "ambient": 2.0}

# Trim only edge punctuation; keep internal apostrophes/hyphens so contractions
# ("nation's") and hyphenates ("thirty-five") survive identically on both sides.
# Mirrors qa_drift so a phrase resolves the same way for sound and visuals.
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


def _load_whisper(project_dir: Path) -> List[Tuple[str, float]]:
    """Return [(normalized_token, start_s), ...] in transcript order.

    Tokens that normalize away are dropped, but each surviving token keeps its
    own word's ``start`` so a resolved run's first word maps back to a real
    timestamp (unlike qa_drift, which only needs a yes/no and discards times).
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


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    stream = _load_whisper(project_dir)
    data = load_json(project_dir / "artifacts" / "sound_cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("sound_cuelist.json has no 'cues' array")

    findings: List[Finding] = []
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            findings.append(Finding(
                "fail", "malformed_cue", "cue is not an object",
                where="cue[{0}]".format(i)))
            continue

        cid = str(cue.get("id") or "cue[{0}]".format(i))
        category = (cue.get("category") or "").strip().lower()

        phrase = cue.get("anchor_phrase")
        phrase_str = phrase if isinstance(phrase, str) else ""
        tokens = _tokenize(phrase_str)

        # 1) sfx MUST be anchored. (music/ambient beds may legitimately float.)
        if not tokens:
            if category == "sfx":
                findings.append(Finding(
                    "fail", "missing_anchor",
                    "sfx cue has no anchor_phrase — an unanchored accent will "
                    "drift off the VO",
                    where=cid))
            # No phrase to resolve -> nothing more to police for this cue.
            continue

        # 2) Resolve the phrase to an expected time.
        run_start = _resolve_run_start(tokens, stream)
        fallback = cue.get("fallback_absolute_s")
        has_fallback = _is_number(fallback)

        if run_start is None:
            if not has_fallback:
                findings.append(Finding(
                    "fail", "anchor_not_found",
                    "anchor_phrase {0!r} is NOT FOUND as a contiguous run in the "
                    "VO transcript and has no fallback_absolute_s — the cue has "
                    "nothing to anchor to".format(phrase_str),
                    where=cid))
                continue
            expected_t = float(fallback)
        else:
            expected_t = run_start

        # 3) Budget check on t_in vs the resolved/expected time.
        t_in = cue.get("t_in")
        if not _is_number(t_in):
            findings.append(Finding(
                "fail", "missing_timing",
                "cue needs a numeric t_in to verify it against its anchor at "
                "{0:.2f}s".format(expected_t),
                where=cid))
            continue

        budget = BUDGET.get(category)
        if budget is None:
            findings.append(Finding(
                "fail", "unknown_category",
                "category {0!r} has no drift budget (expected one of "
                "music/sfx/ambient)".format(cue.get("category")),
                where=cid))
            continue

        delta = abs(float(t_in) - expected_t)
        if delta > budget:
            findings.append(Finding(
                "fail", "drift_exceeds_budget",
                "t_in {0:.2f}s is {1:.2f}s off anchor at {2:.2f}s (category {3} "
                "budget {4:.2f}s)".format(
                    float(t_in), delta, expected_t, category, budget),
                where=cid))
    return findings


if __name__ == "__main__":
    run_cli("qa_audio_drift", check)
