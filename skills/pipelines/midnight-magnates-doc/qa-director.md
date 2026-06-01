# QA Director — Midnight Magnates

The **visual-QA** stage — its stage id in `pipeline_defs/midnight-magnates-doc.yaml` is
qa_visual. Its product is the machine-authored `artifacts/qa_report.json` plus a
human-style review pass. **You do not certify QA.** A deterministic runner —
`lib/midnight_magnates/runner.py` — shells every blocking gate, captures the REAL exit
codes, and writes that report. Your job is to (1) run the runner, (2) read what it
found, (3) fix the storyboard / cuelist / scene-graphs until it goes green, then (4)
run a review swarm aimed at the things gates can't see (noir consistency, emotional-face
coverage, 2D/3D scene-graph reconciliation, perfect time+space synchrony) and feed those
findings back as concrete edits. The runner — not your say-so — decides "done."

## The load-bearing model (read this before anything else)

There is **no loose list of standalone QA scripts for you to run by hand, and no "I
reviewed it, it passes" certification.** Every hard rule in this pipeline lives as a real
gate module under `lib/midnight_magnates/gates/` and is wired into the manifest's stage
`hard_gates`.
The runner enumerates them, runs them, and is the single source of truth for pass/fail:

```bash
# Run EVERY stage's blocking gates and (re)write artifacts/qa_report.json. At final-QA
# time you want the whole-pipeline sweep (this is what the render-lock validates against),
# so omit --stage; the runner enumerates and runs all blocking gates across all stages.
python3 -m lib.midnight_magnates.runner run-gates \
    --pipeline midnight-magnates-doc --project <project_dir>

# (To iterate on just this stage's gates while fixing, pass --stage with this stage's id
#  from the manifest. The whole-pipeline run above is the one that gates the render.)

# Then read the machine-authored verdict — NOT your own judgment:
#   <project_dir>/artifacts/qa_report.json
```

Each entry in `qa_report.json` `gates[]` carries `name`, the exact `cmd` that ran,
`exit_code`, `passed`, `blocks`, and `stdout_tail` / `stderr_tail` (the gate's own
findings). `all_passed` is true only when every blocking gate exited 0. **Any non-zero
blocking exit means the build cannot advance — fix the underlying artifact and re-run the
runner.** You never hand-edit `qa_report.json`, and a green entry you wrote yourself is a
falsified pass.

Before any render the **render-lock** is the additional precondition — `assert_green_and_fresh`
refuses a final render unless `qa_report.json` is all-green AND its input hashes still
match the artifacts on disk (a green report that went stale after a storyboard/cuelist/
scene-graph/whisper edit fails). Confirm it:

```bash
python3 -m lib.midnight_magnates.runner check-lock \
    --pipeline midnight-magnates-doc --project <project_dir>
# RENDER-LOCK: GREEN  -> the report is all-green and fresh.
# RENDER-LOCK: BLOCKED -> it lists exactly why (a failing gate, or a stale hash).
```

To see the real gate set the runner will execute, read it off the manifest (the
authoritative list) or list the modules — never invent a gate name:

```bash
# the gates this stage actually runs (their cmd lines):
grep -A1 'name: qa_' pipeline_defs/midnight-magnates-doc.yaml
# every real gate module on disk:
ls lib/midnight_magnates/gates/qa_*.py
```

## What the runner enforces at this stage (the real gates — do NOT hand-run these)

These are the blocking gates the manifest attaches to the visual-QA stage; the runner runs
them all. They are listed so you understand WHAT is being checked and can map a red exit to a
concrete fix — **not** so you run them individually. Every name below is a real module at
`lib/midnight_magnates/gates/<name>.py`.

- `qa_no_custom_scripts` / `qa_no_reimplementation` — anti-monolith: the composition must
  be compiler-stamped (no hand-authored HTML, no hand-rolled Web-Mercator; geo goes
  through `lib.mapkit_subjects`). Hand-rolled project `.py` compositors are forbidden.
- `qa_primitive_utilization` — the storyboard actually USES its vocabulary (enough
  distinct primitives across map-bound + off-map + persistent-UI), so the video isn't
  seven primitives on repeat.
- `qa_min_hold` — every text-bearing cue stays on screen long enough to read
  (`hold >= max(2.5, ceil(words/3)+2)`).
- `qa_card_bounds` — every cue bbox lies fully inside 1920x1080 (catches lower-thirds
  anchored from the top).
- `qa_element_overlap` — no two cues on the same/adjacent layer collide in BOTH time and
  space unless they declare `interaction_with` (text-on-text collisions).
- `qa_cue_lifecycle` — no overlay outlives the timeline or lingers past its budget (the
  "missed its exit" bug).
- `qa_character_presence` — a named figure is PRESENT, not a postage stamp: a character
  beat is a hero cutout, a full-screen card, or a lower-corner card scene-anchored over a
  full-frame panel — never a tiny lone card on empty background.
- `qa_chapter_ui` — no "Chapter N" badge bleeding into a narrative shot (chapter labels
  belong only on a dedicated chapter-intro card).
- `qa_duplicate_face` — one portrait must not appear at two on-screen locations at once
  (a face in both the card and the subject badge in overlapping windows).
- `qa_pin_label_pulse_align` — when a map IS used, a pin, its pulse halo, and its leader
  line endpoint are co-located.
- `qa_basemap_present` — a map-family shot actually paints a geo-grounded basemap, not a
  flat fill (non-map shots are exempt — maps are supporting, not the default canvas).
- `qa_stray_mover` — no actor races a long raw-pixel path with no geo/narrative anchor
  (unmotivated movement); geo-grounded travel and settle-into-formation are exempt.
- `qa_physics` — diorama motion-path scene-graphs: actors don't clip through props or each
  other, stay in frame, and face their travel direction (passes for chapters with no
  diorama).
- `qa_asset_reference_closure` — every sourced asset is referenced by >=1 cue (or formally
  scrapped with evidence); no dangling `asset_id`.
- `qa_ui_sfx_coverage` — every high-priority UI cue (pin drop / card pop) has a
  taxonomy-matching SFX over its window (no pin dropping in dead silence). SFX placed here
  is LIBRARY-ONLY per `skills/core/sound-design-rules.md` — a needed sound absent from the
  curated library is a STOP + Missing-SFX proposal, never a silent substitute/generate.
- `qa_cue_drift` — the visual drift gate: every cuelist cue fires within its per-kind
  budget (faces/cards 0.4s, maps/animations 0.5s, clips 0.3s) of its anchor word; also
  catches unanchored intra-beat actions and ambiguous anchors.
- `qa_scene_sync` — the 2D/3D reconciliation gate: every `animation_tier` 2d or 3d beat
  must emit a scene-graph with `scene_t0_master_s` + `key_moments` resolving to their
  words; a tagged beat with no scene-graph is a LOUD fail (no silent 2D pass).
- `qa_master_offset` — catches a whole-chapter slide (the per-cue checks can all pass
  while the entire block is offset against the master VO).
- `qa_skill_gate_refs` — the anti-phantom guard: every `qa_*` token cited in any director
  skill (including this one) must resolve to a real gate module and must NOT be written as
  a standalone-script path. This is why this skill cites gates only by their real
  import-form name — a phantom or wrong-path citation BLOCKS the build here.

When a gate exits red, open its `stdout_tail`/`stderr_tail` in `qa_report.json` for the
specific finding, fix the **artifact** (storyboard chapter JSON, cuelist, scene-graph,
sound cuelist, or whisper spine — never the gate), and re-run the runner. Loop until
`all_passed: true`.

## HARD RULES

These are the Midnight Magnates channel identity, expressed as QA obligations. They are
non-skippable. Do not drift, reinterpret, or "review them as basically fine" — the runner
backs most of them with a real gate, and the ones it can't pixel-check are the review
swarm's explicit job.

1. **The runner owns the verdict — you NEVER hand-certify QA.** "Done" means
   `python3 -m lib.midnight_magnates.runner run-gates --pipeline midnight-magnates-doc
   --project <project_dir>` produced a `qa_report.json` with `all_passed: true`, AND
   `check-lock` reports GREEN. A prose "I reviewed it and it looks good" is not a pass and
   never substitutes for a green report.

2. **Noir LOOK consistency is a review obligation across the whole runtime.** The channel
   look is HyperFrames-generated flat-segmented noir ("night colors, noir atmosphere,
   moonlit, flat segmented color illustration") — NOT Recraft/Flux/Imagen/DALLE output and
   NOT the clip grades. The clip grades (`grade_cyan_orange` / `grade_crushed_warm` /
   `pitch_up_1st`) exist ONLY to transform third-party copyright material away from
   copyright; they are never the channel style. The image-generation policy is enforced
   upstream at the assets stage, so by the time the build reaches visual-QA the look is
   locked — your job is to sweep for noir DRIFT (a scene that reads too bright/saturated, a
   non-noir palette, a raw untreated third-party frame) and route it back as a fix.

3. **2D and 3D are co-equal — reconcile the scene-graph, don't assume.** Best fit per shot
   (`animation_tier` 2d = flat-segmented noir; 3d = bird's-eye diorama); the video is a
   mix, not all-one-mode. `qa_scene_sync` makes a tagged beat with no scene-graph a loud
   fail and `qa_physics` checks the diorama geometry — verify both went green and the
   3D/2D split looks deliberate, not collapsed to one tier.

4. **Emotional beats need real FACES — verify the coverage is live, not stamped.** An
   emotional moment rides a medium/close-up human face (real still/clip first; Nano Banana
   only as fallback, under the per-video cap — Recraft/Flux/Imagen/DALLE are FORBIDDEN).
   Face presence is gated upstream (`qa_emotion_face_coverage` at storyboard,
   `qa_face_visibility` at assets); in visual-QA confirm `qa_character_presence` /
   `qa_duplicate_face` are green AND sweep that every emotional VO line actually lands on a
   face that's big enough and not a frozen postage-stamp card.

5. **Maps are supporting, not central — don't QA as if a map is always on screen.** Shot
   scale is macro/medium/micro and most MM visuals are medium+micro; a map is supporting
   evidence, never the default canvas. The map gates (`qa_basemap_present`,
   `qa_pin_label_pulse_align`) only apply to map-family shots and are exempt elsewhere — a
   medium/micro shot with no map is correct, not a coverage gap.

6. **Perfect time+space synchrony is the bar.** Every visible cue resolves to (a) the
   right VO word — `qa_cue_drift` (per-kind budgets) and `qa_master_offset` (no
   whole-chapter slide) enforce timing against the Whisper spine — AND (b) the right action
   location, declared as a resolvable `spatial_target` (gated upstream by
   `qa_spatial_anchor` at storyboard). In visual-QA confirm those went green and, in the
   review swarm, eyeball that the moment a thing is named is the moment it appears, where
   the narration says it is.

7. **The brand through-line is agent-selected per video — never hardcoded.** The recurring
   spine (map / case_file / timeline / cast_of_players / other) is declared in the
   storyboard `through_line` field and enforced for presence + cross-chapter consistency by
   `qa_spine_consistency`. Do NOT assume any particular spine, and never reintroduce a
   hardcoded one — your review checks the chosen spine is consistent chapter to chapter,
   whatever it is.

## Review swarm — what gates can't see (after the runner is green)

Run this only once `qa_report.json` is `all_passed: true`. Pixel/CSS gates catch geometry,
timing, and presence; they do NOT catch taste, monotony, or whether the noir mood holds.
Dispatch parallel sweeper subagents aimed squarely at MM concerns. **Any finding → fix the
artifact → re-run the runner (`run-gates`, whole-pipeline) → re-sweep.** A fix can only
"count" once the runner is green again — never carry a finding forward on a stale report.

### Breadth swarm (parallel sweepers — MM concerns)

1. **Noir consistency** — Does the flat-segmented noir look hold across the whole runtime?
   Any scene that drifts too bright/saturated, breaks the palette, or reads as a different
   illustration style? Any raw, untreated third-party frame that should have a grade +
   approved frame? (Rule 2.)
2. **Emotional-face coverage** — Walk every emotional VO line: does it actually land on a
   medium/close-up human face that's large enough to carry the beat, real-source-first?
   Any emotional moment riding a map, a wide establisher, or a tiny stamped card instead of
   a face? (Rule 4.)
3. **2D/3D scene-graph reconciliation** — Does the per-shot 2d/3d split look deliberate and
   varied, or has it collapsed toward one tier? For diorama (3d) beats, does the motion
   read as real bird's-eye action (not a frozen cutout)? Do the 2D flat-noir beats and 3D
   diorama beats sit together coherently, or does the mode-switch jar? (Rule 3.)
4. **Time+space synchrony** — Spot-check that the instant a person/place/object is NAMED is
   the instant it appears, AND that it appears where the narration locates it. Gates bound
   the drift numerically; you're checking it FEELS locked — no early flash, no late reveal,
   nothing firing over empty frame. (Rule 6.)
5. **Through-line consistency** — Whatever spine the storyboard declared, is it presented
   identically every time it recurs (same elements, same positions, monotonic progression),
   and does it actually carry the brand thread chapter to chapter? (Rule 7.)
6. **Sensitive-content + authenticity sweep** — Per the `youtube_ai_slop_signals` and
   `youtube_ai_slop_signals`-adjacent memory notes and per-era sensitivities: any framing
   that reads as conspiratorial, gratuitously graphic, or as inauthentic/duplicated content
   (the demonetization signal for two near-identical sleep channels in one niche)? Flag for
   a fix or a producer decision.

### Depth review (one reviewer subagent, after breadth is empty)

Reads the draft render at speed + the compiler-stamped master HTML. Looks for what no gate
encodes:

- Subjective quality and noir-mood cohesion across the full runtime.
- Visual fatigue / monotony — three consecutive chapters sharing the same arc shape or
  camera-move rhythm; the 2D/3D mix going flat.
- Pacing problems gates can't catch (a beat that lands technically but drags, or rushes
  past an emotional peak).
- Missed opportunities — an emotional line that deserved a face it didn't get, a medium/
  micro moment that a stronger primitive would have sold.

Outputs findings + proposed fixes. The animator/storyboard applies them. Re-run the runner
(`run-gates`, whole-pipeline), then re-sweep breadth + depth.

**Loop until the reviewer returns "no new improvements found" AND the runner is green.**

## Stop conditions

1. **Clean** — `qa_report.json` is `all_passed: true`, `check-lock` is GREEN, breadth swarm
   is empty, and the depth reviewer returns no findings.
2. **Steady-state** — round N produces the same findings as round N-1 with the runner green.
   Escalate to the user with a "stable but imperfect" status rather than looping forever.
3. **Resource cap** (safety) — if total fix-time blows past a few hours of wall clock
   without converging, escalate to the user with the current `qa_report.json` summary and
   the outstanding subjective findings.

## Output

`artifacts/qa_report.json` is authored by the runner (you never write it). Treat its shape
as read-only:

```jsonc
{
  "pipeline": "midnight-magnates-doc",
  "stage": "ALL",
  "ran_at": "<iso8601>",
  "runner_signature": "midnight_magnates.runner@<version>",
  "input_hashes": { "...": "<sha256>" },   // freshness for the render-lock
  "gates": [
    { "name": "qa_scene_sync", "exit_code": 0, "passed": true, "blocks": true,
      "stdout_tail": "...", "stderr_tail": "..." }
    // ... one entry per blocking gate the runner ran
  ],
  "all_passed": true
}
```

The stage is complete only when the whole-pipeline `run-gates` reports `all_passed: true`,
`check-lock` reports GREEN, and the breadth + depth review swarm has converged with no open
findings. Record the swarm's accepted/rejected findings in your stage notes — but the
pass/fail verdict is the runner's `qa_report.json`, not yours.
