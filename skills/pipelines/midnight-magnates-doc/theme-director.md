# Theme Director — Midnight Magnates

Author `artifacts/theme.json` — the per-project theme that adapts the **noir channel look** and the
voice persona to *this* video's subject, era(s), and culture. The theme is the first creative
artifact downstream stages read: the script, geography, storyboard, and every render inherits the
palette + typography + posture you set here.

The channel look is FIXED (noir — see HARD RULES). What is **per-video** is the *coloring inside the
noir frame*: a Civil-War parchment-and-iron accent set reads differently from a Prohibition smoke-and-
brass set, but both sit on the same noir basemap, the same moonlit flat-segmented idiom. You pick the
era-specific accents; you do NOT pick the channel look.

## Read first

- `[[midnight_magnates_style_locked_v2]]` (memory) — the LOCKED channel look:
  `"night colors, noir atmosphere, moonlit, flat segmented color illustration"`. This is the
  `palette_master.basemap_filter = "noir"` lock, not a suggestion.
- `[[feedback_mm_noir_look_vs_grades]]` (memory) — noir is the HyperFrames-generated **scene look**;
  it is NOT Recraft and it is NOT the clip grades. (HARD RULE 1.)
- `[[video_specific_coloring]]` (memory) — the palette *derives from each video's subject/era/culture*
  (parchment + iron for a Civil-War story; smoke + brass for a 1920s story). Noir is constant; the
  accents are not.
- `schemas/artifacts/midnight_magnates_theme.schema.json` — the contract. `basemap_filter` is an enum
  of exactly `["noir"]`; warm / illuminated / light_minimal basemaps are **rejected by the schema**.
  Read the `required` list and the `voice_persona` / `palette_per_period` shapes before authoring.

## Manifest contract (pipeline_defs/midnight-magnates-doc.yaml, stage `theme`)

- **produces:** `theme` → `artifacts/theme.json`
- **requires_human_approval:** `false` — there is no human checkpoint at this stage. It is
  gate-validated: the build advances to the script stage on schema-validation pass.
- **hard_gates:** none wired on the `theme` stage itself today (the manifest carries a TODO to add a
  `qa_schema_validate` theme check). Until that lands, theme.json is schema-checked downstream by
  `qa_schema_validate` (the validate stage validates theme/geography/canonical_names/storyboard
  against their registered schemas). So: an invalid theme does NOT silently pass — it surfaces at the
  validate gate. Author to the schema exactly.

## Enforcement model (the runner decides "done", not you)

A deterministic runner — not the agent — shells the gates and writes the machine-authored
`artifacts/qa_report.json`. You never hand-author that report or claim a stage passed. To check your
theme against the gates that touch it, run the runner. Run gates ONLY through the runner shown below —
never invoke a gate by a project-local `scripts/` file path, and never use the wrong gate package
(the gates live under `lib.midnight_magnates.gates`, NOT under any `animated_history_map` package):

```bash
# run the theme stage's gates (today: none on the stage; the schema check lands at validate):
python3 -m lib.midnight_magnates.runner run-gates --pipeline midnight-magnates-doc --project <project_dir> --stage theme

# confirm the run-lock state at any point:
python3 -m lib.midnight_magnates.runner check-lock --pipeline midnight-magnates-doc --project <project_dir>
```

Read `artifacts/qa_report.json` for the verdict. If you ever name a specific gate, it MUST exist as
`lib/midnight_magnates/gates/<name>.py` — run `ls lib/midnight_magnates/gates/qa_*.py` to see the
real set. Prefer "run the runner, read qa_report.json" over enumerating gate names.

## HARD RULES

These are the channel identity. They are non-skippable. Do not drift, reinterpret, or "improve" them.

1. **NOIR IS THE REQUIRED CHANNEL LOOK — `basemap_filter` is LOCKED to `"noir"`.**
   Every Midnight Magnates video uses the noir look:
   `"night colors, noir atmosphere, moonlit, flat segmented color illustration"`. The theme schema
   ENFORCES this — `palette_master.basemap_filter` is an enum of exactly `["noir"]`; warm,
   illuminated, and light_minimal basemaps are **rejected**. Do NOT author a warm/parchment/daylight
   basemap, and do NOT treat noir as "for another channel." It is THIS channel's mandatory look.
   - Noir is the look of the **HyperFrames-generated scenes** (flat-segmented, moonlit, chiaroscuro).
     It is NOT a Recraft style and it is NOT a clip grade.
   - The clip grades (`grade_cyan_orange` / `grade_crushed_warm` / `pitch_up_1st`) transform
     THIRD-PARTY COPYRIGHTED assets *away from copyright* — they are a legal treatment on borrowed
     footage/images/audio, NOT the channel style. Never confuse a clip grade with the noir look, and
     never set the theme's look from a grade. (memory `feedback_mm_noir_look_vs_grades`,
     `midnight_magnates_style_locked_v2`.)

2. **THE PALETTE IS PER-VIDEO; THE LOOK IS NOT.** Derive `palette_master` accents +
   `palette_per_period` from the video's SUBJECT / TIME PERIOD / CULTURE — never a fixed default and
   never a hardcoded channel palette. A Civil-War story gets aged-iron + parchment-ash accents on the
   noir base; a 1920s story gets brass + smoke; a Cold-War story gets steel + amber. The noir basemap
   stays constant across all of them; only the accents, sub-themes, and region colors shift. If the
   video spans multiple eras, define `palette_per_period` with one sub-theme per `year_range`,
   shifting `accent_shifts` (and `region_colors` where relevant) while keeping the noir base + UI
   chrome consistent. Cover EVERY year range the research brief mentions. (memory
   `video_specific_coloring`.)

3. **MAPS ARE NOT CENTRAL — author postures in SHOT-SCALE terms.** Midnight Magnates is a
   documentary channel, not a map channel. Most visuals are **medium** (the scene where the action
   happens) and **micro** (a close-up on a face / object / document); **macro** is the occasional
   establishing wide (which *may* be a map, an aerial, or a wide noir scene — a map is one option for
   macro, never the default canvas). The storyboard expresses this per-beat via `shot_scale`
   (macro|medium|micro). Your theme's two posture fields are still **required by the schema** — set
   them, but interpret them through the shot-scale lens, NOT as a map-stays-on-screen menu:
   - `map_posture` ∈ `{canvas, bookend, hybrid}` — for MM this declares *how much* a map appears at
     all. Default to **`bookend`** (a map opens/closes or punctuates, the body of the video lives in
     medium+micro scenes) or **`hybrid`** (a map recurs as supporting evidence between scenes). Choose
     `canvas` (map persistently on screen) ONLY for a genuinely cartographic story, and even then most
     beats still cut to medium/micro faces and documents over it. A map is supporting evidence, never
     the assumed background.
   - `camera_language` ∈ `{static_with_accents, continuous_drift}` — how the frame moves: held shots
     with motion accents, or a slow continuous drift. Pick per the video's pacing, not per "the map."

4. **EMOTIONAL BEATS USE HUMAN FACES — and AI image generation is locked to Nano Banana.** The theme
   doesn't place faces (the storyboard does, via `emotion_face`), but the look you set must support
   them: medium/close-up human faces carry the emotional beats, **real still or clip FIRST**, and only
   if no real source exists, **Nano Banana** under the per-video generation cap. Recraft / Flux /
   Imagen / DALL·E are FORBIDDEN as image generators on this channel — Nano Banana is the ONLY allowed
   AI image generator. Keep this in mind when choosing `sprite_style`: the noir sprite option
   (`noir_lithograph_silhouette`) keeps stylized figures consistent with the channel; faces are not
   sprites and are not Recraft.

5. **THE BRAND THROUGH-LINE IS AGENT-SELECTED PER VIDEO — never hardcode a presidents/pins spine.**
   Every MM video has ONE recurring through-line it returns to at every chapter close (a recurring
   `map` of pins, a recurring `case_file` panel, a recurring `timeline`, a recurring
   `cast_of_players` board, or `other`). It is DECLARED in the **storyboard** (`through_line`) and
   ENFORCED by `qa_spine_consistency` (presence + identical type/primitive + consistency-key
   stability across chapters). The theme's `spine_thread` (`planted_in_first_minute` /
   `callback_in_closing`) is the *narrative* plant-and-payoff line that braces the video — author it
   so it sets up whatever through-line the storyboard will return to. Do NOT bake a fixed
   presidents/all-presidents-pins spine into the theme; the through-line is per-video and chosen
   downstream.

6. **PERFECT TIME + SPACE SYNCHRONY is the channel's quality floor.** Every downstream visual /
   overlay / animation / SFX must hit the right VO word (its `anchor_phrase`, resolved against the
   Whisper spine) AND the right action location (its `spatial_target`). The theme can't author beats,
   but the choices you make here either help or hurt sync: a `voice_persona.wpm_target` that matches
   the `pacing_target`, an `emotion_tag_frequency` only at topic pivots, and `break_tags_after` at key
   beats give the storyboard clean anchor points. Set the persona so the timing spine the downstream
   stages build is steady and the anchors land. (memory `feedback_perfect_synchrony_required`.)

## Workflow

1. **Read the research brief.** What year-range(s) does the video cover? What subject / culture /
   era? What tone? Which `hook_engine` fits — `rolling_payoff` (recurring small reveals) or
   `deep_mystery` (one big question held open)? What `pacing_target` — `broadcast`, `cliffhanger`, or
   `explainer`?

2. **Set the postures (in shot-scale terms — HARD RULE 3):**
   - `map_posture`: `bookend` (default) / `hybrid` / `canvas` (cartographic stories only).
   - `camera_language`: `static_with_accents` / `continuous_drift`.
   - `pacing_target`: `broadcast` / `cliffhanger` / `explainer`.
   - `hook_engine`: `rolling_payoff` / `deep_mystery`.

3. **Author `palette_master` on the LOCKED noir base (HARD RULE 1 + 2).**
   - `basemap_filter`: **`"noir"`** — the only legal value; the schema rejects anything else.
   - `primary_accent`, `secondary_accent`, `ui_dark`, `ui_light`: hex colors DERIVED from this
     video's era/subject (parchment-ash + aged-iron for Civil War; smoke + brass for the 1920s; etc.).
     Keep them readable against the noir base.

4. **Per-period sub-themes (`palette_per_period`) — if the video spans multiple eras (HARD RULE 2).**
   One object per `year_range`, each with a `sub_theme` name + `accent_shifts` (and `region_colors`
   when geography differs by era). Cover EVERY year range the research brief mentions. Keep the noir
   base + UI chrome consistent across periods; only accents shift.

5. **Typography.** Map labels + UI chrome want a serif that survives the noir filter (Cinzel reads
   well); use the same serif family for UI chrome. Body overlays use a contrast serif (Georgia italic
   works). Year stamps want a heavier weight. Fill the `typography.*` font_specs
   (`family`/`weight`/`style`/`transform`) the schema defines.

6. **`sprite_style` (optional).** For the noir channel, prefer `noir_lithograph_silhouette` (stylized
   figures that stay consistent with the moonlit flat-segmented look). The other enum values exist for
   non-MM use — do not pick a warm/illuminated sprite style that fights the noir look.

7. **Voice persona (HARD RULE 6).** Fill `voice_persona`: `provider: "inworld_tts_v2"`, the
   project's `voice_id`, `delivery_mode` (typically `more_creative` for Sleep Network), and a
   `wpm_target` that MATCHES the `pacing_target`. Set `emotion_tag_frequency: topic_pivots_only`,
   `caps_emphasis: climactic_words_only`, `long_pause_style: em_dash`, and
   `break_tags_after: key_beats_and_chapter_ends`. (NOTE: on MM-maps the VO is **user-provided
   finished audio** — the voice stage *ingests + transcribes*, it does not run Inworld. This persona
   block is the schema-required spec the script stage reads for markup craft and the voice stage reads
   for its compatibility ledger; it does not itself trigger generation.)

8. **Sound-design defaults (optional `sound_design` block).** Mirror the channel's locked policy:
   `music_density_0_10_min: continuous_underbed`, `music_density_10_plus_min:
   sparse_period_appropriate`, `loudness_target_lufs` ≈ -15-(-16), an `lra_target_lu`, and
   `sfx_alarming_after_10_min: false`. (The sound-design stage enforces this; the theme just records
   the intent.)

9. **UI furniture (optional `ui_furniture`).** Pick the recurring chrome the video uses, e.g.
   `chapter_subject_badge`, `structure_tree`, `year_card`, `chapter_timeline`, `vignette_breath`,
   `paper_grain`, `film_grain`.

10. **Spine thread (`spine_thread`) — the narrative plant + payoff (HARD RULE 5).** Write
    `planted_in_first_minute` and `callback_in_closing` so they brace the video and set up whatever
    through-line the storyboard will declare and return to. Do NOT hardcode a presidents/pins spine —
    the recurring artifact is chosen per video downstream.

## Quality bar

- All schema-`required` fields present (`project_id`, `video_title`, `target_duration_min`,
  `map_posture`, `camera_language`, `pacing_target`, `hook_engine`, `palette_master`, `typography`,
  `voice_persona`) and the whole file validates against the schema.
- `palette_master.basemap_filter == "noir"` (the only legal value — HARD RULE 1).
- `palette_master` accents are DERIVED from the video's era/subject, not a fixed default (HARD RULE 2).
- `palette_per_period` (when present) covers EVERY year range the research brief mentions.
- `voice_persona.wpm_target` matches the `pacing_target`.
- `spine_thread` has an explicit plant + callback, and does NOT hardcode a presidents/pins spine
  (HARD RULE 5).

## Output

Single file `artifacts/theme.json`. No human checkpoint at this stage by default — it is
schema/gate-validated downstream. Proceed to the script stage on a clean validate.
