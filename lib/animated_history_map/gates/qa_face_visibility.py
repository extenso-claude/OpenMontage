"""qa_face_visibility — character portraits/cutouts must show a visible, uncropped face.

Catches the "shippable" character-art bug where a CharacterCard / cutout ends up
with a placeholder, a thumbnail too small to read, or a face cropped off at the
frame edge. A face the viewer cannot see makes the card pointless.

Selection: from artifacts/asset_manifest.json, every asset whose
    category == 'portrait'  OR  whose id/kind contains
    'character' / 'cutout' / 'portrait'.
Each asset's 'path' is relative to the project dir.

Rule (fail), STRUCTURAL (no ML required):
  - the asset file must EXIST,
  - open as a valid image (PIL),
  - be >= 200x200 px,
  - if it declares a 'face_bbox' {x,y,w,h}: that box must lie FULLY within the
    image bounds AND cover >= 6% of the image area (a real face, not a sliver).

Optional ML cross-check: if cv2 is importable, run a Haar frontalface detector
and FAIL on zero detected faces OR a detected face box touching an image edge
(cropped). If cv2 is NOT importable, emit a single 'warn' that automated face
detection was skipped — never fail merely because cv2 is absent.

Reads:  <project>/artifacts/asset_manifest.json
Shape:  {"assets":[{"id","path","category","required"?:bool,
                    "kind"?, "face_bbox"?:{"x","y","w","h"}}]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

MIN_DIM = 200            # px floor on both width and height
MIN_FACE_AREA_FRAC = 0.06  # declared face_bbox must cover >= 6% of the image

# Substrings that mark an asset as a character/portrait even if category differs.
_CHARACTER_HINTS = ("character", "cutout", "portrait")


def _is_character_asset(asset: dict) -> bool:
    """True if this asset is a character portrait/cutout that must show a face."""
    category = asset.get("category")
    if isinstance(category, str) and category.strip().lower() == "portrait":
        return True
    for key in ("id", "kind"):
        val = asset.get(key)
        if isinstance(val, str):
            low = val.lower()
            if any(hint in low for hint in _CHARACTER_HINTS):
                return True
    return False


def _load_cv2():
    """Return the cv2 module if importable, else None (no hard dependency)."""
    try:
        import cv2  # type: ignore
        return cv2
    except Exception:
        return None


def _detect_faces_cv2(cv2, img_path: Path):
    """Return a list of (x, y, w, h) face boxes, or None if detection couldn't run.

    None means "the detector itself failed to load/read" (treated as a non-fatal
    skip), distinct from an empty list which means "ran, found zero faces".
    """
    try:
        import numpy as np  # noqa: F401  (cv2 pulls numpy; keep optional-safe)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(cascade_path)
        if cascade.empty():
            return None
        gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            return None
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        # detectMultiScale returns an ndarray (or empty tuple) of [x,y,w,h] rows.
        return [tuple(int(v) for v in box) for box in faces]
    except Exception:
        return None


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    manifest = load_json(project_dir / "artifacts" / "asset_manifest.json")
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise GateInputError("asset_manifest.json has no 'assets' array")

    # PIL is required for this gate's structural checks.
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover - PIL is an allowed/expected dep
        raise GateInputError(
            "Pillow (PIL) is required for qa_face_visibility but is not importable: "
            + str(exc)
        )

    cv2 = _load_cv2()

    findings: List[Finding] = []
    portraits = [a for a in assets if isinstance(a, dict) and _is_character_asset(a)]

    for asset in portraits:
        aid = asset.get("id") or "<unknown>"
        rel_path = asset.get("path")
        if not isinstance(rel_path, str) or not rel_path.strip():
            findings.append(Finding(
                "fail", "missing_path",
                "character asset has no usable 'path' to inspect",
                where=str(aid),
            ))
            continue

        img_path = (project_dir / rel_path).resolve()
        if not img_path.exists():
            findings.append(Finding(
                "fail", "asset_missing",
                "character portrait file does not exist at '{}' "
                "(placeholder / never sourced).".format(rel_path),
                where=str(aid),
            ))
            continue

        # Must open as a valid image.
        try:
            with Image.open(img_path) as im:
                im.verify()  # cheap integrity check
            with Image.open(img_path) as im:
                width, height = im.size  # reopen: verify() leaves the file unusable
        except Exception as exc:
            findings.append(Finding(
                "fail", "not_an_image",
                "could not open '{}' as a valid image: {}".format(rel_path, exc),
                where=str(aid),
            ))
            continue

        # Resolution floor.
        if width < MIN_DIM or height < MIN_DIM:
            findings.append(Finding(
                "fail", "too_small",
                "image is {}x{}px, below the {}x{}px floor — too small to read a face."
                .format(width, height, MIN_DIM, MIN_DIM),
                where=str(aid),
            ))
            continue

        # Declared face_bbox sanity: in-bounds and not a sliver.
        bbox = asset.get("face_bbox")
        if bbox is not None:
            bad = _check_face_bbox(bbox, width, height, aid)
            if bad is not None:
                findings.append(bad)
                continue

        # Optional ML cross-check.
        if cv2 is not None:
            faces = _detect_faces_cv2(cv2, img_path)
            if faces is None:
                findings.append(Finding(
                    "warn", "detector_unavailable",
                    "cv2 present but the Haar cascade could not run on '{}'; "
                    "skipped automated face detection.".format(rel_path),
                    where=str(aid),
                ))
            elif len(faces) == 0:
                findings.append(Finding(
                    "fail", "no_face_detected",
                    "Haar detector found no frontal face in '{}' — likely a "
                    "placeholder or non-portrait image.".format(rel_path),
                    where=str(aid),
                ))
            else:
                edge = _face_touches_edge(faces, width, height)
                if edge is not None:
                    findings.append(Finding(
                        "fail", "face_cropped",
                        "detected face box {} touches an image edge in '{}' — "
                        "the face is cropped.".format(edge, rel_path),
                        where=str(aid),
                    ))

    # If cv2 is entirely absent, emit ONE advisory warn for the whole gate
    # (never fail just because cv2 is missing).
    if cv2 is None and portraits:
        findings.append(Finding(
            "warn", "ml_detection_skipped",
            "cv2 is not importable; automated face detection was skipped. "
            "Structural checks (exists / valid image / >= {0}x{0}px / face_bbox) "
            "still ran.".format(MIN_DIM),
            where="qa_face_visibility",
        ))

    return findings


def _check_face_bbox(bbox: object, width: int, height: int, aid: object) -> Optional[Finding]:
    """Return a fail Finding if the declared face_bbox is malformed, out of
    bounds, or too small; else None."""
    if not isinstance(bbox, dict):
        return Finding(
            "fail", "bad_face_bbox",
            "face_bbox is declared but is not an object {x,y,w,h}",
            where=str(aid),
        )
    try:
        x = float(bbox["x"]); y = float(bbox["y"])
        w = float(bbox["w"]); h = float(bbox["h"])
    except (KeyError, TypeError, ValueError):
        return Finding(
            "fail", "bad_face_bbox",
            "face_bbox must carry numeric x, y, w, h",
            where=str(aid),
        )

    if w <= 0 or h <= 0:
        return Finding(
            "fail", "bad_face_bbox",
            "face_bbox has non-positive width/height ({}x{})".format(w, h),
            where=str(aid),
        )

    # Fully within image bounds.
    if x < 0 or y < 0 or (x + w) > width or (y + h) > height:
        return Finding(
            "fail", "face_out_of_bounds",
            "face_bbox (x={:.0f},y={:.0f},w={:.0f},h={:.0f}) runs off the "
            "{}x{}px image — the face is cropped.".format(x, y, w, h, width, height),
            where=str(aid),
        )

    # Area floor: a real face, not a sliver.
    frac = (w * h) / float(width * height)
    if frac < MIN_FACE_AREA_FRAC:
        return Finding(
            "fail", "face_too_small",
            "face_bbox covers only {:.1%} of the image (< {:.0%}) — a cropped "
            "sliver, not a visible face.".format(frac, MIN_FACE_AREA_FRAC),
            where=str(aid),
        )
    return None


def _face_touches_edge(faces, width: int, height: int):
    """Return the first detected face box that touches an image edge, else None."""
    for (fx, fy, fw, fh) in faces:
        if fx <= 0 or fy <= 0 or (fx + fw) >= width or (fy + fh) >= height:
            return (fx, fy, fw, fh)
    return None


if __name__ == "__main__":
    run_cli("qa_face_visibility", check)
