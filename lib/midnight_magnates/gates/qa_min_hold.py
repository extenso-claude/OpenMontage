"""qa_min_hold — every text-bearing cue must stay on screen long enough to read.

Catches the documented "animation on screen too briefly to read" bug.
Rule (locked, per memory animation_hold_time_required):
    required_hold = max(2.5, ceil(word_count / 3) + 2)   seconds
A cue may set "min_hold_override" to raise (never lower) the bar. Map cues with
many labels need longer holds: >2 labels -> >=6s, >4 labels -> >=8s.

Reads:  <project>/artifacts/cuelist.json
Shape:  {"cues": [{"id","kind","text","start_s","end_s",
                    "label_count"?, "min_hold_override"?}, ...]}
"""

from __future__ import annotations

import math
from argparse import Namespace
from pathlib import Path
from typing import List

from ._contract import Finding, GateInputError, load_json, run_cli

EPSILON = 1e-6


def _required_hold(cue: dict) -> float:
    text = (cue.get("text") or "").strip()
    words = len(text.split())
    base = max(2.5, math.ceil(words / 3) + 2) if words else 0.0

    # Map cues with dense labels need to breathe.
    if "map" in (cue.get("kind") or "").lower():
        labels = int(cue.get("label_count", 0))
        if labels > 4:
            base = max(base, 8.0)
        elif labels > 2:
            base = max(base, 6.0)

    override = cue.get("min_hold_override")
    if override is not None:
        base = max(base, float(override))
    return base


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    findings: List[Finding] = []
    for i, cue in enumerate(cues):
        cid = cue.get("id", f"#{i}")
        required = _required_hold(cue)
        if required <= 0:
            continue  # no text + not a dense map cue -> no readability requirement

        # Accept t_in/t_out as aliases for start_s/end_s (overlay cuelist uses t_in/t_out;
        # maps cuelist uses start_s/end_s — read either so one gate serves both pipelines).
        start, end = cue.get("start_s", cue.get("t_in")), cue.get("end_s", cue.get("t_out"))
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            findings.append(Finding(
                "fail", "missing_timing",
                f"cue needs numeric start_s/end_s (or t_in/t_out) to verify a {required:.1f}s hold",
                where=cid,
            ))
            continue

        actual = end - start
        if actual + EPSILON < required:
            findings.append(Finding(
                "fail", "too_brief",
                f"on screen {actual:.2f}s but needs >= {required:.2f}s to read",
                where=cid,
            ))
    return findings


if __name__ == "__main__":
    run_cli("qa_min_hold", check)
