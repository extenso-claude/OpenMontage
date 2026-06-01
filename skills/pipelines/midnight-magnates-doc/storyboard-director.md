# Storyboard Director — Midnight Magnates

This is the **most important authoring stage** in the pipeline. Per chapter you emit one
schema-valid `artifacts/storyboard/storyboard_<chapter_id>.json`. You orchestrate; the real
per-beat authoring is dispatched to one **Scene Director subagent per chapter, in parallel**.

A Midnight Magnates storyboard is NOT a map walkthrough. It is a noir documentary told in
**shots** — most of them medium scenes and close-ups of faces, objects, and documents — that
**return to one recurring brand through-line** the agent chooses per video. Maps are supporting
evidence used by a minority of beats, never the default canvas.

The storyboard is the spec the animator agents build from. Every beat must (a) pick its
**shot scale** and **render mode (2D/3D)**, (b) hit the right narrated word **and** the right
on-screen location (perfect time + space synchrony), and (c) for the minority of beats that
carry it, advance the chosen through-line. The gate runner — not you — decides when a chapter is
done.

## Read first

- `schemas/artifacts/midnight_magnates_storyboard.schema.json` — the artifact contract. Every
  field below (`through_line`, `shot_scale`, `animation_tier`, `emotion_face`, `spatial_target`,
  `start_anchor`/`end_anchor`) is defined there; the `layer_action.primitive` enum is the only
  legal primitive set. Read it before authoring anything.
- `lib/midnight_magnates/vocab.py` — the primitive catalog and its families (a verbatim mirror
  of the schema enum, plus `FACE_PRIMS`, the off-map visual set, chrome vs event-FX kinds). Use
  it to pick primitives and to know which family a beat satisfies.
- `artifacts/whisper/full.json` — **the master timing spine** (word-level timestamps on one
  continuous master clock, built by the voice stage). Every beat's `start_anchor.phrase` /
  `end_anchor.phrase` MUST be an exact contiguous run of words from this file. This is the
  single source of timing truth; there is no other clock.
- `artifacts/script.json` — the locked narration (what the chapter says, in order).
- `artifacts/research_brief.json` (or the research stage's artifact) — the source you mine to
  CHOOSE the through-line type and to know which figures get emotional close-ups.
- `artifacts/theme.json` — channel posture, camera language, UI furniture, palette. The noir
  look is locked here (HARD RULE 1).
- `artifacts/canonical_names.json` — the per-video figure/place dictionary. `emotion_face.subject_id`
  and any character reference must be an `id` from this file.
- `artifacts/geography.json` — anchor IDs. Read this **only** for the minority of beats that use
  a real map/aerial; a no-map chapter never touches it.
- `skills/core/overlay-positioning-rules.md` and `skills/core/clip-treatments.md` for placement
  and third-party-material craft when a beat uses an archival panel/clip.

## Manifest contract (`pipeline_defs/midnight-magnates-doc.yaml`, stage `storyboard`)

- **produces:** `storyboard` → `artifacts/storyboard/*.json` (one file per chapter).
- **requires_human_approval: true** → **G2** (approve storyboard + assets).
- **hard_gates (all block):** `qa_continuity`, `qa_drift`, `qa_render_directive`,
  `qa_beat_visual_coverage`, `qa_migration_icon`, `qa_spine_consistency`, `qa_spatial_anchor`,
  `qa_emotion_face_coverage`. (Run the runner — next section — to exercise them; do not invoke
  individual gate files by hand or hand-certify any of them.)
- **review_focus:** `binding_vs_intent_fields_present`, `phase_state_contract_per_phase_boundary`.

## Enforcement model (the runner decides "done", not you)

A deterministic runner — not the agent — shells the gates and writes the machine-authored
`artifacts/qa_report.json`. You never hand-author that report, never cite a `scripts/qa_*.py`
path, and never claim a gate passed. Run the gates **through the runner** and read the report:

```bash
# run every storyboard-stage hard gate, then read artifacts/qa_report.json:
python3 -m lib.midnight_magnates.runner run-gates --pipeline midnight-magnates-doc --project <project_dir> --stage storyboard

# the gates + the G2 human-approval check, in one call:
python3 -m lib.midnight_magnates.runner run-stage  --pipeline midnight-magnates-doc --project <project_dir> --stage storyboard

# confirm the render-lock view (all-green + fresh inputs):
python3 -m lib.midnight_magnates.runner check-lock  --pipeline midnight-magnates-doc --project <project_dir>
```

Iterate with `run-gates` until `artifacts/qa_report.json` is all-green, then collect G2 with
`run-stage`. A chapter is done only when the runner says so. If you ever need the exact set of
gates that exist, run `ls lib/midnight_magnates/gates/qa_*.py` — never assume a gate name.

## HARD RULES

These are the channel identity. Author them into every chapter; an agent that drifts from them
ships the wrong channel.

1. **NOIR LOOK = HyperFrames-generated, flat-segmented noir scenes.** The channel style is
   `"night colors, noir atmosphere, moonlit, flat segmented color illustration"`, authored as
   HyperFrames/GSAP scenes (and bird's-eye dioramas for 3D), driven by `theme.json`. It is
   **NOT** Recraft/Flux/Imagen/DALLE, and it is **NOT** the clip grades. Clip grades
   (`grade_cyan_orange` for video, `grade_crushed_warm` for images, `pitch_up_1st` for kept clip
   audio) exist ONLY to transform third-party COPYRIGHT material away from copyright — they are a
   sourcing/legal treatment, never the channel look. Never describe the noir look as "a grade."
   Author beats so the look comes from the scene, not from a filter on someone else's footage.

2. **2D and 3D are CO-EQUAL render modes, chosen per shot via `animation_tier`.**
   - `animation_tier: "2d"` = a flat-segmented noir scene (HyperFrames/GSAP) — the chiaroscuro /
     ledger / silhouette idiom. Best for medium scenes, document/object focus, and most faces.
   - `animation_tier: "3d"` = a bird's-eye **diorama** (the cel-shaded set). Best when geography,
     troop/crowd movement, or built-environment scale carries the beat.
   Pick **best fit per shot** — not all-3D, not all-2D. `animation_tier` MUST be resolved on every
   hero beat and every medium-scale scene (it is what the Render Directive briefs the animator to
   build). A medium-scale scene with no `animation_tier` is "not yet chosen" and will block at
   `qa_render_directive`. (3D is no longer the automatic "hero" trigger — the hero is the
   `shot_scale` + `animation_tier` choice, RULE 3.)

3. **Maps are NOT central. The three tiers are SHOT SCALE (map-OPTIONAL), declared per beat via
   `shot_scale`:**
   - `macro` = the establishing shot. **May** be a map or aerial, but is just as often a wide
     noir scene (a city skyline at night, a harbor, a boardroom from the back).
   - `medium` = the scene where the action happens (the room, the alley, the deck). This is the
     workhorse — most beats live here.
   - `micro` = a close-up on a single face, object, or document.
   Most MM visuals are **medium + micro**. Reach for a real map only when geography is genuinely
   the evidence; then (and only then) fill the chapter's `geography` block and use
   `anchor_id`-targeted map primitives. For everything else use the `setting` block
   (`location_name`, `set_dressing`, `scene_anchors[]`) so off-map cues still have named regions
   to target. Do NOT default any chapter to a basemap; a no-map chapter omits `geography`
   entirely. There is **no presidents/all-pins default canvas** — see RULE 5.

4. **EMOTIONAL beats use medium/close-up human FACES, declared via `emotion_face`.** When a beat
   is emotional (grief, fear, triumph, betrayal, a confession, a death), author it as a face:
   set `emotion_face: { source, subject_id, … }` AND include a **face primitive** in `layers[]`
   (`face_closeup` / `face_medium` / `face_reaction` / `reaction_cut` — see `vocab.FACE_PRIMS`).
   - `source` precedence: **real `still` or `clip` FIRST**, else `nano_banana` (the ONLY allowed
     AI image generator, under the per-video cap). Recraft / Flux / Imagen / DALLE are
     **FORBIDDEN** for faces or anything else.
   - `subject_id` references `canonical_names.json` `people[].id`.
   The schema **requires** a face primitive whenever `emotion_face` is present, and
   `qa_emotion_face_coverage` blocks an emotional beat that resolves to a non-face shot. Do not
   put an emotional line over a wide map or a document — put it on the person's face.

5. **The brand THROUGH-LINE is AGENT-SELECTED per video — NEVER a hardcoded presidents/all-pins
   spine.** From research, the orchestrator PICKS one recurring device this video returns to at
   every chapter close, and DECLARES it at the top of every chapter storyboard in the top-level
   `through_line` object:

   ```jsonc
   "through_line": {
     "type": "case_file",                 // map | case_file | timeline | cast_of_players | other
     "primitive": "spine_panel",          // MUST be a member of the layer_action primitive enum
     "close_phase_kinds": ["return_to_map", "chapter_outro"],  // phases that count as a "close"
     "consistency_keys": ["params.dossier_order", "params.subject_slots"], // must match across chapters
     "label": "The dossier grows one name per chapter"
   }
   ```

   - Choose the `type` from the story's spine: a `map` (only if geography is the spine — not the
     default), a `case_file` / dossier, a `timeline` rail, a `cast_of_players` board, or `other`.
   - `primitive` must be a real primitive (commonly `spine_panel`; or a `timeline`/board rendered
     via the appropriate primitive). At each chapter close (the `close_phase_kinds` phases —
     typically a `return_to_map` or `chapter_outro` phase) emit a beat that advances the
     through-line (reveals the new name, lights the new timeline node, adds the new dossier card)
     while keeping prior state intact.
   - `consistency_keys` are the param paths that MUST stay identical across chapters (roster +
     positions for a board; row order for a timeline). `qa_spine_consistency` enforces that every
     chapter declares the through-line, that a close-phase beat carries it, and that those keys do
     NOT drift between chapters. Declare the SAME `through_line` (same `type`/`primitive`/keys) in
     every chapter of the video.
   - **Never** invent a presidents map or an all-pins canvas as the spine. The through-line is
     whatever the research says this story keeps returning to.

6. **PERFECT TIME + SPACE SYNCHRONY — every beat carries explicit time anchors AND a spatial
   target.**
   - **Time:** every beat has `start_anchor` and `end_anchor`, each an exact contiguous phrase
     from `artifacts/whisper/full.json` (use `occurrence_index` / `near_s` to disambiguate a
     repeated phrase; the silent "first match" binding is banned). A NOT_FOUND anchor is a hard
     fail at `qa_drift`. For a beat whose actions fire at different narrated moments, give the
     later `layer_action` its own `cue_anchor` and set `time_distinct: true` so each action lands
     on its own word.
   - **Space:** every visible non-chrome action cue declares a resolvable `spatial_target`
     (exactly one of `anchor_id` for a map pixel / `region_id` for a named region in the shot's
     `scene_anchors` or `setting.scene_anchors` / `target_px` for an authored pixel). A flash, a
     reaction, an arrow must sit ON the thing the narration names — a cue over empty frame fails
     `qa_spatial_anchor`. Mark genuinely action-independent UI (year card, badge, citation) as
     `placement: "chrome"` so it is exempt; everything else is `on_action` and needs a target.
   - This is the channel's hardest requirement: the right word AND the right place, every cue.

## Workflow

### 1. As orchestrator, choose the through-line and write the showrunner contract

Before dispatching subagents, read the research brief and **PICK the through-line** (RULE 5).
Then write `artifacts/storyboard/showrunner_contract.json` — the shared spec every Scene Director
receives:

```jsonc
{
  "macro_arc": {
    "tonal_contour": ["solemn_curious", "rising_stakes", "tragic_inevitability", "modern_anxiety", "open_question"],
    "chapter_runtime_budget_s": { "ch00_cold_open": 45, "ch01_...": 70, "ch02_...": 100 }
  },
  "through_line": {
    "type": "case_file",
    "primitive": "spine_panel",
    "close_phase_kinds": ["return_to_map", "chapter_outro"],
    "consistency_keys": ["params.dossier_order", "params.subject_slots"],
    "label": "The dossier grows one name per chapter"
  },
  "phase_template": ["scene_establish", "approach", "characters", "story_dive", "climax", "aftermath", "chapter_outro", "transition"],
  "phase_durations_default_s": { "scene_establish": 5, "approach": 5, "characters": 12, "story_dive": 25, "climax": 8, "aftermath": 15, "chapter_outro": 6, "transition": 4 },
  "shot_scale_default": "medium",
  "camera_language": "static_with_accents",
  "noir_atmosphere": true
}
```

The `phase_template` uses MM `phase_kind` values (`scene_establish`, `characters`, `story_dive`,
`object_focus`, `face_beat`, `climax`, `aftermath`, `chapter_outro`, …). `map_breath` /
`return_to_map` are legal but used **only** in chapters where a map is genuinely the spine — they
are not the default rhythm.

### 2. Dispatch per-chapter Scene Director subagents (parallel)

One subagent per chapter, in parallel. Each receives:

- the showrunner contract (incl. the chosen `through_line`),
- `theme.json`,
- the slice of `canonical_names.json` relevant to this chapter,
- this chapter's VO text **and** its words from `artifacts/whisper/full.json`,
- `geography.json` **only if** this chapter has map beats,
- the adjacent chapters' `outgoing_state` (for the phase-state contract).

Each Scene Director's deliverable: `artifacts/storyboard/storyboard_<chapter_id>.json`.

### 3. Phase-state contract (cross-chapter continuity)

Every chapter declares `incoming_state` (= prior chapter's `outgoing_state`) and `outgoing_state`
(passed to the next chapter). For MM the state is **shot/scene/subject** centric (map fields are
optional): `scene_tier`, `active_scene_id`, `current_location_id`, `on_screen_character`,
`active_subjects[]` / `dimmed_subjects[]`, `noir_atmosphere`, `year_display`, `time_of_day`,
`active_ui_furniture[]`, `chapter_subject_id`. Include `basemap_tier` / `active_pins` ONLY for
map chapters. `qa_continuity` compares only the fields present on BOTH sides of a boundary, so a
no-map chapter need not carry pin state — but a face/scene that persists across the boundary must
match.

### 4. Per-beat authoring

Each beat (`definitions.beat`) carries:

- `shot_scale` (`macro` | `medium` | `micro`) — RULE 3.
- `animation_tier` (`2d` | `3d`) — RULE 2; **required** on hero + medium-scale beats.
- `hero: true` + `render_directive` for any hero shot or medium-scale scene (see Render
  Directives below).
- `emotion_face` + a face primitive for emotional beats — RULE 4.
- `start_anchor` and `end_anchor` resolving to `whisper/full.json` — RULE 6.
- `layers[]` — each `layer_action` declares its `layer` (L0–L11), a `primitive` from the enum,
  and (for visible non-chrome cues) a `spatial_target` + `placement`. Give time-distinct actions
  their own `cue_anchor`.
- `transitions_out[]` — explicit fade/cut/morph rules.

Use `vocab.py` to pick primitives by family. For an emotional medium/close-up, reach for
`face_closeup` / `face_medium` / `face_reaction` / `reaction_cut`. For off-map story beats use the
OFF_MAP family (`panel_archival`, `panel_illustration`, `panel_quote`, `document_overlay`,
`character_card`, `clip_archival`, …). Use map-bound primitives (`pin_drop`, `migration_arrow`,
`territory_wash`, `map_label`, …) ONLY in map beats with a filled `geography` block.

### 5. Through-line beat at each chapter close

In each chapter's close phase (a `chapter_outro` — or `return_to_map` for a map-spine video),
emit one beat that advances the declared `through_line` via its `primitive`, keeping
`consistency_keys` identical to every other chapter. This is the recurring device the audience
learns to expect (RULE 5); `qa_spine_consistency` blocks a chapter that omits it or drifts its
roster/order.

### 6. Experimental escape hatch

Per phase, MAX 2 beats may set `experimental: true` with `experimental_rationale` (uses the
`experimental` primitive to bypass the enum). Reserve it for genuinely novel beats; depth-review
catches abuse.

### 7. Enhancement scout subagent (per chapter, parallel)

A separate "enhancement scout" reviews each chapter's draft and proposes 3–5 enhancements
(period-instrument SFX moments, concept-stamp typography, an etymology micro-spike, an
atmospheric breath between scenes, a reaction-cut to a listening face). The Scene Director
incorporates or rejects each with rationale. Keep proposals inside the noir look (RULE 1) and on
the timing spine (RULE 6).

## Render Directives — HARD RULE (`qa_render_directive`)

Every **hero shot** — any beat with `hero: true`, **and every medium-scale scene (2D or 3D)** —
MUST carry a `render_directive`: a path to a rich per-shot brief at
`artifacts/shot_briefs/<beat>.md` (format in `artifacts/shot_briefs/_TEMPLATE.md`). This is the
spec handed to the animator agents, and the build **blocks** without it. Each directive must
also resolve `animation_tier` (RULE 2) — the brief reads differently for a 2D flat-segmented
scene vs a 3D diorama.

- **Vocabulary by shot scale + tier:**
  - `macro` — establishing. For a 2D wide noir scene: skyline/harbor/room composition, depth
    layers, light sources. For a 3D diorama or a map establisher: terrain/route/set scale, the
    bird's-eye framing. (NOT close character acting.)
  - `medium` — the scene where action happens. The workhorse; 2D flat-segmented set or 3D
    diorama, with blocking for the figures and the action.
  - `micro` — close-up on a face/object/document; the emotional and evidentiary beats.
- Every directive carries the **BINDING** facts (timing anchors, geo/region IDs, copy, asset IDs,
  physics constraints), the richness sections (camera/style, environment, subject animation *with
  timing intent*, key moments, FX, pacing, lighting/mood — all inside the noir look), and an
  explicit **LOCKED / IMPROVISE** split so the animator keeps creative latitude.
- **Motion is authored per shot from the directive — there is NO canned motion library.** Declare
  the planned paths + interactions in the directive's physics section; `qa_physics` verifies
  paths/collisions/facing downstream (physics is the gate, never left to the prompt).
- Keep directives to **hero + medium-scale shots only.** A `micro` document-stamp or a chrome
  year-card needs two lines, not 400 words.

## Human checkpoint (G2)

Present, for the user's approval: the master chapter outline + a 1-paragraph synopsis per
chapter + a sample beat, **the declared through-line** (so the user signs off on the recurring
device), the human-readable storyboard (`<chapter>.human.md`), and the hero-shot Render
Directives. Wait for explicit approval before advancing. Done is when
`run-stage … --stage storyboard` reports the gates green **and** G2 approval is present — the
runner's verdict, not yours.
