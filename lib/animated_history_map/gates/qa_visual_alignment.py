"""qa_visual_alignment — a rendered pin must land where its lat/lon says it should.

Catches the documented "pin on the wrong place" failure
(geographic_pin_accuracy_required): the geometry is computed correctly by mapkit,
but a CSS offset, a wrong transform-origin, or a stale cached position drifts the
*rendered* marker away from the pixel the projection demands. qa_geo proves the
DECLARED pixel is derived from lat/lon; this gate proves the PIXEL THAT ACTUALLY
RENDERED matches that declaration — closing the gap between "we computed the right
spot" and "the dot is on the right spot".

For each pin cue that declares its target pixel (anchor_px, anchor_py), it grabs
the rendered frame while the pin is on screen, searches a window centred on the
declared pixel for the marker blob (the brightest / most-saturated cluster, or
pixels matching a declared anchor_color), takes that blob's centroid, and fails if
the centroid is more than TOL_PX from the declared pixel.

Rule (fail):
    * For each pin cue with numeric anchor_px/anchor_py, sample the render at a
      time the pin is up (mid-life, clamped past any drop-in animation).
    * Search a (2*SEARCH_R) box around the declared pixel for the marker:
        - if anchor_color [r,g,b] is declared: pixels within COLOR_TOL of it;
        - else: the saturated/bright blob (top luma+saturation percentile).
    * "fail" if no marker pixels are found in the window (the pin did not render
      anywhere near its declared spot), OR the found centroid is > TOL_PX away.

A gate that cannot run must never silently pass:
    * no cuelist.json                     -> GateInputError (blocking)
    * neither mp4 present                  -> GateInputError
    * ffprobe/ffmpeg not on PATH           -> GateInputError
    * ffprobe cannot read a duration       -> GateInputError
    * a needed frame cannot be decoded     -> GateInputError
    * a declared pixel outside the frame   -> "fail" (pin placed off-canvas)

Reads:   <project>/artifacts/cuelist.json
         <project>/renders/final.mp4   (fallback <project>/renders/master.mp4)
Shape:   {"cues":[{"id","kind":"pin_drop"|...,"start_s","end_s",
                    "anchor_px":num,"anchor_py":num,
                    "anchor_color"?:[r,g,b]}, ...]}
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

from ._contract import Finding, GateInputError, load_json, run_cli

# Max allowed gap between the declared pin pixel and the rendered marker centroid.
# Generous enough for the marker glyph's own radius + sub-frame seek slop, tight
# enough that a pin on the wrong city (tens-to-hundreds of px) always trips.
TOL_PX = 28.0

# Half-size of the search window around the declared pixel. A marker that lands
# inside this box is "near"; nothing found in it means the pin rendered elsewhere
# (or not at all). Wider than TOL_PX so a near-miss is measured, not missed.
SEARCH_R = 90

# Colour match tolerance (per-channel, 0..255) when anchor_color is declared.
COLOR_TOL = 60.0

# When no colour is declared, the marker is found as the brightest+most-saturated
# cluster: pixels above this luma AND saturation percentile within the window.
LUMA_PCTL = 88.0
SAT_PCTL = 80.0

PROBE_TIMEOUT_S = 60
EXTRACT_TIMEOUT_S = 60

# Cue kinds that drop/own a point marker the viewer should see at a pixel.
_PIN_KINDS = frozenset({"pin_drop", "pin_pulse_breath", "pin_dimming", "map_sprite"})


def _find_render(project_dir: Path) -> Path:
    renders = project_dir / "renders"
    final = renders / "final.mp4"
    master = renders / "master.mp4"
    if final.exists() and final.is_file():
        return final
    if master.exists() and master.is_file():
        return master
    raise GateInputError(
        "no render found: neither renders/final.mp4 nor renders/master.mp4 "
        "exists (cannot check pin alignment without a rendered video)"
    )


def _probe_dims_duration(mp4: Path) -> Tuple[int, int, float]:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height:format=duration",
         "-of", "json", str(mp4)],
        capture_output=True, timeout=PROBE_TIMEOUT_S,
    )
    if proc.returncode != 0:
        raise GateInputError(f"ffprobe failed on {mp4.name}")
    try:
        meta = json.loads(proc.stdout.decode("utf-8", "replace"))
        stream = (meta.get("streams") or [{}])[0]
        w = int(stream["width"]); h = int(stream["height"])
        dur = float(meta.get("format", {}).get("duration"))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise GateInputError(f"could not read width/height/duration from {mp4.name}: {exc}")
    if w <= 0 or h <= 0 or dur <= 0:
        raise GateInputError(f"non-positive width/height/duration from {mp4.name}")
    return w, h, dur


def _extract_frame_rgb(mp4: Path, t: float) -> np.ndarray:
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{t:.3f}", "-i", str(mp4),
         "-frames:v", "1", "-f", "image2", "-vcodec", "ppm", "-"],
        capture_output=True, timeout=EXTRACT_TIMEOUT_S,
    )
    if proc.returncode != 0 or not proc.stdout:
        raise GateInputError(f"could not extract a frame at {t:.2f}s from {mp4.name}")
    try:
        with Image.open(io.BytesIO(proc.stdout)) as im:
            return np.asarray(im.convert("RGB"), dtype=np.uint8)
    except (OSError, ValueError) as exc:
        raise GateInputError(f"could not decode the sampled frame at {t:.2f}s: {exc}")


def _num(value) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _anchor_color(cue: dict) -> Optional[np.ndarray]:
    c = cue.get("anchor_color")
    if isinstance(c, (list, tuple)) and len(c) == 3:
        try:
            rgb = [float(v) for v in c]
        except (TypeError, ValueError):
            return None
        if all(0 <= v <= 255 for v in rgb):
            return np.asarray(rgb, dtype=np.float64)
    return None


def _marker_centroid(window: np.ndarray, color: Optional[np.ndarray]
                     ) -> Optional[Tuple[float, float]]:
    """Centroid (cx, cy) of the marker blob within ``window`` (H,W,3), or None.

    With a declared colour: the centroid of pixels within COLOR_TOL of it.
    Without: the centroid of the bright+saturated cluster (top percentiles).
    Coordinates are LOCAL to the window (0,0 = window top-left).
    """
    rgb = window.astype(np.float64)
    if color is not None:
        dist = np.sqrt(((rgb - color) ** 2).sum(axis=2))
        mask = dist <= COLOR_TOL
    else:
        luma = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
        mx = rgb.max(axis=2)
        mn = rgb.min(axis=2)
        sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1.0), 0.0) * 255.0
        luma_thr = np.percentile(luma, LUMA_PCTL)
        sat_thr = np.percentile(sat, SAT_PCTL)
        mask = (luma >= luma_thr) & (sat >= sat_thr)
        # Fall back to luma-only if saturation gate emptied it (greyscale marker).
        if not mask.any():
            mask = luma >= np.percentile(luma, LUMA_PCTL)
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return None
    return float(xs.mean()), float(ys.mean())


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    # Collect pin cues that declare a target pixel.
    pins = []
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError(f"cuelist.json cue #{i} is not an object")
        kind = cue.get("kind")
        px, py = _num(cue.get("anchor_px")), _num(cue.get("anchor_py"))
        if px is None or py is None:
            continue
        # A declared anchor pixel on a pin-ish cue is what we verify.
        if isinstance(kind, str) and kind not in _PIN_KINDS:
            continue
        s, e = _num(cue.get("start_s")), _num(cue.get("end_s"))
        if s is None or e is None or e <= s:
            continue
        pins.append((cue.get("id", f"#{i}"), px, py, s, e, _anchor_color(cue)))

    if not pins:
        return []  # no pins to verify -> legitimately a pass (lint, not presence)

    mp4 = _find_render(project_dir)
    for tool in ("ffprobe", "ffmpeg"):
        if shutil.which(tool) is None:
            raise GateInputError(
                f"{tool} not found on PATH; cannot inspect {mp4.name} for pin alignment"
            )
    frame_w, frame_h, duration = _probe_dims_duration(mp4)

    # Sample each pin past its drop-in (favour 60% through its life, clamped to
    # the render duration). Bucket identical times to decode each frame once.
    by_t: dict = {}
    for cid, px, py, s, e, color in pins:
        t = s + 0.6 * (e - s)
        t = min(max(t, 0.0), max(duration - 1e-3, 0.0))
        by_t.setdefault(round(t, 2), []).append((cid, px, py, color))

    findings: List[Finding] = []
    for t in sorted(by_t):
        frame = _extract_frame_rgb(mp4, t)
        fh, fw = frame.shape[:2]
        for cid, px, py, color in by_t[t]:
            where = f"pin {cid} declared=({px:.0f},{py:.0f}) @ {t:.2f}s"

            # A declared pixel outside the rendered frame is itself the bug.
            if px < 0 or py < 0 or px > fw or py > fh:
                findings.append(Finding(
                    "fail", "pin_declared_off_frame",
                    f"declared pin pixel ({px:.0f},{py:.0f}) is outside the "
                    f"{fw}x{fh} rendered frame — the projection or the cue is wrong.",
                    where=where,
                ))
                continue

            x0 = max(0, int(round(px)) - SEARCH_R)
            y0 = max(0, int(round(py)) - SEARCH_R)
            x1 = min(fw, int(round(px)) + SEARCH_R)
            y1 = min(fh, int(round(py)) + SEARCH_R)
            window = frame[y0:y1, x0:x1]
            if window.size == 0:
                findings.append(Finding(
                    "fail", "pin_search_empty",
                    "search window around the declared pin pixel is empty (pixel "
                    "at the very frame edge) — cannot confirm the marker rendered.",
                    where=where,
                ))
                continue

            local = _marker_centroid(window, color)
            if local is None:
                findings.append(Finding(
                    "fail", "pin_not_found",
                    f"no marker found within {SEARCH_R}px of the declared pixel — "
                    "the pin did not render at its lat/lon position (CSS offset, "
                    "wrong transform-origin, or stale cached position).",
                    where=where,
                ))
                continue

            cx = x0 + local[0]
            cy = y0 + local[1]
            err = float(np.hypot(cx - px, cy - py))
            if err > TOL_PX:
                findings.append(Finding(
                    "fail", "pin_misaligned",
                    f"rendered marker centroid ({cx:.0f},{cy:.0f}) is {err:.0f}px "
                    f"from the declared pixel ({px:.0f},{py:.0f}) (> {TOL_PX:.0f}px "
                    "tolerance) — the dot drifted off its geographic position.",
                    where=where,
                ))

    return findings


if __name__ == "__main__":
    run_cli("qa_visual_alignment", check)
