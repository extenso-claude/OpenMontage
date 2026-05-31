"""qa_placement — no hero/image rendered into a letterbox band.

Catches the documented CSS placement bug where an image-led clip is composited
into a band: the top and bottom strips of the frame stay pure black and the real
content is squeezed into the middle. The file plays, the duration is right, and
the agent can visually miss it when a noir scene happens to have a dim sky/floor
— so this gate makes it loud by sampling the render across its whole timeline.

It does NOT reimplement the band detector: it delegates to the existing, tuned
engine ``lib.render_placement_qa.check_clip``, which flags a band only when a
top/bottom strip is BOTH near-uniformly pure-black (ratio > 0.92) AND has
near-zero variance (stddev < 4) — the two-condition test that lets legitimate
starry/grainy noir backdrops pass while a true black band trips.

Rule:
    * Locate the render: renders/final.mp4, else renders/master.mp4.
    * ffprobe the duration, sample at ~10/30/50/70/90% of it.
    * Run check_clip(mp4, time_s=t) at each sampled timestamp.
    * "fail" (placement_band) if ANY sampled timestamp returns flag == True,
      reporting which timestamp and the band stats.

A gate that cannot run must never silently pass, so:
    * neither mp4 present                 -> GateInputError (blocking)
    * ffprobe/ffmpeg not on PATH          -> GateInputError
    * ffprobe cannot read a duration      -> GateInputError
    * check_clip cannot decode a frame    -> GateInputError
        (a frame we cannot inspect is not a frame we can clear)

Reads:   <project>/renders/final.mp4   (fallback <project>/renders/master.mp4)
Allowed: subprocess + ffprobe, and lib.render_placement_qa (which shells ffmpeg).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from lib import render_placement_qa

from ._contract import Finding, GateInputError, load_json, run_cli  # noqa: F401

# Fractions of the duration to sample. Spread across the timeline so a banded
# stretch anywhere (not just the head/tail) gets caught.
SAMPLE_FRACTIONS = (0.10, 0.30, 0.50, 0.70, 0.90)

PROBE_TIMEOUT_S = 60


def _find_render(project_dir: Path) -> Path:
    """renders/final.mp4 preferred, renders/master.mp4 fallback.

    Neither present is a BLOCKING input error: there is nothing to inspect, and
    a render gate that finds no render must not report a pass."""
    renders = project_dir / "renders"
    final = renders / "final.mp4"
    master = renders / "master.mp4"
    if final.exists() and final.is_file():
        return final
    if master.exists() and master.is_file():
        return master
    raise GateInputError(
        "no render found: neither renders/final.mp4 nor renders/master.mp4 "
        "exists (cannot check placement without a rendered video)"
    )


def _probe_duration(mp4: Path) -> Optional[float]:
    """Container duration in seconds via ffprobe, or None if unparseable."""
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", str(mp4),
        ],
        capture_output=True, text=True, timeout=PROBE_TIMEOUT_S,
    )
    if proc.returncode != 0:
        return None
    try:
        dur = json.loads(proc.stdout).get("format", {}).get("duration")
        return float(dur) if dur is not None else None
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    mp4 = _find_render(project_dir)
    rel = mp4.relative_to(project_dir).as_posix()

    # The tools must be present to inspect a render that exists; their absence is
    # blocking, not a pass. check_clip shells ffmpeg; we also ffprobe directly.
    for tool in ("ffprobe", "ffmpeg"):
        if shutil.which(tool) is None:
            raise GateInputError(
                f"{tool} not found on PATH; cannot inspect {rel} for placement bands"
            )

    try:
        duration = _probe_duration(mp4)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise GateInputError(f"ffprobe failed on {rel}: {exc}")
    if duration is None or duration <= 0:
        raise GateInputError(
            f"could not read a positive duration from {rel} "
            "(corrupt or not a valid video container)"
        )

    findings: List[Finding] = []
    for frac in SAMPLE_FRACTIONS:
        t = duration * frac
        where = f"{rel} @ {t:.2f}s ({int(frac * 100)}%)"
        try:
            result = render_placement_qa.check_clip(mp4, time_s=t)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            # A frame check_clip can't decode is a frame we can't clear -> blocking.
            raise GateInputError(
                f"could not inspect a frame at {t:.2f}s from {rel} "
                f"(cannot verify it is not banded): {exc}"
            )

        if result.get("flag"):
            findings.append(Finding(
                "fail", "placement_band",
                "hero/image rendered into a letterbox band — top/bottom strip is "
                "uniformly black (CSS placement bug, not a full-frame composite) "
                f"[top near-black {result.get('top_near_black')} "
                f"stddev {result.get('top_stddev')}, "
                f"bottom near-black {result.get('bottom_near_black')} "
                f"stddev {result.get('bottom_stddev')}]",
                where=where,
            ))

    return findings


if __name__ == "__main__":
    run_cli("qa_placement", check)
