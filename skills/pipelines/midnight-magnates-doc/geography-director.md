# Geography Director — Midnight Magnates

Geography is an **on-demand helper**, not the spine of a Midnight Magnates video. There is no
continental → regional → urban → building basemap cascade and no map that the story revolves around.
Most MM visuals are **medium** and **micro** shots — the scene and the close-up on a face / object /
document — and the per-video brand through-line is whatever the storyboard declares (`map`,
`case_file`, `timeline`, `cast_of_players`, or `other`), never a hardcoded map of pins.

This skill exists for the narrower job: **when a beat DOES place something in geographic space**
(a `macro` establishing shot on a map, a `pin_drop`, a map-anchored `glow_region` or
`connection_line`), that placement must be **real and pixel-accurate**. A pin on the wrong city —
sometimes the wrong continent — because someone eyeballed a CSS percentage is a shippable bug
(memory: `geographic_pin_accuracy_required`). You produce the projection + the derived pixels so the
spatial gates can prove every map/space cue lands where the coordinates demand.

If the video has no map-anchored beat at all, this stage produces nothing and is a no-op — that is a
valid outcome. Do not invent a map to satisfy this skill.

## HARD RULES

These are the channel identity for spatial work. Author to them; do not drift, skip, or reinterpret.

1. **Maps are NOT central; geography is on-demand.** Map-anchored placement appears only where a
   specific beat needs it (`shot_scale: macro` establishing, or a cue with a map-pixel
   `spatial_target`). It is supporting evidence, never the default canvas. Medium/micro shots that
   place action in an off-map 2D/3D scene resolve their `spatial_target` against the storyboard's
   `setting.scene_anchors` (a `region_id`) or an authored `target_px` — that is the **storyboard
   director's** job, not this one. This skill owns only the geo-grounded pixels.
2. **No eyeballed coordinates. Ever.** Every map pixel is DERIVED from `(lat, lon)` through the SAME
   Web-Mercator projection the basemap was rendered with, via
   `lib.mapkit_subjects.latlon_to_local_pixel(lat, lon, map_info)` (pure math — no tile fetch). You
   never hand-edit a stored `px`/`py`, and you never nudge a pin in CSS. `qa_geo` recomputes every
   stored pixel from its coordinates and FAILS on a >2px discrepancy.
3. **Every coordinate carries provenance.** Each anchor's `(lat, lon)` traces to a real source
   (gazetteer / Wikidata / a cited primary map). Put it in the anchor record; the asset-sourcing
   discipline is the same license/provenance hygiene used everywhere on the channel.
4. **Perfect TIME + SPACE synchrony.** This skill owns the SPACE half of the contract for
   map-anchored cues: the right action lands on the right place. The storyboard supplies each cue's
   `spatial_target`; you make every map-pixel `anchor_id` it references resolve to a real, projected
   pixel. (The TIME half — `anchor_phrase` resolved to a narrated word — lives in the storyboard +
   cue-drift gates, not here.)
5. **Noir look is untouched here.** Basemaps you build use the MM theme's `basemap_filter` (the
   channel noir look is HyperFrames-generated, never Recraft, never a clip grade). When a basemap is
   needed at all, build it through the theme — do not restyle it.

## Read first

- memory `geographic_pin_accuracy_required` — never eyeball CSS percentages on a map; derive pixels
  from real `lat`/`lon`.
- `lib/mapkit_subjects.py` — the projection + basemap API. The functions this stage uses:
  `latlon_to_pixel` / `latlon_to_local_pixel` (pure projection, no network) and `render_basemap`
  (builds the noir basemap and returns the `map_info` projection dict).
- `skills/pipelines/midnight-magnates-doc/theme-director.md` — for the `basemap_filter` and palette,
  if a basemap is needed.
- `skills/pipelines/midnight-magnates-doc/storyboard-director.md` — where `spatial_target`,
  `shot_scale`, and the `through_line` are authored; this skill only resolves the map-pixel anchors
  the storyboard references.

## Workflow

Run this stage ONLY if the storyboard has at least one map-anchored beat (a `macro` shot on a map, a
`pin_drop`, or any cue whose `spatial_target` is an `anchor_id`). Otherwise skip — there is nothing
to ground.

1. **Collect the map-anchored anchors** the storyboard references by `anchor_id`. For each, look up a
   real `(lat, lon)` from a cited source and record provenance.

2. **Build the basemap(s) you actually need** — usually one establishing extent for a `macro` shot,
   not a tier cascade. Use `mapkit_subjects.render_basemap(...)` with the theme's `basemap_filter`.
   Keep the returned **`map_info` projection dict** (it carries `zoom`, `global_x_left`,
   `global_y_top` — the exact fields the projection helper reads).

3. **Derive every pixel from coordinates** with the SAME `map_info`:
   `px, py = mapkit_subjects.latlon_to_local_pixel(lat, lon, map_info)`. Never author a pixel by
   hand; never reuse a stale cached pixel after the extent changes.

4. **Patch OOB pixels** (memory `mapkit_oob_pixel_patch`): at low zoom + width 1920 the out-of-bounds
   tile fill becomes a bright white band after the noir filter. Fill any near-white column
   (mean luma > 235) with dark navy `(12, 18, 30)` before saving the basemap PNG.

5. **Write `artifacts/positions.json`** — the canonical output the spatial gates read:

   ```jsonc
   {
     "map_info": { "zoom": 5, "width": 1920, "height": 1080,
                   "global_x_left": 0.0, "global_y_top": 0.0 },   // from render_basemap
     "anchors": [
       { "id": "dc",  "lat": 38.8951, "lon": -77.0364, "px": 1322, "py": 470,
         "provenance": { "source": "Wikidata Q61 — Washington, D.C." } }
     ]
   }
   ```

   `px`/`py` MUST equal `latlon_to_local_pixel(lat, lon, map_info)`. If you change the extent, recompute
   ALL pixels — do not leave a stale one behind.

6. **(Optional) `artifacts/geography.json`** — only if you built more than one map extent and want the
   advisory anchor-in-extent check. It lists `map_extents[]` (`tier` / `center_lat` / `center_lon` /
   `zoom` [/`width`/`height`]) and `anchors[]` (`id` / `lat` / `lon` / `tier`). Its ABSENCE is not a
   failure — a single-extent video legitimately omits it.

## Enforcement model (the runner decides "done", not you)

A deterministic runner — not the agent — shells the gates and writes the machine-authored
`artifacts/qa_report.json`. You never hand-author that report, never claim this stage passed, never
cite a `scripts/qa_*.py` path, and never run a gate as `python -m lib.<other_pkg>.gates.*`. To check
your spatial work, run the runner and read the report:

```bash
# run the spatial/geo gates that touch this stage, then read artifacts/qa_report.json:
python3 -m lib.midnight_magnates.runner run-gates --pipeline midnight-magnates-doc --project <project_dir> --stage geography

# confirm the build is green AND fresh before any downstream stage trusts it:
python3 -m lib.midnight_magnates.runner check-lock --pipeline midnight-magnates-doc --project <project_dir>
```

The real gates that exercise this stage's output (run `ls lib/midnight_magnates/gates/qa_*.py` for the
full set — if you ever name a gate, it MUST exist there):

- **`qa_geo`** — PRIMARY (blocking): every stored `(px, py)` in `positions.json` must equal the value
  recomputed PURELY from its `(lat, lon)` via `latlon_to_local_pixel` (>2px off ⇒ a hand-edited pixel
  ⇒ fail). SECONDARY (advisory): if `geography.json` is present, each anchor must project inside its
  tier's extent viewport (the "pin on the wrong continent" symptom).
- **`qa_spatial_anchor`** — every visible non-chrome action cue declares a resolvable `spatial_target`;
  an `anchor_id` target only resolves if that id exists in your `positions.json` anchors. (Authoring
  the targets is the storyboard's job; making the map ids resolvable is yours.)
- **`qa_visual_alignment`** — after render, the marker that actually painted must land within tolerance
  of its declared pixel (catches CSS-offset / transform-origin / stale-cache drift between "we computed
  the right spot" and "the dot is on the right spot").

Iterate with `run-gates` until `artifacts/qa_report.json` is all-green. Prefer "run the runner, read
qa_report.json" over reasoning about individual gate internals.

## Output

- `artifacts/positions.json` — `map_info` projection dict + `anchors[]` with coordinate-derived
  `px`/`py` and per-anchor `provenance`. (Required only when the video has map-anchored beats.)
- `artifacts/geography.json` — OPTIONAL; only for multi-extent videos wanting the advisory
  anchor-in-extent check.
- `assets/maps/<extent_id>.png` — the noir basemap(s) actually used, OOB-patched.

## Quality bar

- No eyeballed coordinates anywhere — every map pixel recomputes from `lat`/`lon` through the basemap's
  own projection.
- Every `anchor_id` a cue's `spatial_target` references resolves to a real anchor in `positions.json`.
- Every coordinate has provenance.
- If the video has no map-anchored beat, this stage produces nothing — and that is correct, not a gap.
