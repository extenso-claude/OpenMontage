"""qa_black_frame — the finished render must never go black / near-black.

Catches the documented "black frame mid-video" failure: a timeline gap, a
GSAP ``filter: brightness()`` interpolation glitch (memory
gsap_filter_brightness_gotcha), a dropped basemap, or a compose bug renders one
or more frames as black. The container duration looks right and the file plays,
so duration/existence checks pass — but the viewer sees a dead black hole in the
middle of the video. This gate samples luminance across the timeline and makes
that loud.

Rule:
    * Locate the render: renders/final.mp4, else renders/master.mp4.
    * ffprobe the duration, sample frames at ~10/30/50/70/90% of it.
    * Extract each sampled frame (ffmpeg -> PPM on stdout) and compute its mean
      luma (Rec.601 weighting) in 0-255.
    * "fail" if ANY sampled frame's mean luma < MIN_MEAN_LUMA (12).

A gate that cannot run must never silently pass, so:
    * neither mp4 present                -> GateInputError (blocking)
    * ffprobe/ffmpeg not on PATH          -> GateInputError
    * ffprobe cannot read a duration      -> GateInputError
    * a sampled frame cannot be decoded   -> GateInputError
        (a render we can't inspect is not a render we can clear)

Reads:   <project>/renders/final.mp4   (fallback <project>/renders/master.mp4)
Allowed: subprocess + ffmpeg/ffprobe, numpy/PIL (no required pip deps).
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
from argparse import Namespace
from pathlib import Path
from typing import List, Optional

import numpy as np
from PIL import Image

from ._contract import Finding, GateInputError, load_json, run_cli  # noqa: F401

# A frame this dark across its whole area reads as "black" to a viewer. 12/255
# leaves headroom above true black (0) and above the channel's darkest legit
# night basemap (navy ~0x1a2740, luma ~33) so deep-but-intentional scenes pass.
MIN_MEAN_LUMA = 12.0

# Fractions of the duration to sample. Spread across the timeline so a black
# stretch anywhere (not just the head/tail) gets caught.
SAMPLE_FRACTIONS = (0.10, 0.30, 0.50, 0.70, 0.90)

PROBE_TIMEOUT_S = 60
EXTRACT_TIMEOUT_S = 60


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
        "exists (cannot check for black frames without a rendered video)"
    )


def _probe_duration(mp4: Path) -> Optional[float]:
    """Container duration in seconds via ffprobe, or None if unparseable."""
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", str(mp4),
        ],
        capture_output=True, timeout=PROBE_TIMEOUT_S,
    )
    if proc.returncode != 0:
        return None
    try:
        dur = json.loads(proc.stdout.decode("utf-8", "replace")).get(
            "format", {}
        ).get("duration")
        return float(dur) if dur is not None else None
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _extract_frame_ppm(mp4: Path, t: float) -> Optional[bytes]:
    """Decode a single frame at timestamp ``t`` as a PPM blob on stdout.

    -ss before -i seeks fast (keyframe-accurate is plenty for a luma sample).
    Returns the raw PPM bytes, or None if ffmpeg produced nothing.
    """
    proc = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-nostdin",
            "-ss", f"{t:.3f}", "-i", str(mp4),
            "-frames:v", "1",
            "-f", "image2", "-vcodec", "ppm", "-",
        ],
        capture_output=True, timeout=EXTRACT_TIMEOUT_S,
    )
    if proc.returncode != 0 or not proc.stdout:
        return None
    return proc.stdout


def _mean_luma(ppm_bytes: bytes) -> float:
    """Rec.601 mean luma (0-255) of a decoded PPM frame."""
    with Image.open(io.BytesIO(ppm_bytes)) as im:
        arr = np.asarray(im.convert("RGB"), dtype=np.float64)
    # Rec.601 luma; matches how "brightness" is perceived.
    luma = arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114
    return float(luma.mean())


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    mp4 = _find_render(project_dir)
    rel = mp4.relative_to(project_dir).as_posix()

    # The tools must be present to inspect a render that exists; their absence is
    # blocking, not a pass.
    for tool in ("ffprobe", "ffmpeg"):
        if shutil.which(tool) is None:
            raise GateInputError(
                f"{tool} not found on PATH; cannot inspect {rel} for black frames"
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
            ppm = _extract_frame_ppm(mp4, t)
        except (subprocess.TimeoutExpired, OSError) as exc:
            raise GateInputError(f"ffmpeg failed extracting frame at {t:.2f}s: {exc}")
        if ppm is None:
            # A frame we can't decode is a frame we can't clear -> blocking.
            raise GateInputError(
                f"could not extract a frame at {t:.2f}s from {rel} "
                "(cannot verify it is not black)"
            )
        try:
            mean = _mean_luma(ppm)
        except (OSError, ValueError) as exc:
            raise GateInputError(
                f"could not decode the sampled frame at {t:.2f}s from {rel}: {exc}"
            )

        if mean < MIN_MEAN_LUMA:
            findings.append(Finding(
                "fail", "black_frame",
                f"mean luma {mean:.2f} < {MIN_MEAN_LUMA:.0f} — frame is "
                "black/near-black (timeline gap, dropped basemap, or a "
                "brightness-interpolation glitch)",
                where=where,
            ))

    return findings


if __name__ == "__main__":
    run_cli("qa_black_frame", check)
