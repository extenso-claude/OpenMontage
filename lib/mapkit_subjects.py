"""mapkit_subjects — shared library for the "animated subjects on a map" workflow.

This is the reusable foundation behind every map-led OpenMontage sequence:
Midnight Magnates noir trade-route maps, Grandpa Huxley warm-parchment expedition
maps, illuminated-manuscript medieval-history maps, and any other variant where a
project needs to animate subjects (armies, fleets, caravans, processions, traders)
on a geographically accurate basemap.

Tools provided here:
    - Web-Mercator tile fetching (with on-disk cache, multi-provider)
    - Style filters: noir, warm, illuminated, light_minimal
    - Polygon highlight overlay (regional fill with feathered edges)
    - Geographic <-> pixel coordinate math
    - Sprite anchor computation (centroid + offsets formation)

The HyperFrames composition + SFX mixing patterns live in
`skills/core/animated-subjects-on-map.md` (Layer 2 skill). This module is
the pure Python building block — the skill drives how it's used.

Reference implementations:
    - Midnight Magnates noir: projects/iran-history-overlay-v1/scripts/mapkit.py
    - Grandpa Huxley warm:    projects/europe-style-opener/scripts/mapkit_warm.py
    - Illuminated manuscript: projects/medieval-europe-opener-test/scripts/mapkit_illuminated.py
"""
from __future__ import annotations

import json
import math
import pathlib
import sys
import urllib.request
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

TILE_SIZE = 256
DEFAULT_UA = "OpenMontage-mapkit_subjects/1.0 (educational use)"

# ── Tile providers ────────────────────────────────────────────────────────
# Use *_nolabels variants whenever the style filter is going to recolor land/water
# from luma + chroma heuristics — admin labels and road networks contaminate the
# classification. See the illuminated-manuscript reference for the worked example.
PROVIDERS = {
    "carto_dark":              "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
    "carto_dark_nolabels":     "https://a.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png",
    "carto_light":             "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
    "carto_light_nolabels":    "https://a.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png",
    "carto_voyager":           "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
    "carto_voyager_nolabels":  "https://a.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}.png",
    "arcgis_imagery":          "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "arcgis_topo":             "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    "osm":                     "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "wiki":                    "https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png",
}


# ── Provider ⇄ style binding ──────────────────────────────────────────────
# A style filter only behaves on the tile family it was *designed* for, because
# each filter classifies land vs water from the SOURCE tiles' luma+chroma.
# Mismatches were the documented Lincoln-map failure: carto_dark tiles (water is
# dark-GRAY, R≈G≈B, no blue dominance) fed to `style_warm` (whose water test is
# "blue beats red") classified ~the whole frame as land and collapsed the map to
# one flat parchment tone — no water, no contrast. The binding makes that a hard
# error at render time instead of a silent monochrome PNG.
#
# Keyed by style name -> the set of providers whose tiles that filter can grade.
STYLE_PROVIDER_BINDING: dict[str, set[str]] = {
    # warm/parchment grade needs warm earth tones + BLUE water already present.
    "warm":          {"carto_voyager", "carto_voyager_nolabels"},
    # noir grade is authored for the already-dark carto_dark palette.
    "noir":          {"carto_dark", "carto_dark_nolabels"},
    # illuminated reclassifies from a near-white label-free light base.
    "illuminated":   {"carto_light_nolabels", "carto_light"},
    # light_minimal is a gentle desaturate; the light family is the right base.
    "light_minimal": {"carto_light", "carto_light_nolabels",
                      "carto_voyager", "carto_voyager_nolabels"},
}


class StyleProviderMismatch(ValueError):
    """Raised when a style filter is paired with a tile provider it cannot grade.

    This is the guardrail for the Lincoln-map regression: carto_dark + style_warm
    produced a flat parchment frame with no blue water. Rather than emit that
    broken PNG, the binding refuses the pair and names the provider to switch to.
    """


def assert_style_provider(style: str, provider: str) -> None:
    """Raise StyleProviderMismatch unless `provider` is bound to `style`.

    Styles not present in the binding table (custom callables) are unconstrained.
    """
    allowed = STYLE_PROVIDER_BINDING.get(style)
    if allowed is None:
        return
    if provider not in allowed:
        raise StyleProviderMismatch(
            f"style {style!r} requires one of {sorted(allowed)} but got provider "
            f"{provider!r}. Land/water classification is tuned to the source "
            f"tiles; this pairing produces a no-contrast / no-water basemap "
            f"(the documented Lincoln-map failure). Re-render with an allowed "
            f"provider."
        )


# ── Theme-driven basemap colors ───────────────────────────────────────────
# The land/water/contrast colors are NOT hardcoded here — they come from the
# project's theme.json so each video gets period/culture-appropriate water
# (Lincoln 1865 = a muted antique blue, not a universal saturated blue) while a
# distinct land↔water separation is still guaranteed. This dataclass is the
# resolved, render-ready form; `load_basemap_colors` parses it from a theme dict.
@dataclass
class BasemapColors:
    """Resolved land/water/contrast spec for a basemap render + its QA.

    land_rgb / water_rgb : 0-255 RGB triples the warm grade paints onto land and
        water. `water_rgb` MUST be a visibly distinct hue from land — a muted
        period blue, never a parchment/sepia tone — so water reads as water.
    contrast_min : the minimum acceptable land↔water separation (a blend of luma
        and chroma distance, 0-255-ish) that the qa_map_contrast gate enforces.
    variance_min : minimum whole-frame luma std-dev; guards the "monochrome
        collapse" failure where the entire map is one flat tone.
    """
    land_rgb: tuple[int, int, int] = (228, 214, 178)     # antique parchment
    water_rgb: tuple[int, int, int] = (108, 142, 168)    # muted antique blue
    contrast_min: float = 40.0
    variance_min: float = 12.0


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    s = value.strip().lstrip("#")
    if len(s) != 6:
        raise ValueError(f"expected a #RRGGBB hex color, got {value!r}")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def load_basemap_colors(theme: dict) -> BasemapColors:
    """Resolve a BasemapColors from a project theme dict (theme.json contents).

    Looks for ``palette_master.basemap_colors`` first (the explicit, preferred
    place), then falls back to sensible warm-map defaults. Recognized keys:
        land | land_hex            -> land_rgb
        water | water_hex          -> water_rgb     (must be a period water hue)
        contrast_min               -> contrast_min  (gate threshold)
        variance_min               -> variance_min  (gate threshold)
    Unknown / missing keys keep the BasemapColors defaults, so an older theme
    that predates this block still renders blue water with separation.
    """
    out = BasemapColors()
    pm = (theme or {}).get("palette_master", {}) or {}
    bc = pm.get("basemap_colors", {}) or {}
    land = bc.get("land", bc.get("land_hex"))
    water = bc.get("water", bc.get("water_hex"))
    if land:
        out.land_rgb = _hex_to_rgb(land)
    if water:
        out.water_rgb = _hex_to_rgb(water)
    if "contrast_min" in bc:
        out.contrast_min = float(bc["contrast_min"])
    if "variance_min" in bc:
        out.variance_min = float(bc["variance_min"])
    return out


# Style-aware fallback fill for out-of-bounds / un-fetched tile area. The old
# universal bright (200,220,230) became a glaring white band on dark maps at low
# zoom (memory: mapkit_oob_pixel_patch). Each style gets a fill that disappears
# into its own palette.
_FALLBACK_FILL: dict[str, tuple[int, int, int, int]] = {
    "noir":          (26, 39, 64, 255),    # deep navy — matches noir water/voids
    "warm":          (88, 116, 140, 255),  # muted blue — reads as open water
    "illuminated":   (28, 63, 138, 255),   # lapis — matches illuminated ocean
    "light_minimal": (210, 224, 232, 255),
}


# ── Web Mercator math (EPSG:3857) ─────────────────────────────────────────
def latlon_to_pixel(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    """Return global pixel coordinates at the given zoom level."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xt = (lon + 180.0) / 360.0 * n
    yt = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    return xt * TILE_SIZE, yt * TILE_SIZE


def latlon_to_local_pixel(lat: float, lon: float, info: dict) -> tuple[int, int]:
    """Convert geographic coords to pixel coordinates inside a fetched basemap."""
    px, py = latlon_to_pixel(lat, lon, info["zoom"])
    return int(round(px - info["global_x_left"])), int(round(py - info["global_y_top"]))


# ── Tile fetching ─────────────────────────────────────────────────────────
def fetch_tile(provider: str, z: int, x: int, y: int,
               cache_dir: pathlib.Path | None = None,
               user_agent: str = DEFAULT_UA) -> Image.Image:
    """Fetch one tile (cached on disk). Returns RGBA PIL image."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown tile provider '{provider}'. Known: {sorted(PROVIDERS)}")
    cache_dir = cache_dir or pathlib.Path("_tile_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cp = cache_dir / f"{provider}_z{z}_x{x}_y{y}.png"
    if cp.exists() and cp.stat().st_size > 100:
        return Image.open(cp).convert("RGBA")
    url = PROVIDERS[provider].format(z=z, x=x, y=y)
    req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Referer": "https://example.com/"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read()
    cp.write_bytes(data)
    return Image.open(cp).convert("RGBA")


def render_basemap(center_lat: float, center_lon: float, zoom: int,
                   width: int, height: int, provider: str,
                   cache_dir: pathlib.Path | None = None,
                   user_agent: str = DEFAULT_UA,
                   fill_rgba: tuple[int, int, int, int] | None = None
                   ) -> tuple[Image.Image, dict]:
    """Fetch + composite tiles into a single RGB(A) image centered on (lat, lon).

    Returns (image, info) where `info` carries the projection metadata needed by
    `latlon_to_local_pixel` to convert any (lat, lon) into the basemap's pixel space.

    `fill_rgba` is the color used for any out-of-bounds / un-fetched tile area
    (e.g. ocean past the world edge at low zoom). It defaults to a neutral light
    blue for backward compatibility, but callers should pass a style-appropriate
    fill — a bright fill becomes a glaring white band on a dark map at low zoom
    (memory: mapkit_oob_pixel_patch). `build_basemap` does this automatically.
    """
    fill = fill_rgba if fill_rgba is not None else (200, 220, 230, 255)
    cx, cy = latlon_to_pixel(center_lat, center_lon, zoom)
    ox, oy = cx - width / 2, cy - height / 2
    tx0 = int(math.floor(ox / TILE_SIZE))
    ty0 = int(math.floor(oy / TILE_SIZE))
    tx1 = int(math.floor((ox + width - 1) / TILE_SIZE)) + 1
    ty1 = int(math.floor((oy + height - 1) / TILE_SIZE)) + 1
    canvas = Image.new("RGBA", ((tx1 - tx0) * TILE_SIZE, (ty1 - ty0) * TILE_SIZE), fill)
    n_max = 2 ** zoom
    for ty in range(ty0, ty1):
        for tx in range(tx0, tx1):
            if not (0 <= tx < n_max and 0 <= ty < n_max):
                continue
            try:
                tile = fetch_tile(provider, zoom, tx, ty, cache_dir=cache_dir, user_agent=user_agent)
            except Exception as e:
                print(f"  tile {provider} z={zoom} x={tx} y={ty} failed: {e}", file=sys.stderr)
                continue
            canvas.paste(tile, ((tx - tx0) * TILE_SIZE, (ty - ty0) * TILE_SIZE))
    crop_x = int(ox - tx0 * TILE_SIZE)
    crop_y = int(oy - ty0 * TILE_SIZE)
    img = canvas.crop((crop_x, crop_y, crop_x + width, crop_y + height))
    info = {
        "center_lat": center_lat, "center_lon": center_lon, "zoom": zoom,
        "width": width, "height": height,
        "global_x_left": ox, "global_y_top": oy,
        "provider": provider,
    }
    return img, info


# ── Style filters ─────────────────────────────────────────────────────────
# Each filter accepts a basemap image (any provider) and returns a recolored image
# in that channel's visual identity. Reference implementations live in
# `projects/<ref>/scripts/mapkit*.py`; this is the consolidated version.

def _edge_mask(mask: np.ndarray) -> np.ndarray:
    """1-pixel boundary of a boolean mask (4-neighbour comparison)."""
    up = np.roll(mask, -1, axis=0); up[-1, :] = mask[-1, :]
    down = np.roll(mask, 1, axis=0); down[0, :] = mask[0, :]
    left = np.roll(mask, -1, axis=1); left[:, -1] = mask[:, -1]
    right = np.roll(mask, 1, axis=1); right[:, 0] = mask[:, 0]
    return (mask != up) | (mask != down) | (mask != left) | (mask != right)


def _dilate(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    m = mask.copy()
    for _ in range(iterations):
        up = np.roll(m, -1, axis=0)
        down = np.roll(m, 1, axis=0)
        left = np.roll(m, -1, axis=1)
        right = np.roll(m, 1, axis=1)
        m = m | up | down | left | right
    return m


def style_noir(img: Image.Image, strength: float = 1.0) -> Image.Image:
    """Midnight Magnates noir grade — preserves label/road readability on carto_dark.

    Designed for `carto_dark` provider (already in noir palette). Lifts highlights,
    cools midtones, leaves bright labels readable. Verified against `MEMORY.md`
    rule: "Map base layer must keep place names + roads readable".
    """
    img = img.convert("RGB")
    img = ImageEnhance.Color(img).enhance(0.8 + 0.15 * (1 - strength))
    img = ImageEnhance.Brightness(img).enhance(1.10)
    img = ImageEnhance.Contrast(img).enhance(1.04)
    arr = np.array(img).astype(np.float32)
    lum = arr.mean(axis=2, keepdims=True)
    highlight_mask = np.clip((lum - 100) / 70.0, 0, 1)
    arr = arr + highlight_mask * 30
    arr = np.clip(arr, 0, 255)
    midtone_mask = np.clip(1.0 - np.abs(lum - 90) / 90.0, 0, 1)
    arr[..., 0] = np.clip(arr[..., 0] - midtone_mask[..., 0] * 8, 0, 255)
    arr[..., 1] = np.clip(arr[..., 1] - midtone_mask[..., 0] * 4, 0, 255)
    arr[..., 2] = np.clip(arr[..., 2] + midtone_mask[..., 0] * 2, 0, 255)
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")


def style_warm(img: Image.Image, strength: float = 1.0,
               colors: "BasemapColors | None" = None) -> Image.Image:
    """Documentary-warm grade — themed parchment land + DISTINCT period water.

    Designed for the `carto_voyager[_nolabels]` provider, where water already
    carries blue dominance (B > R) and land is warm/near-white. Land is shaded
    toward `colors.land_rgb`; water is painted toward `colors.water_rgb` — a
    muted, period-appropriate blue that is a visibly different hue from land
    (Lincoln 1865 = antique blue), NOT a parchment/sepia wash and NOT a hardcoded
    universal blue.

    Blue-water guarantee: if the chroma classifier finds an implausibly small
    water fraction (it would on the wrong provider — the carto_dark failure),
    this raises StyleProviderMismatch rather than emit a monochrome basemap.
    Pass the right provider (enforced upstream by `assert_style_provider`) and
    real coastlines will classify.

    `colors` defaults to BasemapColors() (antique-parchment land, antique-blue
    water) so callers that don't thread a theme still get blue water + contrast.
    """
    if colors is None:
        colors = BasemapColors()
    land_rgb = np.asarray(colors.land_rgb, dtype=np.float32)
    water_rgb = np.asarray(colors.water_rgb, dtype=np.float32)

    img = img.convert("RGB")
    img = ImageEnhance.Color(img).enhance(0.85)
    img = ImageEnhance.Contrast(img).enhance(1.12)
    arr = np.array(img).astype(np.float32)
    R, G, B = arr[..., 0], arr[..., 1], arr[..., 2]
    luma = 0.299 * R + 0.587 * G + 0.114 * B

    # Water classifier for the voyager family: water is bluish (blue beats red)
    # AND not bright-near-white land. A small positive margin (B > R + 3) rejects
    # the warm near-gray of land while keeping pale coastal shelf water. This is
    # the SOURCE-tile test; recoloring happens after.
    is_water = (B > R + 3) & (luma < 232)
    is_land = ~is_water

    water_frac = float(is_water.mean())
    # On the correct provider, any CONUS/regional extent has clearly >1.5% water
    # (coast, lakes, rivers). A near-zero fraction means the source tiles have no
    # blue water to find — i.e. a provider mismatch slipped past the binding (or
    # a landlocked micro-extent). Refuse to emit a no-water parchment frame.
    if water_frac < 0.006:
        raise StyleProviderMismatch(
            f"style_warm found only {water_frac*100:.2f}% blue water in the source "
            f"tiles — far below the ~1.5%+ expected on carto_voyager for any coastal "
            f"or riverine extent. The source provider almost certainly lacks blue "
            f"water (the carto_dark→style_warm regression); re-render from "
            f"carto_voyager[_nolabels]. (If this extent is genuinely landlocked, "
            f"use style_noir/illuminated instead.)"
        )

    # Land: shade the themed parchment by the source land's luma so terrain and
    # admin tone still read; brighter source land -> lighter parchment. Both
    # targets are full HxWx3 (the shade factors carry the H,W dims), so masked
    # assignment indexes them per-pixel.
    land_shade = np.clip((luma - 150.0) / 105.0, -0.35, 0.35)[..., None]
    land_target = land_rgb[None, None, :] * (1.0 + 0.18 * land_shade)
    arr[is_land] = land_target[is_land]

    # Water: blend toward the themed period blue, modulated by source blueness so
    # deeper/bluer source water reads slightly deeper. Always a clear blue hue.
    blue_depth = np.clip((B - R) / 40.0, 0.0, 1.0)[..., None]
    water_target = water_rgb[None, None, :] * (1.0 - 0.16 * blue_depth)
    arr[is_water] = water_target[is_water]

    arr = np.power(np.clip(arr, 0, 255) / 255.0, 0.96) * 255.0
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


# Illuminated-manuscript palette anchors
_VELLUM = np.array([239, 226, 196], dtype=np.float32) / 255.0
_VELLUM_DARK = np.array([218, 200, 162], dtype=np.float32) / 255.0
_LAPIS = np.array([28, 63, 138], dtype=np.float32) / 255.0
_LAPIS_DEEP = np.array([15, 38, 92], dtype=np.float32) / 255.0
_INK = np.array([58, 36, 16], dtype=np.float32) / 255.0


def style_illuminated(img: Image.Image, strength: float = 1.0) -> Image.Image:
    """Flat illuminated-manuscript style — vellum land, lapis ocean, ink coastlines.

    Requires a label-free provider (e.g. `carto_light_nolabels`); the filter
    classifies land vs water by luma+chroma and any text/road artifacts will
    survive as black smudges. Applies two-pass median to kill admin borders,
    posterizes to 5 levels, and draws a dilated ink coastline.
    """
    img = img.filter(ImageFilter.MedianFilter(size=9))
    img = img.filter(ImageFilter.MedianFilter(size=7))
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))

    rgb = np.array(img.convert("RGB"), dtype=np.float32) / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    # Tuned for carto_light_nolabels: water ~RGB(220, 225, 226), land near-white.
    is_water = (b > r + 0.008) & (luma < 0.94)

    h, w = is_water.shape
    out = np.zeros_like(rgb)

    water_depth = np.clip((b - 0.55) / 0.45, 0.0, 1.0)
    water_color = _LAPIS * (1.0 - 0.35 * water_depth)[..., None] + _LAPIS_DEEP * (0.35 * water_depth)[..., None]
    out[is_water] = water_color[is_water]

    land = ~is_water
    land_shade = np.clip(1.0 - (luma - 0.7) / 0.3, 0.0, 1.0)
    land_color = _VELLUM * (1.0 - land_shade)[..., None] + _VELLUM_DARK * land_shade[..., None]
    out[land] = land_color[land]

    levels = 5
    out = np.round(out * (levels - 1)) / (levels - 1)

    coast = _dilate(_edge_mask(is_water), iterations=2)
    out[coast] = _INK

    rng = np.random.default_rng(seed=20260520)
    grain = 1.0 - rng.uniform(0, 0.06, size=(h, w))
    out = out * grain[..., None]

    return Image.fromarray(np.clip(out * 255.0, 0, 255).astype(np.uint8)).convert("RGBA")


def style_light_minimal(img: Image.Image, strength: float = 1.0) -> Image.Image:
    """Clean light-minimal grade — flat gray land + pale blue water, no ornament.

    For technical / clean-professional briefs where the map is a background and
    subjects should completely dominate. Pairs with `clean-professional` playbook.
    """
    img = img.convert("RGB")
    img = ImageEnhance.Color(img).enhance(0.6)
    img = ImageEnhance.Brightness(img).enhance(1.05)
    img = ImageEnhance.Contrast(img).enhance(0.95)
    return img.convert("RGBA")


STYLES: dict[str, Callable[..., Image.Image]] = {
    "noir":          style_noir,
    "warm":          style_warm,
    "illuminated":   style_illuminated,
    "light_minimal": style_light_minimal,
}


def apply_style(img: Image.Image, style: str, strength: float = 1.0,
                colors: "BasemapColors | None" = None,
                provider: str | None = None) -> Image.Image:
    """Dispatch to a named style filter. Raises if `style` is unknown.

    If `provider` is given, the provider⇄style binding is enforced first (so a
    mismatched pair is refused before any pixels are produced). `colors` is the
    theme-resolved BasemapColors; it is threaded to filters that honor it
    (currently `warm`) and ignored by the rest.
    """
    if style not in STYLES:
        raise ValueError(f"Unknown style '{style}'. Known: {sorted(STYLES)}")
    if provider is not None:
        assert_style_provider(style, provider)
    if style == "warm":
        return style_warm(img, strength=strength, colors=colors)
    return STYLES[style](img, strength=strength)


# ── Polygon-region highlight overlay ──────────────────────────────────────
def apply_polygon_highlight(img: Image.Image, info: dict,
                            polygon_latlon: list[tuple[float, float]],
                            color: tuple[int, int, int],
                            blend: float = 0.45,
                            feather_px: float = 18.0,
                            land_only: bool = True) -> Image.Image:
    """Paint a translucent color wash over a lat/lon polygon, with feathered edges.

    `color` is RGB 0-255. `blend` is the peak alpha (0..1) at the polygon centre.
    `feather_px` controls how soft the polygon boundary is. When `land_only=True`,
    the wash only affects pixels that look like land (not the existing water/coastline).

    Used for: highlighting Western Europe in verdigris (medieval), trade-route
    territory shading (Midnight Magnates), or campaign extents (any channel).
    """
    rgb = np.array(img.convert("RGB"), dtype=np.float32) / 255.0
    color_norm = np.array(color, dtype=np.float32) / 255.0

    poly_px = [latlon_to_local_pixel(lat, lon, info) for lat, lon in polygon_latlon]
    mask_img = Image.new("L", (info["width"], info["height"]), 0)
    ImageDraw.Draw(mask_img).polygon(poly_px, fill=255)
    if feather_px > 0:
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=feather_px))
    poly_alpha = np.array(mask_img).astype(np.float32) / 255.0

    if land_only:
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        is_blue_water = (b > r + 0.05) & (b > g + 0.02) & (b > 0.10)
        is_dark_ink   = (r < 0.30) & (g < 0.30) & (b < 0.20)
        is_land = (~is_blue_water) & (~is_dark_ink)
    else:
        is_land = np.ones(rgb.shape[:2], dtype=bool)

    alpha = (blend * poly_alpha)[..., None]
    blended = (1 - alpha) * rgb + alpha * color_norm
    rgb = np.where(is_land[..., None], blended, rgb)

    return Image.fromarray(np.clip(rgb * 255.0, 0, 255).astype(np.uint8)).convert("RGBA")


# ── Sprite anchor computation ─────────────────────────────────────────────
@dataclass
class SpriteAnchor:
    """One geo-anchored sprite (castle, ship, marker, etc.)."""
    id: str
    lat: float
    lon: float
    px: tuple[int, int] = field(default=(0, 0))
    scale: float = 1.0
    rotation: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class FormationMember:
    """One sprite in a moving formation, offset in pixels from the centroid."""
    id: str
    dx: int
    dy: int
    scale: float = 1.0
    rotation: float = 0.0


def compute_anchor_pixels(anchors: list[SpriteAnchor], info: dict) -> list[SpriteAnchor]:
    """Fill `px` on every anchor from its (lat, lon)."""
    for a in anchors:
        a.px = latlon_to_local_pixel(a.lat, a.lon, info)
    return anchors


def compute_formation_pixels(centroid_latlon: tuple[float, float],
                             formation: list[FormationMember],
                             info: dict) -> list[dict]:
    """Compute per-sprite pixel positions for a formation centred on `centroid_latlon`.

    Returns a list of dicts ready to emit to positions.json:
        [{ "id": "k_lead", "px": [x, y], "scale": 1.05, "rot": 0.0 }, ...]
    """
    cx, cy = latlon_to_local_pixel(*centroid_latlon, info)
    return [
        {"id": m.id, "px": [cx + m.dx, cy + m.dy], "scale": m.scale, "rot": m.rotation}
        for m in formation
    ]


# ── Convenience: bundle a whole render in one call ────────────────────────
@dataclass
class MapConfig:
    """Configuration for one map render — style, geographic extent, provider.

    `colors` carries the theme-resolved land/water/contrast spec; when None a
    BasemapColors() default (antique-parchment land, antique-blue water) is used.
    """
    center_lat: float
    center_lon: float
    zoom: int
    width: int = 1920
    height: int = 1080
    provider: str = "carto_light_nolabels"
    style: str = "illuminated"
    cache_dir: pathlib.Path | None = None
    colors: "BasemapColors | None" = None


def build_basemap(cfg: MapConfig) -> tuple[Image.Image, dict]:
    """Fetch tiles + apply the configured style filter. Returns (image, info).

    Enforces the provider⇄style binding BEFORE fetching (fail fast on a bad pair)
    and feeds `render_basemap` a style-appropriate out-of-bounds fill so a low-zoom
    world edge never shows up as a bright band on a dark map.
    """
    assert_style_provider(cfg.style, cfg.provider)
    fill = _FALLBACK_FILL.get(cfg.style, (200, 220, 230, 255))
    raw, info = render_basemap(cfg.center_lat, cfg.center_lon, cfg.zoom,
                               cfg.width, cfg.height, cfg.provider,
                               cache_dir=cfg.cache_dir, fill_rgba=fill)
    styled = apply_style(raw, cfg.style, colors=cfg.colors, provider=cfg.provider)
    info["style"] = cfg.style
    return styled, info


# ── Rule Zero: one theme-aware basemap entry point ────────────────────────
# Per-project scripts must NOT re-implement provider selection, style binding,
# fill choice, or land/water coloring. They declare an extent + read theme.json,
# then call this. The binding/blue-water/contrast logic lives here once.
#
# `basemap_filter` -> provider/style resolution. carto_dark*/carto_voyager* etc.
# are chosen so the style filter gets the tile family it can grade. `*_nolabels`
# is preferred for warm/illuminated (labels contaminate land/water classification);
# noir keeps labels because style_noir is tuned to preserve them.
_FILTER_DEFAULTS: dict[str, tuple[str, str]] = {
    # basemap_filter : (style, default provider)
    "warm":          ("warm", "carto_voyager_nolabels"),
    "noir":          ("noir", "carto_dark"),
    "illuminated":   ("illuminated", "carto_light_nolabels"),
    "light_minimal": ("light_minimal", "carto_light_nolabels"),
}


def resolve_style_provider(theme: dict,
                           provider_override: str | None = None
                           ) -> tuple[str, str]:
    """Map a theme's ``palette_master.basemap_filter`` to (style, provider).

    Raises StyleProviderMismatch if an explicit `provider_override` isn't bound
    to the resolved style — so a project can't ask for warm tiles on a dark base.
    """
    pm = (theme or {}).get("palette_master", {}) or {}
    filt = pm.get("basemap_filter", "warm")
    if filt not in _FILTER_DEFAULTS:
        raise ValueError(
            f"unknown basemap_filter {filt!r}; known: {sorted(_FILTER_DEFAULTS)}"
        )
    style, default_provider = _FILTER_DEFAULTS[filt]
    provider = provider_override or default_provider
    assert_style_provider(style, provider)
    return style, provider


def build_basemap_from_theme(theme: dict, center_lat: float, center_lon: float,
                             zoom: int, width: int = 1920, height: int = 1080,
                             cache_dir: pathlib.Path | None = None,
                             provider_override: str | None = None
                             ) -> tuple[Image.Image, dict]:
    """THE entry point for a theme-driven basemap (Rule Zero).

    Resolves style+provider from the theme's basemap_filter, resolves land/water/
    contrast colors from the theme, enforces the binding, and renders with a
    style-appropriate OOB fill. Returns (styled_image, info) where `info` also
    carries `style`, `basemap_colors` (land/water hex + thresholds) so the
    qa_map_contrast gate can read the same theme spec the render used.
    """
    style, provider = resolve_style_provider(theme, provider_override)
    colors = load_basemap_colors(theme)
    cfg = MapConfig(center_lat=center_lat, center_lon=center_lon, zoom=zoom,
                    width=width, height=height, provider=provider, style=style,
                    cache_dir=cache_dir, colors=colors)
    img, info = build_basemap(cfg)
    info["basemap_colors"] = {
        "land": "#%02x%02x%02x" % colors.land_rgb,
        "water": "#%02x%02x%02x" % colors.water_rgb,
        "contrast_min": colors.contrast_min,
        "variance_min": colors.variance_min,
    }
    return img, info


def write_positions_json(path: pathlib.Path,
                          info: dict,
                          anchors: list[SpriteAnchor],
                          subject_centroid_latlon: tuple[float, float] | None = None,
                          subject_formation: list[FormationMember] | None = None,
                          extra: dict | None = None) -> None:
    """Emit a positions.json bundle for the HyperFrames composition to consume."""
    positions: dict = {
        "map_info": info,
        "anchors": [
            {"id": a.id, "lat": a.lat, "lon": a.lon, "px": list(a.px),
             "scale": a.scale, "rotation": a.rotation, **a.metadata}
            for a in anchors
        ],
    }
    if subject_centroid_latlon is not None:
        positions["subject_centroid_latlon"] = list(subject_centroid_latlon)
        positions["subject_centroid_px"] = list(latlon_to_local_pixel(*subject_centroid_latlon, info))
    if subject_formation is not None and subject_centroid_latlon is not None:
        positions["subject_formation"] = compute_formation_pixels(
            subject_centroid_latlon, subject_formation, info
        )
    if extra:
        positions.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(positions, f, indent=2)
