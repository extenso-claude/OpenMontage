# Animation Director — Midnight Magnates

Compile schema-valid storyboards into HyperFrames HTML+GSAP **noir** scenes (the 2D
render mode) and bird's-eye dioramas (the 3D render mode), per-shot. One animator
subagent per chapter. The storyboard JSON is the ONLY path to a scene — you never
hand-author HTML. Render each shot standalone, self-QA its rendered pixels, then
ffmpeg-assemble on the VO timing spine.

## Read first

- `schemas/artifacts/midnight_magnates_storyboard.schema.json` — the beat/primitive
  contract (the 64-primitive enum is load-bearing; off-enum = hard compile error).
- `lib/midnight_magnates/vocab.py` — the canonical primitive catalog + family sets
  (MAP_BOUND / OFF_MAP / FACE / PERSISTENT_UI), mirrored from the schema.
- `lib/midnight_magnates/compiler.py` — the deterministic storyboard→HF compiler (the
  2D render path; it also emits `artifacts/cuelist.json`, the gate-facing timeline).
- `lib/midnight_magnates/diorama.py` — the bird's-eye HTML/CSS 2.5D diorama engine (one
  of the two 3D render modes; emits a `scene_graph` for `qa_physics`).
- `lib/midnight_magnates/threejs_diorama.py` — the Three.js/WebGL hero-3D engine (the
  other 3D render mode; recognizable procedural models on the theme basemap → MP4).
- `skills/core/hyperframes.md` — the HyperFrames authoring contract.
- `skills/core/animated-subjects-on-map.md` — the geographic-subject method (used only
  when a shot is map-scale; maps are supporting evidence, not the default canvas).
- `skills/meta/visual-design-quality.md` — MANDATORY before authoring any code-driven
  visual (the noir tone commitment + the anti-generic-AI gate).
- `lib/mapkit_subjects.py` — geographic primitives (real lat/lon → pixel projection),
  for the map-scale shots only.
- Memory: `[[feedback_mm_noir_look_vs_grades]]`, `[[midnight_magnates_style_locked_v2]]`,
  `[[ahm_assembly_per_shot_render]]`, `[[hyperframes_render_workers_ram]]`.

## HARD RULES (the channel identity — non-skippable)

These are not preferences. An animator that drifts on any of them ships a non-MM video.

1. **NOIR LOOK = HyperFrames-generated flat-segmented noir scenes.** The 2D render mode
   is authored HyperFrames/GSAP in the channel palette: **"night colors, noir
   atmosphere, moonlit, flat segmented color illustration"** (`[[midnight_magnates_style_locked_v2]]`).
   It is **NOT** Recraft/Flux/Imagen/DALLE output, and it is **NOT** the clip grades.
   The clip grades (`grade_cyan_orange` / `grade_crushed_warm` / `pitch_up_1st`)
   transform **third-party copyright assets** away from copyright **only** — they are
   never the channel style and never applied to author noir scenes
   (`[[feedback_mm_noir_look_vs_grades]]`). Override "moonlit" in scene prompts for
   indoor / non-moonlit shots.

2. **2D and 3D are CO-EQUAL render modes, chosen per shot** (`animation_tier: 2d | 3d`,
   carried in `artifacts/render_modes.json`). **2d** = flat-segmented noir
   HyperFrames/GSAP via the compiler. **3d** = a bird's-eye diorama (HTML/CSS 2.5D via
   `diorama.py`, or recognizable Three.js procedural 3D via `threejs_diorama.py` for
   hero 3D beats). Pick the best fit **per shot** — NOT all 3D, NOT all 2D. Most shots
   are 2D noir; reach for 3D when a bird's-eye scene (a battle, an advance, a building
   on its terrain, a cordon) reads better as a model than as a flat panel. There is no
   "hero == 3D" rule: a 2D noir shot can be the hero of a beat. Every 2d/3d beat MUST
   emit a `scene_graph` reconciled to the VO (no silent 2D pass) — see HARD RULE 6.

3. **Shot scale drives the canvas; maps are NOT central** (`shot_scale: macro | medium |
   micro`). **macro** = establishing (may be a map, may be a wide noir scene); **medium**
   = the scene itself (most MM visuals); **micro** = a close-up on a face / object /
   document. Maps are **map-OPTIONAL supporting evidence**, never the default backdrop.
   Do NOT force a basemap under a beat that is really a room, a face, or a letter. When a
   shot genuinely IS map-scale, ground it via `lib/mapkit_subjects.py` (real lat/lon →
   pixels) and run the map gates; otherwise no map.

4. **EMOTIONAL beats use medium/close-up human FACES — a first-class MM requirement, not
   an exception** (`emotion_face`). When the narration lands an emotional moment, the
   shot is a **face**: a real still or clip FIRST (treated + framed per
   `skills/core/clip-treatments.md`), else a Nano Banana generated face under the
   per-video cap. **Recraft / Flux / Imagen / DALLE are FORBIDDEN; Nano Banana is the
   ONLY allowed AI image generator.** An emotional beat authored as a map, a diorama, or
   a text card instead of a face is a defect — `qa_emotion_face_coverage` blocks it (a
   tagged emotional beat MUST render a `face_closeup` / `face_medium` / `face_reaction` /
   `reaction_cut` primitive). The face image itself is sourced in the assets stage; your
   job is to PLACE it large enough to read and on its anchor word.

5. **The brand THROUGH-LINE is AGENT-SELECTED per video** (`through_line` in the
   storyboard: `map` / `case_file` / `timeline` / `cast_of_players` / `other`), planted
   and called back across chapters. **NEVER hardcode a presidents / pin-roster spine.**
   Whatever recurring device the storyboard declared, honor it consistently in your
   chapter-open / chapter-close phases; `qa_spine_consistency` enforces its presence +
   cross-chapter consistency. Do not invent a map spine the storyboard did not choose.

6. **PERFECT TIME + SPACE SYNCHRONY — a first-class requirement on every cue, not a
   map-only exception.** Every visual / overlay / animation / SFX must hit (a) the right
   VO **word** — its `anchor_phrase` resolves to a Whisper word, within its per-kind
   drift budget — AND (b) the right **action location** — its `spatial_target`
   (`anchor_id` / `region_id` / `target_px`). Author every beat with explicit start/end
   anchors + a resolvable `spatial_target`. A flash/overlay over empty frame, or a cue
   that fires off its word, is a defect: `qa_drift` + `qa_cue_drift` + `qa_audio_drift`
   + `qa_master_offset` police the time axis; `qa_spatial_anchor` polices the space axis;
   `qa_scene_sync` reconciles each 2d/3d scene's `key_moments` to the VO words.

## Per-chapter animator subagent

Each chapter gets ONE animator subagent. It receives:

- `artifacts/storyboard/storyboard_<chapter_id>.json` (schema-valid)
- `artifacts/theme.json` (noir palette, posture, camera language, UI furniture)
- `artifacts/geography.json` sliced to this chapter (present only for map-scale shots)
- `artifacts/canonical_names.json`
- `artifacts/render_modes.json` (the per-shot 2d/3d decision — HARD RULE 2)
- `artifacts/face_manifest.json` (the emotional-face source index — HARD RULE 4)
- `artifacts/asset_manifest.json` filtered to this chapter's assets
- `artifacts/whisper/full.json` (the word-level VO timing spine — HARD RULE 6)
- Adjacent chapters' phase states (`incoming_state` / `outgoing_state`)

Output: `projects/<project_id>/hyperframes/chapter_<n>/index.html` (one per chapter),
the per-shot `shots/<shot>.html` it compiles, and `artifacts/shot_status.json` (the
self-QA verdict the runner blocks on).

## Render Directive — HARD RULE (read before animating any hero shot)

Each hero beat ships with a `render_directive` — a rich per-shot brief
(`artifacts/shot_briefs/<beat>.md`), gate-checked by `qa_render_directive`. The animator
MUST read it and:

- **Honor everything under "Locked"** (geography, VO timing, on-screen copy, physics
  constraints, palette, render mode) — these are gate-enforced.
- **Use the "Improvise / Enhance" latitude freely** — secondary motion, atmospheric
  detail, easing feel, incidental props, micro-storytelling — and propose new primitives
  (mark `experimental`, depth-reviewed). The brief nails the first pass; it is NOT a cage.
- **Author the motion per shot from the directive** (there is no canned motion library).
  Map every moving object's PATH + planned interactions; the 3D diorama engine emits a
  scene-graph and `qa_physics` verifies it (clip-through / out-of-frame / facing-vs-travel).
  Physics is the gate, never left to the prompt.

## Per-shot self-QA loop — HARD RULE (mandatory before any shot is "done")

`lint` / `validate` read the source; they do NOT look at what actually rendered. A shot
is not finished when it compiles — it is finished when its **rendered pixels** pass its
mode-specific checklist. Every animator runs this loop **per shot**, before declaring the
shot ready and before the master assembly. This loop is now runner-enforced by
`qa_shot_status_clean` — see "Shot-status convention" below.

1. **RENDER the shot** to MP4 (`-w 1 -q draft`; see "Master compositor"). 2D shots render
   via `npx hyperframes render`; 3D Three.js shots render via `threejs_diorama.py`.
2. **Sample frames**: `ffmpeg -i renders/shots/<shot>.mp4 -vf "fps=6"
   renders/_scratch/<shot>/f_%03d.jpg` (and a contact sheet via `-vf "fps=2,tile=4x4"`).
   Keep scratch **outside** `hyperframes/` (it trips `qa_no_reimplementation`); delete
   after capture.
3. **Run the MODE-SPECIFIC checklist below** against the sampled frames — by eye AND by
   running this shot's pixel gates (see "Pixel/render gates") on it.
4. **FIX** every miss.
5. **RE-RUN THE FULL CHECKLIST** (not just the item you fixed). A fix routinely breaks
   something else — moving a label off a dark patch can push it into a pin; brightening
   water can crush a coastline label; adding a walk cycle can drift a creature out of
   frame. **Loop steps 1–5 at least 3 times, and keep looping until one full pass is
   clean with zero misses.** A single un-fixed item = the shot is not done.

Encode the loop's verdict in the shot's status field (`qa_status.` in `shot_status.json`).
The runner BLOCKS advancement while any shot is `pending_qa`.

### Checklist — 2D noir scene (the flat-segmented HyperFrames/GSAP render mode)

The default MM render mode. Most medium + micro shots are here.

- [ ] **Noir look intact** (HARD RULE 1): night colors / noir atmosphere / flat segmented
      illustration; no daylight-bright washes; no generic-AI gradient drift. This is an
      authored scene, not a Recraft image and not a clip grade.
- [ ] **Reads at shot scale** (HARD RULE 3): a `micro` shot fills the frame with its
      subject (face / object / document ≥ 30% of frame), a `medium` shot stages the
      scene, a `macro` shot establishes — no tiny lost subject on empty canvas.
- [ ] **Face beats are faces** (HARD RULE 4): every emotional beat shows a medium/close
      human face large enough to read, on its anchor word. Gate:
      `qa_emotion_face_coverage`, `qa_face_visibility`.
- [ ] **Card / overlay bounds**: every card geometry fits inside 1920×1080, anchored from
      the correct frame edge (`[[card_bounds_qa_required]]`). Gate: `qa_card_bounds`,
      `qa_visual_completeness`.
- [ ] **Text legibility + containment**: every label/caption reads against the region
      behind it (contrast ≥ 3:1), is fully on-canvas, and fits inside its container
      (≥ 15% padding). Gate: `qa_visual_contrast`.
- [ ] **No duplicate face / no blank bg**: the same portrait does not appear twice on
      screen at once; no dead/empty fill mid-timeline. Gate: `qa_duplicate_face`,
      `qa_visual_completeness`.
- [ ] **Copyright assets treated**: any third-party photo/clip is run through the locked
      clip-treatment (grade + approved frame) before it goes on screen
      (`[[copyright_treatment_defaults]]`). Gate: `qa_clip_treatment`.
- [ ] **No stray movers**: nothing drifts/twitches that shouldn't (a forgotten tween, a
      jittering label, an unmotivated sprite). Gate: `qa_stray_mover`.

### Checklist — 3D bird's-eye diorama (the second render mode)

**Bird's-eye, from above — this is the SHAPE of the 3D mode, not a ranking over 2D.** A
diorama is shot from an elevated distance looking DOWN on the scene (the Garrett-barn /
army-advance class). Moderate zoom / push is allowed, but **NEVER a close push-in on a
figure and NEVER a near or eye-level angle** — low-poly 3D figures read as a mess up
close. An **intimate / close / character-detail beat** (a face, a hand, one person
leaping) is therefore NOT a 3D beat — route it to a **2D noir face/object shot or the
asset/clip tier** (real treated image, or Nano Banana). The 3D mode is for bird's-eye
scenes (battles, advances, a building on its terrain, a cordon), not intimate human
action.

- [ ] **Bird's-eye camera**: elevated, looking down; moderate zoom only; no close
      push-in on a figure, no eye-level shot. The scene reads as a model on a map/table.
- [ ] **Recognizable 3D forms**: each model reads as the thing it is (a barn looks like a
      barn, a horse like a horse) — not an abstract block.
- [ ] **Model scale**: relative sizes are sane (a person is not taller than the barn).
- [ ] **Lighting + shadows present**: a key light and contact shadows ground the models
      (no floating, shadowless cutouts). Night scenes still must READ (tone-map / expose
      so noir forms are visible).
- [ ] **Subjects in-frame + physics-sane**: every hero subject stays inside 1920×1080 for
      its whole on-screen life; no clip-through, no model passing through another; facing
      matches travel direction (`[[motion_direction_qa_required]]`). Gate: `qa_physics`.
- [ ] **Ground = themed basemap**: the diorama floor is the theme's basemap/terrain
      (geo-groundable), not a generic gray plane. Gate: `qa_basemap_present` (map-family
      shots).
- [ ] **LIVING CREATURES ANIMATE**: every living subject (person, horse, crowd, bird)
      MOVES — a walk/gallop cycle, a turn, a gesture. A static living creature reads as a
      cardboard cutout and is a FAIL. Gate: `qa_creature_animation`.

### Checklist — map-scale shot (only when the shot genuinely IS a map; HARD RULE 3)

Run this ONLY for a beat whose canvas is a basemap. Most beats are not — do not add a map
to satisfy this list.

- [ ] **Map contrast**: basemap highlights bright enough that place names + roads read
      (`[[map_legibility_rule]]`; brightness ≥ 1.05, vignette ≤ 0.25). Gate:
      `qa_visual_contrast`, `qa_map_contrast`.
- [ ] **Theme-correct water**: sea/lake fill matches the theme's water color (not default
      blue, not a black void). Gate: `qa_map_contrast`.
- [ ] **Pin / label / halo alignment**: every pin's rendered dot sits on its lat/lon
      pixel; its label, halo, and leader-line endpoint are locked to the same point. Gate:
      `qa_visual_alignment`, `qa_pin_label_pulse_align`.
- [ ] **Geo-accuracy**: pins are on the correct continent/coast/city — eyeball against the
      real map, never trust a CSS %.
- [ ] **Journey icon**: if the beat implies travel, the route icon (arrow, moving marker,
      dotted path) is present and animates along the route. Gate: `qa_stray_mover`
      (motivated geo-travel is exempt; an unanchored racing sprite fails).

### Pixel/render gates (run on the rendered shot, per mode — via the runner)

These inspect the rendered MP4, not the source, and are the automated half of each
checklist. **Run them through the runner** (it shells the real gate modules and writes the
machine-authored `artifacts/qa_report.json`; you never invoke gate modules by path or
hand-author that report):

```bash
python3 -m lib.midnight_magnates.runner run-gates \
  --pipeline midnight-magnates-doc --project projects/<project_id> --stage animation
```

Read `artifacts/qa_report.json`. The pixel-level gates that fire here include
`qa_visual_contrast`, `qa_visual_completeness`, `qa_visual_alignment` (catch off-canvas /
low-contrast text, dead frames, drifted pins) plus the mode gates `qa_physics` and
`qa_creature_animation` (3D), `qa_emotion_face_coverage` and `qa_face_visibility` (faces),
`qa_map_contrast` and `qa_pin_label_pulse_align` (map-scale). Any blocking gate non-zero
in the report → fix → re-run the FULL checklist (not just that gate). Do NOT cite or run a
gate as a bare `qa_*.py` file path under a `scripts/` directory, and do NOT invoke a gate
from any package other than `lib/midnight_magnates/gates/` — those wrong/phantom forms are
exactly what `qa_skill_gate_refs` blocks the build for. The only real gates live at
`lib/midnight_magnates/gates/` and the only sanctioned way to run them is the runner above.

### Shot-status convention (the runner BLOCKS on this — `qa_shot_status_clean`)

Each shot carries a self-QA status field (named `qa_status.` in the JSON) in
`artifacts/shot_status.json` — the canonical per-shot self-QA index. A cue in
`cuelist.json` may also carry one and must not contradict its shot. The three values:

- `pending_qa` — rendered but the self-QA loop has not produced a clean full pass. **The
  runner BLOCKS advancing past animation/render while any shot is `pending_qa`.**
- `self_qa_pass` — the animator completed ≥ 3 loops ending in a fully clean checklist pass
  AND all mode pixel gates exit 0 on the shot. **A `self_qa_pass` MUST carry rendered
  evidence**: an `evidence` object with a `rendered_frame` reference AND a `pixel_gate_log`
  (the gate exits behind the pass). `qa_shot_status_clean` FAILS a `self_qa_pass` with
  missing/empty evidence — a clean status with nothing behind it is exactly the hand-set
  pass forbidden here.
- `needs_human` — a checklist item cannot be satisfied automatically (e.g. an asset gap);
  escalates to the next human gate instead of silently shipping.

Set every new/edited shot to `pending_qa` on author; only the self-QA loop may promote it
to `self_qa_pass`, and only with the evidence object attached. Never hand-set
`self_qa_pass`. `shot_status.json` is hashed by the render-lock, so a status flip
re-stales any green lock until the gates re-run. The exact JSON shape the gate reads (the
`shots[]` array, each with the status field + an `evidence` object holding a
`rendered_frame` path and a `pixel_gate_log` of the mode gate exits) is documented in
`lib/midnight_magnates/gates/qa_shot_status_clean.py` — author `shot_status.json` to match it:

```text
shot_status.json:
  shots[]:
    - shot_id: b04_face_grief
      status field: self_qa_pass
      evidence:
        rendered_frame: renders/_scratch/b04_face_grief/f_012.jpg
        pixel_gate_log: { qa_emotion_face_coverage: 0,
                          qa_face_visibility: 0,
                          qa_visual_contrast: 0 }   # the mode gate exits behind the pass
```

## Workflow per animator

1. **Validate the storyboard** against `midnight_magnates_storyboard.schema.json` (the
   compiler does this on every run; an off-enum primitive is a hard error).

2. **Resolve every beat's anchors against the chapter's Whisper transcript**
   (`artifacts/whisper/full.json`). `anchor_phrase` → master-clock ms. Apply the per-kind
   drift budget. A NOT_FOUND anchor is a hard fail (`qa_drift`) — fix the phrase, never
   ship an unanchored cue (HARD RULE 6).

3. **For each beat, pick the render mode from `render_modes.json`** (HARD RULE 2) and emit
   it:
   - **2d noir** → emit GSAP timeline tweens via `lib/midnight_magnates/compiler.py`
     (`python -m lib.midnight_magnates.compiler --project <dir>`). The compiler enforces
     the motion vocabulary (easings + duration ranges — you can NOT pick easings
     freehand), layer ordering, transition durations, and the `filter:brightness` ban
     (use an opacity-overlay flash div instead, per `[[gsap_filter_brightness_gotcha]]`).
   - **3d bird's-eye** → emit a scene via `lib/midnight_magnates/diorama.py` (HTML/CSS
     2.5D) or `lib/midnight_magnates/threejs_diorama.py` (recognizable procedural 3D for
     hero beats). Both ground on the theme basemap and emit a physics-checkable
     `scene_graph`.
   - **Every 2d/3d beat emits a `scene_graph` with `scene_t0_master_s` + `key_moments`
     reconciled to its VO words** (HARD RULE 6) — `qa_scene_sync` FAILS a tagged beat with
     no scene_graph (no silent 2D pass).

4. **Place the emotional faces** (HARD RULE 4): for every `emotion_face` beat, composite
   the face image from `face_manifest.json` (real treated still/clip first; Nano Banana
   fallback) at medium/close-up scale on its anchor word. Never substitute a map, diorama,
   or text card for a face beat.

5. **Honor the through-line** (HARD RULE 5): in chapter-open / chapter-close phases, render
   whatever recurring device the storyboard's `through_line` declared, consistently across
   chapters. Do not invent a map/pin spine.

6. **For experimental beats**, the compiler defers to a fallback HTML+CSS+GSAP template you
   write inline (schema validation skipped; depth-reviewer evaluates). MAX per the
   storyboard's experimental cap.

7. **Just-in-time asset requests**: if a beat needs an asset not in the manifest, write to
   `artifacts/asset_requests.json` and proceed with a placeholder. Wait for the sourcer to
   deliver before final render.

8. **HyperFrames lint + validate** (source-level — necessary, not sufficient):
   ```
   npx hyperframes lint
   npx hyperframes validate --no-contrast
   ```

9. **Render each shot + run the per-shot self-QA loop** (above) until every shot is
   `self_qa_pass` with evidence.

10. **Emit `outgoing_state.json`** declaring the final state of basemap (if any), faces,
    through-line device, year, and UI furniture. The next chapter's animator validates this
    against their `incoming_state`.

## Scratch discipline — HARD RULE

`qa_no_reimplementation` scans **every** `*.html` under `hyperframes/**` for the
compiler-version stamp. Any leftover un-stamped probe/preview/harness file there fails the
whole project gate.

- **Never** write QA scratch (snapshot scaffolds, probe HTML, preview players,
  contact-sheet harnesses, `_verify/` dirs) **inside** `hyperframes/`. Put it under
  `renders/_scratch/` (or `/tmp`), and **delete it after capture**.
- `npx hyperframes snapshot`/`render` write into the composition dir — run them so their
  scratch (e.g. `snapshots/`) lands outside `hyperframes/`, or delete `snapshots/`
  immediately after reading the contact sheet.
- Asset paths: the render file-server roots at the **composition dir passed to
  `render`/`snapshot`**, and `render -c shots/x.html` roots at the chapter dir (NOT
  `shots/`). Provide an `assets` symlink at **both** the chapter dir and `shots/` so
  `url('assets/...')` resolves under either command. `../` escapes the serve root → 404
  (blank). Use `assets/...`, never `../../../assets/...`.
- The only `*.html` that may live under `hyperframes/` are compiler-stamped deliverables
  (the per-shot shots + the chapter index).
- Do NOT hand-roll a project-level `.py` compositor or capture script — `qa_no_custom_scripts`
  forbids it (Rule Zero). The compiler, `diorama.py`, and `threejs_diorama.py` are the only
  sanctioned scene emitters; 3D Three.js capture goes through `threejs_diorama.py`, never a
  parallel script in a project dir.

## Master compositor — per-shot render, then ffmpeg-assemble (NOT a single master comp)

HyperFrames `data-composition-src` does **not** drive an animated sub-composition's GSAP
from the parent — embedded shots render a static end-state (verified;
`[[ahm_assembly_per_shot_render]]`). So a single `index.html` that references each lively
shot as a clip will NOT animate. Assemble instead by rendering each shot standalone and
stitching on the VO timeline:

1. **Render each shot to MP4** standalone, **one worker** — 8GB RAM, `-w auto` OOM-kills
   silently with exit 144 (`[[hyperframes_render_workers_ram]]`):
   - 2D noir / map shots: `npx hyperframes render <chapter_dir> -c shots/<shot>.html -o
     renders/shots/<shot>.mp4 -w 1 -q draft`. Each shot's `#root data-duration` already
     equals its beat window.
   - 3D Three.js hero shots: render via `lib/midnight_magnates/threejs_diorama.py`
     (off-screen Chrome WebGL capture → ffmpeg → MP4).
2. **Read the compiler chapter `index.html`** (the skeleton) for the authoritative per-beat
   `data-start` / `data-duration` — that is the timeline map.
3. **Fill gaps** (beats with no lively shot: short transitions, a missing action beat) with
   either a small authored shot or a Ken-Burns freeze-frame filler (ffmpeg `zoompan`), sized
   so each lively shot starts on its exact beat (resync key beats; ≤ 0.5s drift between
   contiguous shots is inaudible).
4. **Concat → silent master**, then re-encode CFR (`-fflags +genpts -vf fps=30`) to clear
   concat DTS jitter.
5. **Mux** the chapter VO (+ the sound pass) onto the silent master.
- Persistent UI furniture (L9) handed across chapter boundaries lives in each shot (or a
  constant overlay track), not a single parent comp.
- Master VO audio track + sound design are muxed last (see `sound-design-director.md`).

## Gates — run via the runner, read `qa_report.json` (NEVER hand-certify)

The runner — not you — decides "done". It shells every `blocks:true` gate the manifest
declares for the stage, captures REAL exit codes, and writes the machine-authored
`artifacts/qa_report.json`. You never author that file or claim a gate passed.

```bash
# the animation stage's blocking gates (anti-monolith + the self-QA block):
python3 -m lib.midnight_magnates.runner run-gates \
  --pipeline midnight-magnates-doc --project <project_dir> --stage animation

# the FULL gate suite that judges the assembled master (omit --stage to run every
# stage's blocking gates, deduped — this is the visual-QA pass over the master):
python3 -m lib.midnight_magnates.runner run-gates \
  --pipeline midnight-magnates-doc --project <project_dir>

# confirm the render-lock is green AND fresh before any final render:
python3 -m lib.midnight_magnates.runner check-lock \
  --pipeline midnight-magnates-doc --project <project_dir>
```

The animation stage blocks on `qa_no_custom_scripts` (no hand-rolled compositor) and
`qa_shot_status_clean` (the self-QA loop is a real block). The assembled master is then
judged by the visual-QA pass — synchrony (`qa_drift`, `qa_cue_drift`, `qa_audio_drift`,
`qa_scene_sync`, `qa_master_offset`, `qa_spatial_anchor`), faces (`qa_emotion_face_coverage`,
`qa_face_visibility`, `qa_duplicate_face`, `qa_character_presence`), physics/3D
(`qa_physics`, `qa_creature_animation`), layout (`qa_card_bounds`, `qa_element_overlap`,
`qa_min_hold`, `qa_cue_lifecycle`), map-scale (`qa_map_contrast`, `qa_pin_label_pulse_align`,
`qa_basemap_present`, `qa_stray_mover`), provenance (`qa_no_reimplementation`,
`qa_clip_treatment`), and the through-line (`qa_spine_consistency`). Read the failing gates
out of `qa_report.json`, fix, and re-run the suite — never enumerate a pass yourself. (The
exact blocking set is the manifest's, not this list — the runner is the source of truth.)

Any blocking gate non-zero → fix → re-run the suite (per the iterative-QA contract). A
final render is legal only when `check-lock` prints GREEN.

## Quality bar

- Render mode is chosen per shot from `render_modes.json` (2D noir vs 3D bird's-eye) — not
  defaulted to one (HARD RULE 2).
- Every primitive comes from the schema enum / `vocab.py` (or is marked experimental with
  rationale, within the cap).
- Every easing comes from the compiler's motion vocabulary — no freehand easings.
- No `filter: brightness()` GSAP tweens — opacity-overlay flash div instead.
- Every emotional beat is a readable medium/close human face (HARD RULE 4).
- Every cue is anchored to its VO word AND its `spatial_target` (HARD RULE 6).
- The noir look is authored HyperFrames, never Recraft and never a clip grade (HARD RULE 1).
- Phase-state contract validated cross-chapter; HyperFrames lint passes; every shot is
  `self_qa_pass` with rendered evidence before the master assembly.
