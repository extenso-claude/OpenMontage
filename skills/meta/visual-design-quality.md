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

**Skip** for:

- AI image-generation prompts via `image_selector` (use the playbook's `image_prompt_prefix` and `consistency_anchors` instead — those are the asset director's domain)
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
| **Midnight Magnates** | `editorial-magazine` + `art-deco/geometric` + `luxury/refined` | Boardroom noir, hidden-history-of-power framing — geometric precision, single shaft of light, brass-on-deep-navy |
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
| `animation` | `asset-director` | Reads this skill before authoring code-driven assets (Remotion components, kinetic type) |
| `cinematic` | `scene-director` | Same |
| `documentary-montage` | `asset-director` | Same — channel-locked, especially for end cards and stat cards |
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
