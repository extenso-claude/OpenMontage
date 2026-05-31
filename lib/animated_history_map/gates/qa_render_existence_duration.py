"""qa_render_existence_duration — the final.mp4 must actually exist and match plan.

Catches the "fabricated final.mp4 that doesn't exist / wrong length" failure: a
render step that reports success but never wrote a file, wrote a stub, or wrote a
clip whose runtime doesn't match the approved voiceover. A render that silently
disagrees with the planned duration is a black-box lie — this gate makes it loud.

Rule:
    * "fail" if renders/final.mp4 does not exist.
    * Else ffprobe it for the container duration.
    * "fail" if duration < 1s (a stub / single-frame artifact).
    * "fail" if |actual - planned| / planned > 0.02  (2% tolerance), where
      planned = artifacts/voice_report.json -> total_duration_s.
    * "warn" if a decoded frame count is obtainable and deviates from
      duration * 24 by > 2% (advisory: hints at a frame-rate / dropped-frame bug).

Required input: artifacts/voice_report.json (with a positive total_duration_s).
A gate that cannot read its plan must never silently pass, so a missing/garbled
voice_report raises GateInputError (-> blocking fail via the harness).

Reads:  <project>/renders/final.mp4
        <project>/artifacts/voice_report.json
Allowed: subprocess + ffprobe (no pip deps).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

DURATION_TOLERANCE = 0.02   # 2% of planned voiceover duration
FRAME_TOLERANCE = 0.02      # 2% of duration*FPS
ASSUMED_FPS = 24.0          # pipeline renders at 24fps
MIN_DURATION_S = 1.0        # anything shorter is a stub, not a video
PROBE_TIMEOUT_S = 60


def _planned_duration(project_dir: Path) -> float:
    """Read the approved voiceover runtime. Missing/garbled/non-positive is a
    BLOCKING input error — we cannot judge the render without a target."""
    report = load_json(project_dir / "artifacts" / "voice_report.json")
    planned = report.get("total_duration_s")
    if not isinstance(planned, (int, float)) or isinstance(planned, bool):
        raise GateInputError(
            "voice_report.json missing numeric 'total_duration_s' "
            "(cannot validate render length without a planned duration)"
        )
    if planned <= 0:
        raise GateInputError(
            f"voice_report.json total_duration_s must be positive, got {planned}"
        )
    return float(planned)


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


def _probe_frame_count(mp4: Path) -> Optional[int]:
    """Decoded video-frame count via ffprobe, or None if not obtainable.

    Uses -count_frames (decodes the stream) which is reliable across containers
    even when nb_frames is absent from the header. Best-effort: any failure just
    means we skip the advisory frame-count check rather than block.
    """
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-count_frames",
            "-show_entries", "stream=nb_read_frames",
            "-of", "json", str(mp4),
        ],
        capture_output=True, text=True, timeout=PROBE_TIMEOUT_S,
    )
    if proc.returncode != 0:
        return None
    try:
        streams = json.loads(proc.stdout).get("streams") or []
        if not streams:
            return None
        nb = streams[0].get("nb_read_frames")
        if nb in (None, "N/A"):
            return None
        return int(nb)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    # Plan is required — load it first so a render with no target can't sneak by.
    planned = _planned_duration(project_dir)

    findings: List[Finding] = []
    mp4 = project_dir / "renders" / "final.mp4"

    # 1) Existence. A fabricated/absent render is the headline bug.
    if not mp4.exists() or not mp4.is_file():
        findings.append(Finding(
            "fail", "render_missing",
            "renders/final.mp4 does not exist — the render step reported success "
            "but no video file is present",
            where="renders/final.mp4",
        ))
        return findings  # nothing further to probe

    # ffprobe must be on PATH to verify a render that does exist.
    if shutil.which("ffprobe") is None:
        raise GateInputError(
            "ffprobe not found on PATH; cannot verify renders/final.mp4 duration"
        )

    # 2) Duration. Probe; an unreadable/corrupt file is itself a failure.
    try:
        actual = _probe_duration(mp4)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise GateInputError(f"ffprobe failed on renders/final.mp4: {exc}")

    if actual is None:
        findings.append(Finding(
            "fail", "render_unreadable",
            "renders/final.mp4 exists but ffprobe could not read a duration "
            "(corrupt or not a valid video container)",
            where="renders/final.mp4",
        ))
        return findings

    if actual < MIN_DURATION_S:
        findings.append(Finding(
            "fail", "render_too_short",
            f"renders/final.mp4 is {actual:.3f}s (< {MIN_DURATION_S:.0f}s) — looks "
            "like a stub or single-frame artifact, not a finished video",
            where="renders/final.mp4",
        ))
        # No point comparing a stub against the plan; report the headline issue.
        return findings

    # 3) Plan agreement: within 2% of the approved voiceover runtime.
    drift = abs(actual - planned)
    rel = drift / planned
    if rel > DURATION_TOLERANCE:
        findings.append(Finding(
            "fail", "duration_mismatch",
            f"render is {actual:.3f}s but planned voiceover is {planned:.3f}s "
            f"(off by {drift:.3f}s = {rel * 100:.1f}%, tolerance "
            f"{DURATION_TOLERANCE * 100:.0f}%)",
            where="renders/final.mp4",
        ))

    # 4) Advisory: decoded frames vs duration*24. Best-effort, never blocks.
    try:
        frames = _probe_frame_count(mp4)
    except (subprocess.TimeoutExpired, OSError):
        frames = None
    if frames is not None:
        expected_frames = actual * ASSUMED_FPS
        if expected_frames > 0:
            frame_rel = abs(frames - expected_frames) / expected_frames
            if frame_rel > FRAME_TOLERANCE:
                findings.append(Finding(
                    "warn", "frame_count_drift",
                    f"decoded {frames} frames but duration*{ASSUMED_FPS:.0f}fps "
                    f"= {expected_frames:.0f} (off {frame_rel * 100:.1f}%); "
                    "possible frame-rate or dropped-frame issue",
                    where="renders/final.mp4",
                ))

    return findings


if __name__ == "__main__":
    run_cli("qa_render_existence_duration", check)
