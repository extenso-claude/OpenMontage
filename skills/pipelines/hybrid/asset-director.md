# Asset Director - Hybrid Pipeline

## When To Use

This stage prepares the support kit around the anchor edit: subtitles, diagrams, generated inserts, narration, music, and reusable overlay systems.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/asset_manifest.schema.json` | Artifact validation |
| Prior artifacts | `state.artifacts["scene_plan"]["scene_plan"]`, `state.artifacts["script"]["script"]`, `state.artifacts["idea"]["brief"]` | Support needs and variant plan |
| Tools | `subtitle_gen`, `tts_selector`, `image_selector`, `video_selector`, `diagram_gen`, `code_snippet`, `music_gen`, `audio_enhance` — selectors auto-discover all available providers from the registry | Optional support asset production |
| Playbook | Active style playbook | Consistency rules |

## Process

### 1. Build Shared Support Assets First

Start with reusable systems:

- subtitle treatment,
- lower-third or label system,
- stat-card system,
- CTA container,
- diagram style.

### 1b. Sample Preview (Prevents Wasted Spend)

Before batch-generating support assets, produce one sample of each expensive generated type and show the user:

1. **TTS sample** (if narration is needed): Generate one section. Confirm voice and tone before batching.
2. **Image/video sample** (if generating inserts): Generate one representative visual. Confirm style fits the source footage before batching.

If rejected, adjust parameters and retry (max 3 iterations). Do not batch until approved.

### 2. Generate Only The Support Assets You Need

Support assets should fill identified needs from the script and scene plan, not speculative possibilities.

### 3. Preserve Anchor Truth

Keep the metadata clear about which assets are:

- source-derived,
- provided,
- recorded,
- generated.

### 4. Use Metadata For The Support Map

Recommended metadata keys:

- `shared_support_assets`
- `scene_asset_index`
- `source_vs_generated_map`
- `variant_assets`

### 5. Quality Gate

- support assets map to real narrative needs,
- reusable kits are present,
- source and generated assets are clearly separated,
- every referenced file exists.

### Mid-Production Fact Verification

If you encounter uncertainty during asset generation:
- Use `web_search` to verify visual accuracy of subjects (e.g. what does this building actually look like?)
- Use `web_search` to find reference images before generating illustrations
- Log verification in the decision log: `category="visual_accuracy_check"`

Visual accuracy matters. If the script mentions a specific place, person, or object,
verify what it actually looks like before generating images. Don't rely on
the AI model's training data — it may be wrong or outdated.

## Common Pitfalls

- Overbuilding support assets before the anchor cut is proven.
- Losing track of which assets are generated versus supplied.
- Creating inconsistent overlay systems across one project.


## When You Do Not Know How

If you encounter a generation technique, provider behavior, or prompting pattern you are unsure about:

1. **Search the web** for current best practices — models and APIs change frequently, and the agent's training data may be stale
2. **Check `.agents/skills/`** for existing Layer 3 knowledge (provider-specific prompting guides, API patterns)
3. **If neither helps**, write a project-scoped skill at `projects/<project-name>/skills/<name>.md` documenting what you learned
4. **Reference source URLs** in the skill so the knowledge is traceable
5. **Log it** in the decision log: `category: "capability_extension"`, `subject: "learned technique: <name>"`

This is especially important for:
- **Video generation prompting** — models respond to specific vocabularies that change with each version
- **Image model parameters** — optimal settings for FLUX, DALL-E, Imagen differ and evolve
- **Audio provider quirks** — voice cloning, music generation, and TTS each have model-specific best practices
- **Remotion component patterns** — new composition techniques emerge as the framework evolves

Do not rely on stale knowledge. When in doubt, search first.

## Crisp Text For Alpha-Channel Overlays (MANDATORY)

When the deliverable is a true-alpha overlay (ProRes 4444 .mov, transparent WebM, qtrle ARGB MOV) intended to composite over source footage in an editor:

### Text rendering — always stroke, never bare anti-alias
Anti-aliased text edges have alpha gradients (transparent → opaque over ~2px). When composited at the editor's timeline, those partial-alpha edge pixels mix with whatever is in the source frame underneath. Over bright source pixels (sky, lights, white walls), this reads as graininess or "fuzzy" text.

The fix: render every text glyph with a **fully-opaque black stroke** so the edge becomes a hard binary transition.

```python
# PIL recipe — stroke_width 2 is enough at 1080p
draw.text((x, y), text, font=font, fill=WHITE,
          stroke_width=2, stroke_fill=(0, 0, 0, 255))
```

Combined with a soft drop shadow (offset 2-3px), this produces broadcast-quality text that holds against any source backdrop.

### Plate alpha — go solid, not translucent
Backing plates behind text should use alpha ≥ 225 (out of 255). Lower alpha (180-200) lets ~25% of source bleed through, which produces shimmer when source pixels vary frame-to-frame. The savings in "subtle integration" are not worth the readability cost on text.

For lower-thirds, photo-card captions, and pull-quote backings, use alpha 235–240. Reserve fully-opaque (255) for very small body text where every pixel of source bleed is detrimental.

### Photo cards: scrap if photo is bad
If no public-domain or fair-use editorial photo exists for a named figure, **drop the photo card entirely** and use only a lower-third for identification. Never ship a placeholder ("[no public domain photo]") inside an empty frame — viewers see the literal placeholder text. Generic noir silhouettes can work but only when the silhouette pattern is intentional channel-wide; one-off silhouettes break the design system.

## Word-Anchored Cue Timing (MANDATORY when source has VO)

Never use uniform proportional rescale to align overlays. Always run faster-whisper on the source audio and lock named-entity cues to their actual word timestamps. Drift budget: ±0.4s per cue.

```bash
# faster-whisper base.en is fast enough for 10-min videos (<3 min on M2 CPU)
# Output: word-level timestamps that anchor every "Powell" / "Curveball" / "1990" cue.
```

Uniform rescale drifts hundreds of ms over 9-10 minutes — fine for ambient overlays, fatal for lower-thirds keyed to a specific name. Whisper anchoring eliminates the drift class of bugs entirely.
