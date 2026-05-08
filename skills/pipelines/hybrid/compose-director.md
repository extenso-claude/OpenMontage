# Compose Director - Hybrid Pipeline

## When To Use

Render the hybrid project so source media, support graphics, and audio all remain coherent across outputs.

## Runtime Routing (MANDATORY first step)

Read `edit_decisions.render_runtime`. Hybrid work typically sticks with Remotion because source footage + React support overlays compose cleanly in one pass:

- **`render_runtime="remotion"`** — default. Source footage via `<OffthreadVideo>`, support graphics as React components, one render.
- **`render_runtime="hyperframes"`** — pick only when the support layer is HTML/GSAP-native (e.g., animated text callouts, registry blocks). Source footage is still possible via `<video class="clip">` but lose some of the Remotion component stack. See `skills/core/hyperframes.md`.
- **`render_runtime="ffmpeg"`** — rare on this pipeline; implies no generated support layer.

Silent runtime swap is a CRITICAL governance violation. Escalate blockers per AGENT_GUIDE.md before substituting.

**Pass `proposal_packet` to `video_compose.execute()`** so the tool's in-tool swap-detection check runs against the proposal directly instead of being `skipped`.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/render_report.schema.json` | Artifact validation |
| Prior artifacts | `state.artifacts["edit"]["edit_decisions"]`, `state.artifacts["assets"]["asset_manifest"]` | Edit logic and support assets |
| Tools | `video_compose`, `audio_mixer`, `video_stitch`, `video_trimmer`, `color_grade`, `audio_enhance` | Final assembly and polish |
| Playbook | Active style playbook | Output consistency |

## Process

### 1. Verify Source And Support Balance

The final render should still look like a source-led video with support, not a collage of unrelated systems.

### 2. Check Variant Integrity

For each output variant, verify:

- crop safety,
- text safety,
- subtitle legibility,
- audio consistency.

### 3. Keep Audio Coherent

Source dialogue, narration, music, and effects should feel like one mix, not separate layers fighting for space.

### 4. Use Render Metadata

Recommended metadata keys:

- `variant_outputs`
- `balance_checks`
- `subtitle_checks`
- `audio_notes`

## Common Pitfalls

- Good master cut, broken platform variants.
- Support graphics clipping in vertical exports.
- Audio loudness shifting between source and generated sections.

## Memory-Check Before HyperFrames (MANDATORY)

`hyperframes doctor` reports system memory. If `free RAM < 1 GB`, do NOT route to HyperFrames even if `render_runtime="hyperframes"` is locked — HF spawns Chrome (~256 MB per worker) and fails non-deterministically at low memory.

Procedure:
1. Run `hyperframes doctor` and parse the memory line.
2. If `free RAM < 1 GB`, surface the blocker per AGENT_GUIDE.md "Escalate Blockers Explicitly":
   - What was attempted: HyperFrames render at locked `render_runtime`
   - What failed: insufficient memory (specific number)
   - Options: free memory and retry, OR switch to PIL+FFmpeg keyframe rendering (deterministic, OOM-safe), OR re-render on a higher-memory machine
   - Recommended option, with rationale
3. Wait for user approval. Log `render_runtime_selection` decision with `options_considered` and `rejected_because`.

**PIL+FFmpeg keyframe rendering is a legitimate fallback for HyperFrames.** It produces equivalent-quality alpha output (qtrle ARGB intermediates → ProRes 4444 final). What you give up: GSAP timeline syntax convenience and CSS-based scene authoring. What you gain: deterministic output, no memory risk, faster iteration.

## Output Both True-Alpha And Screen-Blend Fallback

Always produce two deliverables from the same composite source:

1. **Primary**: `*_alpha.mov` — ProRes 4444 (yuva444p12le), true alpha. Editor drops at 100% opacity, no blend mode.
2. **Fallback**: `*_screen.mp4` — H.264 (yuv420p), black background. Editor uses Premiere "Screen" blend mode.

Generate the .mp4 fallback by overlaying the alpha master onto a black canvas and re-encoding. ~10s extra render time, gives the editor format flexibility without you having to re-render anything if their NLE rejects ProRes.

## True-Alpha Text Crispness Requirements

When producing alpha overlays, all text MUST be rendered with a fully-opaque black stroke (PIL: `stroke_width=2, stroke_fill=(0,0,0,255)`). Soft anti-aliased edges blend with source pixels at composite time and read as graininess against bright source frames. See `skills/pipelines/hybrid/asset-director.md` "Crisp Text For Alpha-Channel Overlays" section for the recipe.

Plate alphas behind text must be ≥225 out of 255. Translucent plates (180-200) let source pixel variation shimmer through and degrade text readability frame-by-frame.
