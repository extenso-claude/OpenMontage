"""qa_source_collision — an overlay must never cover the SOURCE video's baked UI.

The overlay layer is composited ABOVE a finished source MP4 that already carries
its own burned-in elements: a baked chyron / lower-third, a "SUBSCRIBE" stack, a
"leave a comment" speech bubble, a (stale, previous-episode) title card, and
on-screen faces. Placing an overlay card on top of any of the HARD elements
hides the source's own UI underneath — the documented Rule 3 (source-aware
placement) failure (memory overlay_positioning_locked): a chapter title cue
dropped over the source's baked "Chapter X: Jim Jones" template, or a photo card
slapped over the baked SUBSCRIBE stack. Those are hard rules. A face overlap is
softer (sometimes a portrait corner over a tight chyron is intentional) so it
warns rather than blocks.

Rule:
  For every overlay cue carrying a bbox, against every baked source element:
    * if their time windows overlap ([t_in, t_out] vs the element's [t_in, t_out])
      AND their bboxes intersect (axis-aligned, top-left origin) ->
        - element type in {chyron, subscribe, comment_bubble, title} -> "fail"
          (an overlay must NEVER cover the source's baked chyron/SUBSCRIBE/
           comment-bubble/title), reported as `covers_baked_<type>`.
        - element type == "face" -> "warn" (`overlaps_source_face`); manual
          override allowed when intentional.
  A cue with no bbox is skipped (nothing to collide). Touching edges / touching
  end-to-end is NOT an overlap (mirrors qa_element_overlap).

Missing artifacts/source_baked_elements.json -> GateInputError: with no catalog
of what the source baked in, source collision CANNOT be verified, and a gate that
cannot run must never silently pass.

The optional OpenCV/Mediapipe face detection on the actual source frames is only
attempted when rendered frames are present; on artifacts alone it skips with a
note so the gate stays deterministically fixture-testable.

Reads:  <project>/artifacts/cuelist.json
        <project>/artifacts/source_baked_elements.json
        <project>/renders/source_frames/  (OPTIONAL — face auto-detect only)
Shapes (only the fields this gate reads):
    cuelist               = {"cues": [
        {"id", "kind", "t_in", "t_out", "bbox"?: {"x","y","w","h"}, ...}, ...]}
    source_baked_elements = {"elements": [
        {"type": "chyron"|"subscribe"|"comment_bubble"|"title"|"face",
         "t_in", "t_out", "bbox": {"x","y","w","h"}}, ...]}
        bbox is in pixels in a 1920x1080 canvas, top-left origin.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

EPSILON = 1e-6

# Source elements an overlay may NEVER cover (hard rule -> "fail"). Anything else
# recognized as a face is advisory ("warn"); an unknown element type is treated
# as a hard zone too (fail-safe: better to block than to wave through a baked UI
# region we don't recognize).
HARD_TYPES = {"chyron", "subscribe", "comment_bubble", "title"}
FACE_TYPES = {"face"}


def _num(value) -> Optional[float]:
    """Return value as float if it is a real number, else None.

    bool is an int subclass — reject it explicitly so True/False can't pose as a
    coordinate or a timestamp.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _bbox(obj: dict) -> Optional[Tuple[float, float, float, float]]:
    """Return (x, y, w, h) as floats if `obj` carries a usable bbox, else None.

    A degenerate box (w<=0 or h<=0) covers no pixels and cannot collide.
    """
    box = obj.get("bbox")
    if not isinstance(box, dict):
        return None
    x, y, w, h = (_num(box.get(k)) for k in ("x", "y", "w", "h"))
    if x is None or y is None or w is None or h is None:
        return None
    if w <= 0 or h <= 0:
        return None
    return (x, y, w, h)


def _time_overlap(
    a_in: Optional[float], a_out: Optional[float],
    b_in: Optional[float], b_out: Optional[float],
) -> bool:
    """True iff [a_in, a_out] and [b_in, b_out] share an open span.

    Touching end-to-end (a ends exactly when b starts) is NOT an overlap — the
    two are never on screen simultaneously. A missing/non-numeric bound on EITHER
    side is treated as "could be on screen at any time": we cannot prove the
    windows are disjoint, so we do not exonerate the cue on timing alone (the
    collision is then decided purely by geometry). This keeps a malformed/omitted
    time from silently letting an overlay sit on a baked chyron.
    """
    if a_in is None or a_out is None or b_in is None or b_out is None:
        return True
    return (a_in < b_out - EPSILON) and (b_in < a_out - EPSILON)


def _rects_intersect(
    r1: Tuple[float, float, float, float],
    r2: Tuple[float, float, float, float],
) -> bool:
    """True iff two axis-aligned rectangles (x, y, w, h, top-left origin) overlap.

    Edge-touching (shared border, zero overlap area) is NOT a collision.
    """
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    if x1 + w1 <= x2 + EPSILON or x2 + w2 <= x1 + EPSILON:
        return False
    if y1 + h1 <= y2 + EPSILON or y2 + h2 <= y1 + EPSILON:
        return False
    return True


def _load_baked_elements(project_dir: Path) -> List[dict]:
    """Load + validate the baked-element catalog.

    Missing file -> GateInputError (handled by load_json). A present-but-malformed
    catalog is also a blocking input error: we cannot verify collisions against a
    catalog we can't read.
    """
    data = load_json(project_dir / "artifacts" / "source_baked_elements.json")
    elements = data.get("elements")
    if not isinstance(elements, list):
        raise GateInputError(
            "source_baked_elements.json has no 'elements' array — cannot verify "
            "source collision"
        )
    return elements


def _frames_present(project_dir: Path) -> bool:
    """True iff rendered source frames exist (enables the optional face detector)."""
    frame_dir = project_dir / "renders" / "source_frames"
    if not frame_dir.is_dir():
        return False
    for pattern in ("*.png", "*.jpg", "*.jpeg"):
        if any(frame_dir.glob(pattern)):
            return True
    return False


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    # 1) Baked-element catalog is REQUIRED. No catalog => cannot verify => block.
    elements = _load_baked_elements(project_dir)

    # 2) Overlay cuelist.
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    # Pre-extract baked regions once. Each entry must carry a real bbox; a baked
    # element without a usable bbox is a malformed catalog (we can't tell what it
    # covers) -> blocking input error rather than a silent skip.
    baked: List[Tuple[str, Tuple[float, float, float, float], Optional[float], Optional[float]]] = []
    for i, el in enumerate(elements):
        if not isinstance(el, dict):
            raise GateInputError(
                "source_baked_elements.json element #{0} is not an object".format(i)
            )
        etype = str(el.get("type") or "").strip().lower()
        if not etype:
            raise GateInputError(
                "source_baked_elements.json element #{0} has no 'type'".format(i)
            )
        ebox = _bbox(el)
        if ebox is None:
            raise GateInputError(
                "source_baked_elements.json element #{0} ({1}) has no usable bbox "
                "(needs numeric x/y/w/h, w>0, h>0) — cannot verify collision".format(
                    i, etype)
            )
        baked.append((etype, ebox, _num(el.get("t_in")), _num(el.get("t_out"))))

    findings: List[Finding] = []

    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError("cuelist.json cue #{0} is not an object".format(i))
        cid = str(cue.get("id") or "#{0}".format(i))
        cbox = _bbox(cue)
        if cbox is None:
            continue  # no geometry -> nothing to collide with the source

        c_in = _num(cue.get("t_in"))
        c_out = _num(cue.get("t_out"))

        for etype, ebox, e_in, e_out in baked:
            if not _time_overlap(c_in, c_out, e_in, e_out):
                continue  # cue and baked element are never on screen together
            if not _rects_intersect(cbox, ebox):
                continue  # on screen together but geometrically clear

            win = ""
            if e_in is not None and e_out is not None:
                win = " (baked window {0:.2f}-{1:.2f}s)".format(e_in, e_out)

            if etype in FACE_TYPES:
                findings.append(Finding(
                    "warn", "overlaps_source_face",
                    "overlay cue '{0}' bbox overlaps the source's on-screen "
                    "face{1} — confirm this is intentional (e.g. a portrait "
                    "corner), otherwise it hides the source character".format(
                        cid, win),
                    where=cid))
            else:
                # HARD_TYPES, plus any unrecognized type (fail-safe).
                label = etype if etype in HARD_TYPES else "unknown:{0}".format(etype)
                findings.append(Finding(
                    "fail", "covers_baked_{0}".format(
                        etype if etype in HARD_TYPES else "element"),
                    "overlay cue '{0}' covers the source's baked {1}{2} — an "
                    "overlay must NEVER sit on top of the source's "
                    "chyron/SUBSCRIBE/comment-bubble/title".format(cid, label, win),
                    where=cid))

    # OPTIONAL: face auto-detection on the real source frames. Deterministically
    # skipped (advisory note) when no frames are present, so the gate is fully
    # testable on artifacts alone.
    if _frames_present(project_dir):
        findings.append(Finding(
            "warn", "frame_face_scan_skipped",
            "rendered source frames are present but on-frame face auto-detection "
            "(OpenCV/Mediapipe) is not run in this environment — verify face "
            "overlaps against the catalog manually",
            where="renders/source_frames"))

    return findings


if __name__ == "__main__":
    run_cli("qa_source_collision", check)
