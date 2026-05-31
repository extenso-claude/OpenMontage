# Asset Director - Character Animation Pipeline

## Goal

Produce `asset_manifest` with character parts, backgrounds, props, audio, music,
and preview artifacts.

## Visual Design Quality Gate (mandatory)

Before any image generation or character-card authoring, read
**`skills/meta/visual-design-quality.md`**. Especially relevant for this pipeline:

- **Rule: Never ship placeholder portraits.** Any CharacterCard MUST have a real
  PD photo sourced before render. Use `lib/asset_sourcing/portraits.py` (Wikipedia
  REST → Commons API → LoC search fallback chain) to source autonomously. Memory:
  `never_placeholder_portraits`.
- **Recraft V4.1 defaults** — `recraftv4_1` raster for character props/subjects
  (via `tools/graphics/recraft_image.py` or `tools/animation/catalog/recraft_gen.py`).
- **Motion direction QA** — character facing must match direction of travel; if
  the source asset faces wrong way, flip with `transform: scaleX(-1)`.

## Layer 3 Gate

Before authoring or generating animation assets, read the relevant Layer 3 skills:

- `character-rigging`
- `svg-character-animation`
- `pose-library-design`
- `canvas-procedural-animation` when p5/canvas effects are used
- `character-animation-qa` before review
- `gsap-core`, `gsap-timeline`, and `gsap-react` for GSAP/Remotion work
- `remotion` and `remotion-best-practices` for Remotion render work
- `hyperframes` and `hyperframes-cli` for HyperFrames work

Before image/TTS/music generation, read the tool's `agent_skills` from the
registry.

## Asset Organization

Write character assets under:

```text
projects/<project-name>/assets/characters/<character-id>/
```

Use subfolders:

```text
parts/
poses/
previews/
```

Generated backgrounds go under:

```text
projects/<project-name>/assets/backgrounds/
```

## Process

1. Produce or source only the parts required by `rig_plan`.
2. Keep each moving part separate.
3. Preserve transparent backgrounds for parts.
4. Record prompts, seeds, providers, and model names.
5. Build a small preview before full asset expansion.

## Quality Bar

All parts referenced by `rig_plan` must exist before compose. Missing parts are a
blocker unless the action timeline removes the action requiring them.
