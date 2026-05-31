# Animation Catalog (channel-themed)

## When to use

Use this catalog when producing branded animation clips for any channel that has a registered **theme**. A theme defines the channel's palette, style addendum, default scene prompts, and default copy. The 19 recipe types are channel-agnostic — same motion, same composition logic — only the look + content differ.

Reach for this catalog instead of authoring a one-off HyperFrames composition when:

- The scene matches one of the 19 recipe types (title card, document reveal, parallax window, tarot reveal, …)
- The channel has a theme (or you're willing to add one — 10-minute task)
- You want a 6-second clip that drops cleanly into a longer cut, with placement QA baked in

When NOT to use:
- The scene is creative and outside the 19 recipe types — use `hyperframes_compose` directly
- Final delivery: pass `quality="standard"` (~25s render). For iteration use `quality="draft"` (~14s render).

## Registered themes

| slug | display name | mood | use case |
|---|---|---|---|
| `midnight-magnates` | Midnight Magnates | noir documentary | dark histories of wealth |
| `grandpa-huxley` | Grandpa Huxley | sleep-documentary | warm earth-tone bedtime stories |

Theme files live at `tools/animation/catalog/themes/<slug>.py`. Each exposes a `THEME` dict with palette, style addendum, negative prompt, noir filter CSS, default scenes, and default copy.

## The 19 chosen recipe types

| # | Name | Recommended version | Recipe family |
|---|---|---|---|
| 1 | Living scene | recraft+hf | hero_overlay |
| 2 | Aged document | hyperframes | document |
| 3 | Mood loop | recraft+hf | hero_overlay |
| 8 | Moving train window | recraft+hf | parallax |
| 9 | Diorama shadow box | hyperframes+image | parallax |
| 17 | Tarot card draw | hyperframes | card_stage |
| 18 | Wanted poster slap | hyperframes | card_stage |
| 20 | Polaroid scatter | hyperframes | card_stage |
| 21 | Tier list ranking | hyperframes | card_stage |
| 31 | Recipe steps | hyperframes | step_seq |
| 44 | Pulse halo character | recraft+hf | hero_overlay |
| 46 | iMessage scroll | hyperframes | ui_mockup |
| 48 | Search query | hyperframes | ui_mockup |
| 53 | Newspaper unfold | hyperframes | card_stage |
| 55 | Old-film projector | hyperframes+image | vintage_media |
| 58 | Inventory slot reveal | hyperframes | card_stage |
| 67 | Equation derivation | hyperframes | card_stage |
| 107 | Photo album spread | hyperframes | document |
| 111 | Shadow puppet | hyperframes+image | surreal |

## How to use

```python
from tools.tool_registry import registry
registry.discover()
tool = registry.get("animation_catalog")

result = tool.execute({
    "format_id": 23,
    "out_path": "renders/title.mp4",
    "theme": "midnight-magnates",      # or "grandpa-huxley" or any other registered theme
    "duration": 6.0,
    "version": "recraft",              # or "hyperframes" (no AI image, $0)
    "quality": "draft",                # or "standard" for final
    "scene_overrides": {
        "title": "DARK MONEY",
        "subtitle": "the dark histories of wealth",
    },
})
```

If you don't pass `theme`, the default is `midnight-magnates`.

## Recraft model (V4.1, May 2026 lock)

The catalog's `recraft_gen.py` defaults to `model="recraftv4_1"` (raster). For
backgrounds, pass `model="recraftv4_1_vector"`. V4+ schema is auto-routed —
`style` / `substyle` / `negative_prompt` are silently stripped because V4+
doesn't accept them. Pricing is unchanged from V3 ($0.04 raster / $0.08
vector). Pro tier ($0.25+) is banned.

The MM theme's `style_addendum` is `"night colors, noir atmosphere, moonlit,
flat segmented color illustration"` — auto-prepended to every prompt. For
indoor / non-moonlit scenes, the scene prompt must override `"moonlit"` with
phrases like `"interior scene, no moonlight"`. See `recraft_v4_1_upgrade` +
`midnight_magnates_style_locked_v2` memories.

## Adding a new channel theme

To bring a new channel into the catalog:

1. Create `tools/animation/catalog/themes/<channel_slug>.py` exposing a `THEME` dict. Copy `midnight_magnates.py` as a starting point and edit:
   - `name`, `display_name`
   - `palette_rgb` (RGB list for Recraft `controls.colors`)
   - `palette_css` (CSS variable overrides — these override `assets/mm_tokens.css` `:root`)
   - `style_addendum` (prepended to every Recraft prompt — the visual style direction)
   - `negative_prompt` (kept out of every generation)
   - `noir_filter_css` (`filter:` applied to `.hero` / `.noir-grade`)
   - `default_scenes` (per format_id → Recraft scene prompt)
   - `default_copy` (per format_id → `{title, subtitle}`)
2. Add the slug to `KNOWN_THEMES` in `tools/animation/catalog/themes/__init__.py`.
3. Smoke-test with `tool.execute({format_id: 18, theme: "<slug>", version: "hyperframes", ...})` — this is free + 14s.
4. For full validation, run an R&D micro-sprint: pick 3-5 representative formats, render both versions, build contact sheets, eyeball for palette adherence.

## Bring-your-own Recraft image

```python
tool.execute({
    "format_id": 1,
    "out_path": "renders/saloon.mp4",
    "version": "recraft",
    "recraft_image_path": "projects/episode-7/assets/saloon.png",
})
```

Skips the $0.04 generation. Useful for batch episode builds where multiple cuts share one base image.

## Custom Recraft prompt

```python
tool.execute({
    "format_id": 1,
    "theme": "midnight-magnates",
    "out_path": "renders/saloon_dawn.mp4",
    "version": "recraft",
    "recraft_prompt": "A wild west saloon at dawn, gold light through the doors, wagon parked outside, mountains in the distance",
})
```

The theme's `style_addendum` is prepended automatically; the theme's palette is applied via `controls.colors`. Your prompt only needs to describe the scene content, not the style.

## QA — automatic, mandatory

Every render runs `lib/render_placement_qa.check_clip()` before returning success. If a placement bug is detected, the tool **fails** and returns the QA findings — silent shipping of broken clips is impossible.

The QA is variance-aware: it flags only TRUE black-band bugs (uniform near-black pixels across ≥92% of the top/bottom 80 rows AND stddev < 4). Legitimate noir backdrops with stars/grain/texture pass.

If a flag fires, the common root causes:

1. **Hero `<img>` CSS broke** — use `top:0; left:0; width:100%; height:100%; object-fit:cover`. Don't use `top:50%; transform:translate(-50%,-50%); width:106%; height:106%` — that pattern silently breaks under Chromium percent-height resolution.
2. **Darkening overlay opacity too high at top** — cap top-band overlay opacity at ≤0.20.
3. **Aspect mismatch** — Recraft images are 1820×1024; canvas is 1920×1080. With `object-fit:cover` this is invisible.

## Costs

| Operation | Cost |
|---|---|
| Recraft V4 raster (one image, palette-controlled) | **$0.04** |
| HyperFrames render (draft, single-worker, 8GB) | **~14s wallclock**, $0 |
| HyperFrames render (standard, single-worker, 8GB) | **~25s wallclock**, $0 |

A 19-clip catalog used end-to-end for one episode: ~$0.76 in Recraft + 8 minutes of local render time.

## Source / R&D provenance

This catalog is the WINNER subset from the 99-format R&D sprint at `experiments/animation-format-test/`. The sprint produced 210 draft clips, 22 family-level QA montages, and a comparison report.

See [COMPARISON_REPORT.md](../../experiments/animation-format-test/COMPARISON_REPORT.md) for the per-format verdicts that informed which 19 to promote.

## Reusable assets

Lifted from the sprint into `tools/animation/catalog/`:

- `assets/mm_motion.js` — 20 motion primitives (channel-agnostic; named "mm" historically but generic)
- `assets/mm_tokens.css` — base CSS tokens; themes override `:root` variables via `theme_palette.css` emitted at render time
- `composer.py` — HTML scaffolding + particle generator + decoratives
- `recipes.py` — 11 generic scene recipes + 11 procedural silhouettes
- `recraft_gen.py` — Recraft direct-API wrapper, accepts theme dict, 80-credit ceiling
- `themes/<slug>.py` — channel-specific palette + scenes + copy
- `format_dispatch.py` — per-format kwargs for all 99 sprint formats (the 19 chosen are gated via `CHOSEN_FORMATS` in the tool wrapper)

## Mandatory checklist before shipping

1. ✅ The clip rendered without error (`ToolResult.success == True`).
2. ✅ Placement QA returned 0 flagged (the tool enforces).
3. ✅ The clip was visually inspected (extract 6 frames + contact sheet via `lib/qa.py:contact_sheet`).
4. ✅ Title + subtitle text reads cleanly at 1080p (cap font sizes ≤ 80px for titles, ≤ 24px for subtitles in 6-second clips).
5. ✅ For Recraft versions: the AI image matches the brief (re-roll prompt if the AI took it too literally).
6. ✅ For the theme: confirm the palette overlays applied — view via `assets/theme_palette.css` in the workspace.

## Common pitfalls

- **Don't bypass the catalog for catalog use cases.** If your scene fits one of the 19 names, use the catalog — you get the channel's mood, palette, and QA for free.
- **Don't hardcode channel-specific copy** in the dispatcher kwargs — push it into the theme's `default_copy`. The tool prefers theme copy over dispatcher kwargs.
- **Don't ship a clip without running placement QA.** The tool runs it for you; if you assemble a HF composition outside the tool, run `lib/render_placement_qa.check_clip()` yourself before checkpointing.
