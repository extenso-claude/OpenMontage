# Sound Design Director — Animated History Map

Post-render only. Adds music + SFX to the locked visual cut.

## Read first

- `skills/core/sound-design-rules.md` — first-10-min dense, after-10-min sparse + period-appropriate + never-alarming
- `docs/animated-history-map-design-intel.md` §5 — broadcast mix target -15 LUFS, LRA 2.5, no auto-duck

## Workflow

1. **Run Whisper** on the locked render's audio for word-level timestamps.

2. **Mood-mapping agent** (one subagent): scans the visual at 1Hz + reads script with timestamps. Emits `artifacts/mood_timeline.json` — per-10s labels (somber / tense / mournful / urgent / quiet / climactic).

3. **Music curator subagent**: per mood label, source 4–6 candidates from `music_library/` + YouTube Audio Library + Free Music Archive. All free. Save to `assets/music/candidates/<mood>_<n>.mp3`.

4. **SFX hunter swarm (5 parallel by category)**:
   - Gunshots / impacts (Freesound CC0)
   - Ambient weather (rain, wind, crowd)
   - Period instruments (telegraph, telephone, train, sirens-pre-1900-only)
   - Transitions (whoosh, paper rustle, pin drop)
   - Crowd / scene (period-appropriate)

5. **Ranking listener subagent**: head-to-head paired comparisons of music candidates against the VO at each cue point. Top 3 mixes submitted.

6. **Human gate via local review tool**: top 3 mixes presented in A/B mode. User picks.

7. **Compose with ffmpeg `amix`**:
   - Music continuous 0–10 min underbed, sparse after 10 min
   - SFX accents at climaxes (gunshot freeze, panel transitions)
   - Loudnorm to -15 LUFS, LRA 2.5
   - No alarming SFX after 10:00 (sirens, klaxons, explosions banned)

8. **Drift audit** — run `qa_audio_drift.py` to verify every cue (SFX accent ±150ms, music swell ±500ms).

## Output

- `assets/audio/sfx_mix.wav`
- `assets/audio/music_mix.wav`
- `artifacts/sound_design_report.json`
