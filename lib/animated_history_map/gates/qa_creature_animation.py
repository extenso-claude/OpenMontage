"""qa_creature_animation — living creatures must actually MOVE on screen.

Catches the documented "living creatures animate" rule for the medium-diorama
tier (memory ahm_human_gates / animation-director medium_diorama checklist): a
horse, soldier, crowd, bird, or any living subject that is placed as a static
sprite reads as a cardboard cutout and breaks the diorama. The cue exists, the
geometry is fine, the frame isn't black — but the creature is frozen. This gate
samples several frames across the creature's on-screen life and FAILS if its
region does not change.

Selection: cues flagged as a living creature —
    * cue.get("is_creature") is True, OR
    * cue.get("creature") is truthy, OR
    * cue.get("tags") contains "creature"/"living", OR
    * cue.get("subject_kind") in {"creature","animal","person","crowd"}.
Each such cue must carry a bbox (the region to watch) and a finite
[start_s, end_s] life.

Rule (fail):
    * Sample N frames evenly across (start_s, end_s) (clamped past any pop-in).
    * Crop each frame to the creature's bbox and isolate the SUBJECT silhouette
      (bright tail of the crop) so a busy/compressed basemap behind a frozen
      sprite cannot fake motion.
    * Measure motion two ways and require EITHER to clear:
        - the fraction of the subject silhouette that changes between consecutive
          frames (animation-in-place: a galloping leg), vs MIN_SILHOUETTE_CHANGE;
        - travel of the subject silhouette's centroid between the first and last
          sample (bulk movement), vs MIN_CENTROID_TRAVEL_PX.
    * "fail" if BOTH are below threshold -> the creature is static.

A gate that cannot run must never silently pass:
    * no cuelist.json                     -> GateInputError (blocking)
    * neither mp4 present                  -> GateInputError
    * ffprobe/ffmpeg not on PATH           -> GateInputError
    * ffprobe cannot read a duration       -> GateInputError
    * a needed frame cannot be decoded     -> GateInputError
    * a creature cue without a bbox        -> "fail" (cannot place/animate it)

Reads:   <project>/artifacts/cuelist.json
         <project>/renders/final.mp4   (fallback <project>/renders/master.mp4)
Shape:   {"cues":[{"id","start_s","end_s","bbox":{"x","y","w","h"},
                    "is_creature"?:bool,"creature"?,"tags"?:[...],
                    "subject_kind"?:str}, ...]}
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

# Number of frames sampled across each creature's on-screen life.
N_SAMPLES = 5

# Motion is measured on the SUBJECT, not the whole crop, so a busy/compressed
# basemap behind a frozen sprite cannot masquerade as movement. We isolate the
# lit subject as the bright tail of the crop (pixels above the SUBJECT_PCTL
# luminance percentile) and watch that silhouette across frames.
SUBJECT_PCTL = 80.0

# Fraction of the subject-silhouette pixels that must CHANGE (appear/disappear)
# between consecutive samples for the body to count as animating in place
# (a galloping leg, a turning head). A frozen sprite's silhouette is identical
# frame-to-frame -> ~0. Robust to additive background noise because the basemap
# is dark and rarely crosses the bright-subject threshold.
MIN_SILHOUETTE_CHANGE = 0.06  # 6% of the body's pixels

# Travel (px) of the subject-silhouette centroid between first and last sample
# below which there is no bulk movement. A walking/running subject moves many px.
MIN_CENTROID_TRAVEL_PX = 3.0

# Fraction of the life to start/stop sampling, skipping pop-in / pop-out so a
# static body during a fade is not mistaken for motion (and vice-versa).
LIFE_PAD = 0.15

PROBE_TIMEOUT_S = 60
EXTRACT_TIMEOUT_S = 60

_CREATURE_SUBJECTS = frozenset({"creature", "animal", "person", "crowd", "horse", "bird"})
_CREATURE_TAGS = frozenset({"creature", "living", "animal", "person", "crowd"})


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
        "exists (cannot check creature animation without a rendered video)"
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


def _extract_luma_crop(mp4: Path, t: float, box: Tuple[int, int, int, int]) -> np.ndarray:
    """Decode the frame at ``t`` and return the luma (float) crop of ``box``."""
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
    x0, y0, x1, y1 = box
    luma = arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114
    return luma[y0:y1, x0:x1]


def _num(value) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _is_creature(cue: dict) -> bool:
    if cue.get("is_creature") is True:
        return True
    if cue.get("creature"):
        return True
    sk = cue.get("subject_kind")
    if isinstance(sk, str) and sk.strip().lower() in _CREATURE_SUBJECTS:
        return True
    tags = cue.get("tags")
    if isinstance(tags, (list, tuple)):
        for tg in tags:
            if isinstance(tg, str) and tg.strip().lower() in _CREATURE_TAGS:
                return True
    return False


def _bbox(cue: dict) -> Optional[Tuple[float, float, float, float]]:
    box = cue.get("bbox")
    if not isinstance(box, dict):
        return None
    x, y, w, h = (_num(box.get(k)) for k in ("x", "y", "w", "h"))
    if None in (x, y, w, h) or w <= 0 or h <= 0:
        return None
    return x, y, w, h


def _subject_mask(crop: np.ndarray, threshold: float) -> np.ndarray:
    """Boolean silhouette of the lit subject: pixels brighter than ``threshold``.

    Isolating the bright subject from the dark basemap makes the motion signal
    robust to additive background noise / compression dither (which sits down in
    the dark levels and rarely crosses the subject threshold)."""
    return crop >= threshold


def _mask_centroid(mask: np.ndarray) -> Optional[Tuple[float, float]]:
    """Centroid (cx, cy) of a boolean silhouette, local to the crop."""
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return None
    return float(xs.mean()), float(ys.mean())


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    creatures = []
    findings: List[Finding] = []
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError(f"cuelist.json cue #{i} is not an object")
        if not _is_creature(cue):
            continue
        cid = cue.get("id", f"#{i}")
        box = _bbox(cue)
        s, e = _num(cue.get("start_s")), _num(cue.get("end_s"))
        if box is None:
            findings.append(Finding(
                "fail", "creature_without_bbox",
                "cue is flagged as a living creature but declares no bbox — it "
                "cannot be placed or verified as animating.",
                where=str(cid),
            ))
            continue
        if s is None or e is None or e <= s:
            findings.append(Finding(
                "fail", "creature_without_life",
                "cue is flagged as a living creature but has no on-screen "
                "[start_s, end_s] window to sample for motion.",
                where=str(cid),
            ))
            continue
        creatures.append((cid, box, s, e))

    if not creatures:
        return findings  # no creatures with a valid life -> nothing to sample

    mp4 = _find_render(project_dir)
    for tool in ("ffprobe", "ffmpeg"):
        if shutil.which(tool) is None:
            raise GateInputError(
                f"{tool} not found on PATH; cannot inspect {mp4.name} for creature motion"
            )
    frame_w, frame_h, duration = _probe_dims_duration(mp4)

    for cid, (bx, by, bw, bh), s, e in creatures:
        # Clamp the bbox into the frame so the crop is always valid.
        x0 = max(0, int(round(bx)))
        y0 = max(0, int(round(by)))
        x1 = min(frame_w, int(round(bx + bw)))
        y1 = min(frame_h, int(round(by + bh)))
        where = f"creature {cid} bbox=({x0},{y0},{x1 - x0}x{y1 - y0})"
        if x1 - x0 < 2 or y1 - y0 < 2:
            findings.append(Finding(
                "fail", "creature_bbox_off_frame",
                "creature bbox does not intersect the rendered frame in a usable "
                "area — cannot sample it for motion.",
                where=where,
            ))
            continue

        # Sample times across the padded life, clamped to the render duration.
        t_lo = s + LIFE_PAD * (e - s)
        t_hi = e - LIFE_PAD * (e - s)
        if t_hi <= t_lo:
            t_lo, t_hi = s, e
        times = [
            min(max(t_lo + (t_hi - t_lo) * k / (N_SAMPLES - 1), 0.0),
                max(duration - 1e-3, 0.0))
            for k in range(N_SAMPLES)
        ]

        crops = [_extract_luma_crop(mp4, t, (x0, y0, x1, y1)) for t in times]

        # Isolate the lit subject per frame with a single threshold derived from
        # the whole sampled window (so the silhouette is comparable across frames).
        stack = np.concatenate([c.reshape(-1) for c in crops])
        threshold = float(np.percentile(stack, SUBJECT_PCTL))
        masks = [_subject_mask(c, threshold) for c in crops]

        # (a) Silhouette change between consecutive frames, as a fraction of the
        #     average body size — robust to additive background noise.
        changes = []
        for k in range(len(masks) - 1):
            a, b = masks[k], masks[k + 1]
            body = (a.sum() + b.sum()) / 2.0
            if body <= 0:
                continue
            changed = float(np.logical_xor(a, b).sum())
            changes.append(changed / body)
        silhouette_change = float(np.max(changes)) if changes else 0.0

        # (b) Bulk travel of the subject silhouette's centroid.
        c_first = _mask_centroid(masks[0])
        c_last = _mask_centroid(masks[-1])
        if c_first is not None and c_last is not None:
            travel = float(np.hypot(c_last[0] - c_first[0], c_last[1] - c_first[1]))
        else:
            travel = 0.0

        moved = (silhouette_change >= MIN_SILHOUETTE_CHANGE) or (travel >= MIN_CENTROID_TRAVEL_PX)
        if not moved:
            findings.append(Finding(
                "fail", "creature_static",
                f"living creature does not move: subject-silhouette change "
                f"{silhouette_change:.3f} (< {MIN_SILHOUETTE_CHANGE:.2f}) and "
                f"centroid travel {travel:.2f}px (< {MIN_CENTROID_TRAVEL_PX:.1f}px) "
                f"across {N_SAMPLES} samples of [{s:.2f}..{e:.2f}s] — it rendered "
                "as a frozen cardboard cutout.",
                where=where,
            ))

    return findings


if __name__ == "__main__":
    run_cli("qa_creature_animation", check)
