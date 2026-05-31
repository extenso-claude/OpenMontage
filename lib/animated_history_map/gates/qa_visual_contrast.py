"""qa_visual_contrast — rendered text/labels must read against their background.

Catches the documented "label too dark to read" failure (memory
map_legibility_rule / overlay_positioning_locked): a label, year stamp, or
chapter title is composited over a basemap region whose luminance is too close
to the ink, so the text vanishes. The container plays, the cue exists, the bbox
is in-bounds — and the viewer still cannot read the word. This gate inspects the
ACTUAL RENDERED PIXELS inside each declared text region and makes a low-contrast
label loud.

It works on the render (not on CSS): for every cue that declares on-screen TEXT
and a bbox, it grabs the rendered frame at the cue's mid-time, crops the bbox,
splits the crop into "ink" pixels (the extreme tail of the luminance histogram,
toward whichever pole the text sits) and "background" pixels (the dominant mass),
and computes the WCAG contrast ratio between the two luminances. Ratio below
MIN_CONTRAST (3.0 : 1 — the WCAG AA floor for large/bold text, which all of this
channel's overlays are) is a fail.

Selection: cues in cuelist.json whose ``kind`` is text-bearing (map_label,
time_stamp, concept_stamp, label_cluster, source_citation, etymology_card,
region_label_in, year_card_update, chapter_timeline_update, ...) OR that carry a
non-empty ``text``/``label`` string — AND that carry a usable bbox.

Rule (fail):
    * For each such cue, sample the render at t = midpoint(start_s, end_s).
    * Crop the declared bbox; if it has fewer than MIN_REGION_PX pixels, skip
      (too small to judge — a different gate owns "too small").
    * Estimate ink vs background luminance from the crop's luma histogram.
    * "fail" if the WCAG contrast ratio < MIN_CONTRAST.

A gate that cannot run must never silently pass, so:
    * no cuelist.json                     -> GateInputError (blocking)
    * neither mp4 present                  -> GateInputError
    * ffprobe/ffmpeg not on PATH           -> GateInputError
    * ffprobe cannot read a duration       -> GateInputError
    * a needed frame cannot be decoded     -> GateInputError
    * a declared bbox falls outside frame  -> "fail" (a label off-canvas is a bug)

Reads:   <project>/artifacts/cuelist.json
         <project>/renders/final.mp4   (fallback <project>/renders/master.mp4)
Shape:   {"cues":[{"id","kind","start_s","end_s",
                    "text"?|"label"?:str, "bbox":{"x","y","w","h"}}, ...]}
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

# WCAG AA contrast floor for large/bold text. Every overlay this channel ships is
# large display type, so 3.0:1 (not the 4.5:1 body-text floor) is the right gate.
MIN_CONTRAST = 3.0

# A region smaller than this (in pixels) is too small for a stable fg/bg split;
# "too small to read" belongs to a different gate, so we skip rather than guess.
MIN_REGION_PX = 400  # e.g. 20x20

# Fraction of the crop's pixels treated as the text "ink" tail of the histogram.
INK_FRACTION = 0.15

PROBE_TIMEOUT_S = 60
EXTRACT_TIMEOUT_S = 60

# Cue kinds that paint on-screen words even when no literal string is carried.
_TEXT_KINDS = frozenset({
    "map_label", "label_cluster", "time_stamp", "concept_stamp",
    "source_citation", "etymology_card", "region_label_in", "region_label_out",
    "year_card_update", "chapter_timeline_update", "year_sweep", "panel_quote",
    "concept_diagram",
})


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
        "exists (cannot check text contrast without a rendered video)"
    )


def _probe_dims_duration(mp4: Path) -> Tuple[int, int, float]:
    """(width, height, duration_s) via ffprobe. Any unreadable field is blocking."""
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height:format=duration",
            "-of", "json", str(mp4),
        ],
        capture_output=True, timeout=PROBE_TIMEOUT_S,
    )
    if proc.returncode != 0:
        raise GateInputError(f"ffprobe failed on {mp4.name}")
    try:
        meta = json.loads(proc.stdout.decode("utf-8", "replace"))
        stream = (meta.get("streams") or [{}])[0]
        w = int(stream["width"])
        h = int(stream["height"])
        dur = float(meta.get("format", {}).get("duration"))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise GateInputError(f"could not read width/height/duration from {mp4.name}: {exc}")
    if w <= 0 or h <= 0 or dur <= 0:
        raise GateInputError(f"non-positive width/height/duration from {mp4.name}")
    return w, h, dur


def _extract_frame_rgb(mp4: Path, t: float) -> np.ndarray:
    """Decode a single frame at timestamp ``t`` as an (H,W,3) uint8 RGB array.

    A frame we cannot decode is a frame we cannot clear -> blocking input error.
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
        raise GateInputError(f"could not extract a frame at {t:.2f}s from {mp4.name}")
    try:
        with Image.open(io.BytesIO(proc.stdout)) as im:
            return np.asarray(im.convert("RGB"), dtype=np.uint8)
    except (OSError, ValueError) as exc:
        raise GateInputError(f"could not decode the sampled frame at {t:.2f}s: {exc}")


def _rel_luminance(rgb: np.ndarray) -> np.ndarray:
    """WCAG relative luminance (0..1) for an array of sRGB pixels (...,3 uint8)."""
    srgb = rgb.astype(np.float64) / 255.0
    lin = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    return lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722


def _contrast_ratio(l1: float, l2: float) -> float:
    """WCAG contrast ratio between two relative luminances (order-independent)."""
    hi, lo = (l1, l2) if l1 >= l2 else (l2, l1)
    return (hi + 0.05) / (lo + 0.05)


def _ink_bg_luma(crop_rgb: np.ndarray) -> Tuple[float, float]:
    """Split a text crop into (ink_luma, background_luma) WCAG luminances.

    The background is the dominant luminance mass (median). The ink is the tail
    of the histogram on whichever side of the median holds the extreme pixels —
    light text on a dark plate OR dark text on a light plate, decided per-crop so
    the gate is theme-agnostic.
    """
    lum = _rel_luminance(crop_rgb).reshape(-1)
    median = float(np.median(lum))
    n_ink = max(1, int(len(lum) * INK_FRACTION))

    lo_tail = np.sort(lum)[:n_ink]              # darkest pixels
    hi_tail = np.sort(lum)[-n_ink:]             # brightest pixels
    # Ink is whichever tail is farther from the (background) median.
    dark_gap = median - float(lo_tail.mean())
    light_gap = float(hi_tail.mean()) - median
    if light_gap >= dark_gap:
        ink_luma = float(hi_tail.mean())
    else:
        ink_luma = float(lo_tail.mean())
    return ink_luma, median


def _is_text_cue(cue: dict) -> Optional[str]:
    """Return a short label for the cue's text if it bears on-screen words, else None."""
    txt = cue.get("text")
    if not isinstance(txt, str) or not txt.strip():
        txt = cue.get("label")
    if isinstance(txt, str) and txt.strip():
        return txt.strip()
    kind = cue.get("kind")
    if isinstance(kind, str) and kind in _TEXT_KINDS:
        return f"<{kind}>"
    return None


def _bbox(cue: dict) -> Optional[Tuple[float, float, float, float]]:
    box = cue.get("bbox")
    if not isinstance(box, dict):
        return None
    try:
        x = float(box["x"]); y = float(box["y"])
        w = float(box["w"]); h = float(box["h"])
    except (KeyError, TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    return x, y, w, h


def _num(value) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    mp4 = _find_render(project_dir)
    for tool in ("ffprobe", "ffmpeg"):
        if shutil.which(tool) is None:
            raise GateInputError(
                f"{tool} not found on PATH; cannot inspect {mp4.name} for text contrast"
            )

    frame_w, frame_h, duration = _probe_dims_duration(mp4)

    # Group text cues by the frame timestamp we will sample, so we decode each
    # needed frame at most once (cheap even with many labels).
    by_t: dict = {}
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError(f"cuelist.json cue #{i} is not an object")
        label = _is_text_cue(cue)
        if label is None:
            continue
        box = _bbox(cue)
        if box is None:
            continue
        s, e = _num(cue.get("start_s")), _num(cue.get("end_s"))
        if s is None or e is None or e <= s:
            continue
        t = min(max((s + e) / 2.0, 0.0), max(duration - 1e-3, 0.0))
        # Round to a frame-ish bucket so near-identical times share one decode.
        by_t.setdefault(round(t, 2), []).append((cue.get("id", f"#{i}"), label, box))

    findings: List[Finding] = []
    for t in sorted(by_t):
        frame = _extract_frame_rgb(mp4, t)
        fh, fw = frame.shape[:2]
        for cid, label, (x, y, w, h) in by_t[t]:
            x0, y0 = int(round(x)), int(round(y))
            x1, y1 = int(round(x + w)), int(round(y + h))
            where = f"cue {cid} '{label}' @ {t:.2f}s bbox=({x0},{y0},{int(round(w))}x{int(round(h))})"

            # A label whose box falls outside the rendered frame is itself a bug.
            if x0 < 0 or y0 < 0 or x1 > fw or y1 > fh:
                findings.append(Finding(
                    "fail", "text_bbox_off_frame",
                    f"declared text bbox runs outside the {fw}x{fh} rendered frame "
                    "— the label is partly/fully off-canvas.",
                    where=where,
                ))
                continue

            crop = frame[y0:y1, x0:x1]
            if crop.size == 0 or crop.shape[0] * crop.shape[1] < MIN_REGION_PX:
                continue  # too small to judge contrast here; not this gate's call

            ink, bg = _ink_bg_luma(crop)
            ratio = _contrast_ratio(ink, bg)
            if ratio < MIN_CONTRAST:
                findings.append(Finding(
                    "fail", "low_contrast",
                    f"rendered text contrast {ratio:.2f}:1 < {MIN_CONTRAST:.1f}:1 "
                    f"(ink luma {ink:.3f} vs background {bg:.3f}) — the label does "
                    "not read against the basemap region behind it.",
                    where=where,
                ))

    return findings


if __name__ == "__main__":
    run_cli("qa_visual_contrast", check)
