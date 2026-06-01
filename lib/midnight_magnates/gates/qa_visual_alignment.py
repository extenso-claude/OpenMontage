"""qa_visual_alignment — a rendered marker must land where its declared pixel says.

Catches the documented "pin on the wrong place" failure
(geographic_pin_accuracy_required): the geometry is computed correctly by mapkit,
but a CSS offset, a wrong transform-origin, or a stale cached position drifts the
*rendered* marker away from the pixel the projection demands. qa_geo proves the
DECLARED pixel is derived from lat/lon; this gate proves the PIXEL THAT ACTUALLY
RENDERED matches that declaration — closing the gap between "we computed the right
spot" and "the dot is on the right spot".

The gate verifies every cue that declares WHERE it lands. The compiler stamps a
focal pixel onto two kinds of cue (compiler.py `_build_cue`): a map-anchored pin
gets anchor_px/anchor_py from its lat/lon, and ANY cue carrying a spatial_target
gets both spatial_target AND (when the target is a pixel) anchor_px/anchor_py.
This gate must verify BOTH — a pin's lat/lon pixel AND any spatial_target's pixel —
or an off-map FX / 2D-3D scene element painted on the wrong spot ships unseen.

For each alignable cue (one resolving to a target pixel via anchor_px/anchor_py or
spatial_target.target_px), it grabs the rendered frame while the cue is on screen,
searches a window centred on the declared pixel for the marker blob (the brightest
/ most-saturated cluster, or pixels matching a declared anchor_color), takes that
blob's centroid, and fails if the centroid is more than TOL_PX from the declared
pixel.

Rule (fail):
    * For each cue with a resolvable target pixel (anchor_px/anchor_py, else
      spatial_target.target_px's [x,y]), sample the render at a time the cue is up
      (mid-life, clamped past any drop-in animation).
    * Search a (2*SEARCH_R) box around the declared pixel for the marker:
        - if anchor_color [r,g,b] is declared: pixels within COLOR_TOL of it;
        - else: the saturated/bright blob (top luma+saturation percentile).
    * "fail" if no marker pixels are found in the window (the cue did not render
      anywhere near its declared spot), OR the found centroid is > TOL_PX away.

A gate that cannot rule on anything must never silently pass. When the cuelist has
cues but NOT ONE of them is alignable — no pin and no spatial_target/anchor_px
anywhere — there is nothing to verify yet the gate is wired in as the spatial-
alignment rail; that is a "fail" (a vacuous rubber-stamp), not a pass. Only a
genuinely empty cuelist (zero cues) is a legitimate pass.

A gate that cannot run must never silently pass:
    * no cuelist.json                     -> GateInputError (blocking)
    * neither mp4 present                  -> GateInputError
    * ffprobe/ffmpeg not on PATH           -> GateInputError
    * ffprobe cannot read a duration       -> GateInputError
    * a needed frame cannot be decoded     -> GateInputError
    * a declared pixel outside the frame   -> "fail" (cue placed off-canvas)
    * cues exist but none are alignable    -> "fail" (nothing to verify; no pass)

Reads:   <project>/artifacts/cuelist.json
         <project>/renders/final.mp4   (fallback <project>/renders/master.mp4)
Shape:   {"cues":[{"id","kind":"pin_drop"|"flash_burst"|...,"start_s","end_s",
                    "anchor_px":num,"anchor_py":num,            # or:
                    "spatial_target":{"target_px":[x,y(,w,h)]},
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

from .. import vocab
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

# Cue kinds that drop/own a point marker the viewer should see at a pixel. These
# carry a lat/lon-derived anchor_px/anchor_py; sourced from the single-source
# vocabulary so the catalog cannot drift between the compiler and the gates.
_PIN_KINDS = vocab.PIN_KINDS


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


def _target_px(cue: dict) -> Optional[Tuple[float, float]]:
    """The cue's declared focal pixel, or None if it declares none.

    Prefers the top-level anchor_px/anchor_py the compiler stamps (a pin's
    lat/lon pixel, or the [x,y] copied off a spatial_target.target_px), and falls
    back to spatial_target.target_px directly ([x,y] or [x,y,w,h]) so a cue is
    still alignable even if only the spatial_target survived. This is what makes
    the gate cover ANY cue carrying a spatial_target — not just map pins."""
    px, py = _num(cue.get("anchor_px")), _num(cue.get("anchor_py"))
    if px is not None and py is not None:
        return px, py
    st = cue.get("spatial_target")
    if isinstance(st, dict):
        tp = st.get("target_px")
        if isinstance(tp, (list, tuple)) and len(tp) >= 2:
            tx, ty = _num(tp[0]), _num(tp[1])
            if tx is not None and ty is not None:
                return tx, ty
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

    # A genuinely empty cuelist is the only legitimate empty pass: there is no
    # spatial claim to honour. (A populated cuelist with nothing alignable is a
    # FAIL below — the gate must not rubber-stamp a render it never inspected.)
    if not cues:
        return []

    # Collect every cue that declares WHERE it lands: a pin's lat/lon pixel
    # (anchor_px/anchor_py on a PIN kind) OR any cue carrying a spatial_target /
    # anchor_px/anchor_py (the compiler stamps both onto off-map action cues). We
    # verify the rendered marker against that declared pixel regardless of kind.
    targets = []          # (id, kind_label, px, py, start_s, end_s, anchor_color)
    saw_alignable = False  # any cue that declared a focal pixel at all
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError(f"cuelist.json cue #{i} is not an object")
        target = _target_px(cue)
        if target is None:
            continue  # cue makes no spatial claim (transition / camera / audio)
        saw_alignable = True
        px, py = target
        s, e = _num(cue.get("start_s")), _num(cue.get("end_s"))
        if s is None or e is None or e <= s:
            continue  # alignable in principle, but no on-screen window to sample
        # Label lat/lon pins as "pin" and everything else (spatial_target FX / scene
        # elements) as "cue" in diagnostics — _PIN_KINDS (vocab.PIN_KINDS) draws the
        # line, and a pin off its mark reads differently from an FX off its mark.
        label = "pin" if cue.get("kind") in _PIN_KINDS else "cue"
        targets.append(
            (cue.get("id", f"#{i}"), label, px, py, s, e, _anchor_color(cue)))

    # Cues exist but NONE declared a focal pixel (no pin, no spatial_target,
    # no anchor_px anywhere): the spatial-alignment rail has nothing to verify and
    # would otherwise pass vacuously. That is the documented rubber-stamp failure —
    # FAIL instead of an empty pass so a cuelist that lost all its anchors is caught.
    if not saw_alignable:
        return [Finding(
            "fail", "no_alignable_cues",
            f"cuelist has {len(cues)} cue(s) but not one declares a focal pixel "
            "(no pin anchor_px/anchor_py and no spatial_target anywhere) — there is "
            "nothing to align, so this gate cannot confirm anything rendered on its "
            "mark. A populated cuelist with zero spatial anchors is a compiler/"
            "authoring bug, not a clean pass.",
        )]

    if not targets:
        # Every alignable cue declared a pixel but none had a usable on-screen
        # window (missing/invalid start_s/end_s). We saw spatial claims yet cannot
        # sample any of them, so this too is a fail, not a silent pass.
        return [Finding(
            "fail", "no_sampleable_window",
            "every cue that declared a focal pixel is missing a valid on-screen "
            "window (start_s/end_s) — the marker positions cannot be sampled, so "
            "their alignment cannot be confirmed.",
        )]

    mp4 = _find_render(project_dir)
    for tool in ("ffprobe", "ffmpeg"):
        if shutil.which(tool) is None:
            raise GateInputError(
                f"{tool} not found on PATH; cannot inspect {mp4.name} for pin alignment"
            )
    frame_w, frame_h, duration = _probe_dims_duration(mp4)

    # Sample each cue past its drop-in (favour 60% through its life, clamped to
    # the render duration). Bucket identical times to decode each frame once.
    by_t: dict = {}
    for cid, label, px, py, s, e, color in targets:
        t = s + 0.6 * (e - s)
        t = min(max(t, 0.0), max(duration - 1e-3, 0.0))
        by_t.setdefault(round(t, 2), []).append((cid, label, px, py, color))

    findings: List[Finding] = []
    for t in sorted(by_t):
        frame = _extract_frame_rgb(mp4, t)
        fh, fw = frame.shape[:2]
        for cid, label, px, py, color in by_t[t]:
            where = f"{label} {cid} declared=({px:.0f},{py:.0f}) @ {t:.2f}s"

            # A declared pixel outside the rendered frame is itself the bug.
            if px < 0 or py < 0 or px > fw or py > fh:
                findings.append(Finding(
                    "fail", "pin_declared_off_frame",
                    f"declared focal pixel ({px:.0f},{py:.0f}) is outside the "
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
                    "search window around the declared focal pixel is empty (pixel "
                    "at the very frame edge) — cannot confirm the marker rendered.",
                    where=where,
                ))
                continue

            local = _marker_centroid(window, color)
            if local is None:
                findings.append(Finding(
                    "fail", "pin_not_found",
                    f"no marker found within {SEARCH_R}px of the declared pixel — "
                    "the cue did not render at its declared position (CSS offset, "
                    "wrong transform-origin, stale cached position, or unmounted "
                    "spatial_target layer).",
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
                    "tolerance) — the marker drifted off its declared geographic / "
                    "spatial_target position.",
                    where=where,
                ))

    return findings


if __name__ == "__main__":
    run_cli("qa_visual_alignment", check)
