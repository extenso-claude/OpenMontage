# Animated Subjects on a Map (OpenMontage method)

A reusable Layer-2 method for producing map-led sequences where sprites (armies,
fleets, caravans, traders, expedition parties, processions) are animated over a
geographically accurate basemap. Used by both Sleep Network channels:

| Channel | Style | Typical subjects |
|---|---|---|
| **Midnight Magnates** | `noir` (Carto dark + brass) | trade routes, merchant fleets, banking-house markers, Rothschild-style red shields |
| **Grandpa Huxley** | `warm` (parchment + teal) | expedition parties, exploration ships, colonial outposts, period figures |
| **Either, medieval briefs** | `illuminated` (vellum + lapis + gold) | knights, castles, monks, crusader fleets |
| **Technical / explainer** | `light_minimal` | abstract markers, data points, network nodes |

## When to use this method

Trigger conditions — pick this method whenever the brief calls for:

- A geographic backdrop where viewers need to read locations (countries / regions / cities)
- Multiple animated subjects placed at strategic / historical / canonical points
- A focal "action" subject — usually a moving formation (group of riders, fleet, caravan) — that the camera follows
- Period or themed styling (noir, parchment, illuminated, minimalist) — NOT photoreal satellite imagery
- A **multi-stop "world tour"** with camera zooming in/out of each location and crossfading to per-location imagery — see **Variant: Guided world-tour zoom (multi-stop)** below
- A **historical-event sequence** (battles, expeditions, founding events) where each stop deserves its OWN animated mini-scene with multiple sprites — see **Variant: Themed-battle scenes** below

If the brief just needs a still map or a static slide, use the simpler
`flat-motion-graphics` playbook with a single image. This method earns its
complexity when the *map is the scene*, not a backdrop.

### Picking a variant

| Brief shape | Variant |
|---|---|
| Campaign / movement / journey across a single map view | **Default formation variant** (knights, ships, caravan, procession) — sprites move, camera stays |
| World tour, "across-the-globe" sequence, hitting N specific places one at a time | **Guided world-tour zoom (multi-stop)** — sprites stay put, camera moves and crossfades to per-location posters |
| Historical events / battles / decisive moments, where each location needs ITS OWN mini-scene with multiple animated sprites | **Themed-battle scenes** — guided zoom + per-stop populated combat scene + per-stop climax + winner-marker stamp + closing stats card |

## Reference implementation

`projects/medieval-europe-opener-test/` is the worked example — 7 knights + 5
castles + 5 realm labels + 2 sea labels + dust particles + wisp clouds + camera
push-in + SFX-synced sword clashes, rendered through HyperFrames at 1080p.
Read its [index.html](projects/medieval-europe-opener-test/hyperframes/index.html)
and [scripts/mapkit_illuminated.py](projects/medieval-europe-opener-test/scripts/mapkit_illuminated.py)
when authoring a new variant.

## Workflow (six stages)

### 1. Pick the style + provider

Style chooses the channel identity; provider chooses the source tiles. Some
filters require label-free providers — see the table.

| Style | Recommended provider | Why |
|---|---|---|
| `noir` | `carto_dark` | tiles already in noir palette; filter lifts highlights for label legibility |
| `warm` | `carto_voyager` | warm earth tones; filter pushes parchment + teal |
| `illuminated` | `carto_light_nolabels` **(mandatory — no labels)** | filter recolors land/water by luma+chroma; admin lines and labels survive as ink smudges and ruin the look |
| `light_minimal` | `carto_light_nolabels` or `carto_light` | minimal desat; either works |

### 2. Compute geographic extent + tile zoom

Decide which `lat/lon` extent the story needs, then pick a zoom that fits a
1920×1080 frame. Rule of thumb at zoom 6:

- 1920 px horizontal ≈ 42° longitude
- 1080 px vertical at lat 45° ≈ 21° latitude (Mercator stretches at higher latitudes)

Centre the map so the focal subjects (formation centroid + critical castles)
are not hidden behind the camera vignette, which sits roughly on a 1300×800 inner
ellipse.

### 3. Generate basemap + positions.json

Drive the [`lib/mapkit_subjects`](../../lib/mapkit_subjects.py) library from a
small per-project script. This is the medieval-europe-opener pattern, generalized:

```python
import pathlib
from lib.mapkit_subjects import (
    MapConfig, SpriteAnchor, FormationMember,
    build_basemap, apply_polygon_highlight, compute_anchor_pixels,
    write_positions_json,
)

PROJECT = pathlib.Path(__file__).parent.parent

# 1. Configure the basemap
cfg = MapConfig(
    center_lat=46.0, center_lon=5.0, zoom=6,
    width=1920, height=1080,
    provider="carto_light_nolabels",      # MUST be nolabels for illuminated
    style="illuminated",                  # noir | warm | illuminated | light_minimal
    cache_dir=PROJECT / "scripts" / "_tile_cache",
)
img, info = build_basemap(cfg)

# 2. Optional: paint a regional highlight (verdigris over Western Europe, etc.)
WESTERN_EUROPE = [
    (60.5, -10.0), (60.5, 9.5), (52.0, 10.0), (49.5, 9.0), (47.5, 8.5),
    (45.0, 8.0), (43.0, 8.0), (41.0, 4.0), (39.0, 1.5), (35.5, -2.0),
    (35.5, -10.5), (44.0, -11.5), (50.0, -8.0), (55.0, -7.5), (58.5, -9.5),
]
img = apply_polygon_highlight(img, info, WESTERN_EUROPE,
                              color=(110, 142, 95),   # muted verdigris
                              blend=0.45, feather_px=18.0, land_only=True)
img.save(PROJECT / "assets" / "maps" / "basemap.png")

# 3. Anchor sprites by lat/lon, emit positions.json
castles = [
    SpriteAnchor(id="london", lat=51.51, lon=-0.13, metadata={"name": "Tower of London"}),
    SpriteAnchor(id="paris",  lat=48.86, lon= 2.35),
    SpriteAnchor(id="aachen", lat=50.78, lon= 6.08),
    SpriteAnchor(id="toledo", lat=39.86, lon=-4.02),
    SpriteAnchor(id="rome",   lat=41.90, lon=12.50),
]
compute_anchor_pixels(castles, info)

formation = [  # wedge: 1 lead + 2 + 4
    FormationMember("k_lead",  dx=0,    dy=-65, scale=1.10, rotation= 0.0),
    FormationMember("k_l1",    dx=-85,  dy=-25, scale=1.02, rotation=-2.0),
    FormationMember("k_r1",    dx= 85,  dy=-25, scale=1.04, rotation= 2.0),
    FormationMember("k_l2",    dx=-170, dy= 25, scale=0.96, rotation=-4.0),
    FormationMember("k_l3",    dx=-60,  dy= 30, scale=1.00, rotation=-1.0),
    FormationMember("k_r3",    dx= 60,  dy= 30, scale=1.00, rotation= 1.0),
    FormationMember("k_r2",    dx= 170, dy= 25, scale=0.95, rotation= 4.0),
]

write_positions_json(
    PROJECT / "artifacts" / "positions.json",
    info,
    anchors=castles,
    subject_centroid_latlon=(47.3, 3.5),  # Auvergne — central France
    subject_formation=formation,
    extra={"realm_labels": [...], "sea_labels": [...]},  # see below
)
```

### 4. Author the HyperFrames composition

HyperFrames is the **only** runtime that fits this method — Remotion doesn't
have GSAP-native organic motion (gallop bob, lance wiggle, dust particles,
elastic burst). Don't try to silently swap to Remotion; if the brief locks
`render_runtime="hyperframes"` and the runtime isn't installed, surface a blocker
per `AGENT_GUIDE.md` → "Escalate Blockers Explicitly".

Read [skills/core/hyperframes.md](hyperframes.md) for the authoring contract
before writing the HTML. The skeleton:

```html
<div id="comp" data-composition-id="<project>" data-width="1920" data-height="1080"
     data-start="0" data-duration="<seconds>">

  <div id="stage" class="stage clip" data-start="0" data-duration="<seconds>" data-track-index="0">
    <img class="basemap" src="basemap.png" />
    <div class="paper-grain"></div>

    <!-- wisp clouds (parallax background) -->
    <div class="wisp wisp-back" ...></div>

    <!-- realm + sea labels (geographic, inside .stage so they scale with the camera) -->
    <div class="map-label realm-label" id="lbl-<id>" style="left:Xpx; top:Ypx;">...</div>
    <div class="map-label sea-label"   id="lbl-<id>" style="left:Xpx; top:Ypx;">...</div>

    <!-- anchored sprites (castles, ports, markers) -->
    <div class="sprite-anchor" style="left:<px>px; top:<py>px;">
      <div class="castle-burst" id="burst-<id>"></div>
      <img class="castle" id="castle-<id>" src="castle.svg" />
    </div>

    <!-- dust particles container (populated deterministically in JS) -->
    <div id="dust-field"></div>

    <!-- subject formation sprites -->
    <div class="sprite-anchor" style="left:<px>px; top:<py>px;">
      <img class="knight" id="k-lead" src="knight.svg" />
    </div>

    <!-- ornamental frame (style-dependent) -->
    <div class="gold-frame">...</div>
    <div class="vignette"></div>
  </div>

  <audio id="sfx" class="clip" data-start="0" data-duration="<seconds>"
         data-track-index="10" src="sfx_mix.wav" data-volume="1"></audio>
</div>
```

GSAP timeline — register on `window.__timelines["<project>"]`, `paused: true`,
all timelines synchronous, no `repeat:-1`, no `Math.random()` (use mulberry32):

```js
const tl = gsap.timeline({ paused: true });
window.__timelines["<project>"] = tl;
const DUR = 8.0;

// 1. Camera push-in (1.000 → 1.045 over the full duration)
tl.fromTo(".stage", { scale: 1.000 }, { scale: 1.045, duration: DUR, ease: "sine.inOut" }, 0);

// 2. Basemap + frame fade-in
tl.fromTo(".basemap", { opacity: 0 }, { opacity: 1, duration: 0.6, ease: "power2.out" }, 0);
tl.fromTo(".gold-frame", { opacity: 0 }, { opacity: 1, duration: 0.5 }, 0.3);

// 2a. Labels paint in (realms first, seas slightly later)
tl.fromTo(".realm-label", { opacity: 0, scale: 0.92 },
  { opacity: 0.92, scale: 1.0, duration: 0.9, ease: "power2.out", stagger: 0.08 }, 0.55);
tl.fromTo(".sea-label", { opacity: 0 },
  { opacity: 0.80, duration: 0.7, stagger: 0.10 }, 1.10);

// 3. Anchored sprites — staggered elastic burst-in with gold-leaf flash
const anchors = [
  { id: "london",  t: 0.70 }, { id: "paris",  t: 0.95 }, { id: "aachen", t: 1.20 },
  { id: "toledo",  t: 1.45 }, { id: "rome",   t: 1.70 },
];
anchors.forEach(a => {
  tl.set(`#castle-${a.id}`, { scale: 0, opacity: 0 }, 0);
  tl.fromTo(`#burst-${a.id}`,
    { scale: 0.4, opacity: 0 },
    { scale: 1.4, opacity: 0.9, duration: 0.18, ease: "power2.out" }, a.t);
  tl.to(`#burst-${a.id}`, { scale: 1.8, opacity: 0, duration: 0.35, ease: "power2.in" }, a.t + 0.18);
  tl.fromTo(`#castle-${a.id}`,
    { scale: 0, opacity: 0 },
    { scale: 1.15, opacity: 1, duration: 0.45, ease: "back.out(2.2)" }, a.t + 0.05);
  tl.to(`#castle-${a.id}`, { scale: 1.0, duration: 0.20, ease: "power2.out" }, a.t + 0.50);
});

// 4. Anchor pulse + bounce loop (finite repeat, NOT repeat:-1)
const PULSE_CYCLE = 2.4;
const pulseStart = 2.0;
const pulseRepeats = Math.max(0, Math.floor((DUR - pulseStart) / PULSE_CYCLE) - 1);
anchors.forEach((a, i) => {
  tl.to(`#castle-${a.id}`, {
    scale: 1.025, y: -3, duration: PULSE_CYCLE / 2,
    ease: "sine.inOut", yoyo: true, repeat: pulseRepeats * 2 + 1,
  }, pulseStart + i * 0.25);
});

// 5. Formation: gallop bob + lance wiggle + slow eastward drift
const subjectIds = ["k-lead", "k-l1", "k-r1", "k-l2", "k-l3", "k-r3", "k-r2"];
const BOB_CYCLE = 0.20, WIG_CYCLE = 0.33;
const bobRepeats = Math.max(0, Math.floor((DUR - 1.8) / BOB_CYCLE) - 1);
const wigRepeats = Math.max(0, Math.floor((DUR - 1.8) / WIG_CYCLE) - 1);
subjectIds.forEach((id, i) => {
  tl.fromTo(`#${id}`, { opacity: 0, y: 12 },
    { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }, 1.5 + i * 0.07);
  tl.to(`#${id}`, { y: -3, duration: BOB_CYCLE / 2, ease: "sine.inOut",
    yoyo: true, repeat: bobRepeats * 2 + 1 }, 1.8 + (i * 0.041) % BOB_CYCLE);
  tl.fromTo(`#${id}`, { rotation: -2 }, { rotation: 2, duration: WIG_CYCLE / 2,
    ease: "sine.inOut", yoyo: true, repeat: wigRepeats * 2 + 1 }, 1.8 + (i * 0.073) % WIG_CYCLE);
  tl.to(`#${id}`, { x: "+=14", duration: DUR - 1.8, ease: "sine.inOut" }, 1.8);
});

// 6. Wisp clouds — slow parallax drift
tl.fromTo("#wisp-b1", { x: 0 }, { x:  200, duration: DUR, ease: "sine.inOut" }, 0);
tl.fromTo("#wisp-f1", { x: 0 }, { x: -340, duration: DUR, ease: "sine.inOut" }, 0);
tl.fromTo(".wisp", { opacity: 0 }, { opacity: 1, duration: 1.0 }, 0);

// 7. Dust particles — built deterministically with mulberry32 seed in DOM, then animated
// (see medieval-europe-opener-test/hyperframes/index.html for the full pattern)
```

### 5. Mix SFX with precise timestamps + fades

Royalty-free pulls from **Mixkit** (verified) or **Pixabay SFX**. Recipe ([build_sfx_mix.sh](../../projects/medieval-europe-opener-test/scripts/build_sfx_mix.sh)
is the canonical example):

```bash
# 4 layered tracks: wind bed (cont.), gallop bed (cont.), war-cry bed (mid),
# 3 sword impacts at exact timestamps. Each layer fades in + out separately.

ffmpeg -y -i wind.mp3 -i hooves.mp3 -i cries.mp3 -i clash.mp3 \
  -filter_complex "
    [3:a]aformat=channel_layouts=stereo,asplit=3[sa][sb][sc];

    [0:a]aformat=channel_layouts=stereo,atrim=0:8,
         afade=t=in:st=0:d=1.0, afade=t=out:st=7.4:d=0.6,
         volume=0.14[wind];

    [1:a]aformat=channel_layouts=stereo,atrim=0:7.3,asetpts=PTS-STARTPTS,
         afade=t=in:st=0:d=0.5, afade=t=out:st=6.7:d=0.6,
         adelay=700|700, volume=0.34[hooves];

    [2:a]aformat=channel_layouts=stereo,atrim=0:4.4,asetpts=PTS-STARTPTS,
         afade=t=in:st=0:d=1.5, afade=t=out:st=3.8:d=0.6,
         adelay=2000|2000, volume=0.22[cries];

    [sa]adelay=3200|3200, pan=stereo|c0=1.0*c0+0.4*c1|c1=0.4*c0+1.0*c1, volume=0.55[s1];
    [sb]adelay=5000|5000, pan=stereo|c0=0.4*c0+1.0*c1|c1=1.0*c0+0.4*c1, volume=0.55[s2];
    [sc]adelay=6800|6800, volume=0.60[s3];

    [wind][hooves][cries][s1][s2][s3]
        amix=inputs=6:duration=first:normalize=0,
        alimiter=limit=0.97[out]
  " -map "[out]" -t 8 -ac 2 -ar 48000 -c:a pcm_s16le sfx_mix.wav
```

Mix-bus levels (verified, tuned to not crush the master limiter):

| Track | Volume | Fade in | Fade out |
|---|---|---|---|
| Wind ambient bed | 0.14 (~-17dB) | 0–1.0s | 7.4–8.0s |
| Hooves / motion bed | 0.34 (~-9dB) | 0.7–1.2s | 7.4–8.0s |
| War-cry / atmosphere bed | 0.22 (~-13dB) | 2.0–3.5s | 7.4–8.0s |
| Impact hits | 0.55–0.60 (~-5dB) | none | natural decay |

Impacts get stereo panning (L, R, C) so they feel placed. Verify timing post-mix
by extracting peak energy windows from the decoded WAV (see the medieval reference's
QA pass — `python3` with `wave` + `struct` is enough).

### 6. Render + QA (mandatory)

Per [MEMORY.md](../../.../memory/MEMORY.md):

- **`render_self_qa_required`** — Always extract frames + visually inspect before presenting.
- **`hyperframes_render_workers_ram`** — On 8GB-RAM machines, `-w 1 -q draft` for QA passes; `-w 1 -q standard` for finals. The `-w auto` default OOM-kills silently with exit 144.

QA loop:

```bash
# 1. Lint + validate (browser-based runtime check)
npx hyperframes lint
npx hyperframes validate --no-contrast

# 2. Draft render for QA
npx hyperframes render --output ../renders/draft_v1.mp4 \
  --quality draft --fps 24 --workers 1

# 3. Extract frames at 15 FPS for visual inspection
ffmpeg -i ../renders/draft_v1.mp4 -vf "fps=15" ../qa/draft_v1_frames/f_%03d.jpg

# 4. Open frames in order, scan for:
#    - sprite collisions (knight covering Paris, label clipping castle, etc.)
#    - invisible elements (dust too small, sea labels too dark on lapis, etc.)
#    - asymmetric distribution (one side of formation overcrowded)
#    - off-frame elements (sprites near gold frame edge)
#    - colour clashes (warm sprite on warm map = invisible)

# 5. Fix + re-render. Iterate until clean.

# 6. Final render at standard quality
npx hyperframes render --output ../renders/final.mp4 \
  --quality standard --fps 24 --workers 1

# 7. Audio sync check — decode + scan for impact peaks
ffmpeg -i ../renders/final.mp4 -map 0:a -c:a pcm_s16le ../qa/final_audio.wav
# Then use Python (wave + struct) to find peaks > 18000 abs and verify they
# land within ±100ms of the SFX recipe's targets.
```

## QA collision rules

Hard rules (verified during medieval-europe-opener-test development):

1. **Subject formation must not cover any anchor sprite.** Compute the bounding
   box of every anchored sprite, then verify the centroid + formation extent
   doesn't overlap any anchor box. If it does, move the centroid; never trust
   that "they'll just sit on top of each other."
2. **Wedge formations need ≥80 px horizontal spread per knight pair.** Tighter
   than that and the sprites blob together into an unreadable cluster.
3. **Labels can't intersect anchor sprites.** Text width with letter-spacing
   is wider than naïve `len * font_size`; budget at least 1.3× and check the
   right-edge of each label vs the left-edge of any anchor in the same y-band.
4. **Dark labels go on light land; light labels go on dark water.** Don't try
   to make one label colour work for both — the contrast difference between
   verdigris (sage green) and lapis (deep blue) is too narrow.
5. **Polygon highlights must feather (≥15 px Gaussian blur).** Sharp polygon
   cuts where the boundary crosses land read as "computer graphics," not
   "painted wash."
6. **Verdigris / shading colours need ≥40% saturation drop from their pure form.**
   The sprites (red/gold knights, castles) need to stand against the map; a
   too-saturated highlight competes for attention. Tuned blend: `0.45` peak,
   not `0.55`.

## Per-channel guidance

### Midnight Magnates

- `style="noir"`, provider `carto_dark` (label-bearing is fine — noir filter preserves them)
- Sprite palette: brass `#c9a84c`, classified red `#b41e1e` for accents
- Labels: brass-gold serif (Georgia bold), tracked, with black drop shadow
- SFX: low brass drone bed, distant rain, slow shutter clicks at impacts (per `styles/midnight-magnates.yaml`)
- **Music volume ≤ 0.06** (hard rule from playbook)
- No bouncy easing — use `power2.out` / `sine.inOut` only, never `back.out` for anything large

### Grandpa Huxley

- `style="warm"`, provider `carto_voyager`
- Sprite palette: warm leather browns, period gold, parchment cream
- Labels: cream Georgia bold, italic for sea names, drop shadow at 50%
- SFX: warm wind, distant fiddle, paper rustle, grandfather-clock tick at intervals
- Easing: more generous — `back.out(1.8)` allowed for entrance moments

### Illuminated (medieval briefs, either channel)

- `style="illuminated"`, provider `carto_light_nolabels` **mandatory**
- Sprite palette: vermillion + lapis + gold-leaf (matches the basemap palette)
- Labels: Cinzel capitals (Trajan-style), ink brown `#3a2410`, large letter-spacing
- Decorative gold frame + corner rosettes
- SFX: galloping cavalry, sword clashes, war cries, parchment-grain wind

## Variations & extensions

The medieval-europe-opener exercises one formation type (wedge). Other variants
this method supports out of the box:

- **Naval fleet** — formation members are ships, gallop-bob becomes "wake bob"
  (`y: ±2px, 0.4s cycle`), no lance wiggle, add a wake trail particle behind
  each ship
- **Caravan** — formation in single-file line, `dx` increments of 50–60 px,
  no wiggle, dust particles in 360° around each member
- **Bishop's procession** — formation tightly clustered, slow forward drift,
  no bob, candle-glow particles
- **Single-character journey** — N=1 subject, replace bob with footstep
  scuff, animate a dotted-line path drawing behind the figure

For any of these, the basemap + anchor + camera + SFX patterns are identical
— only the formation specification and the per-sprite micro-motion changes.

## Variant: Guided world-tour zoom (multi-stop)

Same basemap + anchor pipeline, but the camera *moves* — sequentially zooming
into each anchor and crossfading to a "poster card" image of that location,
then panning a route through all stops, and ending on a synchronised bounce.
Use this when the brief is **"world tour" / "across-the-world journey"**
rather than **"a campaign moves through this landscape"**.

Reference impl: `projects/world-tour-zoom-test/` — 28s @ 1080p, 5 stops
(Japan / Egypt / Iceland / Brazil / Australia), brass-framed flag medallions
+ hand-authored noir poster cards. Cost: $0 (no AI generation).

### Camera math (transform-origin: 0 0)

The `.stage` uses `transform: translate3d(tx, ty, 0) scale(s)` with
`transform-origin: 0 0`. To center pin `(px, py)` on the 1920×1080 viewport
at scale `s`:

```
tx = 960 - px * s
ty = 540 - py * s
```

Helper:

```js
const VW = 1920, VH = 1080, CX = VW/2, CY = VH/2;
function camWorld() { return { x: 0, y: 0, scale: 1 }; }
function camFocus(pin, scale) {
  return { x: CX - pin.px * scale, y: CY - pin.py * scale, scale };
}
```

### Four-phase timeline

Default 28s @ 30fps for a 5-stop tour. Adjust `STOP_DUR` only — the rest
falls out of it. `STOP_DUR ≥ 3.5s` is the readable minimum.

| Phase | Window | Action |
|---|---|---|
| 1 — Intro | 0–3s | World map fades in; N pins burst-in with brass flares (`back.out(2.2)`, stagger 0.18s); optional title plate fades in 0.4s and out 2.4s |
| 2 — Sequential tour | 3 → 3 + N·3.5 | Per stop: zoom in (0.8s) → poster crossfade in (0.4s @ t0+0.65) → hold (~0.9s) → poster fade out (0.4s @ t0+2.10) → zoom out (0.8s @ t0+2.50) → buffer (0.2s) |
| 3 — Continuous pan | Phase 2 end → +5s | Partial zoom into first stop at scale ≈2.4×, then chained `tl.to(STAGE, ...)` with `"sine.inOut"` through the route, final leg `"power2.inOut"` |
| 4 — Pull back + bounce | last 2.5–3s | Tween back to `camWorld()` (1.0s), then synced `y:-8` `sine.inOut yoyo` on every icon (3 cycles ≈ 1.5s) with brass-burst pulse |

### Layout / DOM contract

```html
<div id="comp" data-composition-id="..." data-width="1920" data-height="1080"
     data-start="0" data-duration="28">

  <!-- Camera. transform-origin: 0 0. -->
  <div id="stage" class="stage clip" data-start="0" data-duration="28" data-track-index="0">
    <img class="basemap" src="basemap.png" />
    <!-- N sprite-anchors with .burst + .icon + .pin-label, lat/lon-derived px positions -->
    <div class="vignette"></div>
  </div>

  <!-- Posters OUTSIDE .stage so they don't inherit camera zoom. -->
  <div class="posters-layer clip" data-start="0" data-duration="28" data-track-index="5">
    <div class="poster" id="poster-japan"> <img src="posters/japan.svg"/> </div>
    <!-- ... one .poster per stop, opacity:0 initially, animated by GSAP -->
  </div>

  <!-- Fixed outer brass frame + title plate (don't scale with camera) -->
  <div class="outer-frame"></div>
  <div class="titleplate" id="titleplate">A WORLD TOUR</div>
</div>
```

Key: **posters live OUTSIDE `.stage`** as a sibling `.clip` wrapper. If they
were inside `.stage` they'd be scaled by the camera (4× during focus phases =
4× larger posters spilling off-frame). Outside the stage they cover the
viewport at native size regardless of zoom.

### Asset layer

- **Icons** — small (80×80) brass-framed flag / symbol medallions per stop.
  Hand-authored SVGs — `feedback_free_over_ai` says no AI here.
- **Poster cards** — 1280×720 noir landscape illustrations. Hand-authored
  SVGs work great ($0). If you'd rather have higher-fidelity scene art,
  route to `recraftv4_1` raster ($0.04 each) — but ask the user first per
  the `feedback_recraft_no_palette_lock` rule and don't pre-lock palette.

### OOB-pixel patch (mandatory when the world doesn't fill the viewport)

`mapkit_subjects.render_basemap()` fills any tile-range overflow with
`(200, 220, 230, 255)` light gray. The noir filter's highlight-lift then
pushes those pixels to pure white, producing a bright vertical band where
the world ends. At zoom 3 with width 1920 there is always ~110 px of OOB
on one side; at zoom 2 it's roughly half the frame.

Patch after `build_basemap()` and before saving:

```python
import numpy as np
from PIL import Image as _Image

arr = np.array(img.convert("RGB"))
near_white = (arr[..., 0] > 235) & (arr[..., 1] > 235) & (arr[..., 2] > 235)
arr[near_white] = [12, 18, 30]   # noir dark navy
img = _Image.fromarray(arr).convert("RGBA")
```

(This should eventually migrate into `lib/mapkit_subjects.style_noir`
itself; documenting at the variant level until that happens.)

### Variant-specific QA additions

On top of the standard collision rules in this skill:

1. **Geographic pin accuracy** — every pin position MUST come from
   `compute_anchor_pixels()`; never eyeballed CSS percentages
   (`geographic_pin_accuracy_required` memory).
2. **OOB-pixel check** — sample per-column luminance on the rendered
   basemap; any column with mean luma > 235 is a bug.
3. **Poster-layer position** — confirm posters are siblings of `.stage`,
   not children, by inspecting the DOM.
4. **Pan-route smoothness** — at draft FPS=2 extraction, the camera should
   not jump between phase-3 legs. Look for visible "snaps" at leg
   transitions — usually fixed by adding a 0.1s overlap into the next leg.
5. **Bounce magnitude** — `y:-8` at scale 1 is the right amount. `y:-16`
   reads jittery; `y:-4` is imperceptible.
6. **No `filter: brightness()` on the burst-pulse during bounce** — use
   opacity/scale on a separate `.burst` element (the
   `gsap_filter_brightness_gotcha` memory).

## Variant: Themed-battle scenes

Extends the guided-zoom mechanism into a documentary-style sequence: each
location gets its own *populated* mini-scene with multiple animated combat
sprites, a unique climax, and a persistent winner marker. Use when the brief
is a **historical-event sequence** — battles, decisive moments, expedition
landings, founding events — where each stop deserves more than a single
poster card.

Reference impl: `projects/europe-ww2-battles-test/` — 62s @ 1080p, 5 WWII
battles (Britain, Stalingrad, Monte Cassino, D-Day, Berlin) on a wartime
parchment Europe map with period country labels (`GERMAN REICH` / `USSR` /
`POLAND` etc., not modern Carto labels). Color coding: navy Allied, red
Soviet, iron-grey Axis. Cost: $0 (hand-authored SVG sprites + Freesound
royalty-free SFX).

### What this variant adds on top of the guided-zoom mechanism

1. **Custom basemap palette** — beyond the 4 default style filters
   (`noir` / `warm` / `illuminated` / `light_minimal`). Post-process the
   basemap in the per-project build script to re-tone land + water by
   luma+chroma masks, add a soft radial vignette. See
   `projects/europe-ww2-battles-test/scripts/build_basemap.py
   ::_post_process_basemap` for the worked wartime-parchment example.
2. **Period-overlay labels** — historical country names positioned by
   lat/lon (same `compute_anchor_pixels` math as battle pins). Always
   use a `*_nolabels` tile provider so the modern labels baked into
   the tile imagery don't conflict.
3. **Reusable sprite library per theme** — top-down silhouettes of every
   unit type that appears in the scenes. For WWII: plane (Spitfire / Bf 109),
   tank (T-34 / Panzer), soldier (red / grey / khaki, per faction),
   landing craft, building markers (monastery / Reichstag).
4. **Scripted multi-sprite combat** per stop — see "Combat-event scheduler"
   below.
5. **Per-stop unique climax animation dispatched by kind** — flag rise,
   faction-stamp, advance arrow, building capture.
6. **Winner markers** that persist after each stop resolves.
7. **Closing stats card** — victor + duration + outcome metadata.
8. **Layered SFX bed** — ambient war drone + per-stop accent + victory
   horn at each climax + outro fanfare. Mixed with ffmpeg `amix`.

### Combat-event scheduler

Each stop's scene config declares a sprite layout (file + class + dx/dy
offset from anchor + initial rotation + side + deploy position). The
scheduler then plays a fixed sequence of beats:

```
sceneBaseT = t0 + ZOOM_IN_DUR
  + 0.0  to + 0.5   sprite opacity fade-in (stagger 0.04s)
  + 0.5  to + 1.7   sprites translate from start position to deploy position
  + 1.7  to + COMBAT_DUR
        - per-sprite idle bob (sine.inOut yoyo, ~0.6-1.2s cycle)
          amplitude: plane 4px, tank 1.5px, soldier 2px
        - 6-10 firing events distributed across the window:
            * muzzle flash at midpoint between shooter & target
              (0.1s fade in, 0.25s fade out, scale 0.4 → 1.4 → 0.8)
            * smoke puff at target (0.6s grow, 0.9s fade-up)
            * 1.2px recoil on shooter
          Use a seeded mulberry32 for deterministic flash positions.
        - 2 axis casualties fade to opacity 0.35 in second half
          plus a persistent big smoke puff at their position
  + COMBAT_DUR  to + COMBAT_DUR + CLIMAX_DUR
        - climax animation dispatched by `kind` string in scene config
```

### Climax dispatcher

A switch on a single `climax` string per stop — keep all the climax
recipes in one place so they're easy to scan and reuse:

| `kind` | What it does |
|---|---|
| `flag-rise` (red / Allied / etc.) | flag sprite fades + rises + yoyos a small rotation |
| `faction-stamp` | giant faction icon (RAF roundel, hammer-sickle, eagle) stamps in with `back.out(2.4)` overshoot, then fades |
| `advance-arrow` | bold directional SVG arrow appears + translates inland (per arrow direction) |
| `building-capture` | flag sprite rises on a building marker (Reichstag / monastery / capitol) |
| `pulse-explosion` | central `explosion.svg` scales 0 → 1.4 + fades over 0.8s |

Add new kinds by extending the `addClimax(tl, battleId, kind, t0, dur)`
function. Each kind appends DOM + tweens to the timeline at `t0` and stays
fully contained.

### Winner-marker pattern

Each anchor has a hidden `winner-marker` sprite (flag of the winning side)
positioned just above and to the right of the anchor's icon. The marker
fades in during the stop's zoom-out and persists for the rest of the run.

**Crucial:** during ANY focused-battle phase, fade out ALL battle icons +
labels + winner markers (past AND current), not just the current battle's.
At scale 3.5×, geographically close pins (e.g. Britain ↔ D-Day, ~1° apart
at zoom 5) WILL occlude each other otherwise. Bring them all back during
zoom-out via:

```js
tl.to(".battle-icon, .battle-pin-label, .winner-marker",
  { opacity: 0, duration: 0.35 }, t0 + ZOOM_IN_DUR - 0.3);
// ...later, during zoom-out...
tl.to(".battle-icon",       { opacity: 0.85, duration: 0.5 }, zoomOutT + 0.6);
tl.to(".battle-pin-label",  { opacity: 0.92, duration: 0.4 }, zoomOutT + 0.6);
// Past winners back to full opacity:
ORDER.slice(0, idx).forEach(pid => {
  tl.to("#winner-" + pid, { opacity: 1, duration: 0.5 }, zoomOutT + 0.6);
});
// New winner stamps in fresh:
tl.fromTo("#winner-" + battleId,
  { opacity: 0, scale: 0.4, y: 10 },
  { opacity: 1, scale: 1.0, y: 0, duration: 0.6, ease: "back.out(2.4)" },
  zoomOutT + 0.8);
```

### Closing stats card

Full-frame `outro-card` div outside `.stage`, dimmed background over the
last-seen world view, with:

- Small Cinzel "crown" line (e.g. `— VICTOR OF THE WAR —`)
- Large winner name (Cinzel 120px)
- Year (Cinzel 56px brass)
- Stats block in Special Elite typewriter font — `KEY · VALUE` rows with
  the value in brass

Fade in over 0.8s after the final zoom-out. Hold for ~5s. Optional gentle
pulse on the winner text via `sine.inOut yoyo`.

### SFX layering

Per the `sound_design_rules_locked` memory, the per-cue stacking is:

| Track | Volume | Notes |
|---|---|---|
| Ambient war bed | 0.18 (~-15dB) | continuous, fade in 2s, fade out 4s |
| Per-stop accent | 0.40 - 0.46 (~-8dB) | aligned to combat window, fade in/out 0.4s/1.0s |
| Victory horn at climax | 0.50 (~-6dB) | trimmed to 3s, panned center, reused per stop |
| Outro fanfare | 0.55 (~-5dB) | starts 2s before card fade-in |

Source SFX from **Freesound** via the search script in the reference impl
(`scripts/fetch_sfx.py`) — CC0 / CC-BY catalog, free for non-commercial.
Mix with `ffmpeg amix=inputs=N:duration=first` + `alimiter=limit=0.95`. Pad
the ambient bed with `apad` if shorter than the comp duration.

### Sensitive-period iconography

For WWII (and WW1) briefs use **historically-accurate non-provocative
iconography** for the Axis units:

- Axis ground/air = **Balkenkreuz** (the Wehrmacht military cross on tanks
  and planes) and **iron grey** — NOT the swastika
- Allied = RAF roundel, white Allied star, US/UK national flags
- Soviet = red star, hammer-and-sickle, Soviet flag

The military cross is sufficient for visual identification and avoids
YouTube AI-slop / inauthentic-content enforcement signals
(`youtube_ai_slop_signals` memory). Same logic for any sensitive period —
choose the most-iconic-but-least-provocative emblem available.

### Variant-specific QA additions

On top of the standard checks in this skill:

1. **Sprite scale awareness** — sprites inside `.stage` scale with the
   camera. A 50px-native sprite renders at 175px on screen at scale 3.5×.
   Author small (25-60px native) for tactical-map clarity.
2. **Sprites must feel alive** — every sprite gets idle bob; verify by
   scrubbing frame extraction — no sprite should sit perfectly still for
   more than ~0.5s.
3. **Pin-occlusion check** — at the focused scale, identify which other
   pins fall inside the viewport (compute viewport box, list pins inside).
   Confirm they're all faded out, not just the current battle's pin.
4. **Custom basemap OOB check** — same as the world-tour variant: any
   near-white column from tile overflow is a bug, patch with the
   theme-appropriate dark fill (see `mapkit_oob_pixel_patch` memory).
5. **Sensitive-iconography sweep** — open every sprite SVG and confirm no
   provocative imagery (swastikas, specific ethnic caricatures, etc.).
6. **Audio sync** — extract the rendered audio with
   `ffmpeg -map 0:a -c:a pcm_s16le ...wav`, find peak energy windows,
   confirm victory-horn peaks land within ±100ms of each scripted climax
   timestamp.

## What this method does NOT cover

- Continent → city → street zoom levels with *different basemaps* per
  level. This variant zooms into a single basemap at higher CSS scale; it
  doesn't swap tiles at higher Mercator zoom levels. For true progressive
  zoom across basemaps, use the `documentary-montage` pipeline — it does
  scene transitions across multiple HF compositions.
- Real-time interactive maps. This is a one-shot rendered video.
- Stat-card overlays on top of the map. Add a Remotion overlay pass
  post-render if a brief needs that.

## File locations

| Thing | Location |
|---|---|
| Python library | [lib/mapkit_subjects.py](../../lib/mapkit_subjects.py) |
| This skill | `skills/core/animated-subjects-on-map.md` |
| HyperFrames authoring contract | [skills/core/hyperframes.md](hyperframes.md) |
| Reference project (formation variant) | `projects/medieval-europe-opener-test/` (gitignored — regenerate from this skill) |
| Reference project (guided world-tour zoom variant) | `projects/world-tour-zoom-test/` (gitignored — regenerate from this skill) |
| Reference project (themed-battle scenes variant) | `projects/europe-ww2-battles-test/` (gitignored — regenerate from this skill) |
| Channel styles | `styles/midnight-magnates.yaml`, `styles/grandpa-huxley.yaml` |
| Tile cache (per project) | `projects/<name>/scripts/_tile_cache/` (gitignored) |
