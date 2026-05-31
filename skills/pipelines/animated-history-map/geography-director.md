# Geography Director — Animated History Map

Author `artifacts/geography.json` (if not already complete from research stage). Then render every basemap tile needed.

## Read first

- `docs/animated-history-map-design-intel.md` §1.3 (cascade zoom) + §11–§12 (projection + location accuracy contracts)
- `lib/mapkit_subjects.py` for the basemap building API
- `skills/core/animated-subjects-on-map.md` for the canonical method

## Workflow

1. **For every event in research_brief**, decide which map tiers will be used:
   - Continental for "here in America"
   - Regional for "in Texas"
   - Urban for "in Dallas"
   - Scene for "Dealey Plaza"
   - Building for "Texas School Book Depository, 6th floor"

2. **Compute lat/lon → pixel for every anchor at every tier** via `mapkit_subjects.compute_anchor_pixels()`. Store in geography.json.

3. **Build basemaps:**
   - Continental + Regional + Urban: `mapkit_subjects.build_basemap()` with the theme's basemap_filter
   - Scene: procedural SVG generated from a real lat/lon bounding box (street grid for cities, landmark blocks)
   - Building: PD floorplan from Library of Congress / FBI / Sanborn Maps when available, procedural fallback otherwise

4. **Patch OOB pixels** per `mapkit_oob_pixel_patch` memory: any near-white column (mean luma > 235) gets filled with dark navy `(12, 18, 30)`.

5. **Polygon regions** if the brief calls for them: territory washes, glow regions, scene-block highlights. Every polygon needs a `provenance.source`.

## Gates

These must pass before storyboard can start:

- `qa_pin_geographic_accuracy.py` — every pin's pixel position derives from `mapkit_subjects`, not eyeballed
- `qa_location_provenance.py` — every coordinate + sub-anchor has provenance
- `qa_projection_consistency.py` — cascade zoom transitions preserve anchored center within ±5px

## Output

- `artifacts/geography.json` (validates against schema)
- `assets/maps/<extent_id>.png` per map extent (continental, regional per state, urban per city)
- `assets/maps/scene_<event_id>.svg` for scene-tier maps
- `assets/floorplans/<building_id>.png` for building-tier maps

## Quality bar

- Every event has a complete tier hierarchy declared
- No eyeballed coordinates anywhere
- Building sub-anchors precise enough that "the presidential box" is recognizable at viewport scale
