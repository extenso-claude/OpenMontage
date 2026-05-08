# Scene Director - Hybrid Pipeline

## When To Use

You are translating the hybrid structure into a visual system that keeps the source visible and the support layers under control.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/scene_plan.schema.json` | Artifact validation |
| Prior artifacts | `state.artifacts["script"]["script"]`, `state.artifacts["idea"]["brief"]` | Hybrid structure and source truth |
| Tools | `frame_sampler`, `scene_detect` | Optional source inspection |
| Playbook | Active style playbook | Layout consistency |

## Process

### 1. Keep The Anchor Medium Visible

If the piece is source-led, the source must remain visually primary in the scene plan. Do not hide the anchor behind constant overlays.

### 2. Reserve Support For Clear Jobs

Use support scenes for:

- chapter transitions,
- clarifying diagrams,
- stat emphasis,
- CTA or summary moments,
- gap-filling inserts.

### 3. Plan Variant Safety

If the project needs multiple aspect ratios, define where:

- subtitles live,
- speaker labels live,
- chart or code safe zones live,
- crop-sensitive source media becomes unsafe.

### 4. Use Metadata For Balance Rules

Recommended metadata keys:

- `anchor_rules`
- `support_rules`
- `safe_zones`
- `variant_rules`
- `overlay_density_limits`

### 5. Quality Gate

- the anchor medium stays primary where intended,
- support layers are limited and purposeful,
- aspect-ratio planning is explicit,
- no scene relies on invisible future magic.

## Common Pitfalls

- Turning source-led scenes into overlay soup.
- Forgetting variant-safe zones until compose.
- Using generated inserts for every transition.

## Source-Baked Element Awareness (MANDATORY for overlay-on-edited-video runs)

When the source MP4 already contains baked-in branding, CTAs, AI imagery, real photos, posters, or text, do not add overlays that duplicate them. Before designing the scene plan:

1. **Extract source frames at 0.5s intervals** with `ffmpeg -vf "fps=2,scale=1280:-2"`. Generates ~2 frames/sec, manageable count for a 10-min video (~1200 frames).
2. **Audit what's already on-screen at each VO beat**: channel branding cards, "SUBSCRIBE" / "Like" / "Leave a comment!!" UI animations, real film posters with titles, AI-illustrated portraits of named people, baked stat charts, US-map visualizations, subtitle bars.
3. **Drop any overlay that would duplicate** a baked element (logo wall over baked logos, "MIDNIGHT MAGNATES" chapter card over baked branding, "Tap follow" CTA over baked SUBSCRIBE button stack).
4. **Document drops in the cuelist** with `_dropped: true` and `_reason` so the editor can verify the choice.

A typical 10-minute edited source MP4 has 4–8 baked elements that would otherwise be doubled by a generic overlay system.

## Single-Description-Per-Entity Rule

Each named person, agency, or organization gets exactly **one** on-screen identity element at a time — either a photo card with full caption text, OR a lower-third with full text. Never both simultaneously.

When two cues would describe the same entity in overlapping time windows:
- Pick the stronger element (photo card if a real PD photo exists; lower-third otherwise).
- Merge the unique facts from the dropped element into the kept element's text (e.g., "Former Chairman of Joint Chiefs" merged into Powell's photo card as line 4).
- Add an explicit `_dropped: true` cuelist entry with rationale for the audit trail.

Symptoms of violation: a person's name on screen twice (once upper-right photo card, once lower-left lower-third) — viewer brain-locks for 1–2 seconds wondering if it's two different people.

## Concurrent-Cue Audit (run before render)

Build an audit plan that lists every pair of cues whose time windows overlap by ≥0.5s. For each pair, judge:
- **Same anchor zone?** (both lower-band, or both upper-right) → reposition or stagger one.
- **Same subject?** → drop one and merge content.
- **Different zones, different content?** → fine, keep both.

This audit takes 30 seconds with a Python script and catches every overlap before it ships.
