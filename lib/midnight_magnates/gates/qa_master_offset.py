"""qa_master_offset — a chapter's VO must sit in the master where it claims to.

Every cue in a chapter is resolved against the MASTER VO transcript
(artifacts/whisper/full.json, absolute seconds over the whole video), and the
chapter's `vo_start_offset_in_master_s` declares where that chapter's VO begins on
the master clock. The compiler uses the offset to (a) scope each chapter's phrase
resolution to its master window and (b) convert master times to chapter-local clip
times for the per-chapter HTML. If the offset is wrong, the chapter's per-chapter
render is mistimed and its scope window selects the wrong words — the documented
"whole-chapter slide" hole. qa_drift / qa_cue_drift prove each cue lands on its WORD;
this gate proves the chapter as a BLOCK sits where it claims.

Ground truth, from the single master full.json (no per-chapter transcripts are
produced by this pipeline):

  measured = the first VO word at/after the declared offset.
  A correct offset lands ON the chapter's first word, so |measured - declared| must
  be <= TOL_S. (Catches an offset set too EARLY: a silence at the window start makes
  measured >> declared.)

  A non-opening chapter's offset must sit at a chapter BOUNDARY — the inter-chapter
  silence. So for declared > GAP_MIN_S there must be a gap of >= GAP_MIN_S between the
  word just before `measured` and `measured` itself. (Catches an offset slid too LATE
  into the middle of a chapter, where measured ~= declared but no boundary precedes
  it.) The opening chapter (declared ~ 0) is exempt — it has no preceding chapter.

Rule:
  * BLOCKING fail — for each chapter that DECLARES vo_start_offset_in_master_s:
      - master_offset_mismatch : |measured - declared| > TOL_S (the offset lands in a
                                 silence/gap, or the whole chapter is slid off the master)
      - offset_past_vo         : declared is after the last VO word
  * ADVISORY warn (NEVER blocks):
      - offset_mid_utterance   : declared > GAP_MIN_S but no >= GAP_MIN_S silence
                                 precedes the chapter's first word. For a section-assembled
                                 VO (separate recordings) this flags a possibly-slid offset;
                                 for a single continuous read chaptered at sentence
                                 boundaries it is EXPECTED and harmless (a contiguous chapter
                                 is legal) — so it warns, never fails. The blocking
                                 master_offset_mismatch check already verified the offset
                                 lands on a real word.
  * A chapter that does not declare the offset is not policed (the field is optional).

A gate that cannot run must never silently pass:
  * no artifacts/storyboard dir / no *.json in it     -> GateInputError (blocking)
  * a chapter DECLARES an offset but full.json is
    missing / has no usable words                      -> GateInputError

Reads:  <project>/artifacts/storyboard/*.json     (one storyboard per chapter)
        <project>/artifacts/whisper/full.json       (the MASTER VO transcript)
Shapes (only the fields this gate reads):
    storyboard = {"chapter_id"?, "vo_start_offset_in_master_s"?: number, ...}
    whisper    = {"words": [{"word": str, "start": float, "end": float}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# Max gap (s) between the declared chapter offset and the measured first-word start.
# 0.20s ~= 5 frames at 24fps — tight enough that a real slide trips, loose enough to
# absorb a few ms of transcriber boundary slop on the first word.
TOL_S = 0.20

# A genuine inter-chapter boundary in the assembled master VO shows as at least this
# much silence (the sections are separate recordings). An offset that lands less than
# this after the previous word is pointing mid-chapter, not at a boundary.
GAP_MIN_S = 1.0

# Trim only edge punctuation; keep internal apostrophes/hyphens. Mirrors qa_drift /
# qa_cue_drift so the first usable word is identified the same everywhere.
_EDGE_PUNCT = ".,!?;:\"'`()[]{}<>—–…“”‘’"


def _is_number(v) -> bool:
    # bool is an int subclass; True/False is not a real timestamp/offset.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _norm_token(tok: str) -> str:
    """Lowercase and strip leading/trailing punctuation. May return ''."""
    return tok.lower().strip().strip(_EDGE_PUNCT)


def _load_master_word_starts(path: Path) -> List[float]:
    """Ascending list of usable spoken-word start times (the master VO clock).

    Skips entries that normalize away (stray punctuation tokens). Raises
    GateInputError on a missing/malformed transcript or one with no usable word —
    we were asked to verify a declared offset and cannot fake an answer.
    """
    data = load_json(path)  # GateInputError on missing / invalid JSON
    words = data.get("words")
    if not isinstance(words, list) or not words:
        raise GateInputError(f"{path}: has no 'words' array")
    starts: List[float] = []
    for w in words:
        if not isinstance(w, dict):
            raise GateInputError(f"{path}: a word entry is not an object")
        raw = w.get("word")
        start = w.get("start")
        if not isinstance(raw, str):
            raise GateInputError(f"{path}: a word entry has no string 'word'")
        if not _is_number(start):
            raise GateInputError(f"{path}: word {raw!r} has no numeric 'start'")
        if _norm_token(raw):
            starts.append(float(start))
    if not starts:
        raise GateInputError(f"{path}: no usable spoken word after normalization")
    starts.sort()
    return starts


def _load_storyboards(project_dir: Path) -> List[Tuple[str, dict]]:
    """[(source_name, storyboard_dict), ...]. Raises if the dir/files are missing."""
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        raise GateInputError(
            f"required input not found: {sb_dir} (no storyboard directory)"
        )
    paths = sorted(sb_dir.glob("*.json"))
    if not paths:
        raise GateInputError(
            f"no storyboard files in {sb_dir} (expected one *.json per chapter)"
        )
    out: List[Tuple[str, dict]] = []
    for p in paths:
        data = load_json(p)  # GateInputError on unreadable / invalid JSON
        if not isinstance(data, dict):
            raise GateInputError(f"{p}: storyboard root is not an object")
        out.append((p.name, data))
    return out


def _chapter_label(name: str, data: dict) -> str:
    cid = data.get("chapter_id")
    return cid if isinstance(cid, str) and cid.strip() else name


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    storyboards = _load_storyboards(project_dir)
    full = project_dir / "artifacts" / "whisper" / "full.json"

    starts: Optional[List[float]] = None  # lazily loaded only if a chapter declares
    findings: List[Finding] = []
    for name, data in storyboards:
        chap = _chapter_label(name, data)

        declared = data.get("vo_start_offset_in_master_s")
        if declared is None:
            continue  # optional field absent -> nothing to verify
        if not _is_number(declared):
            findings.append(Finding(
                "fail", "offset_not_numeric",
                f"vo_start_offset_in_master_s is present but not a number "
                f"({declared!r}); it cannot be checked against the VO",
                where=chap))
            continue
        declared = float(declared)

        if starts is None:
            # GateInputError here (missing/empty master transcript) is blocking: a
            # declared offset with no ground truth must not slip through as a pass.
            starts = _load_master_word_starts(full)

        # measured = the first VO word at/after the declared offset.
        cand = [s for s in starts if s >= declared - TOL_S]
        if not cand:
            findings.append(Finding(
                "fail", "offset_past_vo",
                f"declared vo_start_offset_in_master_s {declared:.2f}s is after the "
                f"last VO word at {starts[-1]:.2f}s — the chapter has no VO at its "
                f"declared position",
                where=chap))
            continue
        measured = cand[0]

        if abs(measured - declared) > TOL_S:
            findings.append(Finding(
                "fail", "master_offset_mismatch",
                f"declared vo_start_offset_in_master_s {declared:.2f}s but the "
                f"chapter's first master VO word is at {measured:.2f}s "
                f"({abs(measured - declared):.2f}s gap > {TOL_S:.2f}s) — the offset is "
                f"set too early (a silence opens the window) or the whole chapter is "
                f"slid against the master and every cue in it drifts by this constant",
                where=chap))
            continue

        # A non-opening chapter's offset must land at a chapter boundary: a real
        # inter-chapter silence precedes the chapter's first word. Without it, the
        # offset points into the middle of a chapter (measured ~= declared but no
        # boundary), i.e. slid too LATE.
        if declared > GAP_MIN_S:
            before = [s for s in starts if s < measured - 1e-6]
            if before and (measured - before[-1]) < GAP_MIN_S:
                findings.append(Finding(
                    "warn", "offset_mid_utterance",
                    f"declared vo_start_offset_in_master_s {declared:.2f}s lands "
                    f"{measured - before[-1]:.2f}s after the previous master word "
                    f"({before[-1]:.2f}s), with no >= {GAP_MIN_S:.2f}s inter-chapter "
                    f"silence — ADVISORY: if the VO is section-assembled this may be a "
                    f"slid offset; if it is one continuous read chaptered at sentence "
                    f"boundaries it is expected (the offset already verified to land on a "
                    f"real word). Does not block.",
                    where=chap))

    return findings


if __name__ == "__main__":
    run_cli("qa_master_offset", check)
