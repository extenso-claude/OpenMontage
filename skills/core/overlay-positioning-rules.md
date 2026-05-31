---
name: overlay-positioning-rules
description: Locked Sleep Network rules for positioning every overlay element so it (a) fits the 1920x1080 frame with safe padding, (b) does not overlap other overlay elements at the same timestamp, (c) does not collide with the source video's existing elements (faces, baked chyrons, AI imagery), and (d) holds on screen long enough to be readable. Read this skill in the cue-design stage of any Sleep Network overlay-postproduction run. The companion qa_element_overlap.py + qa_card_bounds.py + qa_min_hold.py scripts enforce these rules pre-compose.
layer: 2
status: production
applies_to_channels: [midnight_magnates, grandpa_huxley, sleepy_biographer, sleep_network_*]
applies_to_pipelines: [hybrid, documentary-montage, clip-factory]
companion_files:
  - skills/core/asset-coverage-gates.md
  - skills/core/clip-treatments.md
  - skills/core/sound-design-rules.md
  - projects/vatican-entity-mm/scripts/qa_card_bounds.py
  - projects/vatican-entity-mm/scripts/qa_element_overlap.py
  - projects/vatican-entity-mm/scripts/qa_min_hold.py
memory_anchors:
  - overlay_positioning_locked
  - card_bounds_qa_required
  - feedback_qa_text_graphic_overlap
  - animation_hold_time_required
  - source_aware_placement_required
created: 2026-05-21
why_this_exists: |
  The 2026-05-21 Vatican Entity review pass flagged 11 distinct positioning
  failures across 23 comments: character cards covering subject faces, text
  overlapping frame borders, chapter titles spilling outside 1920x1080, map
  labels colliding, animations on screen too briefly to read, lower-thirds
  stacked with photo cards on the same person at the same time. The pattern:
  position was decided in isolation from (a) what other overlays were on
  screen at the same time and (b) what was on the SOURCE video at the same
  time. This skill encodes the full set of positioning rules so future runs
  pre-empt the bug class.
---

# Overlay Positioning Rules — Sleep Network Locked

## The five positioning rules

Every overlay element (card, photo, lower-third, map, animation, chart, clip-frame, PiP avatar) MUST pass all five before compose:

1. **Frame-bounds** — fits inside 1920x1080 with ≥15% padding from every edge
2. **No-overlap (overlay vs overlay)** — does not overlap any other overlay element with which it shares any timeline window
3. **Source-aware (overlay vs source)** — does not cover the source's currently-visible character face, baked chyron, "leave a comment" speech bubble, SUBSCRIBE stack, or AI-painted hero element
4. **Min-readable-hold** — on screen long enough for the viewer to read its text content
5. **Drift-anchored** — `t_in`/`t_out` anchored to a Whisper word, within the per-cue-type drift budget

The first four are the new additions from 2026-05-21. The fifth was already locked.

---

## Rule 1 — Frame bounds (RE-LOCKED, see `card_bounds_qa_required`)

Every card and overlay element fits inside 1920x1080 with safe margins.

| Anchor | Constraint |
|---|---|
| `lower_left` / `lower_right` | `card_y = H - card_h - 40px`. Anchor from BOTTOM, not top. |
| `upper_left` / `upper_right` | `card_y = 40px`, clamped so `card_y + card_h ≤ H - 40`. |
| `center` / `hero` | Card centered; `card_y = (H - card_h)/2`, plate must not touch any edge. |

`block_h` must include EVERY y-increment in the draw flow — brass rule offsets, label gaps, post-rule jumps, NOT just text dimensions. The Iran-history v3→v4 fix: stat cards were under-counting by 28px.

**Plate `pad_y_bot` ≥ 40px** on top of the correct `block_h`.

QA: `qa_card_bounds.py` (canonical at `framework-videos/execution/editing/qa_card_bounds.py`). MANDATORY before compose. `critical_count > 0` blocks compose.

**Chapter title cards specifically** — see Rule 3 (Source-aware) for the navy plate requirement that masks the source's baked stale chapter titles.

---

## Rule 2 — No-overlap (overlay vs overlay) (NEW 2026-05-21)

For every pair of cues `(a, b)` with `overlap(a.timewindow, b.timewindow) > 0.3s`:

- Their visual bounding boxes (after final position) MUST NOT overlap by more than 5% of either box's area.
- If overlap > 5%, one cue MUST be:
  - moved to a non-conflicting quadrant (preferred), OR
  - re-timed so their windows do not overlap (next-best), OR
  - merged into a combined visual (last resort — only when both describe the same entity)

### The four-quadrant placement matrix

For lower-corner photo cards + lower-third chyrons, the 1920x1080 frame is divided into 4 quadrants. Within any 5-second window, only one overlay element may occupy each quadrant.

```
+-----------------+-----------------+
|  upper_left     |   upper_right   |
|  (chapter card  |   (date card,   |
|   slot)         |    stat card)   |
+-----------------+-----------------+
|  lower_left     |   lower_right   |
|  (photo card,   |   (photo card,  |
|   lower-third)  |    lower-third) |
+-----------------+-----------------+
```

**Center is reserved for hero titles + map full-bleeds** — no card overlays the center band when a hero/map is active.

### Lower-third + photo card conflict resolution

If both want to describe the same person in the same window:
- Photo card WINS (richer information)
- Drop the lower-third entirely or merge its unique facts into the photo card's caption block

This is the existing single-description-per-entity rule from the channel directive — now mechanized by the overlap audit.

### QA script

`projects/<project>/scripts/qa_element_overlap.py` — reads cuelist, computes bounding box per cue (per anchor + treatment), checks all pairs with timeline overlap, exits non-zero if any violation. **Compose blocked on failure.**

---

## Rule 3 — Source-aware placement (NEW 2026-05-21)

The overlay layer is composited ABOVE a finished source MP4. The source has its own elements — faces, baked chyrons, AI hero imagery, channel branding. Overlay placement MUST consider what's underneath.

### Mandatory pre-cue source inspection

For every CARD or PHOTO cue, before locking position:

1. Extract a representative frame from the SOURCE at `t = t_in + 0.5s` via:
   ```
   ffmpeg -y -ss <t_in+0.5> -i source.mov -vframes 1 -vf "scale=1920:1080" qa/source_frame_<cue_id>.png
   ```
2. Identify the face/subject quadrant in the source frame (top-left / top-right / bottom-left / bottom-right / center).
3. **Place the overlay in the OPPOSITE quadrant.** Never cover the subject.

For HERO and MAP overlays (which take the full frame):
- Choose timing where the source is in a transition / wide / non-subject moment.
- If no such window exists, postpone the overlay or pick a less-dominant treatment (lower-third instead of hero).

### Specific source-content avoidance zones (from the channel directive)

| Source window | Zone to keep clear |
|---|---|
| 0:00–2:35 (CTA + Cold Open) | "Leave a comment!!" speech bubble + animated typing field on right side |
| Episode end (-10s) | SUBSCRIBE stack + Spotify "Following" pill (right side) |
| Chapter transitions | Baked stale "Jim Jones" chapter title from previous-episode template (center, 200–700px tall) |
| Any baked AI portrait | Don't add a photo card whose subject appearance doesn't match the on-screen character |

### Chapter-title source-bake masking (NEW 2026-05-21)

The Vatican Entity source has the PREVIOUS episode's chapter title cards baked at chapter-transition windows (a stale "Chapter X: Jim Jones — Jonestown" template). The overlay's chapter title cue MUST:

1. Place a navy plate (`(8, 12, 22)` alpha 232) covering the source's baked title region (roughly center-vertical, 1400px × 400px from chapter-transition cataloging).
2. Render the correct overlay chapter title ON TOP of that plate.
3. Plate fade-in 0.4s before text fade-in so the source title is masked before the new one appears.

**Plate placement contract** in cuelist:
```json
{
  "id": "chapter2_title",
  "kind": "card",
  "treatment": "chapter_title_with_plate",
  "plate_box": [240, 340, 1680, 740],
  "plate_color": [8, 12, 22],
  "plate_alpha": 232,
  "text_box": [280, 380, 1640, 700],
  "title": "Chapter Two: The Holy League",
  "subtitle": "Pius V, Don Juan, Lepanto — 1566–1572"
}
```

### QA script

`qa_source_collision.py` — for each card cue, extracts a source frame, runs a face/feature detector, and verifies overlay box is in a quadrant the source isn't occupying. **Warns** for face overlap (manual override allowed when intentional, e.g., portrait-corner with a tight chyron). **Fails** for baked-chyron / SUBSCRIBE-stack overlap (those are hard rules).

---

## Rule 4 — Min-readable-hold time (NEW 2026-05-21)

Every overlay's on-screen duration must allow the viewer to read its text content.

### Hold-time formula

```
min_hold_s = max(2.5, ceil(words / 3.0) + 2.0)
```

Where `words` = total word count of all text in the overlay (title + subtitle + caption + chyron).

| Element | Typical words | Min hold |
|---|---|---|
| Lower-third (name + role) | 4–8 | 4–5s |
| Photo card (name + role + dates) | 10–14 | 6–7s |
| Chapter title (title + subtitle) | 10–18 | 6–8s |
| Hero stat reveal | 1–6 | 3–4s |
| Document animation (X-Report, dossier, telegram) | 40–80 | 10–14s |
| Map with 3+ pin labels | label-word-count × 3 | ≥6s |

### Map animation hold rule (NEW)

If a map has > 2 labeled pins, hold ≥ 6s (so viewer can scan each pin's label sequentially). If > 4 labeled pins, hold ≥ 8s.

### Document/diagram animation hold rule (NEW)

For X-Report, dossier-spread, telegram-reveal, redaction-line animations:
- Compute total visible word count.
- Set hold = max(8s, ceil(words / 3) + 2s).
- Add a +1.5s "settle" at the end where the document is fully visible (no motion) so the viewer's eye can scan.

### QA script

`qa_min_hold.py` — reads cuelist, computes expected min_hold per cue based on words, fails any cue with `t_out - t_in < min_hold`. **Compose blocked on failure.**

---

## Rule 5 — Drift-anchored timing (already locked, see related skills)

Every cue's `t_in` MUST anchor to a Whisper word. Drift budgets:

| Cue type | Drift budget | Skill |
|---|---|---|
| Avatar | ±0.04s (40ms) | `qa_avatar_sync.py` |
| Card (figure/place/year) | ±0.4s | `qa_card_timing.py` |
| Map | ±0.5s | `qa_card_timing.py` |
| Animation | ±0.5s | `qa_card_timing.py` |
| Clip (transformative-use) | ±0.3s | `qa_card_timing.py` |
| Music (-3s pre-roll on anchor word) | ±0.5s | `qa_audio_drift.py` |
| SFX accent | ±0.15s | `qa_audio_drift.py` |
| SFX ambient bed | ±2s | `qa_audio_drift.py` |

---

## Map-label collision avoidance (NEW 2026-05-21)

When a map has multiple pins close together, their labels collide. The 2026-05-21 review found this in `map_vatican_network` and `map_mediterranean`.

### Required label placement algorithm

In `lib/mapkit_subjects.py` (or per-project subclass):

1. Project each pin's lat/lon to pixel coords (per `geographic_pin_accuracy_required`).
2. For each pin, the label has 4 candidate slots: right (preferred), left, above, below.
3. Compute bounding boxes for all label candidates.
4. Greedy-pick: for pin 1, take preferred slot. For pin 2..N, take the first non-colliding slot.
5. If no slot is non-colliding, add a leader line from the pin to a pulled-out label position.

### Visual style

- Labels use Georgia Italic Bold 22pt with brass underline (`#c9a84c`).
- Label plate is a 6px-padded rounded-rect, navy alpha 232.
- Leader lines: brass `#c9a84c` 1.5px stroke, ≤ 60px length.

### QA verification

Render the final map MP4, extract its mid-animation frame, run text-box overlap detection. Any overlap = re-render with different slot assignments.

---

## Per-cue position audit workflow (NEW 2026-05-21)

For EVERY photo card + lower-third + chyron in the cuelist:

```bash
python3 scripts/per_cue_position_audit.py
```

This script:
1. For each card cue, extracts the source frame at `t_in + 0.5s`
2. Auto-detects subject quadrant via OpenCV face detection (or Mediapipe)
3. Recommends overlay placement = opposite quadrant
4. Writes a `qa/position_plan.md` with per-cue recommendations
5. The renderer reads the position plan and uses the recommended anchor

**This eliminates the "character card covers the face" bug class entirely.** Every card gets a per-cue position decision, not a default `lower_left`.

---

## "Don't force-fit" rule (NEW 2026-05-21)

If an asset doesn't sell the moment (e.g., a chart that's too dense, a map that adds nothing, an animation that's confusing) — DROP IT. Document a `scrap_reason` in the cuelist.

The 2026-05-21 review removed 6 cues this way: `anim_5_bricks`, `lt_forensic_2002`, `anim_wax_seal`, `card_senigallia`, `chart_lepanto_galleys`, `chart_lepanto_human`. None were technically broken — they just didn't fit. The coverage gate already allows `scrap_reason` overrides; use them.

**Rule:** any cue that survives QA-as-bug-free but FAILS the "does this sell the moment?" eyeball check is a candidate for drop, not for compose.

---

## Required QA scripts (ALL MANDATORY before compose)

| Script | What it checks | Block compose on fail? |
|---|---|---|
| `qa_card_bounds.py` | Rule 1 — frame bounds | YES |
| `qa_element_overlap.py` | Rule 2 — no overlay-vs-overlay overlap | YES |
| `qa_source_collision.py` | Rule 3 — source-aware placement | YES on hard zones, WARN on faces |
| `qa_min_hold.py` | Rule 4 — readability hold | YES |
| `qa_card_timing.py` | Rule 5 — drift on visual cues | YES |
| `qa_avatar_sync.py` | Rule 5 — drift on avatar cues | YES |
| `qa_audio_drift.py` | Rule 5 — drift on music + SFX cues | YES |
| `qa_asset_coverage.py` | Coverage gates 1–6 | YES |

All scripts share the same I/O pattern: read `artifacts/cuelist_v<N>.json`, read `assets/whisper/full.json`, write `qa/<script_name>_report.md`, exit 0 on pass / non-zero on fail.

The orchestrator (`compose_full_v<N>_chunked.py`) runs all eight before its first chunk and aborts the compose if any fail.

## Self-Annealing Notes

- **2026-05-21**: Created to permanently fix the bug class flagged in the Vatican Entity v4 review pass (11 distinct positioning failures). Each rule maps to a specific user comment or 2026-05-21 review-pass finding. The skill exists so future Sleep Network channel runs don't re-discover these rules empirically.
- **2026-05-21**: Source-aware placement (Rule 3) was previously implicit ("don't cover the face") but not enforced. Per-cue source frame extraction + face-detect quadrant logic makes it programmatic.
- **2026-05-21**: Map label collision avoidance was previously delegated to mapkit's default labeller. The user found 2 map cues (vatican_network, mediterranean) with overlapping labels. The greedy-with-leader-lines algorithm above is the locked solution.
