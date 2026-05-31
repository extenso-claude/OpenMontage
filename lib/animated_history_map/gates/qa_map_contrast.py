"""qa_map_contrast — a rendered basemap must have real land/water contrast.

The documented Lincoln-map failure: maps were rendered from carto_dark tiles
through style_warm. carto_dark water is dark-GRAY (R≈G≈B, no blue dominance), so
style_warm's "blue beats red" water test misfired, classified ~the whole frame as
land, and collapsed every basemap to ONE flat parchment tone — no blue water, no
land/coast separation, near-zero variance. `lint` and `validate` can't see that:
the PNG exists, has the right dimensions, and opens fine. A human only catches it
by eyeballing the render. This gate makes the collapse loud by sampling the actual
pixels of every basemap PNG and failing on any of three symptoms.

Per-basemap rule (thresholds are THEME-DRIVEN, read from theme.json's
``palette_master.basemap_colors``):
    (a) no distinct water — the fraction of pixels near the theme's water hue is
        below WATER_FRAC_MIN (the monochrome-parchment frame has ~0% blue water);
    (b) land↔water separation — the perceptual distance between the dominant
        "land cluster" and the "water cluster" is below the theme's contrast_min
        (a sepia-on-sepia frame has water the same hue as land);
    (c) near-uniform frame — whole-frame luma std-dev is below the theme's
        variance_min (the entire map is one tone).

A gate that cannot run must never silently pass, so:
    * no basemap PNG found under assets/maps/   -> GateInputError (blocking)
    * theme.json missing/unreadable             -> GateInputError
    * a basemap PNG that cannot be decoded       -> GateInputError
        (a map we can't inspect is not a map we can clear)

Theme-color resolution is delegated to the same engine the renderer uses
(``lib.mapkit_subjects.load_basemap_colors``) — the gate never re-derives the
water hue; it checks against exactly the spec the render was told to hit.

Reads:   <project>/assets/maps/*.png  +  <project>/artifacts/theme.json
Allowed: numpy / PIL (no required pip deps beyond what the renderer already uses).
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

from ._contract import Finding, GateInputError, load_json, run_cli  # noqa: F401

# A basemap that is supposed to show coastline/ocean must have at least this
# fraction of pixels near the themed water hue. The collapsed parchment frame has
# essentially 0%; any real CONUS / regional / coastal extent clears a few percent.
# Deliberately low so a genuinely water-light inland city extent still passes if it
# has SOME water — the separation + variance checks carry the rest.
WATER_FRAC_MIN = 0.015

# Color-distance radius (RGB Euclidean, 0..441) for "near the themed water hue".
# Wide enough to catch depth-shaded water, tight enough to exclude parchment land.
WATER_MATCH_RADIUS = 55.0

# Downsample long edge before sampling: pixel statistics are stable at this size
# and it keeps the gate fast on 1920×1080 PNGs.
SAMPLE_LONG_EDGE = 480


def _find_basemaps(project_dir: Path) -> List[Path]:
    """Every basemap PNG under assets/maps/ (excluding the tile cache).

    None found is a BLOCKING input error: a map-contrast gate that inspects no
    map must not report a pass.
    """
    maps_dir = project_dir / "assets" / "maps"
    if not maps_dir.is_dir():
        raise GateInputError(
            f"no assets/maps directory under {project_dir} — nothing to inspect "
            "for map contrast"
        )
    pngs = [
        p for p in sorted(maps_dir.glob("*.png"))
        if "_tile_cache" not in p.parts
    ]
    if not pngs:
        raise GateInputError(
            f"no basemap PNGs found in {maps_dir} (cannot verify land/water "
            "contrast without a rendered basemap)"
        )
    return pngs


def _load_rgb(png: Path) -> np.ndarray:
    """Decode a PNG to an HxWx3 float32 RGB array, downsampled for speed.

    A basemap we can't decode is a basemap we can't clear -> blocking.
    """
    try:
        with Image.open(png) as im:
            im = im.convert("RGB")
            w, h = im.size
            scale = SAMPLE_LONG_EDGE / float(max(w, h))
            if scale < 1.0:
                im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))))
            return np.asarray(im, dtype=np.float32)
    except (OSError, ValueError) as exc:
        raise GateInputError(f"could not decode basemap {png.name}: {exc}")


def _water_fraction(arr: np.ndarray, water_rgb: Tuple[int, int, int]) -> float:
    """Fraction of pixels within WATER_MATCH_RADIUS of the themed water hue."""
    wr = np.asarray(water_rgb, dtype=np.float32)
    dist = np.linalg.norm(arr - wr[None, None, :], axis=2)
    return float((dist < WATER_MATCH_RADIUS).mean())


def _luma(arr: np.ndarray) -> np.ndarray:
    return arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114


def _perceptual_sep(land_rgb: np.ndarray, water_rgb: np.ndarray) -> float:
    """Land↔water separation = luma distance + chroma distance.

    Chroma is measured in (R-G, G-B) opponent space so two colors with the same
    brightness but different hue (the exact sepia-water-on-parchment-land failure)
    still register a large separation. The sum mirrors how a viewer reads "these
    are clearly different regions".
    """
    luma_d = abs(float(_luma(land_rgb[None, None, :])[0, 0])
                 - float(_luma(water_rgb[None, None, :])[0, 0]))
    l_rg, l_gb = land_rgb[0] - land_rgb[1], land_rgb[1] - land_rgb[2]
    w_rg, w_gb = water_rgb[0] - water_rgb[1], water_rgb[1] - water_rgb[2]
    chroma_d = float(np.hypot(l_rg - w_rg, l_gb - w_gb))
    return luma_d + chroma_d


def _land_water_clusters(arr: np.ndarray,
                         water_rgb: Tuple[int, int, int]
                         ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """Split pixels into a water cluster (near the themed water hue) and a land
    cluster (the rest), returning each cluster's mean RGB.

    Returns None when one side is essentially empty (a collapsed monochrome frame
    has no water cluster) — the caller treats that as "no separation measurable",
    which the water-fraction check has already flagged.
    """
    wr = np.asarray(water_rgb, dtype=np.float32)
    flat = arr.reshape(-1, 3)
    dist = np.linalg.norm(flat - wr[None, :], axis=1)
    water_mask = dist < WATER_MATCH_RADIUS
    land_mask = ~water_mask
    if water_mask.sum() < 50 or land_mask.sum() < 50:
        return None
    return flat[land_mask].mean(axis=0), flat[water_mask].mean(axis=0)


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    # Theme drives every threshold; its absence is blocking (we can't know the
    # water hue or the separation floor without it).
    theme = load_json(project_dir / "artifacts" / "theme.json")

    # Resolve the SAME color spec the renderer used — never re-derive the hue.
    try:
        import sys as _sys
        repo_root = Path(__file__).resolve().parents[3]
        if str(repo_root) not in _sys.path:
            _sys.path.insert(0, str(repo_root))
        from lib import mapkit_subjects as mk  # noqa: WPS433 (local import intentional)
    except Exception as exc:  # noqa: BLE001
        raise GateInputError(
            f"cannot import lib.mapkit_subjects (needed to resolve the theme's "
            f"basemap colors the same way the render did): {exc}"
        )
    colors = mk.load_basemap_colors(theme)
    water_rgb = colors.water_rgb
    contrast_min = colors.contrast_min
    variance_min = colors.variance_min

    pngs = _find_basemaps(project_dir)
    findings: List[Finding] = []

    for png in pngs:
        rel = png.relative_to(project_dir).as_posix()
        arr = _load_rgb(png)

        # (c) near-uniform frame — the whole map is one flat tone.
        luma_std = float(_luma(arr).std())
        if luma_std < variance_min:
            findings.append(Finding(
                "fail", "monochrome_basemap",
                f"frame luma std-dev {luma_std:.1f} < {variance_min:.1f} — the "
                "basemap is near-uniform (the carto_dark→style_warm collapse: one "
                "flat parchment tone, no land/water structure)",
                where=rel,
            ))

        # (a) no distinct water in the theme's water hue.
        wfrac = _water_fraction(arr, water_rgb)
        if wfrac < WATER_FRAC_MIN:
            findings.append(Finding(
                "fail", "no_distinct_water",
                f"only {wfrac * 100:.2f}% of pixels are near the theme's water hue "
                f"#{water_rgb[0]:02x}{water_rgb[1]:02x}{water_rgb[2]:02x} "
                f"(< {WATER_FRAC_MIN * 100:.1f}%) — water did not classify; the "
                "basemap has no blue water (wrong tile provider for style_warm, "
                "or a monochrome collapse)",
                where=rel,
            ))

        # (b) land↔water separation below the theme's floor.
        clusters = _land_water_clusters(arr, water_rgb)
        if clusters is None:
            # No measurable water cluster — already reported by (a)/(c); add an
            # explicit separation finding so the cause is unambiguous.
            findings.append(Finding(
                "fail", "low_land_water_separation",
                "no distinct water cluster to separate from land — land and water "
                "share one tone (no antique-blue water against parchment land)",
                where=rel,
            ))
        else:
            land_mean, water_mean = clusters
            sep = _perceptual_sep(land_mean, water_mean)
            if sep < contrast_min:
                findings.append(Finding(
                    "fail", "low_land_water_separation",
                    f"land↔water perceptual separation {sep:.1f} < {contrast_min:.1f} "
                    f"— land mean RGB ({land_mean[0]:.0f},{land_mean[1]:.0f},"
                    f"{land_mean[2]:.0f}) vs water mean RGB ({water_mean[0]:.0f},"
                    f"{water_mean[1]:.0f},{water_mean[2]:.0f}) are too close; water "
                    "reads the same as land (sepia-on-sepia)",
                    where=rel,
                ))

    return findings


if __name__ == "__main__":
    run_cli("qa_map_contrast", check)
