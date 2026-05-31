---
name: character-treatments
description: How a named historical figure is put on screen in the animated-history-map channel. Defines the three sanctioned character treatments (HERO_CUTOUT, FULL_SCREEN_CARD, LOWER_CORNER), WHEN to use each, and the qa_character_presence gate that blocks the "tiny lone card on empty parchment" bug. Read this in the storyboard/asset stage of any animated-history-map shot that introduces or features a person.
layer: 2
status: production
applies_to_channels: [animated_history_map]
applies_to_pipelines: [animated-history-map]
companion_files:
  - lib/animated_history_map/character_treatment.py
  - lib/animated_history_map/cutout.py
  - lib/animated_history_map/gates/qa_character_presence.py
  - lib/animated_history_map/compiler.py
  - skills/core/asset-coverage-gates.md
memory_anchors:
  - never_placeholder_portraits
  - feedback_photo_card_policy
  - motion_direction_qa_required
created: 2026-05-30
why_this_exists: |
  Pre-2026-05-30, every character beat in the animated-history-map channel
  compiled to the SAME tiny lower-left card (the compiler's SLOT_LOWER_LEFT ==
  560x280, ~26% of frame height) floating on empty parchment. The b04_booth
  shot — Booth named at the moment of the assassination — was a 560x300 postage
  stamp on a blank page. The cut-out treatment the channel was supposed to use
  (background removed, white-gray border, placed LARGE on the live scene) was
  built (cutout.py) but never wired in. This skill defines the treatment system
  and the gate (qa_character_presence) makes the postage-stamp bug un-shippable.
---

# Character Treatments — Putting a Named Figure On Screen

A named historical figure is the emotional center of a beat. The old default —
a small lower-corner card on empty parchment — buries that figure in a postage
stamp. **Every character beat must resolve to one of three treatments.** The
`qa_character_presence` gate blocks compose if a character beat is a small lone
card with nothing under it.

The vocabulary, geometry, and the cutout-resolution helper all live in
`lib/animated_history_map/character_treatment.py` (imported by both the compiler
and the gate, so the renderer and the rule can never drift).

## The three treatments

### 1. HERO_CUTOUT — the figure stands IN the scene  *(default for a reveal)*

Background removed + white-gray border (via `cutout.py`), composited **large**
onto the live scene/map. **Frame height ≥ 30% (≥ 324px on 1080)**, backed by a
real sprite (`asset_id`). The figure occupies the frame; it does not sit in a
box in the corner.

- Resolve the sprite with
  `character_treatment.resolve_hero_cutout(portrait_path, out_path)` — it
  delegates to `cutout.cutout` (rembg / U2Net), draws the bordered outline, and
  returns the placed bbox (`SLOT_HERO_CUTOUT`, right-anchored, ~78% frame
  height). Pass `side="left"` to mirror for a subject that faces right (so it
  looks **into** frame — see `motion_direction_qa_required`).
- Transitions ON: pop / slide / fade onto the scene. It is a presence, not a
  label.
- **Use when**: first or important reveal of a figure; a figure who IS the
  moment (the assassin named, the victim introduced, the conspirator unveiled).

### 2. FULL_SCREEN_CARD — the portrait IS the shot

A framed portrait that (nearly) fills the frame — **≥ 85% width AND ≥ 85%
height** (`SLOT_FULL_SCREEN`) — carried by a **camera move** (`camera_push_in`
/ `camera_pull_out` / `camera_pan` / `story_dive`).

- The whole frame is the portrait + its period frame; a slow push-in gives it
  life.
- **Use when**: a held portrait beat with no competing scene — a moment of
  reflection on one person, a "here is who this was" pause.

### 3. LOWER_CORNER — a name-tag over real content  *(scene-anchored only)*

The existing small lower-corner card (the compiler's `SLOT_LOWER_LEFT`). **Only
legitimate when composited over real scene content**: a full-frame scene
primitive (`panel_archival` / `panel_illustration` / `story_dive` /
`clip_archival` / `document_overlay` / `parallax_layers` / `map_sprite`) is live
in the **same time window**, OR a map basemap underlies the timeline.

- A lower-corner card on an **empty** background is the bug. It is allowed only
  as a label while the scene itself carries the frame.
- **Use when**: the figure has already been revealed (a recurring face), or an
  establishing panel / archival scene / map is already on screen and the card
  is just identifying who we're looking at.

## WHEN to use which — decision order

1. Is this the figure's **reveal**, or a figure who **IS** this moment?
   → **HERO_CUTOUT**.
2. Is this a **held single-portrait** beat with a slow camera and no competing
   scene? → **FULL_SCREEN_CARD**.
3. Is there **already a panel / archival scene / map** on screen, and you just
   need a name-tag? → **LOWER_CORNER** (scene-anchored).
4. None of the above → you do not have a finished character beat. Promote it to
   HERO_CUTOUT or put a scene under it.

A storyboard can declare the treatment explicitly via
`layer.params.treatment = "hero_cutout" | "full_screen_card" | "lower_corner"`;
otherwise the compiler/gate infer it from geometry + scene-window overlap.

## The qa_character_presence gate

`lib/animated_history_map/gates/qa_character_presence.py`. Reads
`artifacts/cuelist.json` (and optionally `positions.json` / `geography.json` for
basemap detection). For every cue whose kind is `character_card` /
`character_card_pop`:

- **PASS** if HERO_CUTOUT (bbox height ≥ 30% **and** `asset_id` present), OR
  FULL_SCREEN_CARD (bbox ≥ 85%×85%), OR LOWER_CORNER scene-anchored (a
  full-frame scene primitive overlaps its window, or a map basemap underlies the
  timeline).
- **FAIL** (`small_lone_character_card`) if it is a small lower card with no
  scene primitive overlapping and no basemap — the postage-stamp bug.
- **FAIL** on a mismatched explicit declaration: `hero_cutout` whose bbox is
  < 30% tall (`hero_cutout_too_small`) or has no sprite
  (`hero_cutout_no_sprite`); `full_screen_card` that doesn't fill the frame
  (`full_screen_too_small`); a tall TEXT card with no sprite
  (`tall_card_no_sprite`); an unknown treatment string (`unknown_treatment`).

A project with **zero** character beats passes (nothing to check). The gate is a
lint over what the compiler emitted — it verifies the compiler's real output,
not a plan.

### Fixtures (the bug can never silently return)

- `fixtures/qa_character_presence/good/` — a HERO_CUTOUT (tall + sprite), a
  FULL_SCREEN_CARD (+ camera), a LOWER_CORNER scene-anchored under a
  `panel_archival`, an inferred hero cutout, and an explicit declaration. Exit 0.
- `fixtures/qa_character_presence/bad/` — the b04_booth bug: a 560×280
  `character_card_pop` on parchment with no scene under it. Exit 1.

## Self-Annealing Notes

- **2026-05-30**: Created with the gate to permanently fix the b04_booth
  postage-stamp miss (560×300 lone Booth card = 27.8% frame height, on empty
  parchment, at the most important beat of the chapter). Root cause: the
  compiler routed every `character_card*` primitive to one small lower slot, and
  the bordered-cutout treatment (cutout.py) was never integrated. Fix:
  `character_treatment.py` owns the three treatments + the cutout-resolution
  helper; `qa_character_presence` blocks compose on a small lone card.
