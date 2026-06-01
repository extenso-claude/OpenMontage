"""qa_clip_no_extra_chyron — a frame-wrapped clip already IS the chyron.

Catches the documented "stacked lower-third over a frame-wrapped clip" bug
(memory clip_frame_no_extra_chyron; skill skills/core/clip-treatments.md
"NO-EXTRA-CHYRON rule, LOCKED 2026-05-21"). The 2026-05-21 Vatican Entity review
found 4 clip cues with separate "ARCHIVE FOOTAGE" lower-thirds stacked on top of
the dossier / surveillance / tv-vintage frame wrap — redundant with the frame's
built-in caption slot and read as cluttered. The approved frame wrapping a clip
ALREADY carries the year / location / context, so no separate lower-third or card
may sit on top of a frame-wrapped clip in the same window.

Rule (fail — compose-blocking):
    Identify CLIP cues   (kind == "clip"  OR id starts with "clip_") and
             CHYRON cues (kind in {lower_third, card, photo_card, stat_card,
                          chapter_title} OR id starts with "lt_" / "card_").
    For every (clip, chyron) pair whose time windows overlap:
      * if BOTH carry a bbox and the boxes intersect          -> fail, OR
      * if the chyron has NO bbox but is a full-width lower-third
        (kind == "lower_third" or id starts with "lt_"), it spans the bottom
        band across the clip's whole window and necessarily lands on the clip
                                                                 -> fail.
    A chyron whose own window doesn't touch the clip, or a non-full-width
    bbox-less card that can't be proven to collide, is left alone — the gate
    flags only provable stacks, never guesses.

Time windows use t_in/t_out (canonical overlay cuelist schema), falling back to
start_s/end_s if a cue carries the older field names.

Reads:  <project>/artifacts/cuelist.json
Shape (only the fields this gate reads):
    {"cues": [{"id", "kind", "t_in", "t_out",
               "bbox"?: {"x","y","w","h"}}, ...]}
        bbox is pixel geometry in a 1920x1080 canvas, top-left origin.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

EPSILON = 1e-6

# A chyron cue is any of these kinds OR an id with one of the prefixes below.
_CHYRON_KINDS = {"lower_third", "card", "photo_card", "stat_card", "chapter_title"}
_CHYRON_ID_PREFIXES = ("lt_", "card_")

# A clip cue: kind=="clip" OR an id with this prefix.
_CLIP_ID_PREFIX = "clip_"

# A bbox-less chyron only provably collides if it's a full-width lower-third —
# those render as a bottom band spanning the frame, so they cover any clip
# on screen during their window even without explicit geometry.
_FULLWIDTH_LT_ID_PREFIX = "lt_"


def _num(value) -> Optional[float]:
    """Return value as float if it is a real number, else None."""
    if isinstance(value, bool):  # bool is an int subclass — reject it explicitly
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _kind(cue: dict) -> str:
    return str(cue.get("kind", "")).strip().lower()


def _cid(cue: dict, i: int) -> str:
    cid = cue.get("id")
    return str(cid) if isinstance(cid, str) and cid else "#{0}".format(i)


def _is_clip(cue: dict, cid: str) -> bool:
    return _kind(cue) == "clip" or cid.startswith(_CLIP_ID_PREFIX)


def _is_chyron(cue: dict, cid: str) -> bool:
    return _kind(cue) in _CHYRON_KINDS or cid.startswith(_CHYRON_ID_PREFIXES)


def _is_fullwidth_lower_third(cue: dict, cid: str) -> bool:
    """A lower-third with no geometry => bottom band across the whole frame."""
    return _kind(cue) == "lower_third" or cid.startswith(_FULLWIDTH_LT_ID_PREFIX)


def _window(cue: dict) -> Optional[Tuple[float, float]]:
    """(start, end) seconds from t_in/t_out, falling back to start_s/end_s.

    Returns the pair lo<=hi if both bounds are real numbers, else None (a cue
    with no usable window can't be proven to overlap anything, so it's skipped).
    """
    t0 = _num(cue.get("t_in"))
    t1 = _num(cue.get("t_out"))
    if t0 is None:
        t0 = _num(cue.get("start_s"))
    if t1 is None:
        t1 = _num(cue.get("end_s"))
    if t0 is None or t1 is None:
        return None
    return (t0, t1) if t0 <= t1 else (t1, t0)


def _windows_overlap(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
    """True iff [a0,a1] and [b0,b1] share an open span.

    Touching end-to-end (one ends exactly as the other starts) is NOT an overlap —
    the cues are never on screen together.
    """
    return (a[0] < b[1] - EPSILON) and (b[0] < a[1] - EPSILON)


def _bbox(cue: dict) -> Optional[Tuple[float, float, float, float]]:
    """Return (x, y, w, h) as floats if the cue carries a usable bbox, else None."""
    box = cue.get("bbox")
    if not isinstance(box, dict):
        return None
    x, y, w, h = (_num(box.get(k)) for k in ("x", "y", "w", "h"))
    if x is None or y is None or w is None or h is None:
        return None
    if w <= 0 or h <= 0:
        return None  # degenerate box covers no pixels -> cannot collide
    return (x, y, w, h)


def _rects_intersect(
    r1: Tuple[float, float, float, float],
    r2: Tuple[float, float, float, float],
) -> bool:
    """True iff two axis-aligned rects (x, y, w, h, top-left origin) overlap.

    Edge-touching (shared border, zero overlap area) is NOT a collision.
    """
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    if x1 + w1 <= x2 + EPSILON or x2 + w2 <= x1 + EPSILON:
        return False
    if y1 + h1 <= y2 + EPSILON or y2 + h2 <= y1 + EPSILON:
        return False
    return True


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    # Pre-extract once, then pair clips against chyrons.
    clips = []   # (cid, window, bbox)
    chyrons = []  # (cid, cue, window, bbox)
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError("cuelist.json cue #{0} is not an object".format(i))
        cid = _cid(cue, i)
        win = _window(cue)
        box = _bbox(cue)
        # A cue could theoretically match both predicates; a clip classification
        # wins (it's the wrapped media, never the overlay stacked on top).
        if _is_clip(cue, cid):
            clips.append((cid, win, box))
        elif _is_chyron(cue, cid):
            chyrons.append((cid, cue, win, box))

    findings: List[Finding] = []
    for clip_id, clip_win, clip_box in clips:
        if clip_win is None:
            continue  # no clip window -> can't prove any overlap
        for chy_id, chy_cue, chy_win, chy_box in chyrons:
            if chy_win is None:
                continue
            if not _windows_overlap(clip_win, chy_win):
                continue  # not on screen during the clip -> fine

            if clip_box is not None and chy_box is not None:
                if _rects_intersect(clip_box, chy_box):
                    findings.append(Finding(
                        "fail", "stacked_chyron_over_clip",
                        "chyron '{0}' overlaps frame-wrapped clip '{1}' in time AND "
                        "space — the approved frame already carries the caption; put "
                        "the year/context in the frame's built-in slot, not a stacked "
                        "lower-third/card".format(chy_id, clip_id),
                        where="{0} x {1}".format(clip_id, chy_id),
                    ))
                # Both have boxes but they don't intersect -> no stack, skip.
                continue

            # Chyron has no usable bbox: only a full-width lower-third is provably
            # over the clip (a bottom band spans the frame for its whole window).
            if chy_box is None and _is_fullwidth_lower_third(chy_cue, chy_id):
                findings.append(Finding(
                    "fail", "stacked_chyron_over_clip",
                    "full-width lower-third '{0}' (no bbox) spans the bottom band "
                    "across frame-wrapped clip '{1}' during its window — no stacked "
                    "lower-third over a frame-wrapped clip; use the frame's caption "
                    "slot".format(chy_id, clip_id),
                    where="{0} x {1}".format(clip_id, chy_id),
                ))

    return findings


if __name__ == "__main__":
    run_cli("qa_clip_no_extra_chyron", check)
