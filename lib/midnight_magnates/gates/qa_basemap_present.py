"""qa_basemap_present — a map shot must actually render a basemap under it.

Catches the documented "blank cream, no map" bug (b07_conspiracy): a shot that
is a MAP — its targets are placed by geographic pixels, it declares a map tier
or a geo-grounded scene-graph, it sits over a named basemap extent — but the
shot HTML never paints the basemap layer. The plates/pins/labels then composite
straight onto the bare parchment fill (#root background:var(--paper)) and the
viewer sees a labeled diagram floating over blank cream instead of a map of the
place the narration is describing. lint/validate don't look at the rendered DOM,
so the missing ground sails through.

This gate is a lint over the shot HTML, so it legitimately PASSES a project with
no map shots (it never demands a basemap from a shot that isn't a map — a
side-elevation leap diagram like b08 is not a map and is left alone).

Two questions per shot HTML under hyperframes/**:
  1. IS this a map shot?  Yes if ANY of:
       * a <meta name="shot-tier"> whose value contains map / regional /
         continental / diorama / world / globe / aerial (the map-family tiers);
       * the markup carries a geographic basis: a CSS comment / attribute citing
         a basemap extent (manhunt_regional, conus, continental, latlon_to_),
         a geo_footprint / geo_path / map_info / basemap_swap reference, OR a
         *_regional / *_conus / map_* background-image url;
       * a <meta name="scene-graph"> reference whose JSON, on disk next to the
         shot, actually carries a geographic `ground` (a ground.geo / map_info).
     A bare scene-graph reference does NOT by itself make a shot a map: the same
     physics-graph system drives non-map DIAGRAM shots (a side-elevation leap
     diagram, an interior shooting plate). Those are not maps and are skipped.
  2. Does it PAINT a basemap?  Yes if ANY of:
       * a .mapimg / .ground / .basemap element OR id (#map*, #ground, #basemap);
       * a #root (or .ground / .basemap) rule whose `background` carries an
         `url(...)` (a real raster basemap, not just a flat paper color);
       * an <img> whose src points at assets/maps/ or a *map*/_regional/_conus
         raster.
     A flat-color background alone (background:var(--paper) / #efe6cf) does NOT
     count — that is exactly the blank cream we are guarding against.

A map shot that fails (2) -> "fail" (blank-cream, dropped basemap). Reported with
the offending shot file.

Reads:  <project>/hyperframes/**/*.html  (skips the chapter index.html shells)
"""

from __future__ import annotations

import json
import re
from argparse import Namespace
from pathlib import Path
from typing import List

from ._contract import Finding, run_cli

# A shot whose tier names one of these is a member of the map family and is
# required to render a basemap. (A "diagram" / "card" / "portrait" tier is not.)
_MAP_TIER_TOKENS = (
    "map", "regional", "continental", "conus", "diorama",
    "world", "globe", "aerial", "satellite",
)

# An explicitly OFF-map tier is never a map shot, even though the literal
# substring "map" appears inside "offmap"/"off_map". The off-map tiers are the
# treated-image / card / portrait panels (a micro_offmap leap engraving, an
# off_map character card) — they must NOT be required to paint a basemap.
# Checked BEFORE _MAP_TIER_TOKENS so the substring false-positive can't fire.
_NONMAP_TIER_TOKENS = (
    "offmap", "off_map", "off-map", "nonmap", "non_map", "non-map",
)

# Textual fingerprints that a shot is geographically grounded even if its tier
# meta is absent: a cited basemap extent or the sanctioned geo-pixel projector.
_GEO_BASIS_TOKENS = (
    "manhunt_regional", "latlon_to_pixel", "latlon_to_local_pixel",
    "map_info", "basemap_swap", "geo_footprint", "geo_path",
)

# Signatures of an actually-painted basemap layer (a raster ground, not a flat
# parchment fill). Any one present = the shot paints a map under its overlay.
_BASEMAP_CLASS_RE = re.compile(r'class\s*=\s*["\'][^"\']*\b(mapimg|basemap|ground)\b', re.I)
_BASEMAP_ID_RE = re.compile(r'id\s*=\s*["\'](map[\w-]*|basemap|ground)["\']', re.I)
# A CSS selector block (#map_region / .mapimg / #basemap ...) carrying a url() bg.
_BASEMAP_CSS_RE = re.compile(
    r'(?:#(?:map[\w-]*|basemap|ground)|\.(?:mapimg|basemap|ground))\b[^{}]*\{[^{}]*url\(',
    re.I | re.S,
)
# Any background[-image] that pulls a raster from assets/maps/ or a map-y name.
_BASEMAP_URL_RE = re.compile(
    r'background(?:-image)?\s*:[^;{}]*url\(\s*["\']?[^"\')]*'
    r'(?:assets/maps/|[\w/-]*(?:map|_regional|_conus|continental|basemap)[\w/-]*\.'
    r'(?:png|jpe?g|webp|svg))',
    re.I,
)
# An <img> whose src is a map raster.
_BASEMAP_IMG_RE = re.compile(
    r'<img\b[^>]*\bsrc\s*=\s*["\'][^"\']*'
    r'(?:assets/maps/|[\w/-]*(?:map|_regional|_conus|continental|basemap)[\w/-]*)\.'
    r'(?:png|jpe?g|webp|svg)',
    re.I,
)

_META_TIER_RE = re.compile(
    r'<meta\s+name\s*=\s*["\']shot-tier["\']\s+content\s*=\s*["\']([^"\']*)["\']', re.I
)
_META_SCENEGRAPH_RE = re.compile(
    r'<meta\s+name\s*=\s*["\']scene-graph["\']\s+content\s*=\s*["\']([^"\']*)["\']', re.I
)


def _scene_graph_is_geo(shot_path: Path, ref: str) -> bool:
    """True iff the shot's referenced scene-graph JSON carries a geographic ground.

    The same physics-graph system drives non-map diagrams, so a scene-graph
    reference is only evidence of a MAP when the graph's `ground` actually has
    geo (a ground.geo block or a map_info). Resolved relative to the shot's
    directory (refs are like "shots/b08_leap.graph.json" or "b01.graph.json");
    we also try the shot's own folder. Unreadable/absent -> not geo (don't
    invent a map obligation from a file we can't see)."""
    ref = ref.strip().lstrip("/")
    candidates = [
        (shot_path.parent / ref),
        (shot_path.parent / Path(ref).name),
    ]
    for cand in candidates:
        try:
            if not cand.is_file():
                continue
            data = json.loads(cand.read_text(errors="replace"))
        except (OSError, ValueError):
            continue
        ground = data.get("ground") if isinstance(data, dict) else None
        if isinstance(ground, dict) and ("geo" in ground or "map_info" in ground):
            return True
    return False


def _is_map_shot(txt: str, shot_path: Path) -> bool:
    """Decide whether this shot is a member of the map family (must paint a basemap)."""
    m = _META_TIER_RE.search(txt)
    if m:
        tier = m.group(1).lower()
        # An explicitly off-map tier is exempt outright (and short-circuits the
        # geo-basis text scan below, which could otherwise false-match caption
        # prose). "micro_offmap" is an image panel, not a map.
        if any(neg in tier for neg in _NONMAP_TIER_TOKENS):
            return False
        if any(tok in tier for tok in _MAP_TIER_TOKENS):
            return True
    low = txt.lower()
    if any(tok in low for tok in _GEO_BASIS_TOKENS):
        return True
    sg = _META_SCENEGRAPH_RE.search(txt)
    if sg and _scene_graph_is_geo(shot_path, sg.group(1)):
        return True
    return False


def _paints_basemap(txt: str) -> bool:
    """True iff the shot actually renders a raster basemap layer."""
    return bool(
        _BASEMAP_CLASS_RE.search(txt)
        or _BASEMAP_ID_RE.search(txt)
        or _BASEMAP_CSS_RE.search(txt)
        or _BASEMAP_URL_RE.search(txt)
        or _BASEMAP_IMG_RE.search(txt)
    )


def _is_chapter_shell(path: Path) -> bool:
    """The chapter/master index.html is a stitching shell, not a per-shot map."""
    return path.name == "index.html"


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    findings: List[Finding] = []
    hf_dir = project_dir / "hyperframes"
    if not hf_dir.is_dir():
        # No HF tree yet — nothing to lint. This gate is a lint, not a presence
        # check, so an absent tree is a clean pass (other gates own existence).
        return findings

    for h in sorted(hf_dir.rglob("*.html")):
        if _is_chapter_shell(h):
            continue
        try:
            txt = h.read_text(errors="replace")
        except OSError:
            continue
        if not _is_map_shot(txt, h):
            continue  # not a map — no basemap obligation
        if not _paints_basemap(txt):
            findings.append(Finding(
                "fail", "missing_basemap",
                "shot is a MAP (declares a map tier / geo-grounded scene-graph / "
                "named basemap extent) but renders NO basemap layer — its overlays "
                "composite onto blank cream. A map shot must paint a basemap "
                "(.mapimg/.ground element, a #root/#basemap background url(), or an "
                "<img> from assets/maps/), not a flat parchment fill.",
                where=str(h.relative_to(project_dir)),
            ))

    return findings


if __name__ == "__main__":
    run_cli("qa_basemap_present", check)
