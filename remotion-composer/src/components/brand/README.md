# Brand Components — Remotion

Channel-themed reusable components. Pair with `brand_assets/tokens/playbook_to_tokens.py`
for theme injection from a channel playbook.

See [`brand_assets/README.md`](../../../../brand_assets/README.md) for the
extension guide and theme contract.

---

## Components (stable)

### `CharacterCard`

Figure / organization intro. Auto-alternates top-right (even sceneIndex) and
top-left (odd) for visual variety. Channel-themed frame, optional portrait,
tight text-limit enforcement.

```tsx
<CharacterCard
  name="Marcus Aurelius"
  role="Stoic philosopher and Roman emperor"
  dates="121 – 180 AD"
  stats={["Last of the Five Good Emperors", "Author of Meditations"]}
  portraitSrc="/assets/marcus_aurelius.png"
  sceneIndex={3}                  // odd → top-left
  theme={huxleyTheme}
/>
```

**Text limits (auto-shrink, no ellipsis truncation):**
| Field | Max chars |
|---|---|
| name | 30 |
| role | 50 |
| dates | 25 |
| each stat line | 25 (max 2 lines) |

When the asset director writes character data, it should respect these
limits during script writing — the auto-shrink is a safety net, not a
license to write long.

---

### `TypewriterText`

Chars-per-second reveal with optional blinking cursor. Sleep-safe default of
12 chars/sec — anything faster looks frenetic for sleep content.

```tsx
<TypewriterText
  text="The first lesson of power is patience."
  charsPerSecond={10}
  cursorChar="▍"
  vAlign="center"
  theme={mmTheme}
/>
```

Newlines (`\n`) are honored. Use for quote reveals, document-content reveals,
and dramatic single-statement moments.

---

### `CTABanner`

Lower-band CTA strip. 10 presets cover YouTube + Spotify subscribe / follow /
comment / rate / share. Platform brand color tints the icon block; the rest
of the strip stays in channel theme.

```tsx
<CTABanner preset="youtube_subscribe" holdSeconds={6} theme={huxleyTheme} />
<CTABanner preset="spotify_rate" position="bottom" theme={mmTheme} />
<CTABanner preset="both_subscribe" customText="Find us wherever you sleep" />
```

**Available presets:** `youtube_subscribe`, `youtube_comment`, `youtube_share`,
`spotify_follow`, `spotify_comment`, `spotify_rate`, `spotify_share`,
`both_subscribe`, `both_comment`, `both_rate`.

Use sparingly — once mid-video max, once at end. Stacking CTAs reads as
"AI slop."

---

### `AssetFrame`

Branded wrapper around a copyright-free photo or clip. 5 variants:

| Variant | Best for | Channel fit |
|---|---|---|
| `parchment` | Books, scrolls, ancient artifacts, historical paintings | Huxley (default) |
| `boardroom` | Documents, geometric power imagery, financial records | MM (default) |
| `polaroid` | 19th–20th c. photographs, historical figures (real photos) | Both |
| `document` | Letters, ledgers, treaties; supports CLASSIFIED/REDACTED stamp | MM (stamp = MM-only) |
| `filmstrip` | Video clips with vintage perforated-edge feel | Both |

```tsx
<AssetFrame variant="boardroom" src="/assets/wall_st_1929.jpg" captionText="New York, October 1929" theme={mmTheme} />
<AssetFrame variant="document" src="/assets/treaty.png" stamp="CLASSIFIED" theme={mmTheme} />
<AssetFrame variant="polaroid" src="/assets/dostoevsky.jpg" theme={huxleyTheme} />

{/* Wrap arbitrary content (e.g., a video clip) */}
<AssetFrame variant="filmstrip" theme={mmTheme}>
  <OffthreadVideo src="/assets/wall_st_1929.mp4" />
</AssetFrame>
```

The CLASSIFIED stamp uses `theme.stampRed` — null-safe (Huxley theme has it
as `null`, so passing the wrong stamp on a Huxley scene falls back to a muted
default red rather than crashing).

---

## Components (stub — spec defined, implementation pending)

### `AnimatedMap` (STUB)

Geographic visualization. Sleep-doc cornerstone — used heavily in MM
(empires, dynasties, expeditions) and occasionally in Huxley (philosophical
journeys, historical exiles).

**Planned variants:**

#### `world_route`
Dotted or solid line traces a journey across continents. Animates from
origin to destination over the scene duration. Pin appears at endpoint.
*Use for: expeditions, exiles, trade routes, escapes.*

#### `region_zoom`
Camera starts at world view, zooms into country, then city, then a specific
location. Each zoom level can label key features.
*Use for: "the story begins in [obscure place]" cold opens.*

#### `pin_drop`
Pins drop sequentially at named coordinates with labels. Each pin reveals
~1.5s apart. Optional connecting lines.
*Use for: "they had operatives in 14 cities" reveals; institutional reach.*

#### `empire_extent`
Shaded territory animates outward over time, showing rise of an empire.
Optional "fall" reverse-animation showing collapse.
*Use for: dynasty stories, corporate empire growth.*

**Blocking questions before implementation:**
1. **Base map data:** `react-simple-maps` (npm, 80KB+ TopoJSON world map) is
   the easy path. Alternative: hand-crafted SVG paths (smaller bundle, more
   control). Which?
2. **Coordinate format:** Accept lat/lng pairs, or named places that get
   resolved via a small built-in gazetteer? The latter is friendlier to write
   but limits what the asset director can express.
3. **HyperFrames sibling:** GSAP DrawSVG plugin is built for path-tracing —
   the `world_route` variant might genuinely be better in HyperFrames. Build
   a Remotion-only first or invest in a HyperFrames variant up front?

When you say "build the maps," I'll wait for answers on these before
committing the implementation. Or you can answer "make sensible defaults"
and I'll pick `react-simple-maps` + lat/lng + Remotion-first.

---

### `Timeline` (STUB)

Time-scrubbing visualization for events, dynasties, or chapters.

**Planned variants:**

#### `horizontal`
Left-to-right scrub with year markers and event nodes. Camera moves with
narration. Events reveal as the playhead reaches their year.
*Use for: rise-and-fall arcs, decade-spanning stories.*

#### `vertical_chapter`
Top-to-bottom for long-form chapter dividers. Useful as a recurring spine
that shows "you are here" inside a 10-chapter sleep doc.
*Use for: long-form structure, navigation anchors.*

#### `dynasty`
Multiple parallel lifelines, each labeled. Used for rival figures or
competing institutions whose lives overlap and intersect.
*Use for: MM dynasty stories, philosophical schools that overlapped (Stoics
vs Epicureans).*

#### `branching`
Decision points fork the line. Shows what-ifs, alternate timelines, or
strategic divergences ("two strategies, both rational, both with fatal blind
spots").
*Use for: MM "Boardroom Split" beats — the engagement-beat moment where two
paths diverged.*

**Blocking questions:**
1. **Event input format:** flat array of `{year, label, type?}` (current stub),
   or richer schema with `description`, `imageSrc`, `chapter_id`, etc.?
2. **Camera scrub:** time-driven (constant speed across video duration) or
   beat-synchronized (each event appears at a narration timestamp)?
3. **Default reveal duration per event:** 2–3s feels right for sleep — confirm?

---

## Adding a new component

> **Read `skills/meta/visual-design-quality.md` before starting.** That skill routes you to the universal aesthetic engine (`.agents/skills/frontend-design/SKILL.md`) and the channel tone commitments. Skipping it produces components that drift toward generic AI aesthetic — Inter font, purple-on-dark gradients, predictable layouts — which kills sleep-doc mood and risks YouTube AI-slop demonetization signals.

When you say "add component X for [use case]":

0. **Read the quality gate.** `skills/meta/visual-design-quality.md` → `.agents/skills/frontend-design/SKILL.md` → the active channel's playbook in `styles/<channel>.yaml`.
1. **Drop the file** at `remotion-composer/src/components/brand/<Name>.tsx`.
   Use the existing components as templates — they all follow the same
   pattern (resolveTheme, fade in, hold, fade out).
2. **Default to network-base** for any optional theme prop. Components must
   render standalone in dev preview without a channel selection.
3. **Document here** under "Components (stable)" with a usage example.
4. **Add to `brand_assets/catalog.yaml`** so the agent can discover it.
5. **Export** from `remotion-composer/src/components/index.ts`.
6. **Hard rules** apply (see `brand_assets/README.md`):
   no raw `#ffffff`, no exclamation points, no em dashes, min 1.5s motion,
   max 30% overlay opacity.

### Pre-merge quality checklist

Pulled from `skills/meta/visual-design-quality.md`. Tick before opening a PR:

- [ ] Read `.agents/skills/frontend-design/SKILL.md` and the channel playbook
- [ ] Tone commitment locked (MM = editorial-magazine + art-deco + luxury · Huxley = organic + luxury + soft)
- [ ] No banned items: Inter/Roboto/Arial/Space Grotesk fonts, purple gradients, raw `#ffffff`, em dashes, bouncy easing, translucent plates < 225/255 alpha
- [ ] Burned-in text uses the 8-offset stroke + soft shadow recipe and cream (never raw white)
- [ ] Single shaft of light per scene (Midnight Magnates) — verified visually
- [ ] Min scene hold ≥ 4s, easing is `Easing.inOut(Easing.cubic)` or `Easing.out(Easing.cubic)`
- [ ] No `requestAnimationFrame` — all motion driven by `useCurrentFrame()` for deterministic render
- [ ] Self-QA done: rendered a sample, extracted ≥ 3 keyframes, eyeballed against the playbook's `consistency_anchors`
- [ ] If reusable across channels, both `midnight_magnates.json` and `grandpa_huxley.json` themes have been visually validated
