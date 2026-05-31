---
name: asset-coverage-gates
description: Before any Sleep Network overlay-postproduction compose ships, the cuelist MUST pass the asset-coverage gates. This file documents the mandatory cue-type diversity rules and the qa_asset_coverage.py gate that enforces them. Read this skill in the asset stage of any overlay-postproduction run, on any Sleep Network channel.
layer: 2
status: production
applies_to_channels: [midnight_magnates, grandpa_huxley, sleepy_biographer, sleep_network_*]
applies_to_pipelines: [hybrid, documentary-montage, clip-factory]
companion_files:
  - tools/clip_treatment/approved_toolkit.json
  - skills/core/clip-treatments.md
  - skills/core/animated-subjects-on-map.md
  - lib/mapkit_subjects.py
  - framework-videos/directives/midnight_magnates_overlay_postproduction.md
memory_anchors:
  - feedback_photo_card_policy
  - animated_subjects_on_map_method
  - project_archival_assets_process
  - copyright_treatment_defaults
  - card_bounds_qa_required
created: 2026-05-21
why_this_exists: |
  Pre-2026-05-21, the Vatican Entity full-edit shipped with 36 cards but ZERO archival
  photos, ZERO maps, ZERO HyperFrames animations, ZERO charts, ZERO transformative-use
  clips. Multiple standing rules in user memory + channel briefs were silently
  violated because there was no programmatic gate enforcing cue-type diversity.
  This skill exists to make those misses impossible going forward.
---

# Asset-Coverage Gates — Mandatory Pre-Compose Audit

Before any overlay-postproduction compose ships, the cuelist passes these gates.
**Compose is BLOCKED if any gate fails** unless an explicit `scrap_reason` is
documented for the missing item.

## The six gates

### Gate 1 — Named-figure photo cards (mandatory when PD photo exists)

For every NAMED HISTORICAL FIGURE mentioned in the narration:
- **Required**: a cue with `treatment == "lower_third_anchored"` that uses an
  archival photo (slug starts with `photo_`).
- **Acceptable substitution**: a transformative-use clip with the figure
  on-camera, wrapped in an approved frame per `skills/core/clip-treatments.md`.
- **Only acceptable skip**: `scrap_reason` documents that Wikimedia + Library of
  Congress + Internet Archive were all searched and no PD/CC photo of acceptable
  resolution exists.

**Why**: per the standing channel rule (`feedback_photo_card_policy` memory) —
*"Photo cards — always create when real photo exists"*. The editor is supposed
to be picking between AI portrait and real photo; if we never source the real
photo, the editor has no choice.

### Gate 2 — Animated maps (mandatory for every named place/journey/battle)

For every NAMED PLACE, JOURNEY, BATTLE, or GLOBAL ACTION:
- **Required**: a cue with `kind == "map"` rendered via `lib/mapkit_subjects.py`
  (or any subclass) with Carto Dark base + brightened noir filter
  (`Brightness ≥ 1.05` per `map_legibility_rule.md` memory).
- **Real lat/lon, never eyeballed CSS** (per `geographic_pin_accuracy_required` memory).
- **Animation**: pin drop, journey-line draw-in, or subject movement.
- **Only acceptable skip**: `scrap_reason` documents why the moment doesn't
  benefit from geographic context (rare — most named places do).

**Why**: per the standing brief — *"Maps — every named place or global actions
(animated journeys, objects, pins, etc)"*. Static text cards for locations are
the lazy fallback.

### Gate 3 — Charts/graphs/diagrams (mandatory for comparisons + multi-datapoint stats)

For every COMPARISON ≥ 3 datapoints OR every "vs" stat:
- **Required**: a cue rendered as a bar chart, tristat comparison, or diagram —
  not a plain numeral card.
- **Only acceptable skip**: the stat has only ONE datapoint and a hero numeral
  card is genuinely sufficient.

**Why**: per the standing brief — *"Charts — every number, %, comparison, ranking"*.

### Gate 4 — HyperFrames bespoke animations (minimum 1 per chapter)

For every CHAPTER:
- **Required**: at least ONE cue with `kind == "animation"` anchored to the
  chapter's most cinematic beat. Examples: CLASSIFIED stamp, wax-seal
  pour-and-press, bricks-into-pocket drop, tape-spool spin, document scroll,
  network-node radial reveal, redaction-bar animation, dial rotation.
- **"Go wild" is a hard requirement**, not a suggestion.
- **Only acceptable skip**: chapter is < 90 seconds AND the avatar+card+map
  coverage is already dense.

**Why**: per the standing brief — *"Unique visual animations — strategize
throughout the video how to create more unique animated assets that help
explain VO to viewers or enhance emotions"*.

### Gate 5 — Transformative-use clips (mandatory when iconic source IS the content)

For every moment where:
- A specific famous broadcast / on-camera figure / news photo IS the iconic content
- Or a famous artwork (Veronese painting, Babington Plot ciphered letter, X-Report photo) IS the moment
- AND free stock won't carry it

**Required**: a clip sourced per `skills/core/clip-treatments.md`, treated with
the locked filter + approved frame wrap. Filter rules:
- Video → `grade_cyan_orange` + frame wrap; audio kept (vo-pause) → `pitch_up_1st`
- Image → `grade_crushed_warm` (after Ken Burns) + frame wrap
- Audio → `pitch_up_1st` (loudnorm I=-14 auto)

**Frame** must be one of the 8 approved (see `tools/clip_treatment/approved_toolkit.json`).
Midnight Magnates default picks: `dossier`, `surveillance`, `boardroom`,
`tv-vintage`, `newspaper`, `magnifier`.

**Source priority**: Internet Archive first (`collection:"universal_newsreels"`
is fully PD). yt-dlp `--download-sections` as fallback. 5-min cap on disk.

**Audio role tag mandatory** per `clip_vo_dialogue_handling` memory:
`vo-pause` / `vo-over` / `mixed`.

**Why**: the user-locked default 2026-05-20/21 — and the standing brief —
*"For moments where the iconic source IS the content (specific broadcast /
on-camera figure / news photo / etc) and there is a famous piece of content
that must be included or there is free stock won't carry it"*.

### Gate 6 — Stock footage clips (where free stock outperforms AI)

For period-authentic establishing moments (Thames at dawn, candlelit corridor,
quill writing, ocean waves, etc.):
- **Encouraged** when free Pexels/Pixabay clip outperforms AI generation
- **Mood filter mandatory** — never accept "first keyword-match" without an
  eyeball check for tonal fit (the channel is noir; "candle birthday cake" fails)

### Gate 7 — Positioning + no-overlap (NEW 2026-05-21)

Before compose, every cue must pass:
- **`qa_card_bounds.py`** — frame-bounds compliance (≥15% padding, anchor-from-bottom for lower corners)
- **`qa_element_overlap.py`** — no overlay-vs-overlay collision in shared timeline windows
- **`qa_source_collision.py`** — no overlay covers source's face, baked chyron, SUBSCRIBE stack, or "leave a comment" bubble
- **`qa_min_hold.py`** — every overlay holds long enough to be readable (`words/3 + 2s` formula)

See `skills/core/overlay-positioning-rules.md` for the full rule set. **All four scripts BLOCK compose on failure.**

### Gate 8 — Sound design drift + density (NEW 2026-05-21)

Before compose, every music + SFX cue must pass:
- **`qa_audio_drift.py`** — Whisper-anchored `t_in`; drift ≤ 0.5s for music, ≤ 0.15s for SFX accents, ≤ 2s for ambient SFX
- **Density audit** — first 10 minutes wall-to-wall music OK; after 10:00, music sparse (20–35% of timeline) and period-fit
- **Alarming-SFX check** — no `siren`/`alarm`/`crash`/`boom`/`klaxon`/`explosion` category SFX after 10:00

See `skills/core/sound-design-rules.md` for the full directive. **BLOCKS compose on failure.**

### Gate 9 — Subjective fit (eyeball check, not auto-failure)

For every cue that survives the automated gates, ask: **does this asset SELL the moment?** If no, document a `scrap_reason` and drop the cue rather than ship it.

Examples from the 2026-05-21 Vatican Entity review that were dropped this way (not because they were broken — because they didn't fit):
- `anim_5_bricks` — bricks-into-pocket animation read as confusing, not metaphorical
- `lt_forensic_2002` — lower-third on a forensic moment that the source's own AI imagery already carried
- `anim_wax_seal` — wax-seal animation broke the visual flow rather than punctuating
- `card_senigallia` — period-card overlay that duplicated the source's narrative
- `chart_lepanto_galleys` — chart of galley counts the VO had already verbalized
- `chart_lepanto_human` — same pattern, redundant

This gate is the only one that REQUIRES human judgment. The other gates make it impossible to ship broken assets — Gate 9 makes it possible to drop assets that work but don't fit.

## The qa_asset_coverage.py gate

Lives at `projects/<project>/scripts/qa_asset_coverage.py` (or run via the
shared `framework-videos/execution/qa/asset_coverage.py`). Reads the cuelist
and Whisper transcript and outputs a coverage report.

**Required exit behavior**: if ANY `MISSING` row exists without a documented
`scrap_reason`, the script exits non-zero and the chunked compose script aborts.

**Coverage check pseudocode**:
```python
issues = []
# Gate 1: named figures
for figure in extract_named_figures(whisper, script):
    if not has_photo_card(cuelist, figure):
        issues.append(("MISSING_ARCHIVAL", figure))
# Gate 2: places
for place in extract_named_places(whisper):
    if not has_map_cue(cuelist, place):
        issues.append(("MISSING_MAP", place))
# Gate 3: comparisons
for cmp in extract_comparisons(whisper):
    if not has_chart(cuelist, cmp):
        issues.append(("CANDIDATE_CHART", cmp))
# Gate 4: chapters
for chapter in extract_chapters(whisper):
    if count_animations_in(cuelist, chapter) < 1:
        issues.append(("MISSING_ANIMATION", chapter))
# Gate 5: iconic moments
for moment in extract_iconic_moments(script):
    if not has_treatment_clip(cuelist, moment):
        issues.append(("MISSING_CLIP_TREATMENT", moment))
# Write report
write_coverage_report(issues)
if issues_without_scrap_reason(issues):
    sys.exit(1)  # blocks compose
```

The compose script (or pipeline orchestrator) MUST run this gate before
spawning the chunked compose. No exceptions.

## How to invoke from a pipeline

```bash
# Mandatory before any overlay compose
python3 projects/<project>/scripts/qa_asset_coverage.py
if [ $? -ne 0 ]; then
  echo "Coverage gate failed — see qa/coverage_report.md"
  exit 1
fi
# Only then:
python3 projects/<project>/scripts/compose_full_chunked.py
```

## Cross-channel applicability

This gate applies to **every Sleep Network channel** doing overlay-postproduction:
- **Midnight Magnates** — defined in `framework-videos/directives/midnight_magnates_overlay_postproduction.md`
- **Grandpa Huxley** — same rules, but frame defaults are `fireside`, `library`, `photo-album`, `magnifier`. Animations skew warm.
- **Sleepy Biographer** — same rules; figure cards critical for biographical episodes.
- **Future channels** — add to `applies_to_channels` in this file's frontmatter.

## Self-Annealing Notes

- **2026-05-21**: Created to permanently fix the Vatican Entity miss (36 cards, 0 photos / maps / animations / charts / clips). Root cause was PIL text cards being the path of least resistance with no enforcement that diversified assets must exist. Future runs read this skill in the asset stage; the gate runs before compose; compose can't ship if coverage fails.
- **2026-05-21 (PASS 2)**: Added Gates 7 (positioning), 8 (sound-design drift), 9 (subjective fit). The original 6 gates ensured cue-type diversity but didn't catch positioning bugs (faces covered, text overlapping, chapter titles spilling), didn't catch sound-design drift (music + SFX off the anchor word), and didn't allow human-judgment drops (assets that work but don't fit). These three gates close those gaps.
