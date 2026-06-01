"""qa_element_overlap — text or objects must not collide on screen unless intended.

Catches the documented "text or objects overlapping unless intended" bug
(memory overlay_positioning_locked: no-overlay-vs-overlay overlap). Two cues that
share the screen at the same instant, sit at the same visual depth, and whose
boxes physically intersect will render one on top of the other — an unreadable
collision the editor never asked for.

Rule (locked):
    For every PAIR of cues (a, b):
      * their time intervals [start_s, end_s] overlap, AND
      * they sit on the same or an ADJACENT layer (|layer_a - layer_b| <= 1)
        — cues >=2 layers apart read as depth and never conflict, AND
      * both carry a bbox, AND
      * neither names the other in interaction_with (which marks the overlap as
        deliberate — e.g. a label pinned onto its marker),
    then if their bboxes intersect (rectangle overlap, top-left origin) -> "fail".

Reads:  <project>/artifacts/cuelist.json
Shape:  {"cues": [{"id","kind","start_s","end_s","layer"(int 0-11),
                    "bbox"?:{"x","y","w","h"}, "interaction_with"?:["id"...]}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

EPSILON = 1e-6


def _num(value) -> Optional[float]:
    """Return value as float if it is a real number, else None."""
    if isinstance(value, bool):  # bool is an int subclass — reject it explicitly
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _bbox(cue: dict) -> Optional[tuple]:
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


def _time_overlap(a: dict, b: dict) -> bool:
    """True iff the cues' [start_s, end_s] intervals share any open span.

    Touching end-to-end (a ends exactly when b starts) is NOT an overlap —
    they are never on screen simultaneously.
    """
    a0, a1 = _num(a.get("start_s")), _num(a.get("end_s"))
    b0, b1 = _num(b.get("start_s")), _num(b.get("end_s"))
    if a0 is None or a1 is None or b0 is None or b1 is None:
        return False
    return (a0 < b1 - EPSILON) and (b0 < a1 - EPSILON)


def _rects_intersect(r1: tuple, r2: tuple) -> bool:
    """True iff two axis-aligned rectangles (x, y, w, h, top-left origin) overlap.

    Edge-touching (shared border, zero overlap area) is NOT a collision.
    """
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    # Separating-axis: disjoint if one is fully left/right/above/below the other.
    if x1 + w1 <= x2 + EPSILON or x2 + w2 <= x1 + EPSILON:
        return False
    if y1 + h1 <= y2 + EPSILON or y2 + h2 <= y1 + EPSILON:
        return False
    return True


def _layer(cue: dict) -> Optional[int]:
    val = cue.get("layer")
    if isinstance(val, bool):  # reject bool masquerading as int
        return None
    if isinstance(val, int):
        return val
    return None


def _interacts(a: dict, b: dict, a_id, b_id) -> bool:
    """True iff either cue declares the other in interaction_with (intended overlap)."""
    a_iw = a.get("interaction_with")
    b_iw = b.get("interaction_with")
    if isinstance(a_iw, list) and b_id in a_iw:
        return True
    if isinstance(b_iw, list) and a_id in b_iw:
        return True
    return False


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    findings: List[Finding] = []

    # Pre-extract the fields once so the O(n^2) pairwise scan stays cheap.
    enriched = []
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError(f"cuelist.json cue #{i} is not an object")
        enriched.append((cue.get("id", f"#{i}"), cue, _bbox(cue), _layer(cue)))

    n = len(enriched)
    for i in range(n):
        a_id, a, a_box, a_layer = enriched[i]
        if a_box is None:
            continue  # no geometry -> cannot collide with anything
        for j in range(i + 1, n):
            b_id, b, b_box, b_layer = enriched[j]
            if b_box is None:
                continue

            # Same or adjacent layer only. Missing layers default to 0 so an
            # un-layered cue is still checked rather than silently skipped.
            la = a_layer if a_layer is not None else 0
            lb = b_layer if b_layer is not None else 0
            if abs(la - lb) >= 2:
                continue  # >=2 layers apart reads as depth, never a conflict

            if not _time_overlap(a, b):
                continue  # not on screen at the same time

            if _interacts(a, b, a_id, b_id):
                continue  # overlap is explicitly intended

            if _rects_intersect(a_box, b_box):
                findings.append(Finding(
                    "fail", "elements_overlap",
                    f"cue '{a_id}' (layer {la}) and '{b_id}' (layer {lb}) are on "
                    f"screen together and their bboxes intersect, but neither "
                    f"declares the other in interaction_with — unintended collision",
                    where=f"{a_id} x {b_id}",
                ))

    return findings


if __name__ == "__main__":
    run_cli("qa_element_overlap", check)
