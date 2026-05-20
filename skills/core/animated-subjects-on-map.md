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

If the brief just needs a still map or a static slide, use the simpler
`flat-motion-graphics` playbook with a single image. This method earns its
complexity when the *map is the scene*, not a backdrop.

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

## What this method does NOT cover

- Multiple connected map scenes (zoom from continent → city → street). Use
  the `documentary-montage` pipeline for that — it's a different beast and
  needs scene transitions, not a single composition.
- Real-time interactive maps. This is a one-shot rendered video; for interactive
  output use a different toolchain.
- Stat-card overlays on top of the map. Add a Remotion overlay pass post-render
  if a brief needs that — don't try to inline stat cards into HyperFrames.

## File locations

| Thing | Location |
|---|---|
| Python library | [lib/mapkit_subjects.py](../../lib/mapkit_subjects.py) |
| This skill | `skills/core/animated-subjects-on-map.md` |
| HyperFrames authoring contract | [skills/core/hyperframes.md](hyperframes.md) |
| Reference project | `projects/medieval-europe-opener-test/` (gitignored — regenerate from this skill) |
| Channel styles | `styles/midnight-magnates.yaml`, `styles/grandpa-huxley.yaml` |
| Tile cache (per project) | `projects/<name>/scripts/_tile_cache/` (gitignored) |
