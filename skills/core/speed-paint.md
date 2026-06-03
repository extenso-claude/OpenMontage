# Speed Paint — sketch-then-color reveal animation (Layer 2)

Turn a still illustration into a **speed-draw / speed-paint reveal**: a blank canvas →
the image **drawn on as a pencil sketch, one stroke at a time** → **colored in one whole
area at a time** (coloring-book style) → the finished still **holds** while a slow camera
push + ambient life bring it to life. This is a faithful, full-HD, license-clean, $0
**local equivalent of a1d.ai's "Speed Painter"** — rendered with HyperFrames/GSAP.

- **Tool:** `speed_paint` (capability `graphics`, provider `hyperframes`) — discover via the registry.
- **Engine:** `lib/speedpaint/` (`build_speedpaint`, `validate`, `render`).
- **Layer 3:** `hyperframes`, `hyperframes-cli`, `gsap-core`, `gsap-timeline`.

## When to use
- Channel/episode **openers** and **beat transitions** built from a single illustration.
- **Sleep documentaries** (`mode="sleep"`) — and normal videos (`mode="normal"`).
- Any moment where a static illustration should feel hand-made and alive.

## Two presets
| mode | canvas | ink | colors |
|---|---|---|---|
| `normal` | light paper `#F7F1E6` | graphite `#3a3631` | as-is |
| `sleep` | dark blackboard `#0E1320` | pale chalk `#aab6cc` | **TRUE-to-source** |

**Sleep mode only changes the canvas + ink.** Do NOT dim/desaturate/tint/grade the colors —
sleep-documentary source art is already night-designed, so the colors must reveal exactly
as drawn (grading them looked muddy/"weird"). If a source isn't dark enough, fix the *source*
(generate it in the channel night palette), not the animation.

## HARD RULES (do not violate)
1. **No camera movement or effects during sketch or color.** The frame is locked (scale 1,
   no glow, no motes) until coloring is 100% finished. The camera push + glow + dust motes
   begin **only on the held final still**. (Enforced in `scene.py`; never re-enable motion earlier.)
2. **Always end with a hold** so the viewer can appreciate the finished image. Set
   `hold_secs` per script beat (the rest of the timing varies too).
3. **Sketch is strictly sequential** — one stroke fully drawn before the next (single hand).
4. **Color fills one whole coloring-book cell at a time** (never multiple areas partially at once).

## How it works (auto)
`source illustration` → rasterize (SVG via `rsvg-convert`, or load raster) → **line-art**
(canny edges for clean flat vector; dark-ink extraction for inked / vectorized-raster art) →
**sketch strokes** (clean vector SVG uses its own paths for crisp strokes; raster / 8k-patch
art vectorizes the line-art into outline strokes) → **coloring-book order map**
(`segment.py`: line-art as barriers → enclosed cells → grouped into objects, background last)
→ HyperFrames scene → validate → render.

`sketch_source` and `lineart_method` default to `auto` and almost always pick correctly
(clean vector → svg/canny; raster or 8000-patch vectorized SVG → vectorize/dark).

## Key params (all on the tool's input_schema)
- **Timing (per beat):** `sketch_secs`, `paint_secs`, `hold_secs`.
- **Camera (hold only):** `focus_x`, `focus_y` (0..1 focal point), `zoom` (1.0 = none).
- **Life (hold only):** `particles` (dust motes), `life` (false = static hold).
- **Look:** `mode`, `stroke` (pencil width), `min_area` (coloring-book chunkiness — bigger = fewer/larger fill areas).
- **Output:** `operation` (render | scaffold | validate), `output_path`, `workspace_path`, `quality`, `fps`.

## Source guidance
- **SVG is preferred** (crispest strokes). Clean flat vector (Recraft `recraftv4_1_vector`) is ideal.
- A **vectorized-raster SVG** (thousands of micro-patches, e.g. an AI raster traced to SVG) works:
  it auto-routes to dark-ink line-art + vectorized strokes (the figure draws as a clean outline).
- A **raster** PNG/JPG works too (same raster path).

## Use it
Via the tool (preferred in pipelines):
```python
from tools.tool_registry import registry
registry.discover()
registry._tools["speed_paint"].execute({
    "source": "projects/<p>/assets/images/scene1.svg",
    "mode": "sleep", "hold_secs": 3, "focus_x": 0.56, "focus_y": 0.30,
    "output_path": "projects/<p>/assets/video/scene1_speedpaint.mp4",
})
```
Or the engine directly: `from lib.speedpaint import build_speedpaint, render`.

## Gotchas
- **Don't render inside a folder that a `hyperframes preview` server is watching** — HyperFrames
  allows one instance per project and will kill the preview. Preview and render in separate dirs,
  or stop the preview first.
- Preview live with `npx hyperframes preview --port N` (live Studio link, auto-reloads on regen).
- All final-shot motion uses **bounded** GSAP tweens (HyperFrames forbids `repeat:-1`); particle
  layout is **seeded** so parallel render workers stay in sync.
- The color reveal is driven by the **timeline clock** (not a per-tween callback) so every seeked
  frame — including the hold and worker-split ranges — is correct.

## Pipeline fit
Slot into `animation`, `animated-explainer`, `cinematic` openers, and `sleep-network-overlay`
beats. Produces a standalone MP4 clip (or a HyperFrames workspace) you can place on a timeline.
