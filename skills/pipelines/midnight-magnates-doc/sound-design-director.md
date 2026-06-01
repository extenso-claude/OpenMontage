# Sound Design Director — Midnight Magnates

Post-render only. Adds music + SFX to the locked visual cut. This is the
**`sound_design`** stage of the `midnight-magnates-doc` pipeline; it produces
`artifacts/sound_design_report.json` and `requires_human_approval: false` (the
runner's gates decide "done", not the agent — see "Enforcement model" below).

The visual cut is already locked when you arrive here. You do NOT re-cut, re-time,
or re-color anything; you layer a music underbed + an SFX layer that hit the right
VO words and the right on-screen events, then mix to broadcast loudness.

## Read first

- `skills/core/sound-design-rules.md` — the LOCKED Sleep Network sound rules (these
  apply to Midnight Magnates verbatim):
  - **SFX SOURCING — two HARD RULES** (locked 2026-05-31): library-only + STOP-and-propose.
  - **Music density**: first ~10 min full density; after 10:00 **sparse + period-appropriate**
    (20–35% timeline coverage, NOT zero, NOT wall-to-wall).
  - **SFX never-alarming after 10:00**: no sirens / booms / crashes / klaxons / explosions /
    whip-cracks / sudden screams — suggestive sound only for dramatic events.
  - **Levels reference** (the broadcast-mix target — use this, not any external doc): VO
    -16 LUFS / -2 dB peak; music under VO -22 LUFS, between VO -16 LUFS; SFX immersive bed
    -24…-20 LUFS; SFX accent peak -16…-14; **after 10:00 SFX hard-capped at -20 LUFS peak**.
  - **Drift audit**: every music + SFX cue carries an `anchor_phrase` that resolves in Whisper;
    SFX drift budget ±0.15s, music ±0.5s, ambient bed ±2s.
  - **Cuelist shape** for music + SFX cues (the JSON every cue must follow).
- `lib/midnight_magnates/gates/qa_alarming_sfx.py`, `…/qa_sfx_audibility.py`,
  `…/qa_audio_drift.py`, `…/qa_sfx_event_sync.py` — the four blocking gates for this stage.
  Their code IS the contract for the cuelist you author (shapes/budgets below). Never cite a
  per-project `scripts/`-style QA path or re-implement these gates — run them through the runner only.

## Enforcement model (the runner decides "done", not you)

A deterministic runner — not the agent — shells the gates and writes the
machine-authored `artifacts/qa_report.json`. You never hand-author that report or
claim a gate passed. While iterating, run the stage's gates:

```bash
# the sound_design stage's blocking gates, in one call:
python3 -m lib.midnight_magnates.runner run-gates --pipeline midnight-magnates-doc --project <project_dir> --stage sound_design

# confirm the whole-build render-lock (all gates green AND inputs still fresh):
python3 -m lib.midnight_magnates.runner check-lock --pipeline midnight-magnates-doc --project <project_dir>
```

The runner runs the canonical `lib/midnight_magnates/gates/qa_*.py` modules and is
the source of truth. **NEVER** invoke a per-project `scripts/`-style QA path, and
**NEVER** invoke gates from any other channel's package (the `animated_history_map`
gate package is the WRONG package for this pipeline — every MM gate lives under
`lib/midnight_magnates/gates/`). To see the real gate set:
`ls lib/midnight_magnates/gates/qa_*.py`. The four that block THIS stage:

| Gate | What it enforces |
|---|---|
| `qa_alarming_sfx` | No alarming SFX (siren / boom / crash / klaxon / explosion / …) after 10:00. |
| `qa_sfx_audibility` | Every SFX is audible — ≥ -40 LUFS AND ≥ 3 LU above the VO+music bed (catches "too quiet to hear"). |
| `qa_audio_drift` | Each cue carries an `anchor_phrase` that resolves in Whisper; drift beyond budget (SFX 0.15s / music 0.5s / ambient 2s) fails. |
| `qa_sfx_event_sync` | Each impulsive SFX binds to its visual event via `event_cue_id`; SFX onset must land within 0.08s of the visual cue start. |

(Broadcast loudness on the final muxed master — integrated LUFS in [-17,-13],
true-peak ≤ -1.0 dBFS — is enforced by `qa_loudness` at the **final_render** stage,
not here. Mix toward it anyway; see the Levels reference.)

## HARD RULES

1. **SFX is LIBRARY-ONLY** (sound-design-rules HARD RULE 1). Every SFX placed in the
   video MUST come from the curated **Sleep Documentaries** SFX library on the shared
   Drive. No ad-hoc downloads dropped straight into the project, no SFX invented by a
   generation tool mid-edit, no "close enough" file from anywhere else. Search the
   library — the only sanctioned interface — via its `search_sfx.py`
   (CLAP semantic + metadata filters), per cue category (impacts, ambient/weather,
   period instruments, transitions, crowd/scene — all period-appropriate):
   ```bash
   python search_sfx.py --query "growing dread as the camera pans a dark forest"   # CLAP semantic
   python search_sfx.py --mood calm --category weather --loopable --json           # metadata filter
   ```
2. **MISSING SFX = STOP + PROPOSE** (sound-design-rules HARD RULE 2). The library is
   new and will frequently lack a needed sound. When it does, **do NOT substitute
   something close-enough and do NOT silently generate audio.** STOP and surface a
   **"Missing SFX" proposal**, then wait for the user. Two allowed proposal types:
   (A) free-SFX candidates downloaded for the user to review (Freesound CC0/CC-BY,
   etc.; capture license), or (B) an ElevenLabs sound-effects generation prompt +
   params for the user to approve. State, per missing sound: what's needed + for which
   moment + the proposal + cost + license. After approval the sound enters the library
   via the ONLY allowed path — `ingest_sfx.py` (Gemini 2.5 Pro tagging + loudness) →
   `normalize_sfx.py` (Strategy-B loudness if flagged) → `add_clap_embeddings.py` (CLAP
   embedding) — and is then reusable on every future video. **Music sourcing is
   unchanged** (these two rules govern SFX only; music candidates may be sourced free
   per step 3 of the workflow).
3. **Music: sparse + period-appropriate after 10:00, never wall-to-wall.** First ~10
   minutes = full density underbed. After 10:00 music returns only on scene change /
   location reveal / era anchor / pace shift, sized to ~20–35% of the timeline; period
   palette per scene (pre-1800 strings+harpsichord, WWI/WWII minor-key strings+muted
   brass, Cold War noir sax, modern synth pad+drone). NEVER continuous scoring after
   10:00, NEVER music that thickens when the VO turns emotional (the VO carries the
   emotion — music does not pile on), NEVER modern instrumentation under a pre-1900 scene.
4. **SFX never-alarming after 10:00.** After 10:00, SFX MUST be non-startling and
   hard-capped at **-20 LUFS peak**. FORBIDDEN: air-raid sirens, sudden booms /
   explosions, crashes (car / glass / gunshot), loud alarms / klaxons, whip-cracks /
   thunder-claps, sharp screams, sudden cymbal hits, modern phone / siren / horn,
   industrial machinery. For a dramatic event (a 1942 plane crash, a 1981 shooting) use
   **suggestive** sound — a slow plane drone fading, a single distant gunshot at -22
   LUFS with a reverb tail — never literal alarming sound. `qa_alarming_sfx` blocks the
   build if a banned category lands after 10:00.
5. **Every cue is Whisper-anchored (time AND space).** Every music and SFX cue MUST
   carry an `anchor_phrase` that fuzzy-matches a word in `artifacts/whisper/full.json`,
   plus explicit `t_in`/`t_out`. Music anchors to the FIRST WORD of the scene it
   supports with a 3s lead-in fade (music starts 3s before the anchor word); SFX anchors
   to the SPECIFIC WORD it punctuates (`t_in ≈ wordstart - 0.05s`). Drift budgets: SFX
   ±0.15s, music ±0.5s, ambient bed ±2s. An impulsive SFX that punctuates an on-screen
   event MUST ALSO carry `event_cue_id` (the visual cue it fires with) so `qa_sfx_event_sync`
   can confirm its onset lands within 0.08s of the visual cue start — a bang off its flash
   is a fail. A cue missing `anchor_phrase` cannot pass `qa_audio_drift`.
6. **You do not certify QA — the runner does.** Do not declare the sound stage done on
   your own say-so. It is done only when
   `run-gates … --stage sound_design` reports the four gates green and `check-lock`
   confirms the build is all-green and fresh. A green-looking `sound_design_report.json`
   over red gates still fails.

## Workflow

1. **Confirm the timing spine.** The voice stage already produced
   `artifacts/whisper/full.json` (word-level timestamps on the master VO clock). Every
   cue you place anchors against it — confirm it exists and has a non-empty `words[]`.
   (If you must regenerate Whisper and the model fetch fails with an SSL handshake error
   on this machine, run `pip install --user 'urllib3<2'` and retry — it looks like
   "no network" but isn't.)

2. **Mood-mapping agent** (one subagent): scans the locked render at 1Hz + reads the
   script with timestamps. Emits `artifacts/mood_timeline.json` — per-10s labels
   (somber / tense / mournful / urgent / quiet / climactic) tied to scene/era so the
   period palette (HARD RULE 3) and the never-alarming gate (HARD RULE 4) can be applied.

3. **Music curator subagent**: per mood label, source 4–6 candidates from
   `music_library/` + YouTube Audio Library + Free Music Archive + Pixabay — all free,
   each verified **CC0 / CC-BY** with attribution captured in
   `artifacts/audio_sources_v*.json`. Match the scene's period palette per HARD RULE 3.
   Save to `assets/music/candidates/<mood>_<n>.mp3`. (Music sourcing is free-source —
   the library-only rule is SFX-only.)

4. **SFX library search (HARD RULES 1 + 2 apply):**
   - **LIBRARY-ONLY:** every SFX placed in the video comes from the curated Sleep
     Documentaries SFX library; search it with its `search_sfx.py` per cue category
     (impacts, ambient/weather, period instruments, transitions, crowd/scene — all
     period-appropriate). No ad-hoc downloads, no mid-edit generation, no "close enough"
     file (HARD RULE 1).
   - **MISSING = STOP + PROPOSE:** when the library lacks a needed sound, STOP and
     surface the "Missing SFX" proposal (free candidates OR an ElevenLabs prompt) for the
     user — never substitute or silently generate. After approval, ingest into the
     library (`ingest_sfx.py` → `normalize_sfx.py` → `add_clap_embeddings.py`), then use
     it (HARD RULE 2).

5. **Ranking listener subagent**: head-to-head paired comparisons of music candidates
   against the VO at each cue point (tonal fit > density; no vocals, no modern EDM,
   period-appropriate). Top 3 mixes assembled.

6. **Human gate via local review tool**: top 3 mixes presented in A/B mode. User picks.

7. **Author the sound cuelist** (the JSON the gates read) and **compose with ffmpeg
   `amix`** to the Levels reference:
   - Music continuous 0–~10 min underbed (-22 LUFS under VO, -16 LUFS between VO);
     **sparse + period-appropriate after 10:00** (20–35% coverage), each cue with a 3s
     lead-in fade anchored to its scene's first word (HARD RULE 3 / 5).
   - SFX accents at climaxes (e.g. a single distant gunshot, a panel transition) — peak
     -16…-14 LUFS, ducking to -24 in ~0.8s; **library files only** (HARD RULE 1);
     impulsive SFX carry `event_cue_id` so onset binds to the visual event (HARD RULE 5).
   - SFX immersive bed -24…-20 LUFS for world-building (footsteps on stone, quill on
     parchment, distant crowd murmur, surf, telegraph clatter).
   - **After 10:00**: no alarming SFX, hard cap -20 LUFS peak (HARD RULE 4).
   - Mix toward integrated -16 LUFS / true-peak ≤ -1.0 dBFS (the final-render
     `qa_loudness` gate enforces [-17,-13] LUFS on the muxed master).

8. **Run the stage gates via the runner until green** (HARD RULE 6):
   ```bash
   python3 -m lib.midnight_magnates.runner run-gates --pipeline midnight-magnates-doc --project <project_dir> --stage sound_design
   ```
   - `qa_alarming_sfx` red → a banned-category SFX lands after 10:00; replace it with a
     suggestive, non-startling cue (HARD RULE 4).
   - `qa_sfx_audibility` red → an SFX is below -40 LUFS or buried < 3 LU under the
     VO+music bed; lift it or thin the bed under it.
   - `qa_audio_drift` red → a cue is missing `anchor_phrase` or drifts beyond budget
     (SFX 0.15s / music 0.5s / ambient 2s); add/fix the anchor or re-time the cue.
   - `qa_sfx_event_sync` red → an impulsive SFX's onset is > 0.08s off its visual event,
     or it's missing `event_cue_id`; bind it and nudge the transient onto the cue start.

   Then confirm the whole build with `check-lock` (all-green AND fresh). The stage is
   done only when the runner says so.

## Outputs

- `assets/audio/sfx_mix.wav`
- `assets/audio/music_mix.wav`
- `artifacts/audio_sources_v*.json` — free-music attribution / license capture.
- `artifacts/sound_design_report.json` — the `sound_design_report` artifact (with the
  music + SFX cuelist; every cue carries `anchor_phrase`, and impulsive SFX carry
  `event_cue_id`).
