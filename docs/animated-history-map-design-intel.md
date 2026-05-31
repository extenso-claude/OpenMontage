# Animated History Map — Design Intel

Synthesis of 5 reference videos (6 briefs) into the canonical design input for the
`animated-history-map` pipeline. Every director skill, the storyboard schema, the
QA gate suite, and the theme system reference this document.

Sources analyzed:
- **Ref 1** — *The Terrible End of the 12 Apostles on a Map* (Power of the Word, 39:43)
- **Ref 2** — *The ENTIRE History of Medieval Europe* (History with Dave, 23:37)
- **Ref 3** — *Medieval Europe: 1000 Years in 20 Minutes* (How So, 22:25)
- **Ref 4** — *Battle of Verdun 3D* (Epic History, 20:56)
- **Ref 5** — *The Entire Life of Jesus on a Map* (Ear to Hear, 18:58) — script-only
- **Ref 1 hook follow-up** — 12 Apostles 0:00–2:00 — hook formula

The references span three different production paradigms (cinematic-AI-clip, hand-illustrated, bespoke-3D-diorama) and two different narration paces (115 WPM broadcast, 164–187 WPM YouTube-essay). The pipeline absorbs the structural moves common across paradigms and parameterizes the per-paradigm choices into the `theme.json`.

---

## 1. Six architectural decisions baked into the pipeline

### 1.1 Map posture is a per-project choice (theme.json), NOT a default

The references disagree fundamentally on what role the map plays:

| Posture | Map screen-time | Example | Best for |
|---|---|---|---|
| **canvas** | 60–90% | Ref 2, Ref 3, Ref 4 | Geographic/movement histories (empires, expeditions, battles) where geography IS the story |
| **bookend** | ~7% | Ref 1 | Compilation videos where the map is identity ("N things on a map") but the stories are character-driven |
| **hybrid** | 40–60% | (no single ref) | Event histories (assassinations, plane crashes, royal successions) — map as anchor + structural spine, story-dives carry character interiority |

The pipeline supports all three. The Showrunner picks one at the script stage based on the brief. The choice cascades into the storyboard's `phase` budget allocation: canvas posture allocates more `map_breath` / `approach` / `return_to_map` time, bookend posture allocates more `story_dive`.

**For the Presidential Assassinations test video: HYBRID.** Each assassination has a "where" (anchoring) but the gravity is on character + act, not topography.

### 1.2 Camera language is also a per-project choice

The references split:

| Camera style | Reference | What it looks like |
|---|---|---|
| **static_with_accents** | Ref 2 (one zoom in 4 min — everything else is overlay choreography on a held basemap) | Camera mostly still; "motion" comes from labels, sprites, arrows, polygons fading in/out on the same canvas |
| **continuous_drift** | Ref 4 (every shot has 1–3% per second pan + tilt; never a static frame) | Cinematic, every shot has bake-in motion, "documentary heartbeat" rhythm |

These are not "better/worse" — they're different aesthetics. Ref 2's pattern is cheaper (one basemap, many cues) and information-dense. Ref 4's is more cinematic. The pipeline parameterizes both via `theme.camera_language`. Default to `static_with_accents` (cheaper, fits more briefs); upgrade to `continuous_drift` for high-cinematic projects.

### 1.3 Map renders in 6 tiers (cascade zoom)

Synthesized from refs 2/3 (continental scale only) + ref 4 (regional only) + the new requirement for event-based videos that need scene-level dives:

| Tier | Source | Zoom range | Used for |
|---|---|---|---|
| **continental** | Carto Dark + noir filter (existing `mapkit_subjects`) | z3–z7 | Macro: CONUS, world tour, regional movement |
| **regional** | Carto Dark, lat/lon-anchored | z8–z11 | State, region, multi-city framing |
| **urban** | Carto Light/Voyager OR procedural city grid | z12–z15 | City, neighborhood |
| **scene** | **Procedural SVG schematic** (lat/lon → SVG street grid, hand-styled landmark blocks) | n/a | Dealey Plaza, Ford's Theatre block, Hilton entrance |
| **building** | **PD floorplan** (LoC, FBI, Sanborn) OR procedural | n/a | Theatre balcony, hotel pantry, depository 6th floor |
| **off-map** | Full-frame panel | n/a | Character cards, archival photo Ken-Burns, document overlay |

Transitions between tiers handled by a new `basemap_swap` cue: crossfade with anchored geographic center (Dallas stays at viewport center as we crossfade from Carto z12 → procedural Dealey Plaza SVG).

The hybrid choice (per the user's earlier answer): **procedural SVG for scene-level streets, PD floorplans for building-level when one exists, procedural fallback otherwise.**

### 1.4 Visual primitive library is enum-strict but extensible

The storyboard JSON schema constrains animator agents to a closed enum of `visuals.kind` values. This stops AI-slop hallucination cold (you can't invent a "telegram_animation" cue that doesn't exist in the compiler). The catalog grows by addition — animator agents propose new primitives, depth-reviewer evaluates, accepted ones get enum'd.

**Per-phase escape hatch:** up to 2 beats per phase can be marked `experimental: true` with a written rationale, bypassing the enum. These are caught by depth-review, not gates.

### 1.5 QA is iterative until clean, not bounded by rounds

(Per user's #1 and #6 feedback.) Three layers:

1. **Hard gates** (10 scripts) — any non-zero exit triggers fix → re-run ALL gates (a fix can regress others)
2. **Breadth swarm** (6 parallel sweepers) — any finding triggers fix → re-run gates AND breadth
3. **Depth review** — runs until "no new improvements found" with steady-state detection (round N == round N-1 → escalate to user)

No round cap. Stop condition is **zero new findings**, not "looks good."

### 1.6 All free except Inworld TTS

(Per user's #3 feedback.) Cost target ~$0.25 total per video. No AI image generation (no Recraft, no Flux), no AI music generation (no ElevenLabs Music API), no AI archival generation. Assets sourced from:
- PD photos (Wikimedia Commons + Library of Congress + LoC Sanborn)
- Archival video (Internet Archive PD + copyrighted-but-transformative via `tools/clip_treatment/`)
- Free stock (Pexels + Pixabay)
- Music (`music_library/` + YouTube Audio Library + Free Music Archive)
- SFX (Freesound CC0/CC-BY)
- Procedural SVG (in-repo generation)
- Inworld TTS-2 Tyler (paid, ~$0.20)

---

## 2. Visual primitive catalog (the schema enum)

These map to compiler functions that emit deterministic HF HTML+GSAP. The animator agent chooses which to invoke; the compiler enforces parameter shape; the schema validates the storyboard before compile.

### 2.1 Map-bound primitives (rendered ON the basemap)

| Primitive | Origin | Params | Used for |
|---|---|---|---|
| `pin_drop` | Existing | `{anchor_id, color, ring_style, burst}` | Geographic event markers |
| `map_sprite` | Refs 2/3 | `{anchor_id, sprite_type: silhouette\|portrait_medallion\|chibi_NOT_for_noir, style}` | Named figures at their location |
| `migration_arrow` | Refs 2/3 | `{path: [latlon...], color, draw_duration, curve_intensity}` | Movement vectors, attack arrows, journey routes |
| `front_line_curve` | Ref 4 | `{anchors: [latlon...], dot_color, dot_count, reveal_direction}` | Tactical front lines, expansion fronts, epidemic boundaries |
| `glow_region` | Ref 2 | `{polygon_latlon, color, blur_radius, opacity}` | Non-territorial regions (nomadic peoples, ideology zones) |
| `territory_wash` | Refs 3/4 | `{polygon_latlon, color, opacity, blend_mode}` | Political control, sphere-of-influence |
| `trench_line` | Ref 4 | `{path: [latlon...], stroke_color, stroke_width, texture}` | Hand-painted period cartography lines |
| `concept_stamp` | Ref 3 | `{text, font, region_bbox, fade_in_ms, hold_ms}` | Thematic overlay typography ("FEUDAL SYSTEM", "MANIFEST DESTINY") |
| `label_cluster` | Ref 4 | `{anchors: [{latlon, text}], stagger_ms, layout: staircase\|radial}` | Narrated lists of nearby places ("three forts: A, B, C") |
| `time_stamp` | Refs 2/3 | `{year_or_range, format: blackletter\|art_deco\|period_appropriate}` | Year/era anchor on every map cue and dramatic scene |
| `weather_overlay` | New | `{kind: rain\|snow\|fog\|dust\|smoke, intensity}` | Atmospheric mood |
| `cloud_drift` | Ref 4 | `{opacity, drift_speed_px_per_s}` | Subtle map atmosphere |

### 2.2 Off-map primitives (full-frame or panel overlays)

| Primitive | Origin | Params | Used for |
|---|---|---|---|
| `story_dive` | Ref 1 | `{visual_path, hold_duration, ken_burns_intensity, frame_preset}` | Full-frame character/event illustration or photo |
| `panel_archival` | Refs 3/4 | `{photo_path, treatment: archive_period_film\|grade_cyan_orange\|...}` | PD photo with film-scratch/sepia/vignette |
| `clip_archival` | Refs 3/4 | `{clip_path, treatment, frame_id, audio_role}` | Transformative-use video clip with locked filter + approved frame |
| `character_card` | Refs 1/3 | `{portrait_path, name, dates, role, frame_style}` | Named-figure introduction |
| `document_overlay` | New (Sleep Network) | `{kind: telegram\|newspaper\|letter\|ledger, content, motion: scroll\|unfold\|fly_in}` | Period proof, primary source |
| `source_citation` | Ref 1 | `{citation_text, body_quote, position: lower_third}` | Primary-source quote overlay (Booth's "Sic semper tyrannis", etc.) |
| `concept_diagram` | Ref 2 | `{kind: timeline\|comparison\|stat_callout, data}` | Cartoon-panel framing device (the "Sharpie circle" pattern) |
| `etymology_card` | Ref 5 | `{phrase, modern_word, origin}` | "We still call this X today" micro-spike |

### 2.3 UI furniture (persists across scenes)

| Primitive | Origin | Persistence | Used for |
|---|---|---|---|
| `chapter_subject_badge` | Ref 1 | Top-left, swaps at chapter break | "Who is this chapter about" — never goes away |
| `chapter_timeline` | Ref 3 | Center top, active chapter highlighted | "Where in the master arc am I" |
| `year_card` | Ref 3 | Top-left or top-right, animates between scene years | "When am I" |
| `structure_tree` | Ref 1 | Shown only at chapter transitions | "How many remain" — fills in as chapters complete |
| `vignette_breath` | Multiple | Always-on | Subtle tension/calm contour |
| `paper_grain` / `film_grain` | Refs 2/4 | Always-on | Period texture |

### 2.4 Atmospheric primitives

| Primitive | Origin | Used for |
|---|---|---|
| `time_of_day` | New | dawn/noon/dusk/night tint pass |
| `idle_atmosphere` | New | dust/fireflies/embers/leaves drift |
| `parallax_layer` | Ref 4 | Subtle multi-plane depth |
| `atmospheric_breath` | Ref 3 | PD landscape painting palate cleanser between chapters |

### 2.5 Climax primitives

| Primitive | Origin | Used for |
|---|---|---|
| `flash_burst` | New | Gunshot freeze, flashbulb |
| `bullet_trail` | New | Animated SVG trajectory |
| `slow_zoom_terror` | New | Push into a face with vignette closing |
| `clock_freeze` | New | Time stops at exact moment |
| `mournful_hold` | New | 3–5s quiet beat |
| `dust_settle` | New | Particles fall after climax |

### 2.6 Transition primitives

| Primitive | Origin | Used for |
|---|---|---|
| `chapter_wipe` | New | Hard chapter break |
| `panel_to_pin_morph` | New | Story shrinks back into the pin |
| `basemap_swap` | New | Cascade zoom tier transition with anchored center |
| `time_shift` | New | Cross-decade transition with year sweep |
| `connection_line` | New | Draws between current pin and next |

---

## 3. Pacing target matrix

Three observed pacing profiles. Choice per project goes in `theme.pacing_target`.

| Profile | WPM | Sentence avg | Short-sentence % | Shot length | Source |
|---|---|---|---|---|---|
| **broadcast** | 115 | 17 words | <5% | 7s, continuous drift | Ref 4 (Epic History) |
| **cliffhanger** | 164 | 21 words | 5% (climaxes only) | 3.5s, brisk cuts | Ref 5 (Jesus) |
| **explainer** | 187 | 13 words | ~30% | 5.5s, varied | Refs 2/3 (Medieval Europes) |

**Hard rules across all profiles:**
- Long pauses (>1s) ONLY at chapter breaks (max 2–3 per video)
- ~25 capitalized proper-noun tokens per minute (the "texture of discovery")
- ≥1 concrete number per minute (never "many" when a number exists)
- Quoted dialogue 1 per ~2 minutes, used as climactic punctuation
- Anaphora at sentence-start AVOIDED (Ref 5 rule — vary openings)
- "But/Yet/However" is the standard rhetorical pivot (~14% of sentences)

**For Presidential Assassinations: cliffhanger profile (164 WPM, 21-word avg, short for landings).** Tyler "more creative" delivery renders this naturally; we tag emotion changes in markup, not speed.

---

## 4. Hook architecture (first 90s)

Two engine patterns, picked per project in `theme.hook_engine`:

### 4.1 Rolling payoff (enumerable-list briefs)

For "N things on a map" videos. Pattern (Ref 1 follow-up):

- **Sentence 1 (0:00–0:03):** Ostensive opener. *"This is [N] [things]."* OR *"It's [year], and [protagonist] is [doing X] here, in [place]."*
- **Sentence 2 (0:03–0:09):** Geographic-promise inventory. Name 3–4 places escalating in unfamiliarity (the surprise destinations earn the click).
- **Sentence 3 (0:09–0:15):** Triple-promise. *"...uncovering [X], their [Y], and how each [Z]."*
- **Sentence 4 (0:15–0:20):** **First concrete payoff lands.** The first named figure + their stake is on screen. No "stay with me" beg, no preamble.
- **Sentences 5+ (0:20+):** Rolling small payoffs every ~15s. Ordinal countdown structure ("first", "next", "then").

### 4.2 Deep mystery (narrative-arc briefs)

For single-narrative or character-deep-dive videos. Pattern (Ref 5):

- **Sentence 1 (0:00–0:05):** *"It's [year], and [protagonist] is [doing X] here, in [place]."*
- **Sentence 2 (0:08):** Open loop A. *"You've probably heard X — but most people get [details] WRONG."*
- **Sentence ~5 (0:55):** Open loop B nested inside A. *"...a [shocking thing] that will [strong consequence]."*
- **Sentence ~7 (1:12):** *"But before I share what it is, you first need to understand..."* — drop into context. Two loops now open simultaneously.
- **First major payoff:** ~5 min in.
- **Final payoff:** climax of video (16+ min later in Ref 5's case).

### 4.3 Cross-cutting hook rules (both engines)

- First sentence has a present-tense **diegetic pointer word**: "here", "this is", "look at". The map carries the demonstrative.
- **CTA welded to geography of final act.** Pick CTA placement based on where the final scene lands geographically, not on a fixed timestamp. The viewer never registers a section break.
- **Spine thread** planted in first 60s, called back in closing 60s. Mention it twice in between for closure.

**For Presidential Assassinations: rolling-payoff engine with one spine.** Spine: *"the next pin has not been drawn yet"* — planted in opener, paid off in closing.

---

## 5. Sound design defaults

(Layers onto the existing `sound_design_rules_locked` memory.)

### 5.1 Music

| Phase | Density | Mood |
|---|---|---|
| 0–10 min | Continuous orchestral underbed, never silent (Refs 1/3/4) | Score follows narrative arc — tense under conflict, hopeful under triumph |
| 10+ min | **Sparse + period-appropriate** (per existing memory) | NOT zero — fits scene's emotion, sometimes drops out for chapter cards |
| Chapter transitions | Brief swell or near-silence | Lets the chapter card land |

**Mix targets** (Ref 4):
- Integrated loudness: **-15 to -14 LUFS** (broadcast)
- LRA: **2–3 LU** (compressed; no auto-duck needed)
- VO sits naturally above score without ducking

### 5.2 SFX

| When | Density | Examples |
|---|---|---|
| Camera moves | Sparse | Low whoosh on pans, soft texture on zooms |
| Climaxes | Selective punctuation | Gunshot freeze, distant explosion, dramatic silence |
| Map cues | Cue-aligned | Arrow draw whoosh, pin drop thunk, label appear chime |
| 0–10 min | Dense for immersion | Layer ambient + accents |
| 10+ min | NEVER alarming (locked) | No sirens, booms, crashes, klaxons, explosions |
| Diegetic | When period-appropriate | Quill scratch, telegraph clicks, clock ticks |

### 5.3 Sound design red flags (from Ref 1's AI tells)

- **Wall-to-wall VO with zero pauses** = AI tell. Tyler should breathe between sentences (em-dashes do this).
- **Continuous music with no SFX punctuation** = lazy sound design. SFX scarcity is fine; SFX *absence* under a beheading scene is suspicious.
- **No variance between chapters** = template assembly tell. Each chapter's mood should sound distinct.

---

## 6. Channel-tone production tells (quality vs AI slop)

What the references taught us about how viewers detect slop:

### 6.1 Quality signals (steal these)

- **Persistent character badge** — viewer always knows the subject (Ref 1)
- **Year stamps on every map state** — viewer never wonders "when" (Refs 2/3)
- **One consistent illustrator's hand** across all assets (Ref 2) — for us, this means consistent procedural style + consistent archival treatment
- **Pacing discipline** — no filler shots, no "let me explain X again" repetition (Ref 2)
- **Period-authentic archival** that does heavy lifting (Ref 3 — manuscript illuminations, Bayeux Tapestry)
- **Curved labels that hug geography** (Refs 2/3) — not horizontal axis-aligned
- **Color contrast tactic varies per region** (light labels on dark land, dark labels on light water)
- **Continuous camera motion** even on holds (Ref 4) — 1–3% drift per second

### 6.2 Slop tells (avoid these)

- **Anachronisms in AI-generated illustrations** (Ref 1: St Peter's dome 1500 yrs early, Colosseum 15 yrs early, multi-mast galleon as Roman ship). Fix: use real PD archival, not AI illustration.
- **AI VO with no breath / no pause** (Ref 1: max 0.2s gap, LRA 2.4 — too consistent). Fix: Tyler creative + em-dashes for breath + `<break time="1000ms" />` after key beats.
- **AI character drift across shots** (Ref 1: Paul's face structure shifts between shots). Fix: PD photos are static; no drift possible.
- **Glassy AI eyes, painterly AI skin** (Ref 1). Fix: real photos.
- **Anaphora at sentence-start** (Ref 5 actively avoids). Fix: vary openings.
- **Wall-to-wall narration with no chapter breath** (Ref 1). Fix: long pauses at chapter breaks.
- **Cartoony chibi sprites in serious documentary** (Ref 2's pattern, wrong for noir). Fix: noir lithograph silhouettes for sprite work.
- **All territories same label color** (none of the refs make this mistake but it's a common Claude failure). Fix: per-region contrast tactic.

---

## 7. Per-reference one-line distillation

For quick lookup by future director skills:

- **Ref 1:** Map as 7% bookend; persistent character badge + structure tree are the brand. Steal structural primitives, reject AI execution.
- **Ref 2:** Static basemap + overlay choreography. Camera moves once in 4 min. Chibis are wrong for noir but the dual-vocabulary pattern (figures + glow regions) ports.
- **Ref 3:** Royal portraits at realm centroids + color-coded migration arrows + year card UI furniture + PD manuscript art for off-map dives.
- **Ref 4:** Painted-diorama vibe achievable via Carto+territory wash+trench lines. Front-line dot curves are a killer primitive. Continuous camera drift on every shot. 115 WPM broadcast pace.
- **Ref 5:** Hook = triple-nested cliffhanger for narrative-arc briefs. 164 WPM, 21-word avg, short sentences for emotional landings only. CTA welded to geography.
- **Ref 1 hook:** Ostensive opener + triple-promise + first payoff by 0:20 for enumerable-list briefs. Different engine from Ref 5 but same anchor primitive.

---

## 8. Theme.json schema (per-project posture)

Every video declares its posture in a single JSON document at project root. Director skills read this to know how to behave.

```jsonc
{
  "project_id": "presidential-assassinations-map",
  "video_title": "Every Presidential Assassination + Attempt on a Map",
  "target_duration_min": 20,

  "map_posture": "hybrid",                    // canvas | bookend | hybrid
  "camera_language": "static_with_accents",   // static_with_accents | continuous_drift
  "pacing_target": "cliffhanger",             // broadcast | cliffhanger | explainer
  "hook_engine": "rolling_payoff",            // rolling_payoff | deep_mystery

  "palette_master": {
    "basemap_filter": "noir",
    "primary_accent": "#c9a84c",              // brass
    "secondary_accent": "#b41e1e",            // classified red
    "ui_dark": "#0a0f1a",
    "ui_light": "#f5f0e4"
  },

  "palette_per_period": [
    { "year_range": [1830, 1869], "sub_theme": "frontier_ink", "accent_shifts": { "warm_tint": "#7a5a3a" } },
    { "year_range": [1870, 1899], "sub_theme": "daguerreotype", "accent_shifts": { "warm_tint": "#8a7a5a" } },
    { "year_range": [1900, 1929], "sub_theme": "art_nouveau", "accent_shifts": { "warm_tint": "#9a8a4a" } },
    { "year_range": [1930, 1959], "sub_theme": "art_deco", "accent_shifts": { "warm_tint": "#c9a84c" } },
    { "year_range": [1960, 1979], "sub_theme": "cold_war_technicolor", "accent_shifts": { "warm_tint": "#a04a4a" } },
    { "year_range": [1980, 1999], "sub_theme": "video_era", "accent_shifts": { "warm_tint": "#5a5a8a" } },
    { "year_range": [2000, 2026], "sub_theme": "phone_camera", "accent_shifts": { "warm_tint": "#7a8a8a" } }
  ],

  "typography": {
    "map_labels": { "family": "Cinzel", "weight": "bold", "transform": "uppercase" },
    "ui_chrome": { "family": "Cinzel", "weight": "bold" },
    "body_overlays": { "family": "Georgia", "weight": "regular", "style": "italic" },
    "year_stamp": { "family": "Cinzel", "weight": "black" },
    "source_citation": { "family": "Inter", "weight": "regular", "size": "small" }
  },

  "sprite_style": "noir_lithograph_silhouette",  // never chibi for noir; this is enum'd

  "voice_persona": {
    "provider": "inworld_tts_v2",
    "voice_id": "Tyler",
    "delivery_mode": "more_creative",
    "wpm_target": 164,
    "emotion_tag_frequency": "topic_pivots_only",
    "caps_emphasis": "climactic_words_only",
    "long_pause_style": "em_dash",
    "break_tags_after": "key_beats_and_chapter_ends"
  },

  "sound_design": {
    "music_density_0_10_min": "continuous_underbed",
    "music_density_10_plus_min": "sparse_period_appropriate",
    "loudness_target_lufs": -15,
    "lra_target_lu": 2.5,
    "sfx_alarming_after_10_min": false
  },

  "ui_furniture": [
    "chapter_subject_badge",
    "structure_tree",
    "year_card",
    "chapter_timeline",
    "vignette_breath"
  ],

  "spine_thread": {
    "planted_in_first_minute": "The next pin has not been drawn yet",
    "callback_in_closing": "And the map waits for the next entry"
  }
}
```

---

## 9. Specific guidance for the Presidential Assassinations test build

Synthesizing all of the above into per-stage direction for the test:

### 9.1 Structure (16 chapter segments)

Following Ref 1's compilation pattern + rolling-payoff hook engine:

```
Cold open  (0:00–0:45)  Trump 2024 — present-tense ostensive opener
Chapter 1  (0:45–2:00)  Jackson 1835     — first attempt
Chapter 2  (2:00–3:30)  Lincoln 1865     — first success, sets template
Chapter 3  (3:30–4:45)  Garfield 1881    — doctors killed him
Chapter 4  (4:45–5:45)  McKinley 1901    — white handkerchief gun
Chapter 5  (5:45–7:00)  T.Roosevelt 1912 — bullet in chest, kept speaking
Chapter 6  (7:00–8:15)  FDR 1933         — Cermak deflection
Chapter 7  (8:15–9:30)  Truman 1950      — Officer Coffelt
Chapter 8  (9:30–11:30) JFK 1963         — climax of first half, biggest chapter
Chapter 9  (11:30–13:00) RFK 1968        — pantry kitchen
Chapter 10 (13:00–14:30) Nixon/Ford/Carter — 4 attempts in 5 years
Chapter 11 (14:30–16:00) Reagan 1981     — inch from heart
Chapter 12 (16:00–17:15) Clinton/Bush/Obama — modern attempts
Chapter 13 (17:15–18:30) Trump 2024     — Butler PA, full callback
Closing    (18:30–20:00) "The next pin has not been drawn yet"
```

### 9.2 Hook (0:00–0:30)

Per rolling-payoff engine:

```
[curious] This is a map of every man who tried to KILL an American president.

There have been seventeen attempts — across nineteen states, two centuries,
and seven assassins who succeeded.

Some you remember.

Some — most people have never heard of.
<break time="1000ms" />

[suspenseful] And the next pin on this map — has not been drawn yet.
<break time="1000ms" />
```

(First named-figure payoff lands by 0:30 with cold-open dive into Butler PA 2024.)

### 9.3 Per-chapter phase structure

Each chapter uses the 8-phase template (per existing beat vocabulary):

1. **map_breath** (4–6s) — weather + time-of-day + year tick
2. **approach** (4–6s) — camera arrives at target_pin, date+city+venue overlay
3. **characters** (10–15s) — president card + attacker card + supporting figures
4. **story_dive** (20–30s) — full-frame archival panel sequence
5. **climax** (5–10s) — gunshot_freeze / bullet_trail / clock_freeze
6. **aftermath** (10–20s) — quote overlay + mournful_hold
7. **return_to_map** (5–8s) — panel_to_pin_morph + pin stamp
8. **transition** (3–5s) — year_ticker + structure_tree update

Per-phase animator agents (Tier 3) handle one phase each. 8 phases × 14 chapters = 112 animator agents.

### 9.4 Map tier usage per chapter

For each assassination, the camera works through tiers:

- **map_breath / approach:** continental (CONUS) → regional (state) — Carto Dark
- **characters:** off-map character cards
- **story_dive:** off-map panels OR urban tier (Dallas, DC) — Carto
- **climax:** scene tier (Dealey Plaza SVG, Ford's Theatre balcony floorplan) OR building tier — procedural / PD
- **aftermath:** off-map quote overlay
- **return_to_map:** zoom back out to continental, pin lands

### 9.5 UI furniture (always-on)

- **`chapter_subject_badge`** top-left: portrait of the president, swaps per chapter
- **`structure_tree`** shown only at chapter transitions: 17 portrait nodes, fills red as each completes
- **`year_card`** top-right: animates between chapter years
- **`chapter_timeline`** center-top hairline: 1830–2026 with current chapter highlighted

### 9.6 Spine thread

- Planted in opener: *"the next pin on this map has not been drawn yet"*
- Mentioned at Chapter 5 (TR) and Chapter 11 (Reagan) as breath beats
- Paid off in closing: ghost question-mark pin appears at an empty Northern Plains location while the year counter scrubs 2024 → "?"

### 9.7 Asset sourcing (all free)

- **Portraits** — Wikimedia + Library of Congress PD photos (autonomous via `lib/asset_sourcing/portraits.py`)
- **Archival video** — Internet Archive Universal Newsreels (Garfield-McKinley) + JFK/RFK/Reagan modern news (transformative-use via `tools/clip_treatment/`)
- **PD floorplans** — Ford's Theatre balcony layout (period diagrams), Hilton Hotel entrance, Texas School Book Depository — LoC + period building records
- **Stock B-roll** — Pexels for atmospheric establishers (rainy city, smoke, flags)
- **Music** — `music_library/` first, then YouTube Audio Library + Free Music Archive
- **SFX** — Freesound CC0 (gunshots distant, crowd murmur, period instruments)
- **Sprites/icons** — procedural SVG (theater, hotel, capitol, depository, hospital, gun, briefcase, etc.)

### 9.8 Estimated production cost

| Item | Cost |
|---|---|
| Inworld TTS-2 Tyler, ~3300 words | $0.20 |
| Everything else | $0.00 |
| **Total** | **~$0.20** |

---

## 10. What this design intel does NOT cover (deferred / future)

- **Real higher-zoom Carto tiles at z16+.** We stop at z15; below that we go procedural. If a future video needs photoreal street-level mapping, this is a gap.
- **Interactive maps.** This is one-shot rendered video.
- **Reference 3's real hook formula.** We never got the How So Medieval Europe 0:00–2:00 sample (URL mismatch). Two narrative-arc hook patterns (Ref 5 + the inferred Medieval) would have been better than one.
- **Engagement heatmap data for refs other than Ref 5.** Some pacing claims are structural reasoning, not heatmap-verified.
- **Per-channel persistent brand** (deferred per user — `theme.json` adapts to video, no persistent channel YAML).
- **3D-rendered map diorama.** Out of scope for HyperFrames runtime. We approximate with Carto + territory wash + trench lines.

---

*This document is canonical input to the pipeline. Update it as references are added or design choices change.*
