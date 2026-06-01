"""qa_rendered_sync — the cue actually PAINTED at the spoken word, in the right place.

The synchrony chain has three links and the prior gates only prove the first two:
qa_cue_drift proves a cue's TIME is anchored to a narrated word; qa_spatial_anchor
proves it declares WHERE on the frame it lands; qa_visual_alignment proves a *pin*
marker landed on its lat/lon pixel. The hole the swarm found is the conjunction —
"at the instant the narrator says the word, did the declared thing actually render
at its declared spot?" A cue can be perfectly time-anchored and perfectly
spatially-targeted and STILL ship a black hole: the GSAP enter fired a beat late,
the sub-comp never mounted, the layer was z-ordered under the basemap, or the
asset 404'd — so the frame sampled AT the anchor word shows background where the
cue should be. `lint`/`validate` and the timing/spatial gates cannot see that;
only the rendered pixels can. This gate closes the link by sampling the actual
frame at each high-priority cue's anchor and confirming the cue's color is present
AT its target pixel.

For each HIGH-PRIORITY cue — one that declares BOTH a resolved anchor_time_s AND a
target pixel (anchor_px/anchor_py or spatial_target.target_px) AND an anchor_color
(the [r,g,b] of its rendered content) — the gate:
    * loads the authored frame for that cue at renders/frames/at_<cue_id>.png
      (the compiler samples the master at anchor_time_s and writes this PNG; the
      fixture authors a tiny PNG so the gate stays ffmpeg-free);
    * searches a (2*SEARCH_R) window centred on the target pixel for pixels within
      COLOR_TOL of anchor_color;
    * FAIL "cue_absent_at_anchor" if NO matching pixels are found in the window —
      the declared region shows only background, i.e. the cue did not paint at the
      spoken word (late enter / unmounted sub-comp / z-order / 404 asset);
    * FAIL "cue_misplaced_at_anchor" if matching pixels exist but their centroid is
      > TOL_PX from the target pixel — the cue rendered, but off its mark.

A high-priority cue that is missing its frame PNG, or whose target pixel falls off
the rendered frame, is itself the bug (a gate that cannot run must never silently
pass) and is reported — frame absence as a BLOCKING GateInputError (we cannot clear
a sync we cannot inspect), an off-frame target as a "fail".

Tolerances are deliberately generous (a glyph's own radius + sub-frame seek slop is
fine; a real miss is the whole window empty or a centroid tens-to-hundreds of px
off), and documented at their constants below.

Reads:   <project>/artifacts/cuelist.json
         <project>/renders/frames/at_<cue_id>.png   (one authored PNG per HP cue)
Shape:   {"cues":[{"id","kind","layer","start_s","end_s",
                    "anchor_time_s":num,
                    "anchor_px":num,"anchor_py":num,         # or:
                    "spatial_target":{"target_px":[x,y(,w,h)]},
                    "anchor_color":[r,g,b],
                    "placement"?:"on_action"|"chrome"}, ...]}
Allowed: numpy / PIL (already used by sibling render gates). If PIL is unavailable
         the gate raises GateInputError (blocking) rather than skipping.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from ._contract import Finding, GateInputError, load_json, run_cli

try:
    from PIL import Image
    _PIL_OK = True
except Exception:  # pragma: no cover - exercised only where PIL is absent
    _PIL_OK = False

# Max allowed gap between a cue's target pixel and the centroid of its rendered
# color in the frame. Generous enough for the rendered glyph/sprite's own radius
# plus sub-frame seek slop, tight enough that a cue painted on the wrong actor
# (tens-to-hundreds of px away) always trips cue_misplaced_at_anchor.
TOL_PX = 30.0

# Half-size of the search window around the target pixel. Wider than TOL_PX so a
# near-miss is MEASURED (caught as misplaced) rather than missed entirely; nothing
# matching inside this box means the cue did not paint anywhere near its mark.
SEARCH_R = 100

# Per-channel (0..255) match radius around anchor_color, as Euclidean RGB distance.
# Wide enough to survive noir grading / mild antialias on the cue's fill, tight
# enough that the dark background of a noir frame never counts as a match.
COLOR_TOL = 60.0

# A handful of matching pixels in the window is enough to call the cue "present";
# fewer than this is treated as background speckle / JPEG ringing, not the cue.
MIN_MATCH_PIXELS = 6

# Only cues that must sit on the narrated action are sync-checked. A "chrome" cue
# (year card, badge, citation) is intentionally action-independent and is skipped.
_CHROME = "chrome"


def _num(value) -> Optional[float]:
    # bool is an int subclass; True/False is never a coordinate or a timestamp.
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
    """The cue's authored target pixel: top-level anchor_px/anchor_py, else the
    first two entries of spatial_target.target_px ([x,y] or [x,y,w,h])."""
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


def _load_frame_rgb(path: Path) -> np.ndarray:
    """Decode the authored cue frame to an (H,W,3) uint8 array. Raises
    GateInputError if the PNG is missing or undecodable — a frame we cannot read
    is a sync we cannot clear."""
    if not path.exists() or not path.is_file():
        raise GateInputError(
            "required cue frame not found: {0} (the compiler must sample the master "
            "at the cue's anchor_time_s and write this PNG; without it the cue's "
            "on-screen presence cannot be verified)".format(path)
        )
    try:
        with Image.open(path) as im:
            return np.asarray(im.convert("RGB"), dtype=np.uint8)
    except (OSError, ValueError) as exc:
        raise GateInputError("could not decode cue frame {0}: {1}".format(path, exc))


def _match_centroid(
    window: np.ndarray, color: np.ndarray
) -> Tuple[int, Optional[Tuple[float, float]]]:
    """(match_count, (cx,cy) local to the window) for pixels within COLOR_TOL of
    ``color``; centroid is None when nothing matches. Coords are window-local
    (0,0 = window top-left)."""
    rgb = window.astype(np.float64)
    dist = np.sqrt(((rgb - color) ** 2).sum(axis=2))
    mask = dist <= COLOR_TOL
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return 0, None
    return int(xs.size), (float(xs.mean()), float(ys.mean()))


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    if not _PIL_OK:
        raise GateInputError(
            "PIL (Pillow) is not importable; qa_rendered_sync cannot decode the "
            "sampled cue frames and must not silently pass"
        )

    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    frames_dir = project_dir / "renders" / "frames"

    findings: List[Finding] = []
    checked_any = False

    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError("cuelist.json cue #{0} is not an object".format(i))

        # A cue is HIGH-PRIORITY (sync-verified) only if it carries all three of:
        # a resolved anchor_time_s, a target pixel, and an anchor_color. Anything
        # missing one of those is a lint concern for OTHER gates, not this one
        # (this gate verifies the rendered pixel, it does not police completeness).
        if (cue.get("placement") or "on_action") == _CHROME:
            continue
        t = _num(cue.get("anchor_time_s"))
        if t is None:
            continue
        target = _target_px(cue)
        color = _anchor_color(cue)
        if target is None or color is None:
            continue

        cid = cue.get("id")
        if not isinstance(cid, str) or not cid:
            cid = "#{0}".format(i)
        tx, ty = target
        where = "cue {0} target=({1:.0f},{2:.0f}) @ {3:.2f}s".format(cid, tx, ty, t)

        frame = _load_frame_rgb(frames_dir / "at_{0}.png".format(cid))
        checked_any = True
        fh, fw = frame.shape[:2]

        # A target pixel off the rendered frame is itself the bug (the cue/anchor
        # places the action off-canvas) — and we cannot search around it.
        if tx < 0 or ty < 0 or tx > fw or ty > fh:
            findings.append(Finding(
                "fail", "cue_target_off_frame",
                "target pixel ({0:.0f},{1:.0f}) is outside the {2}x{3} rendered "
                "frame — the cue's spatial_target/anchor places it off-canvas.".format(
                    tx, ty, fw, fh),
                where=where))
            continue

        x0 = max(0, int(round(tx)) - SEARCH_R)
        y0 = max(0, int(round(ty)) - SEARCH_R)
        x1 = min(fw, int(round(tx)) + SEARCH_R)
        y1 = min(fh, int(round(ty)) + SEARCH_R)
        window = frame[y0:y1, x0:x1]
        if window.size == 0:
            findings.append(Finding(
                "fail", "cue_search_empty",
                "search window around the target pixel is empty (pixel at the very "
                "frame edge) — cannot confirm the cue painted at the spoken word.",
                where=where))
            continue

        count, local = _match_centroid(window, color)
        if local is None or count < MIN_MATCH_PIXELS:
            findings.append(Finding(
                "fail", "cue_absent_at_anchor",
                "no cue content (color {0}) found within {1}px of the target pixel "
                "in the frame sampled at the anchor word — the cue did not paint at "
                "the narrated moment (late GSAP enter, unmounted sub-comp, z-order "
                "under the basemap, or a 404 asset).".format(
                    color.astype(int).tolist(), SEARCH_R),
                where=where))
            continue

        cx = x0 + local[0]
        cy = y0 + local[1]
        err = float(np.hypot(cx - tx, cy - ty))
        if err > TOL_PX:
            findings.append(Finding(
                "fail", "cue_misplaced_at_anchor",
                "the cue's rendered content centroid ({0:.0f},{1:.0f}) is {2:.0f}px "
                "from its target pixel ({3:.0f},{4:.0f}) (> {5:.0f}px tolerance) — "
                "it painted at the spoken word but off its mark.".format(
                    cx, cy, err, tx, ty, TOL_PX),
                where=where))

    if not checked_any:
        # No high-priority cue carried time + target + color, so there was nothing
        # to verify. That is a legitimate pass for THIS gate (presence/completeness
        # of those fields is enforced by qa_cue_drift / qa_spatial_anchor), and an
        # informational note keeps it from looking like a silent skip.
        return [Finding(
            "warn", "no_high_priority_cues",
            "no cue declared anchor_time_s + a target pixel + anchor_color; nothing "
            "to rendered-sync (timing/spatial completeness is policed elsewhere).")]

    return findings


if __name__ == "__main__":
    run_cli("qa_rendered_sync", check)
