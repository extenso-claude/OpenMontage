"""qa_card_bounds — every card/overlay bbox must stay inside the 1920x1080 frame.

Catches the documented "anchored from top instead of bottom" bug, where a
lower_* card is positioned by its TOP edge (small y) but sized so y+h spills
past the bottom of the frame — the card geometry busts the canvas edge and the
overlay clips off-screen on render.

Rule (locked, per memory card_bounds_qa_required):
    For every cue carrying a bbox, the box must lie FULLY within the frame:
        x >= 0,  y >= 0,  x + w <= 1920,  y + h <= 1080
    A box that crosses any edge is a "fail" (we report which edge and by how
    many pixels). Cues without a bbox are skipped — only geometry is checked.

Reads:  <project>/artifacts/cuelist.json
Shape:  {"cues": [{"id", ..., "bbox"?: {"x","y","w","h"}}, ...]}
        bbox is in pixels in a 1920x1080 canvas, top-left origin.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

FRAME_W = 1920
FRAME_H = 1080
EPSILON = 1e-6


def _num(value) -> Optional[float]:
    """Return value as float, or None if it is not a real number."""
    if isinstance(value, bool):  # bool is an int subclass — reject it explicitly
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    findings: List[Finding] = []
    for i, cue in enumerate(cues):
        cid = cue.get("id", f"#{i}")
        bbox = cue.get("bbox")
        if bbox is None:
            continue  # no geometry -> nothing to bounds-check

        if not isinstance(bbox, dict):
            findings.append(Finding(
                "fail", "bad_bbox",
                "bbox must be an object with numeric x/y/w/h",
                where=cid,
            ))
            continue

        x = _num(bbox.get("x"))
        y = _num(bbox.get("y"))
        w = _num(bbox.get("w"))
        h = _num(bbox.get("h"))
        if x is None or y is None or w is None or h is None:
            findings.append(Finding(
                "fail", "bad_bbox",
                "bbox needs numeric x/y/w/h to verify it fits the frame",
                where=cid,
            ))
            continue
        if w < 0 or h < 0:
            findings.append(Finding(
                "fail", "bad_bbox",
                f"bbox has negative size (w={w:g}, h={h:g})",
                where=cid,
            ))
            continue

        # One finding per busted edge, with the overflow magnitude.
        if x < -EPSILON:
            findings.append(Finding(
                "fail", "out_of_frame",
                f"left edge off-frame by {-x:.0f}px (x={x:g} < 0)",
                where=cid,
            ))
        if y < -EPSILON:
            findings.append(Finding(
                "fail", "out_of_frame",
                f"top edge off-frame by {-y:.0f}px (y={y:g} < 0)",
                where=cid,
            ))
        right = x + w
        if right > FRAME_W + EPSILON:
            findings.append(Finding(
                "fail", "out_of_frame",
                f"right edge off-frame by {right - FRAME_W:.0f}px "
                f"(x+w={right:g} > {FRAME_W})",
                where=cid,
            ))
        bottom = y + h
        if bottom > FRAME_H + EPSILON:
            findings.append(Finding(
                "fail", "out_of_frame",
                f"bottom edge off-frame by {bottom - FRAME_H:.0f}px "
                f"(y+h={bottom:g} > {FRAME_H}) — lower_* cards must anchor "
                f"from the frame bottom, not the top",
                where=cid,
            ))
    return findings


if __name__ == "__main__":
    run_cli("qa_card_bounds", check)
