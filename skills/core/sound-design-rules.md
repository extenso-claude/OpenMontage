---
name: sound-design-rules
description: Locked Sleep Network sound-design rules for music and SFX placement, density, and tonal fit. Covers the first-10-minutes-only music rule, the sparse-period-appropriate-after-10:00 update, the never-alarming-SFX-after-10:00 update, sound-design drift audit (music + SFX vs Whisper), and the period-fit selection workflow. Read this skill in the audio/asset stage of any Sleep Network overlay-postproduction run.
layer: 2
status: production
applies_to_channels: [midnight_magnates, grandpa_huxley, sleepy_biographer, sleep_network_*]
applies_to_pipelines: [hybrid, documentary-montage, clip-factory]
companion_files:
  - skills/core/asset-coverage-gates.md
  - skills/core/overlay-positioning-rules.md
  - framework-videos/directives/midnight_magnates_overlay_postproduction.md
  - projects/vatican-entity-mm/scripts/qa_audio_drift.py
memory_anchors:
  - sound_design_rules_locked
  - drift_audit_all_cue_types
  - feedback_audio_after_visuals
created: 2026-05-21
why_this_exists: |
  Pre-2026-05-21 the Vatican Entity v4 shipped with (a) music that stopped abruptly
  at 10:00 and never returned, (b) an alarming "air raid siren" SFX at 35:32 that
  broke the sleep-channel tone, and (c) no Whisper-anchored drift audit for music
  or SFX. The user updated the rules during the comment pass: sparse +
  period-appropriate music after 10:00 (not zero), and never-alarming SFX after
  10:00. This skill encodes the new locked rules.
---

# Sound Design Rules — Sleep Network Locked

## Music density rules (LOCKED 2026-05-21)

### First 10 minutes — full music density
- **HOOK → CTA → COLD OPEN → Chapters 1–2 (~0:00–10:00)** are the "music zone."
- Music plays continuously under VO at -16 LUFS (-22 dB peak), ducking to -22 LUFS where speech is dense.
- Tonal fit takes priority over density: noir-jazz / dread-pad / Renaissance-string per scene; never pop, never modern EDM, never anything with a vocal track.

### After 10:00 — **sparse, period-appropriate, never overwhelming** (UPDATED 2026-05-21)

This replaces the older "no music after 10:00" rule. The new rule:

| Trigger | When music returns | Track choice |
|---|---|---|
| **Scene change** | New chapter, new act, new physical location | Match the scene's time period + mood. E.g. 1500s Pius V → Renaissance string ensemble; modern Calvi → noir saxophone; WWII Canaris → minor-key strings. |
| **Location reveal** | Wide establishing shot of a place after a long character-driven sequence | Atmospheric pad sized to ~30–45s, fade in 4s, fade out at next scene transition. |
| **Environment / time-period anchor** | Cuts to a different era from the current sequence (e.g. flash to 1572 from 1980s narrative) | Period-specific cue ≤ 25s, layered under VO at -22 LUFS. |
| **Pace shift** | Section transitions from heavy exposition to emotional / cinematic beats | Light pad rise, never percussion, never crescendo. |

**Sparsity guideline**: after 10:00, music covers **20–35% of timeline**, NOT 100%. Periods of pure VO + ambient SFX are the channel's voice — don't bury them.

**Forbidden after 10:00**:
- Continuous wall-to-wall scoring
- Tracks that thicken when VO gets emotional (channel rule: VO carries emotion, music doesn't pile on)
- Modern instrumentation when the scene is pre-1900 (no synth pads behind Pius V)
- Anything > -16 LUFS measured under VO

### Music selection by period (Midnight Magnates default mapping)

| Story period | Instrument family | Mood tag | Example reference |
|---|---|---|---|
| Pre-1800 (Renaissance, papal courts, Inquisition) | Strings + harpsichord + early choir | Reverent, ceremonial | "Renaissance court" Free Music Archive tag |
| 1800–1939 | Strings + woodwinds + low brass | Solemn, period-document | "Edwardian drama" Pixabay tag |
| WWI / WWII | Minor-key strings + brass mute | Dread, espionage | "Cold war suspense" Free Music Archive |
| Cold War / 1945–1989 | Saxophone + double bass + brushed drums | Noir, smoky | "Noir jazz" Free Music Archive |
| Modern (1989+) | Synth pad + bass drone | Conspiratorial, distant | "Investigative documentary" Pixabay |

Verify each track is **CC0 / CC-BY** with attribution captured in `artifacts/audio_sources_v*.json`.

## SFX density rules (LOCKED 2026-05-21)

### Full episode SFX is encouraged (up to 60-min cap)

Unlike music, SFX is dense throughout — every scene benefits from an immersive layer. Three goals (per channel brief):

1. **Immerse** — environmental sound that places the listener inside the scene (Vatican corridor footsteps, Atlantic surf, Renaissance crowd murmur)
2. **Emote** — sound that carries the emotional beat the VO is leaning into (slow choir swell on a death, single bell toll on a death anniversary, distant church bell at a papal moment)
3. **World-build** — sound that establishes time and place (typewriter clatter for spy office, quill scratch for Renaissance letters, dial-tone for 20th-century telecom)

### After 10:00 — **never-alarming** rule (LOCKED 2026-05-21)

This is the user-added rule from the 2026-05-21 review pass. After 10:00 (and arguably throughout for a sleep-channel), SFX MUST be:

| Allowed | Forbidden |
|---|---|
| Distant church bells | Air raid sirens |
| Quill on parchment | Sudden booms / explosions |
| Footsteps on stone | Crashes (car, glass, gunshot) |
| Page turn / clock tick | Loud alarms or klaxons |
| Wax seal press | Whip-cracks / thunder claps |
| Distant crowd murmur | Sharp screams |
| Telegraph clatter | Sudden cymbal hits |
| Choir swell (soft) | Anything > -10 LUFS peak |
| Wind / rain / surf | Industrial machinery |
| Match strike / candle | Modern phone / siren / horn |

The channel is a **sleep / documentary** brand. Alarming SFX after the first 10 minutes break the "fall asleep to stories" promise. If an event is dramatic (a 1942 plane crash, a 1981 shooting), use suggestive sound (slow plane drone fading, single distant gunshot at -22 LUFS with reverb tail) — not literal alarming sound.

**Specific bans** (from the 2026-05-21 review):
- `s38_air_raid_siren.mp3` — REMOVED, never again
- `s27_cannon.mp3` — restrict to first 10 minutes only
- `s41_table_slam.mp3` — REMOVED, replace with soft document drop
- `s40_plane_engine.mp3` — REMOVED if peaking > -14 LUFS

### Levels reference

| Element | Target | Notes |
|---|---|---|
| VO | -16 LUFS, -2 dB peak | Always the loudest |
| Music under VO | -22 LUFS | Heavy duck |
| Music between VO | -16 LUFS | Lift to fill |
| SFX immersive | -24 to -20 LUFS | Background bed |
| SFX accent | -16 to -14 LUFS peak | Brief hit, ducks to -24 in 0.8s |
| SFX (after 10:00) | -20 LUFS peak (hard cap) | NEVER above this |

## Sound design drift audit (MANDATORY)

Every music + SFX cue's `t_in` / `t_out` must be Whisper-anchored, same as visual cues.

### What to anchor on

- **Music**: anchor `t_in` to the FIRST WORD of the new scene/section the music supports, with a **3s lead-in fade** (so music starts 3s BEFORE the anchor word).
- **SFX**: anchor to the SPECIFIC WORD it punctuates. E.g., the wax-seal press SFX anchors to "...sealed the order" with `t_in = wordstart - 0.05s`.

### Drift budgets

| Cue type | Drift budget | Acceptable miss |
|---|---|---|
| Music (-3s pre-roll) | ±0.5s on the anchor word | The 3s fade-in masks small drift |
| SFX punctuation | ±0.15s on the anchor word | At -16 LUFS peak, larger drift reads as "wrong" |
| SFX ambient bed | ±2s (loose) | Long crossfades hide drift |

### Implementation

```python
# projects/<project>/scripts/qa_audio_drift.py
# Same pattern as qa_card_timing.py — fuzzy-match anchor phrase in Whisper.
# Report row per cue: cue_id, anchor_phrase, expected_t, actual_t, drift_s, status
# Fail compose if any SFX drift > 0.15s OR any music drift > 0.5s.
```

Run BEFORE the chunked compose. The script lives in the same folder as `qa_card_timing.py` and `qa_avatar_sync.py` and uses the same Whisper transcript.

## Cuelist shape for sound design

Every music and SFX cue must include:

```json
{
  "id": "track2",
  "kind": "music",
  "t_in": 196.0,
  "t_out": 450.0,
  "fade_in_s": 3.0,
  "fade_out_s": 4.0,
  "level_lufs": -22,
  "anchor_phrase": "chapter one — the entity is born",
  "period": "renaissance",
  "scrap_reason": null
}
```

```json
{
  "id": "s12",
  "kind": "sfx",
  "t_in": 1242.45,
  "t_out": 1244.85,
  "fade_in_s": 0.05,
  "fade_out_s": 0.8,
  "level_lufs_peak": -16,
  "anchor_phrase": "sealed the order",
  "category": "wax_seal_press",
  "alarming": false,
  "scrap_reason": null
}
```

Cues missing `anchor_phrase` cannot pass the drift audit.

## Cross-channel applicability

- **Midnight Magnates**: full rules above. Renaissance / WWII / Cold War / noir period palette.
- **Grandpa Huxley**: same rules, but period palette skews warmer (fireside / library / family-home). Music after 10:00 favors warm strings + light piano. NO noir saxophone.
- **Sleepy Biographer**: same rules; period palette per subject's era.
- **Future channels**: add to `applies_to_channels` in this file's frontmatter.

## Self-Annealing Notes

- **2026-05-21**: Created after the Vatican Entity v4 review pass where the user added the sparse-music-after-10:00 + never-alarming-SFX-after-10:00 rules. Prior to this skill, the rules existed only inline in chat — easy to miss on the next run. Now they're durable and routed through `applies_to_channels` so the Grandpa Huxley channel inherits them too.
- **2026-05-21**: Drift audit on music + SFX was previously informal. The 2026-05-21 review pass found ~6 SFX cues drifting > 0.15s from their anchor word. New mandatory gate: `qa_audio_drift.py` must pass before compose.
