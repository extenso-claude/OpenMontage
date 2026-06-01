"""qa_geo — pins must be DERIVED from lat/lon, never hand-edited CSS-% positions.

Catches the documented "geographic pin on the wrong continent / hand-edited
pixel position" bug (memory: geographic_pin_accuracy_required). Pixel positions
on a map are only trustworthy when they are computed from (lat, lon) through the
SAME projection the basemap was rendered with — eyeballing CSS percentages (or
nudging a stored px) drifts pins onto the wrong city, sometimes the wrong
continent.

PRIMARY RULE (positions provenance) — BLOCKING:
    For every anchor in artifacts/positions.json, recompute (px, py) PURELY from
    its (lat, lon) using the project's own map_info via
    ``lib.mapkit_subjects.latlon_to_local_pixel`` (pure Web-Mercator math, NO
    network / NO tile fetch). If the stored (px, py) differs from the recomputed
    value by more than TOL_PX pixels, fail — someone hand-edited the pixel
    position instead of deriving it from the coordinates.

SECONDARY RULE (anchor-in-extent) — ADVISORY (warn):
    For every anchor in artifacts/geography.json, find the map_extent matching
    its tier and check the anchor's (lat, lon) projects to a pixel inside that
    extent's viewport (0..width, 0..height) at the extent's zoom. This is pure
    math (extent center_lat/center_lon/zoom -> origin), so it is computed here.
    An anchor that projects outside its tier's viewport is the literal "pin on
    the wrong continent" symptom. When it cannot be cleanly computed (no extent
    for that tier, or missing fields) we skip + record it in `notes` rather than
    guessing. geography.json is OPTIONAL — its absence is not a failure.

Reads:
    <project>/artifacts/positions.json   (REQUIRED — primary rule)
    <project>/artifacts/geography.json   (optional — secondary rule)
Depends: lib.mapkit_subjects (latlon_to_local_pixel — pure, no tiles fetched).

Shapes:
    positions.json = {"map_info": {...projection dict from render_basemap...},
                      "anchors": [{"id","lat","lon","px","py"}, ...]}
        (map_info must carry zoom + global_x_left + global_y_top — the fields
         latlon_to_local_pixel reads.)
    geography.json = per schemas/artifacts/midnight_magnates_geography.schema.json
        (map_extents[] with tier/center_lat/center_lon/zoom[/width/height];
         anchors[] with id/lat/lon/tier).
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# A derived pixel must match the stored pixel to within this tolerance. The
# library rounds to int, so a faithfully-derived position lands within <1px;
# >2px means the value was authored by hand, not computed. (Matches the locked
# rule: hand-edited CSS-% pins are a shippable bug.)
TOL_PX = 2.0

# Defaults from the geography schema for map_extents that omit width/height.
DEFAULT_W = 1920
DEFAULT_H = 1080


def _num(value) -> Optional[float]:
    """Return value as float, or None if it is not a real (non-bool) number."""
    if isinstance(value, bool):  # bool is an int subclass — reject explicitly
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _import_mapkit():
    """Import the projection helper, surfacing import failure as a BLOCKING fail.

    The gate's whole job is to recompute pixels via the canonical projection; if
    that helper can't be imported, the gate cannot run and must NOT silently pass.
    """
    try:
        from lib import mapkit_subjects  # noqa: WPS433 (local import is intentional)
    except Exception as exc:  # pragma: no cover - environment/dependency issue
        raise GateInputError(
            "cannot import lib.mapkit_subjects (needed to recompute pixel "
            "positions from lat/lon): {0}".format(exc)
        ) from exc
    return mapkit_subjects


def _check_positions_provenance(
    project_dir: Path, mapkit, findings: List[Finding]
) -> None:
    """PRIMARY: stored (px,py) must equal the value derived from (lat,lon)."""
    data = load_json(project_dir / "artifacts" / "positions.json")

    info = data.get("map_info")
    if not isinstance(info, dict):
        raise GateInputError("positions.json has no 'map_info' projection object")
    # latlon_to_local_pixel reads exactly these three keys; if any is missing the
    # projection is undefined and we cannot verify provenance -> blocking fail.
    for key in ("zoom", "global_x_left", "global_y_top"):
        if _num(info.get(key)) is None:
            raise GateInputError(
                "positions.json map_info is missing numeric '{0}' (needed to "
                "recompute pixels)".format(key)
            )

    anchors = data.get("anchors")
    if not isinstance(anchors, list):
        raise GateInputError("positions.json has no 'anchors' array")

    for i, anchor in enumerate(anchors):
        aid = anchor.get("id", "#{0}".format(i)) if isinstance(anchor, dict) else "#{0}".format(i)
        if not isinstance(anchor, dict):
            findings.append(Finding(
                "fail", "bad_anchor",
                "anchor entry must be an object with id/lat/lon/px/py",
                where=aid,
            ))
            continue

        lat = _num(anchor.get("lat"))
        lon = _num(anchor.get("lon"))
        px = _num(anchor.get("px"))
        py = _num(anchor.get("py"))
        if lat is None or lon is None:
            findings.append(Finding(
                "fail", "missing_coords",
                "anchor needs numeric lat/lon to derive its pixel position",
                where=aid,
            ))
            continue
        if px is None or py is None:
            findings.append(Finding(
                "fail", "missing_pixels",
                "anchor needs numeric px/py to verify against the derived position",
                where=aid,
            ))
            continue

        # Recompute purely from coordinates — NO tiles fetched.
        exp_x, exp_y = mapkit.latlon_to_local_pixel(lat, lon, info)
        dx = abs(px - exp_x)
        dy = abs(py - exp_y)
        if dx > TOL_PX or dy > TOL_PX:
            findings.append(Finding(
                "fail", "pixel_provenance",
                "stored px=({0:g},{1:g}) but (lat={2:g},lon={3:g}) derives to "
                "({4:d},{5:d}) [off by ({6:.1f},{7:.1f})px > {8:g}px tol] — "
                "pixel was hand-edited, not computed from coordinates".format(
                    px, py, lat, lon, exp_x, exp_y, dx, dy, TOL_PX
                ),
                where=aid,
            ))


def _extent_origin(
    mapkit, extent: dict
) -> Optional[Tuple[dict, str]]:
    """Build a latlon_to_local_pixel-compatible info dict for a map_extent.

    Returns (info, reason) where info is None-able: if the extent can't be
    cleanly resolved we return (None, reason) so the caller can record a note
    instead of guessing.
    """
    clat = _num(extent.get("center_lat"))
    clon = _num(extent.get("center_lon"))
    zoom = extent.get("zoom")
    if clat is None or clon is None or not isinstance(zoom, int) or isinstance(zoom, bool):
        return None
    width = extent.get("width", DEFAULT_W)
    height = extent.get("height", DEFAULT_H)
    width = _num(width) or DEFAULT_W
    height = _num(height) or DEFAULT_H
    # Mirror render_basemap's origin computation exactly.
    cx, cy = mapkit.latlon_to_pixel(clat, clon, zoom)
    info = {
        "zoom": zoom,
        "width": int(width),
        "height": int(height),
        "global_x_left": cx - width / 2.0,
        "global_y_top": cy - height / 2.0,
    }
    return info, ""


def _check_anchor_in_extent(
    project_dir: Path, mapkit, findings: List[Finding], notes: List[str]
) -> None:
    """SECONDARY (advisory): each geography anchor must project inside its tier's extent."""
    geo_path = project_dir / "artifacts" / "geography.json"
    if not geo_path.exists():
        notes.append("geography.json absent — skipped anchor-in-extent (secondary) check.")
        return

    data = load_json(geo_path)  # present-but-unreadable IS a blocking fail (load_json raises)

    extents = data.get("map_extents")
    anchors = data.get("anchors")
    if not isinstance(extents, list) or not isinstance(anchors, list):
        notes.append(
            "geography.json lacks well-formed map_extents/anchors arrays — "
            "skipped anchor-in-extent (secondary) check."
        )
        return

    # Index one usable extent per tier (first wins). Record extents we can't resolve.
    by_tier: dict = {}
    for ext in extents:
        if not isinstance(ext, dict):
            continue
        tier = ext.get("tier")
        if not isinstance(tier, str) or tier in by_tier:
            continue
        built = _extent_origin(mapkit, ext)
        if built is None:
            notes.append(
                "map_extent '{0}' (tier={1}) missing center_lat/center_lon/zoom — "
                "not usable for in-extent check.".format(ext.get("id", "?"), tier)
            )
            continue
        by_tier[tier] = built[0]

    for i, anchor in enumerate(anchors):
        if not isinstance(anchor, dict):
            continue
        aid = anchor.get("id", "#{0}".format(i))
        lat = _num(anchor.get("lat"))
        lon = _num(anchor.get("lon"))
        tier = anchor.get("tier")
        if lat is None or lon is None:
            notes.append("anchor '{0}' missing lat/lon — skipped in-extent check.".format(aid))
            continue
        if not isinstance(tier, str) or tier not in by_tier:
            notes.append(
                "anchor '{0}' has no usable map_extent for tier '{1}' — "
                "cannot cleanly compute in-extent; skipped (TODO: add a {1} extent).".format(aid, tier)
            )
            continue

        info = by_tier[tier]
        px, py = mapkit.latlon_to_local_pixel(lat, lon, info)
        w, h = info["width"], info["height"]
        if not (0 <= px <= w and 0 <= py <= h):
            findings.append(Finding(
                "warn", "anchor_outside_extent",
                "(lat={0:g},lon={1:g}) projects to ({2:d},{3:d}) — OUTSIDE its "
                "'{4}' extent viewport (0..{5},0..{6}); pin would land off-map / "
                "on the wrong region".format(lat, lon, px, py, tier, w, h),
                where=aid,
            ))


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    mapkit = _import_mapkit()
    findings: List[Finding] = []
    notes: List[str] = []

    # PRIMARY (blocking): positions.json pixel provenance.
    _check_positions_provenance(project_dir, mapkit, findings)

    # SECONDARY (advisory): geography.json anchor-in-extent.
    _check_anchor_in_extent(project_dir, mapkit, findings, notes)

    # Surface notes as a single advisory finding so they appear in --json output
    # and the human-readable report, without ever blocking.
    if notes:
        findings.append(Finding(
            "warn", "secondary_notes",
            "; ".join(notes),
            where="geography.json",
        ))
    return findings


if __name__ == "__main__":
    run_cli("qa_geo", check)
