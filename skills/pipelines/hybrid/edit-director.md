# Edit Director - Hybrid Pipeline

## When To Use

This stage creates the layered edit logic for a source-led video with support elements. The order matters: anchor cut first, support layers second.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/edit_decisions.schema.json` | Artifact validation |
| Prior artifacts | `state.artifacts["assets"]["asset_manifest"]`, `state.artifacts["scene_plan"]["scene_plan"]`, `state.artifacts["script"]["script"]` | Source/support assets and timeline intent |
| Playbook | Active style playbook | Typography and motion consistency |

## Process

### 1. Lock The Anchor Cut First

The viewer should understand the story before support overlays are added. If the anchor cut is weak, support layers will not save it.

### 2. Add Support In Priority Order

Typical order:

1. subtitles,
2. speaker or context labels,
3. diagrams or stat cards,
4. optional inserts,
5. CTA elements.

### 3. Protect Readability

Never stack too many support layers in one moment. If subtitles, labels, charts, and overlays collide, simplify.

### 4. Use Metadata For Layering Logic

Recommended metadata keys:

- `anchor_cut_notes`
- `layer_order`
- `overlay_windows`
- `variant_edit_rules`

### 5. Quality Gate

- the anchor cut works on its own,
- support layers clarify instead of distract,
- mobile readability survives,
- variants remain consistent.

## Common Pitfalls

- Trying to fix a weak cut with extra graphics.
- Letting support layers compete with the source.
- Building each platform variant as a separate editorial philosophy.

## Whisper-Anchored Timing (when overlay aligns to existing source VO)

For overlay-on-edited-video runs, every cue with a name/date/figure trigger must be anchored to the actual word timestamp from a faster-whisper transcript of the source audio:

1. Extract source audio: `ffmpeg -i source.mp4 -ac 1 -ar 16000 -c:a pcm_s16le source.wav`
2. Run faster-whisper base.en with `word_timestamps=True` → produces JSON with start/end per word
3. Build a `_anchors` map in the cuelist mapping cue triggers to their first-occurrence word time
4. Set cue `t_in` to the anchor time (or anchor − 0.2s for fade-in lead)

**Drift budget: ±0.4s per cue.** Anything more drifts the cue out of sync with what the narrator is actually saying — viewers register "wrong word on screen" within 600ms.

## Concurrent-Cue Resolution

Before locking edit decisions, programmatically check every pair of cues for time overlap. For pairs ≥0.5s overlapping:
- Same subject? Drop one, merge text.
- Same anchor zone (both lower-band, both upper-right)? Stagger or reposition.
- Different zones + different subjects? Approved — keep both.

## True-Alpha vs Screen-Blend Decision (overlay deliverables)

If the editor's NLE supports ProRes 4444 import (Premiere Pro, Resolve, FCPX, Avid all do), output the overlay as **ProRes 4444 .mov with true alpha**. The editor drops it on a track at 100% opacity, no blend mode. Cleanest output, no artifacts.

If the NLE only accepts H.264 .mp4 (rare; older toolchains, web-first pipelines), output **black-background .mp4** for "Screen" blend mode. Caveats:
- Chroma subsampling (yuv420p) smears italic serif edges
- Screen blend math amplifies any encoding noise
- Prefer ProRes 4444 whenever possible; only ship .mp4 as a fallback

Encode both formats from the same alpha master so the user has the choice without a re-render.
