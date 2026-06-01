"""qa_visual_completeness — no dead frame mid-timeline; every visible cue has geometry.

Two completeness failures this gate makes loud:

  1. DEAD FRAME mid-timeline. A timeline gap, a dropped basemap, or a compose bug
     leaves a stretch of the video with nothing on it — either black/near-black,
     OR a flat uniform blank canvas (a single fill colour, no content). The file
     plays and its duration is right, so existence/duration checks pass, but the
     viewer sees a hole. We sample luminance AND spatial variance across the whole
     timeline: a frame that is both dark-or-uniform reads as dead.

     (This is the spatial-variance complement to qa_black_frame's pure-luma floor:
     a navy basemap with no content can clear a luma floor yet still be a blank
     hole. A frame with real content has structure -> variance.)

  2. GEOMETRY-LESS VISIBLE CUE. Every cue that is supposed to be ON SCREEN (it has
     a finite [start_s, end_s] lifetime and is a *visible* primitive, not an
     audio/camera/transition directive) MUST declare geometry (a bbox, or a pin
     anchor pixel). A visible cue with no geometry was never actually placed —
     the downstream placement / overlap / alignment gates silently skip it, so it
     can render anywhere or nowhere. Declaring it without geometry is an
     incomplete cue, and this gate refuses it.

A gate that cannot run must never silently pass, so:
    * no cuelist.json                     -> GateInputError (blocking)
    * neither mp4 present                  -> GateInputError
    * ffprobe/ffmpeg not on PATH           -> GateInputError
    * ffprobe cannot read a duration       -> GateInputError
    * a sampled frame cannot be decoded    -> GateInputError

Reads:   <project>/artifacts/cuelist.json
         <project>/renders/final.mp4   (fallback <project>/renders/master.mp4)
Shape:   {"cues":[{"id","kind","start_s","end_s",
                    "bbox"?:{...}, "anchor_px"?,"anchor_py"?, "layer"?}, ...]}
Allowed: subprocess + ffmpeg/ffprobe, numpy/PIL (no required pip deps).
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

from .. import vocab
from ._contract import Finding, GateInputError, load_json, run_cli

# A frame this dark reads as black (matches qa_black_frame's floor).
MIN_MEAN_LUMA = 12.0
# A frame whose pixel std-dev is below this carries no structure — a flat fill.
# Combined with a moderate-luma ceiling so a busy bright frame never trips it.
MIN_STDDEV = 4.0
# Only call a low-variance frame "dead" when it is also not bright content; a
# legitimately bright near-uniform frame (rare here) should not fail on variance
# alone. Night basemaps with content sit well above MIN_STDDEV.
UNIFORM_LUMA_CEIL = 70.0

# Sample fractions across the whole timeline (same spread as qa_black_frame).
SAMPLE_FRACTIONS = (0.10, 0.30, 0.50, 0.70, 0.90)

PROBE_TIMEOUT_S = 60
EXTRACT_TIMEOUT_S = 60

# Cue kinds that are NOT visible objects on the canvas — they carry no geometry by
# nature (audio cues, camera moves, whole-frame transitions/atmosphere). These are
# exempt from the "must have geometry" rule. Single-sourced from vocab.
_NON_VISIBLE_KINDS = vocab.NON_VISIBLE_KINDS


def _find_render(project_dir: Path) -> Path:
    """renders/final.mp4 preferred, renders/master.mp4 fallback.

    Neither present is a BLOCKING input error: there is nothing to inspect."""
    renders = project_dir / "renders"
    final = renders / "final.mp4"
    master = renders / "master.mp4"
    if final.exists() and final.is_file():
        return final
    if master.exists() and master.is_file():
        return master
    raise GateInputError(
        "no render found: neither renders/final.mp4 nor renders/master.mp4 "
        "exists (cannot check for dead frames without a rendered video)"
    )


def _probe_duration(mp4: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(mp4)],
        capture_output=True, timeout=PROBE_TIMEOUT_S,
    )
    if proc.returncode != 0:
        raise GateInputError(f"ffprobe failed on {mp4.name}")
    try:
        dur = json.loads(proc.stdout.decode("utf-8", "replace")).get(
            "format", {}).get("duration")
        dur = float(dur) if dur is not None else 0.0
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GateInputError(f"could not read a duration from {mp4.name}: {exc}")
    if dur <= 0:
        raise GateInputError(f"non-positive duration from {mp4.name}")
    return dur


def _frame_stats(mp4: Path, t: float) -> Tuple[float, float]:
    """(mean_luma, stddev_luma) in 0..255 for the frame at timestamp ``t``."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{t:.3f}", "-i", str(mp4),
         "-frames:v", "1", "-f", "image2", "-vcodec", "ppm", "-"],
        capture_output=True, timeout=EXTRACT_TIMEOUT_S,
    )
    if proc.returncode != 0 or not proc.stdout:
        raise GateInputError(f"could not extract a frame at {t:.2f}s from {mp4.name}")
    try:
        with Image.open(io.BytesIO(proc.stdout)) as im:
            arr = np.asarray(im.convert("RGB"), dtype=np.float64)
    except (OSError, ValueError) as exc:
        raise GateInputError(f"could not decode the sampled frame at {t:.2f}s: {exc}")
    luma = arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114
    return float(luma.mean()), float(luma.std())


def _num(value) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _has_geometry(cue: dict) -> bool:
    """True if the cue declares a usable bbox OR an anchor pixel pair."""
    box = cue.get("bbox")
    if isinstance(box, dict):
        x, y, w, h = (_num(box.get(k)) for k in ("x", "y", "w", "h"))
        if None not in (x, y, w, h) and w > 0 and h > 0:
            return True
    px, py = _num(cue.get("anchor_px")), _num(cue.get("anchor_py"))
    if px is not None and py is not None:
        return True
    return False


def _is_visible_cue(cue: dict) -> bool:
    """True if the cue paints something at a position on the canvas (so it owes
    geometry). Audio / camera / whole-frame directives are exempt."""
    kind = cue.get("kind")
    if isinstance(kind, str) and kind in _NON_VISIBLE_KINDS:
        return False
    # A cue explicitly flagged non-visual opts out.
    if cue.get("visible") is False:
        return False
    return True


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    findings: List[Finding] = []

    # 1. Every visible cue with a finite on-screen lifetime must have geometry.
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError(f"cuelist.json cue #{i} is not an object")
        if not _is_visible_cue(cue):
            continue
        s, e = _num(cue.get("start_s")), _num(cue.get("end_s"))
        if s is None or e is None or e <= s:
            continue  # no on-screen lifetime declared -> nothing to place
        if not _has_geometry(cue):
            findings.append(Finding(
                "fail", "cue_without_geometry",
                "visible cue is on screen [{:.2f}..{:.2f}s] (kind={!r}) but declares "
                "no geometry (no bbox and no anchor_px/anchor_py) — it was never "
                "placed; placement/overlap/alignment gates silently skip it."
                .format(s, e, cue.get("kind")),
                where=str(cue.get("id", f"#{i}")),
            ))

    # 2. No dead frame mid-timeline (black/near-black OR flat uniform blank).
    mp4 = _find_render(project_dir)
    for tool in ("ffprobe", "ffmpeg"):
        if shutil.which(tool) is None:
            raise GateInputError(
                f"{tool} not found on PATH; cannot inspect {mp4.name} for dead frames"
            )
    duration = _probe_duration(mp4)
    rel = mp4.relative_to(project_dir).as_posix()

    for frac in SAMPLE_FRACTIONS:
        t = duration * frac
        mean, std = _frame_stats(mp4, t)
        where = f"{rel} @ {t:.2f}s ({int(frac * 100)}%)"
        if mean < MIN_MEAN_LUMA:
            findings.append(Finding(
                "fail", "dead_frame_black",
                f"mean luma {mean:.2f} < {MIN_MEAN_LUMA:.0f} — black/near-black "
                "frame mid-timeline (timeline gap or dropped basemap).",
                where=where,
            ))
        elif std < MIN_STDDEV and mean < UNIFORM_LUMA_CEIL:
            findings.append(Finding(
                "fail", "dead_frame_uniform",
                f"frame is a flat uniform fill (stddev {std:.2f} < {MIN_STDDEV:.0f}, "
                f"mean luma {mean:.2f}) — a blank canvas with no content rendered "
                "(a declared cue did not paint, or the basemap is missing).",
                where=where,
            ))

    return findings


if __name__ == "__main__":
    run_cli("qa_visual_completeness", check)
