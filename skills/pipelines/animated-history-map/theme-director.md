# Theme Director — Animated History Map

Author `artifacts/theme.json` per the project's brief + the design intel doc.

## Read first

- `docs/animated-history-map-design-intel.md` §1 (architectural decisions) + §8 (theme schema example)
- `schemas/artifacts/animated_history_map_theme.schema.json`

## Workflow

1. **Read the research brief.** What year-ranges does the video cover? What tone? What hook engine fits?

2. **Pick the four postures:**
   - `map_posture`: canvas / bookend / hybrid (per §1.1)
   - `camera_language`: static_with_accents / continuous_drift (per §1.2)
   - `pacing_target`: broadcast / cliffhanger / explainer (per §3)
   - `hook_engine`: rolling_payoff / deep_mystery (per §4)

3. **Master palette + per-period sub-themes — VIDEO-SPECIFIC.** Derive the palette from the video's SUBJECT / TIME PERIOD / CULTURE — never a fixed default. **`noir` is for the Midnight Magnates channel ONLY; do NOT use it here.** History-map videos use a legible, period-appropriate base (e.g. aged-parchment antique map for 19th-c. American history) with per-era accents. If the video spans multiple decades, define `palette_per_period` with sub-themes that shift accent colors while keeping the legible base + UI consistent. (Ref: memory video-specific-coloring.)

4. **Typography.** Map labels need a serif that survives noir filter (Cinzel works well). UI chrome should be the same serif family. Body overlays use a contrast serif (Georgia italic). Year stamps need a heavier weight.

5. **Voice persona.** For Sleep Network channels: Inworld Tyler, more_creative, ~164 WPM, emotion tags only at topic pivots, CAPS for climactic words, em-dash for long pauses, `<break time="1000ms" />` after key beats and chapter ends.

6. **Sound design defaults.** Per §5: -15 LUFS broadcast mix, LRA 2.5, first 10 min continuous underbed, after 10 min sparse + period-appropriate + never alarming.

7. **UI furniture list.** Pick from: `chapter_subject_badge`, `structure_tree`, `year_card`, `chapter_timeline`, `vignette_breath`, `paper_grain`, `film_grain`.

8. **Spine thread.** One single planted-and-paid-off line that braces the video.

## Quality bar

- All required fields present per schema
- `palette_per_period` covers every year range mentioned in the research brief
- `voice_persona.wpm_target` matches the `pacing_target`
- Spine thread has explicit plant + callback lines

## Output

Single file `artifacts/theme.json`. No human checkpoint at this stage by default — gate-validated. Skip to script stage on validation pass.
