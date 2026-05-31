# Visual Design Quality (Meta Skill)

OpenMontage's quality gate for **any code-driven visual output** — Remotion components, HyperFrames blocks, brand assets, kinetic typography, illustrated SVG, scene templates, motion backgrounds, end cards. This skill keeps every new visual surface from drifting into "generic AI aesthetic" territory while staying locked to the active channel's playbook.

This skill **wraps and routes to** the universal `frontend-design` skill (`.agents/skills/frontend-design/SKILL.md`) and adds OpenMontage-specific tone commitments, anti-patterns, and review hooks.

---

## When To Read This Skill

**Mandatory before** any of:

- Authoring a new component in `remotion-composer/src/components/brand/` or `remotion-composer/src/components/`
- Authoring a new HyperFrames block under `brand_assets/hyperframes/<name>/`
- Designing a new Remotion scene type (text_card, stat_card, hero_title variants)
- Generating a brand demo, style reel, or end card
- Designing a kinetic-typography sequence
- Producing an illustrated SVG asset (vault doors, chess pieces, skylines, sigils, decorative motifs, etc.)
- Updating a style playbook's `visual_language` or `motion` section

**Also mandatory before** any AI image generation (Recraft, FLUX, Imagen, etc.) — see the **AI Image Generation Rules** section below. Previously this skill skipped that, but the rules in that section apply universally and are non-negotiable.

**Skip** for:

- Cuts/concat/trim with `ffmpeg` (no design surface)
- Subtitle burn-in (caption styling lives in playbook)

## Reading Order

1. **`.agents/skills/frontend-design/SKILL.md`** — universal aesthetic rules, anti-patterns, design-thinking workflow. **Read this first, every time.** It's short.
2. **The active channel's style playbook** in `styles/<channel>.yaml` — the *binding* aesthetic for this project. Playbook always wins where it conflicts with the skill's universal defaults.
3. **This file** — the bridge: how to apply the skill within OpenMontage's brand and channel system.

## Channel Tone Commitments

The frontend-design skill demands a **bold tone commitment** before coding (brutally minimal / maximalist chaos / retro-futuristic / etc.). For Sleep Network channels these are pre-mapped — do not re-decide per scene:

| Channel | Locked tone commitment | Why |
|---|---|---|
| **Midnight Magnates** | `editorial-magazine` + `art-deco/geometric` + `luxury/refined` — **AI image style addendum (LOCKED v2 May 2026):** `"night colors, noir atmosphere, moonlit, flat segmented color illustration"` (override "moonlit" in scene prompts for indoor / non-moonlit scenes). Default Recraft model: **V4.1** — `recraftv4_1_vector` for backgrounds, `recraftv4_1` raster for animated subjects. See `midnight_magnates_style_locked_v2` memory. | Boardroom noir, hidden-history-of-power framing — geometric precision, single shaft of light, brass-on-deep-navy |
| **Grandpa Huxley** | `organic/natural` + `luxury/refined` + soft warmth | Candlelight philosopher — warm earth tones, parchment, hand-feel restraint |
| **Sleep Network base** | `luxury/refined` + restrained minimalism | Sleep-safe default for cross-channel work |
| **Outside Sleep Network** | Pick fresh per the skill's tone menu | No lock-in |

When in doubt, the channel playbook's `identity.mood` field is the canonical statement of tone. Treat the table above as a reading aid, not an override.

## OpenMontage Anti-Patterns (stack on top of the skill's universal ones)

The skill bans Inter/Roboto/Arial, purple gradients, Space Grotesk, cookie-cutter layouts. OpenMontage adds:

| Banned | Reason |
|---|---|
| Raw white `#ffffff` for any burned-in text | Sleep Network rule — always cream (`#f5f0e4` MM, `#f0e6d2` Huxley) |
| Em dashes `—` on screen or in narration | Network-wide rule (originally Huxley, applied universally) |
| Bouncy / overshoot easing | Sleep-safe — never jarring; use `Easing.inOut(Easing.cubic)` or `Easing.out(Easing.cubic)` |
| Hard cuts under 4 seconds | Sleep audience can't tolerate fast cuts; min scene hold 4s |
| Translucent plates with alpha < 225/255 | Plates must be opaque so video underneath doesn't shimmer through |
| More than one shaft of light per scene (MM only) | Boardroom-noir signature — never competing highlights |
| Warm earth tones in Midnight Magnates work | Reserved for Grandpa Huxley — channel separation |
| Cool noir blue or red CLASSIFIED stamp in Grandpa Huxley work | Reserved for Midnight Magnates — channel separation |
| `requestAnimationFrame` inside Remotion components | Breaks frame-deterministic render — drive everything from `useCurrentFrame()` |

## Mandatory Quality Floor (Sleep Network channels)

Every burned-in text element must use:

```
textShadow: "2px 0 0 #000, -2px 0 0 #000, 0 2px 0 #000, 0 -2px 0 #000,
             1.4px 1.4px 0 #000, -1.4px 1.4px 0 #000, 1.4px -1.4px 0 #000, -1.4px -1.4px 0 #000,
             0 4px 14px rgba(0,0,0,0.55)"
```

This simulates a 2px black stroke (Chromium doesn't honor `paint-order` on HTML text, so 8 offsets stand in) plus a soft drop shadow — keeps alpha edges crisp when the text sits over video.

For SVG text use real `stroke` + `stroke-width: 2` + `paint-order: stroke fill`.

Other floors:
- 1920×1080 minimum, 24fps for sleep-network channels
- 1.5s entrance: opacity 0→1 + scale 0.97→1.0 with `Easing.out(Easing.cubic)`
- 1.5s exit: opacity 1→0
- Music ducked to `≤ 0.06` (voice dominates)

## AI Image Generation Rules

These rules apply to **every** AI image generation call across every pipeline — Recraft, FLUX, Imagen, OpenAI, DALL-E. Asset directors and scene directors must respect them before issuing any image-generation request.

### Rule 1 — Never ask AI to render text

Never include text-to-be-rendered in an AI image prompt — no headlines, labels, dates, captions, document body, sign text, calendar numbers, headlines on newspapers, names on dossier covers. AI image models hallucinate spelling and don't match channel typography.

- Generate the surface WITHOUT text and overlay text on top in HyperFrames / Remotion.
- Theme negative prompts already ban "text labels, banners with text, writing on objects, captions, dates, numbers, lorem ipsum" — preserve those.
- If a generation arrives with AI-rendered text anyway: (1) evaluate spelling and legibility on the real render, (2) if wrong or off-brand, re-roll OR mask out the text region and overlay correct text, (3) only ship as-is if spelling is correct AND it matches channel typography (rare).

### Rule 2 — Never reach for AI when a free / procedural option exists

Before specifying an AI image (background OR subject), check whether a free option already covers the beat:

- **Animation library Google Sheet** `1v1pI_x1s7ermhkG1ryNxhNxelDQuliCM6l-3hHRwwY8` — the inventory of every motion primitive, brand component, scene cut, frame, filter, and HF recipe currently in production.
- **19-recipe catalog** (`tools/animation/animation_catalog.py`, `skills/core/animation_catalog.md`) — `Aged document`, `Newspaper unfold`, `Polaroid scatter`, `Tarot card draw`, `iMessage scroll`, `Search query`, etc. Most are HF-only ($0).
- **Sleep Network Remotion brand components** — `CharacterCard`, `MapAnnotation`, `Timeline`, `QuoteCard`, `ChapterCard`, `LowerThird`, `CalendarReveal`, `ClockReveal`, `DocumentReveal`, `NetworkMap`, `KPI grid`, etc.
- **21 GSAP motion primitives** in `tools/animation/catalog/assets/mm_motion.js` — `Comet pass`, `Slam-in`, `Particle drift`, `Card flip`, `Ken Burns drift`, `SVG path draw`, `Stamp slam`, `Type-in`, `Beat flash`, `Window-glow breathe`, etc.

AI generation is reserved for scene environments that can't be procedurally drawn (rooms, landscapes, skylines) and primary subjects with specific period/place identity (a 1953 rotary phone, a Reaper drone, a hospital bed in 1951 Iran). Everything else — particles, reticles, smoke, calendars, clocks, flags, stamps, trails, document layouts, news headlines, charts, stat cards — defaults to procedural.

### Rule 3 — One AI background + one AI subject. That's the ceiling.

For any "AI background + animated subject" shot, the AI budget is **1 BG + 1 subject MAX**. Everything else is built in HyperFrames.

- Often the subject can also be procedural — then the shot is just one AI background plus HF foreground elements. That's a feature, not a compromise.
- Common procedural-in-HF replacements for things that used to drift into AI subject lists:
  - Smoke, exhaust, cigarette smoke, dust motes → `Particle drift`
  - Targeting reticles, crosshairs, UI overlays → SVG circles + lines
  - Calendars, date stamps, clocks → HF text + CSS card styling, optionally with `Card flip` or `Stamp slam`
  - Flames, candle flicker → CSS gradient + jitter rotation
  - Missile trails, comet streaks, signature draws → `Comet pass`, `SVG path draw`
  - Document stamps (CLASSIFIED, FILED) → `Stamp slam` text element
- If a shot spec creeps back toward 2+ AI subjects, that's a signal to split the shot or move secondary subjects to HF.

### Rule 4 — Don't pre-specify motion coordinates before generation

At shot-plan time, describe motion in terms of family and intent only. Don't pin pixel translations, rotation degrees, scale ratios, sub-second timings, or easing curves. Those values depend on the actual generated image — which doesn't exist yet.

What a shot-plan motion field SHOULD contain:

- Motion family — `Slam-in`, `Comet pass`, `Particle drift`, `Ken Burns drift`, `Beat flash`, `SVG path draw` etc. (named primitives from `mm_motion.js`).
- Intent — entrance / emphasis / ambient life / payoff.
- Sync anchor — which VO word/phrase the key motion lands on, with a transcript timestamp.
- Approximate count or cadence — "3 wiggle cycles", "1 single streak across frame", "n=10–14 motes".

What it should NOT contain: exact px translations, rotation degrees, individual durations, easing curve names. Those are tuned after the image lands.

### Rule 5 — Palette is NOT channel-locked in the shot plan

At shot-plan time, palette guidance is **descriptive, not enumerated**. Use phrases like *"noir palette, night scene, avoid bright whites in large areas"* — not hex code lists per shot.

- The theme's `style_addendum` ("simple minimalist flat segmented colors illustration, nighttime noir style, subtle color accents, clean flat shapes") carries the palette signal at the API layer.
- Theme `controls.colors` palette enforcement is fine for catalog recipes that already declare a theme.
- For one-off shots NOT going through `animation_catalog`, either pass `theme="midnight-magnates"` to inherit the addendum, or manually prepend `"simple flat segmented colors illustration, noir style. "` to scene prompts.
- Channel `styles/*.yaml` consistency anchors are the source of truth for code-driven visuals (Remotion components, HF brand assets) — they still hex-lock. But for AI image PROMPTS, palette stays descriptive.

### Rule 6 — Don't include audio / SFX in shot plans

Shot plans are visual specs. Audio decisions (SFX layers, music swells, ambient beds, per-shot impact stings) come AFTER visuals are locked. The proposal-stage Music Plan (per `AGENT_GUIDE.md`) still happens — that decides whether music exists at all and what the source is. Per-shot SFX is its own pass after the visual cut is approved.

### Rule 7b — Recraft V4.1 defaults (Midnight Magnates)

Use Recraft V4.1 by default. Same cost as V3, dramatically better noir adherence:

| Use case | Model string | Cost |
|---|---|---|
| Backgrounds (full scene, animated or not) | `recraftv4_1_vector` | $0.08 |
| Animated subjects / objects (transparent PNG) | `recraftv4_1` (raster) | $0.04 |

**Why vector-for-bg, raster-for-subject:**
- Vector backgrounds scale cleanly to 1080p — no resolution penalty even at the smaller V4.1 16:9 cap of 1344×768
- Raster subjects animate more reliably via GSAP transforms + handle transparent PNG cleanly
- Both at the same standard pricing — no Pro tier needed

V4+ models do NOT accept `style`, `substyle`, `style_id`, `negative_prompt`, or `text_layout`. Bake exclusions into the positive prompt. See `recraft_v4_1_upgrade` + `midnight_magnates_style_locked_v2` memories.

### Rule 7 — Recraft prompt structure

When writing Recraft scene prompts (via `recraft_gen.py` or directly):

- Describe ONLY scene content (subject, action, environment, lighting cue, period detail).
- Do NOT restate: "illustration style", "flat", "noir", "vintage", "muted colors", or hex palette callouts — the theme's `style_addendum` already has them.
- Do NOT include text the model should render (Rule 1).
- For transparent-PNG subjects, append: `"isolated on transparent background, no other objects"`.

Good prompt (BG, scene content only):
> "A 1953 CIA office at night, mahogany desk in lower-left, leather chair turned away, brass desk lamp casting a warm pool of light, paneled wood walls, framed map on far wall, scattered papers, ashtray with smoke, slatted venetian blinds throwing shadow across the floor. No telephone, no people, no text."

Wrong prompt (restates style, hex-locks palette, names text):
> "Vintage 1953 CIA office at night, noir documentary illustration style, limited palette deep navy #0a1628 / black / brass #c9a84c / classified-red #b41e1e, framed map labeled 'IRAN', no telephone."

The italicized portion duplicates the style_addendum, hex-locks palette, and asks for text — three rule violations in one line.

## Three Manual-QA Rules Before Any Render

These three checks have caught more shipped bugs than the lint+validate chain combined. Each is documented in detail under its own memory entry; this is the rollup.

### Rule: Text containment

Every text element inside a small visual container (ticket, stamp, badge, card, stat callout) must FIT inside the container body with ≥15% horizontal padding from any edge. Common failure: text font-size set too large for a narrow stub, glyphs clip past the container border. Per-element font-size cap ≈ container_width / (chars × 0.55). Memory: `text_containment_qa_required`.

### Rule: Motion direction

Every animated subject (drone, missile, car, character, fleet) MUST face the direction it's moving. The nose of the drone, head of the wolf, front of the car — all point the way it's traveling. If the AI-generated asset faces the wrong way, flip horizontally (`transform: scaleX(-1)`) OR reverse the animation. Memory: `motion_direction_qa_required`.

### Rule: Never ship placeholder portraits

`CharacterCard` (or any portrait-bearing component) must have a real photo before render. Placeholder gradient + initials = unfinished work, not a draft. Source PD from Wikimedia / LoC / National Archives. If no PD photo exists for a figure, switch to a different visual treatment (silhouette, symbolic object, signature) — never ship the placeholder. Memory: `never_placeholder_portraits`.

### Rule: Geographic pin accuracy

Any shot placing pins, labels, or sprites at named geographic locations MUST compute pixel positions from real lat/lon — never eyeballed CSS percentages. Two acceptable paths:

1. **`lib/mapkit_subjects.py` (canonical)** — `MapConfig` + `build_basemap()` + `SpriteAnchor(lat, lon)` + `compute_anchor_pixels()`. See `skills/core/animated-subjects-on-map.md` for the worked example.
2. **Per-image measurement** — for stylized AI-generated maps, manually identify pixel positions for each named location against the SPECIFIC rendered image, documented in a `<!-- measured against ... -->` comment.

Eyeballed percentages (`left: 18%; top: 42%`) without lat/lon backing or measurement justification = critical reviewer finding. Even if the map looks beautiful, a Washington D.C. pin in Arizona is a shippable bug. Memory: `geographic_pin_accuracy_required`.

### GSAP filter:brightness gotcha (always-on rule)

Don't animate `filter: brightness(X)` via GSAP — interpolation passes through `brightness(0)` mid-tween, producing pure black frames. Use a flash-overlay div with opacity tween instead. Memory: `gsap_filter_brightness_gotcha`. Static CSS `filter:` for color-grading is fine.

## Sequenced Master Compositions (HyperFrames)

When authoring a master composition that strings multiple shots end-to-end (e.g., a full hook + intro, a montage, any project that uses sub-compositions via `data-composition-src`), you MUST verify timeline coverage before declaring it ready.

`npx hyperframes lint` and `npx hyperframes validate` do NOT flag gaps. They treat gaps as valid (because gaps CAN be intentional — a deliberate black fade). But in a continuous-narration master, every gap is a bug.

**Mandatory gap-coverage check** — add to the QA chain:

```bash
python lib/hf_coverage_qa.py <project>/hyperframes/index.html
```

Threshold default 0.05s. Exits non-zero if any gap > threshold. Indexed in `MEMORY.md` as `gap_coverage_qa_required`.

**Pre-render QA chain for sequenced masters:**

1. `npx hyperframes lint` — structural
2. `npx hyperframes validate` — runtime + contrast
3. `python lib/hf_coverage_qa.py index.html` — gap coverage **(new)**
4. `npx hyperframes preview` — human scrub
5. `npx hyperframes render` — only after all four pass

**How to fix gaps when the script flags them:**

- Small gaps (1–2s, natural VO pauses between shots) — extend the previous shot's `data-duration` to cover the gap. The shot's GSAP timeline ends at its design length; the extra time is a natural hold on the final frame.
- Large gaps (>3s) — a shot is missing. Build it. Anything marked "optional" in a shot plan must be ACTUALLY optional (i.e., the gap is a designed black beat with a purpose) or it must be built. Don't ship an unfilled "optional" slot.

## New-Component Checklist

Use this before opening a PR for a new visual component:

- [ ] Read `.agents/skills/frontend-design/SKILL.md`
- [ ] Read the relevant `styles/<channel>.yaml`
- [ ] Tone commitment locked from the channel table above (or fresh per skill if outside Sleep Network)
- [ ] No banned items from the OpenMontage anti-pattern table
- [ ] All burned-in text uses the stroke+shadow combo above and cream (never raw white)
- [ ] Single shaft of light per scene (Midnight Magnates) — verified
- [ ] Min scene hold ≥ 4s — verified
- [ ] Easing is `Easing.inOut(Easing.cubic)` or `Easing.out(Easing.cubic)` — no bounce
- [ ] Component accepts a `theme: BrandTheme` prop and resolves via `resolveTheme()`
- [ ] Self-QA done: rendered a sample, extracted ≥ 3 keyframes, eyeballed against the playbook's `consistency_anchors`
- [ ] Component exported from `components/index.ts`
- [ ] If reusable across channels, both `midnight_magnates.json` and `grandpa_huxley.json` have been visually validated

## Where This Plugs Into Pipelines

| Pipeline | Stage | Hook |
|---|---|---|
| `animation` | `scene-director` | Reads this skill before authoring scene templates or selecting motion approach |
| `animation` | `asset-director` | Reads this skill before authoring code-driven assets AND before any AI image generation call (Rules 1–7 above) |
| `cinematic` | `scene-director` | Same |
| `cinematic` | `asset-director` | Reads this skill before any AI image / video generation call |
| `hybrid` | `asset-director` | Reads this skill before any AI generation call — same Rules 1–7 |
| `documentary-montage` | `asset-director` | Same — channel-locked, especially for end cards and stat cards |
| `explainer` | `asset-director` | Already enforces Rule 1 (no AI text) locally — defer to this skill for the full ruleset |
| All pipelines | `compose-director` | Reviewer reads this skill to check the final render against the quality floor |

## How This Interacts With Other Skills

- **`frontend-design`** (Layer 3) — universal aesthetic principles. Always read first.
- **`animation-runtime-selector.md`** — tells you WHICH runtime (Remotion/HyperFrames/GSAP/Motion/Lottie) to use. Read after this skill — picking the right runtime depends on the design intent.
- **`hyperframes`, `gsap-*`, `framer-motion`, `lottie-bodymovin`** (Layer 3) — runtime-specific implementation knowledge. Read for the chosen runtime.
- **`web-design-guidelines`** — for any web preview / browser-rendered surface. Complementary; not a replacement for this gate.
- **`vercel-react-best-practices`, `vercel-composition-patterns`** — React composition mechanics. Apply alongside this skill, not in place of it.
- **Style playbooks** (`styles/*.yaml`) — the binding aesthetic. Playbook always wins.

## Reviewer Hook

Reviewer (`skills/meta/reviewer.md`) treats violations of the OpenMontage anti-pattern table or the mandatory quality floor as **critical** findings — must fix before checkpoint advances. The skill's universal anti-patterns (Inter font, purple gradients, etc.) are also critical for new visual components.

The new-component checklist serves as the reviewer's `review_focus` block when reviewing a stage that authored a code-driven visual. Treat unchecked items as suggestions; checked items confirmed false in the render are critical.
