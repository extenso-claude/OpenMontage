"""qa_card_timing — every card / lower-third enters on the word it illustrates.

Prevents the "visual-orphan card" bug class: a stat card, center card, or
named-figure lower-third whose entry (``t_in``) drifts off the narration it is
captioning — it pops on screen seconds before (or after) the fact is actually
spoken, so the viewer reads a number with no sentence behind it, or the sentence
passes with no card. The fix is the same timing spine the rest of the pipeline
hangs off: each card declares an ``anchor_phrase`` (a contiguous word-run in the
source VO) which is resolved against the Whisper transcript to a real timestamp,
and ``t_in`` must land within a TREATMENT-SPECIFIC budget of it:

  * stat / center cards (default): keyword-aligned within ±0.5s of the anchor's
    first word, OR sentence-aligned (enter anywhere from the start of the
    sentence that contains the anchor up to the anchor itself — the normal case
    for a card introducing a mid-sentence fact). Exit must trail the last anchor
    word by no more than 2.5s (and not cut more than 1.0s early).
  * named-figure lower-thirds (``treatment`` ending ``_anchored`` /
    ``lower_third*``): a FACE-FIRST allowance — the card may pre-empt the name by
    up to 4.0s (the face is already on screen) and linger up to 4.0s after, as
    long as it has entered by anchor+0.5s. Flagged for human eyeball.
  * hero titles (``treatment`` ``hero_centered`` / ``hero*``): keyword-aligned
    entry, EXTENDED exit hold up to 5.0s for emphasis.

NOT_FOUND on the anchor lookup is a HARD FAIL — a card whose anchor_phrase
cannot be resolved (and carries no numeric ``fallback_absolute_s``) has nothing
to verify against, and silently passing it is exactly how a mistimed card ships.
A mistranscription synonym map (carried over from the Vatican forks) lets known
Whisper mishears resolve instead of false-failing.

Mirrors qa_audio_drift's whisper-resolution helper (flat ``words`` stream,
edge-punctuation-trimmed lowercased tokens, first-match contiguous run). Sentence
boundaries are synthesized from terminal .?! on the raw words, since the
canonical flat transcript has no segment objects.

Reads:  <project>/artifacts/cuelist.json
        <project>/artifacts/whisper/full.json
Shapes (only the fields this gate reads):
    cuelist = {"cues": [
        {"id", "kind", "t_in", "t_out", "treatment"?, "anchor_phrase"?,
         "fallback_absolute_s"?, "_dropped"?}, ...]}
    whisper = {"words": [{"word": str, "start": float, "end": float}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# ---- Treatment-specific drift budgets (seconds). Carried from qa_card_timing_v4.
# Default (stat / center) card.
KEYWORD_TOL = 0.50          # ± window around the anchor's first word
SENTENCE_LEAD_TOL = 0.30    # how far before the sentence start an entry may sit
SENTENCE_LAG_TOL = 0.30     # how far past the anchor a sentence-aligned entry may sit
DEFAULT_EXIT_LATE = 2.50    # exit may trail the last anchor word by this much
DEFAULT_EXIT_EARLY = 1.00   # ...or cut this much early

# Named-figure lower-third: face-first allowance.
LT_EARLY = 4.00             # may pre-empt the name by this much (face already on)
LT_LATE = 4.00              # may linger this long after the last anchor word
LT_ENTER_BY = 0.50          # but must have entered by anchor_start + this

# Hero title: keyword entry, extended exit hold.
HERO_EXIT_LATE = 5.00
HERO_EXIT_EARLY = 0.50

# Whisper matcher tuning (carried from the forks).
_MATCH_WINDOW = 30          # max words scanned forward from a candidate start
_MAX_SKIPS = 4              # non-matching words tolerated inside a match run

# Known Whisper mistranscriptions: target_token -> [heard variants]. Carried
# verbatim from the Vatican forks so a NOT_FOUND from a mishear stays resolvable.
SYNONYMS: Dict[str, List[str]] = {
    "ghislieri": ["guislieri"],
    "guislieri": ["ghislieri"],
    "lentita": ["l", "entita"],
    "mi6": ["emma"],  # whisper hears "MI6" as "Emma I-6"
}

# Trim only edge punctuation; keep internal apostrophes/hyphens (mirrors
# qa_audio_drift / qa_drift so a phrase resolves identically across gates).
_EDGE_PUNCT = ".,!?;:\"'`()[]{}<>—–…“”‘’"
# Raw terminal marks that close a sentence (checked on the *raw* word).
_SENTENCE_END = (".", "!", "?", "…", ".\"", ".'", "?\"", "!\"", ".”", "?”", "!”")

# Cues we time. Card-like by kind, or by a card treatment. Everything else
# (maps, clips, animations, avatars) is policed by its own gate, not this one.
_CARD_KINDS = {"card", "stat_card", "lower_third", "lower-third", "reveal", "chapter_title"}
_CARD_TREATMENT_HINTS = ("card", "lower_third", "lower-third", "hero", "chapter_title", "stat")


def _is_number(v) -> bool:
    # bool is an int subclass; True/False is not a real timestamp.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


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


class _Word:
    __slots__ = ("norm", "start", "end", "ends_sentence")

    def __init__(self, norm: str, start: float, end: float, ends_sentence: bool):
        self.norm = norm
        self.start = start
        self.end = end
        self.ends_sentence = ends_sentence


def _load_whisper(project_dir: Path) -> List[_Word]:
    """Flat normalized word stream, each carrying start/end + a sentence-end flag.

    Mirrors qa_audio_drift._load_whisper (flat ``words`` array, per-word ``start``)
    and additionally keeps ``end`` (for exit drift) and a synthesized
    ``ends_sentence`` flag (terminal .?! on the RAW word) so we can recover
    sentence boundaries without segment objects.
    """
    data = load_json(project_dir / "artifacts" / "whisper" / "full.json")
    words = data.get("words")
    if not isinstance(words, list) or not words:
        raise GateInputError("whisper/full.json has no 'words' array")

    out: List[_Word] = []
    for w in words:
        if not isinstance(w, dict):
            raise GateInputError("whisper/full.json: a word entry is not an object")
        raw = w.get("word")
        if not isinstance(raw, str):
            raise GateInputError("whisper/full.json: a word entry has no string 'word'")
        start = w.get("start")
        end = w.get("end")
        if not _is_number(start):
            raise GateInputError(
                "whisper/full.json: word {0!r} has no numeric 'start'".format(raw))
        if not _is_number(end):
            raise GateInputError(
                "whisper/full.json: word {0!r} has no numeric 'end'".format(raw))
        norm = _norm_token(raw)
        if not norm:
            continue
        ends_sentence = raw.rstrip().endswith(_SENTENCE_END)
        out.append(_Word(norm, float(start), float(end), ends_sentence))

    if not out:
        raise GateInputError(
            "whisper/full.json: no usable word tokens after normalization")
    return out


def _matches(target_tok: str, heard_tok: str) -> bool:
    """Fuzzy single-token match: exact, substring either way, or synonym."""
    if not target_tok or not heard_tok:
        return False
    if target_tok == heard_tok:
        return True
    if target_tok in heard_tok or heard_tok in target_tok:
        return True
    if heard_tok in SYNONYMS.get(target_tok, []):
        return True
    if target_tok in SYNONYMS.get(heard_tok, []):
        return True
    return False


def _resolve_phrase(
    needle: List[str], stream: List[_Word]
) -> Optional[Tuple[int, int]]:
    """Resolve a phrase to (first_match_index, last_match_index) in ``stream``.

    Fuzzy: from each candidate start, walk forward up to _MATCH_WINDOW words,
    tolerating up to _MAX_SKIPS non-matching words inside the run (handles
    mishears, dropped articles). Returns the highest-quality (fewest-skip)
    full match, or None. Carried from the Vatican forks' find_phrase.
    """
    if not needle or len(needle) > len(stream):
        return None

    best: Optional[Tuple[int, int]] = None
    best_quality = -1
    n = len(needle)
    for i in range(len(stream)):
        wi, ti, skipped = i, 0, 0
        first_idx: Optional[int] = None
        last_idx: Optional[int] = None
        while ti < n and wi < len(stream) and (wi - i) < _MATCH_WINDOW:
            if _matches(needle[ti], stream[wi].norm):
                if first_idx is None:
                    first_idx = wi
                last_idx = wi
                ti += 1
                wi += 1
            else:
                skipped += 1
                if skipped > _MAX_SKIPS:
                    break
                wi += 1
        if ti == n and first_idx is not None and last_idx is not None:
            quality = n - skipped
            if quality > best_quality:
                best = (first_idx, last_idx)
                best_quality = quality
    return best


def _sentence_start(anchor_idx: int, stream: List[_Word]) -> float:
    """Start time of the sentence containing ``stream[anchor_idx]``.

    Walk backward to just after the previous sentence terminator (synthesized
    from terminal .?!), and return that word's ``start``.
    """
    j = anchor_idx
    while j > 0 and not stream[j - 1].ends_sentence:
        j -= 1
    return stream[j].start


def _treatment_class(cue: dict) -> str:
    """One of 'lower_third' | 'hero' | 'default' from the cue's treatment/kind."""
    treatment = str(cue.get("treatment") or "").strip().lower()
    kind = str(cue.get("kind") or "").strip().lower()

    if treatment.endswith("_anchored") or treatment.startswith("lower_third") \
            or treatment.startswith("lower-third") or kind in ("lower_third", "lower-third"):
        return "lower_third"
    if treatment.startswith("hero") or treatment == "hero_centered":
        return "hero"
    return "default"


def _is_card_cue(cue: dict) -> bool:
    """True if this cue is a card / lower-third whose entry timing we police."""
    kind = str(cue.get("kind") or "").strip().lower()
    if kind in _CARD_KINDS:
        return True
    treatment = str(cue.get("treatment") or "").strip().lower()
    return any(h in treatment for h in _CARD_TREATMENT_HINTS)


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    stream = _load_whisper(project_dir)
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    findings: List[Finding] = []
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            findings.append(Finding(
                "fail", "malformed_cue", "cue is not an object",
                where="cue[{0}]".format(i)))
            continue

        # Intentionally-scrapped cues are not rendered -> no timing to check.
        if cue.get("_dropped") is True:
            continue
        if not _is_card_cue(cue):
            continue  # not a card/lower-third -> policed by another gate

        cid = str(cue.get("id") or "cue[{0}]".format(i))
        klass = _treatment_class(cue)

        # --- Resolve the anchor (NOT_FOUND is a HARD FAIL).
        phrase = cue.get("anchor_phrase")
        phrase_str = phrase if isinstance(phrase, str) else ""
        tokens = _tokenize(phrase_str)
        if not tokens:
            findings.append(Finding(
                "fail", "missing_anchor",
                "card cue has no anchor_phrase — its entry timing cannot be "
                "verified against the VO",
                where=cid))
            continue

        resolved = _resolve_phrase(tokens, stream)
        fallback = cue.get("fallback_absolute_s")
        has_fallback = _is_number(fallback)

        if resolved is None:
            if not has_fallback:
                findings.append(Finding(
                    "fail", "anchor_not_found",
                    "anchor_phrase {0!r} is NOT FOUND as a run in the VO "
                    "transcript and has no fallback_absolute_s — the card has "
                    "nothing to time against (NOT_FOUND is a hard fail)".format(
                        phrase_str),
                    where=cid))
                continue
            anchor_start = float(fallback)
            anchor_end = float(fallback)
            sentence_start = float(fallback)
        else:
            first_idx, last_idx = resolved
            anchor_start = stream[first_idx].start
            anchor_end = stream[last_idx].end
            sentence_start = _sentence_start(first_idx, stream)

        # --- Need numeric t_in / t_out to verify.
        t_in = cue.get("t_in")
        t_out = cue.get("t_out")
        if not _is_number(t_in):
            findings.append(Finding(
                "fail", "missing_timing",
                "card needs a numeric t_in to verify against its anchor at "
                "{0:.2f}s".format(anchor_start),
                where=cid))
            continue
        if not _is_number(t_out):
            findings.append(Finding(
                "fail", "missing_timing",
                "card needs a numeric t_out to verify its exit hold",
                where=cid))
            continue
        t_in = float(t_in)
        t_out = float(t_out)

        entry_drift = t_in - anchor_start
        exit_drift = t_out - anchor_end

        # --- Treatment-specific budget check.
        if klass == "lower_third":
            ok_early = (anchor_start - t_in) <= LT_EARLY
            ok_enter = t_in <= anchor_start + LT_ENTER_BY
            ok_late = exit_drift <= LT_LATE
            if not (ok_early and ok_enter):
                findings.append(Finding(
                    "fail", "entry_drift",
                    "lower-third entry {0:+.2f}s off the name at {1:.2f}s "
                    "(face-first allowance is {2:.1f}s early .. +{3:.1f}s "
                    "enter-by)".format(
                        entry_drift, anchor_start, LT_EARLY, LT_ENTER_BY),
                    where=cid))
            elif not ok_late:
                findings.append(Finding(
                    "fail", "exit_drift",
                    "lower-third lingers {0:+.2f}s past the last anchor word "
                    "(budget {1:.1f}s)".format(exit_drift, LT_LATE),
                    where=cid))

        elif klass == "hero":
            keyword_aligned = abs(entry_drift) <= KEYWORD_TOL
            if not keyword_aligned:
                findings.append(Finding(
                    "fail", "entry_drift",
                    "hero title entry {0:+.2f}s off the keyword at {1:.2f}s "
                    "(budget ±{2:.2f}s)".format(
                        entry_drift, anchor_start, KEYWORD_TOL),
                    where=cid))
            elif exit_drift > HERO_EXIT_LATE or exit_drift < -HERO_EXIT_EARLY:
                findings.append(Finding(
                    "fail", "exit_drift",
                    "hero title exit {0:+.2f}s off the last anchor word "
                    "(hold budget -{1:.1f}s .. +{2:.1f}s)".format(
                        exit_drift, HERO_EXIT_EARLY, HERO_EXIT_LATE),
                    where=cid))

        else:  # default stat / center card
            keyword_aligned = abs(entry_drift) <= KEYWORD_TOL
            sentence_aligned = (
                (sentence_start - SENTENCE_LEAD_TOL) <= t_in
                <= (anchor_start + SENTENCE_LAG_TOL)
            )
            if not (keyword_aligned or sentence_aligned):
                findings.append(Finding(
                    "fail", "entry_drift",
                    "card entry {0:+.2f}s off the anchor at {1:.2f}s and not "
                    "sentence-aligned (sentence starts {2:.2f}s; need keyword "
                    "±{3:.2f}s or entry within the sentence)".format(
                        entry_drift, anchor_start, sentence_start, KEYWORD_TOL),
                    where=cid))
            elif exit_drift > DEFAULT_EXIT_LATE or exit_drift < -DEFAULT_EXIT_EARLY:
                findings.append(Finding(
                    "fail", "exit_drift",
                    "card exit {0:+.2f}s off the last anchor word "
                    "(budget -{1:.1f}s .. +{2:.1f}s)".format(
                        exit_drift, DEFAULT_EXIT_EARLY, DEFAULT_EXIT_LATE),
                    where=cid))

    return findings


if __name__ == "__main__":
    run_cli("qa_card_timing", check)
