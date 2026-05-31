# Animation Director — Animated History Map

Compile schema-valid storyboards into HyperFrames HTML+GSAP. Per-chapter animator subagents.

## Read first

- `docs/animated-history-map-design-intel.md` §2 (primitives) + §14 (motion contract) + §15 (timing + layers)
- `skills/core/hyperframes.md` for the authoring contract
- `skills/core/animated-subjects-on-map.md` for the canonical method
- `lib/mapkit_subjects.py` for geographic primitives
- `lib/animated_history_map/compiler.py` (the deterministic storyboard→HF compiler)

## Per-chapter animator subagent

Each chapter gets ONE animator subagent. Subagent receives:

- `storyboard_<chapter_id>.json` (schema-valid)
- `theme.json`
- `geography.json` (sliced to this chapter)
- `canonical_names.json`
- `asset_manifest.json` (filtered to this chapter's assets)
- `artifacts/whisper/chapter_<n>.json` (word-level timestamps)
- Adjacent chapters' phase states

Output: `projects/<project_id>/hyperframes/chapter_<n>/index.html` (one per chapter).

## Render Directive — HARD RULE (read before animating any hero shot)

Each hero beat (`shot_tier: medium_diorama` or `hero: true`) ships with a `render_directive` — a rich per-shot brief (`artifacts/shot_briefs/<beat>.md`). The animator MUST read it and:

- **Honor everything under "Locked"** (geography, VO timing, on-screen copy, physics constraints, palette) — these are gate-enforced.
- **Use the "Improvise / Enhance" latitude freely** — secondary motion, atmospheric detail, easing feel, incidental props, micro-storytelling — and propose new primitives (mark `experimental`, depth-reviewed). The brief is detailed enough to nail the first pass; it is NOT a cage.
- **Author the motion per shot from the directive** (there is no canned motion library). Map out every moving object's PATH + planned interactions; the diorama engine emits a scene-graph and `qa_physics` verifies it (clip-through / out-of-frame / facing-vs-travel). Physics is never left to the prompt.

## Per-shot self-QA loop — HARD RULE (mandatory before any shot is "done")

`lint`/`validate` read the source; they do NOT look at what actually rendered. A shot is not finished when it compiles — it is finished when its **rendered pixels** pass its tier checklist. Every animator runs this loop **per shot**, before declaring the shot ready and before the master assembly:

1. **RENDER the shot** to MP4 (`-w 1 -q draft`; see "Master compositor").
2. **Sample frames**: `ffmpeg -i renders/shots/<shot>.mp4 -vf "fps=6" renders/_scratch/<shot>/f_%03d.jpg` (and a contact sheet via `-vf "fps=2,tile=4x4"`). Keep scratch **outside** `hyperframes/` (trips `qa_no_reimplementation`); delete after capture.
3. **Run the TIER-SPECIFIC checklist below** against the sampled frames — by eye AND by running this tier's pixel gates (see "Pixel/render gates" table) on the shot.
4. **FIX** every miss.
5. **RE-RUN THE FULL CHECKLIST** (not just the item you fixed). A fix routinely breaks something else — moving a label off a dark patch can push it into a pin; brightening water can crush a coastline label; adding a walk cycle can drift a creature out of frame. **Loop steps 1–5 at least 3 times, and keep looping until one full pass is clean with zero misses.** A single un-fixed item = the shot is not done.

Encode the loop's verdict in the shot's `qa_status` (see "qa_status convention"). The runner blocks advancement while any shot is `pending_qa`.

### Checklist — `macro_map` (the map tier)

- [ ] **Map contrast**: basemap highlights bright enough that place names + roads read (memory `map_legibility_rule`; brightness ≥ 1.05, vignette ≤ 0.25). Gate: `qa_visual_contrast`, `qa_map_contrast`.
- [ ] **Theme-correct water**: sea/lake fill matches the theme's water color (not default blue, not black void).
- [ ] **Pin / label / halo alignment**: every pin's rendered dot sits on its lat/lon pixel; its label and halo are locked to the same point (no label floating off its marker). Gate: `qa_visual_alignment`.
- [ ] **Geo-accuracy**: pins are on the correct continent/coast/city — eyeball against the real map, never trust a CSS %.
- [ ] **Label legibility**: every label reads against the region behind it (contrast ≥ 3:1) and is fully on-canvas. Gate: `qa_visual_contrast`.
- [ ] **No stray movers**: nothing drifts/twitches that shouldn't (a forgotten tween, a jittering label).
- [ ] **Journey icon**: if the beat implies travel, the journey/route icon (arrow, moving marker, dotted path) is present and animates along the route.

### Checklist — `medium_diorama` (the 3D tier)

**HARD RULE — BIRD'S-EYE ONLY.** A 3D diorama is ALWAYS shot from an elevated, bird's-eye distance looking DOWN on the scene (the Garrett-barn / army-advance dioramas). Moderate zoom / push is allowed, but **NEVER a close push-in on a figure and NEVER a near or eye-level angle** — low-poly 3D figures read as an incomprehensible mess up close (the close-up Booth-leap failed exactly here and was cut). An **intimate / close / character-detail beat** (a face, a hand, one person leaping, a leg breaking) is therefore NOT a 3D beat — route it to the **asset/clip tier**: a real copyright/PD image (treated + framed) or an AI-generated image (Nano Banana). The 3D tier is for bird's-eye scenes (battles, advances, a building on its terrain, a cordon around a barn), not intimate human action.

- [ ] **Bird's-eye camera**: elevated, looking down on the diorama; moderate zoom only; no close push-in on a figure, no eye-level shot. The whole scene reads as a model on a map/table.
- [ ] **Recognizable 3D forms**: each model reads as the thing it is (a barn looks like a barn, a horse like a horse) — not an abstract block.
- [ ] **Model scale**: relative sizes are sane (a person is not taller than the barn; a horse is not the size of a house).
- [ ] **Lighting + shadows present**: there is a key light and contact shadows ground the models (no floating, shadowless cutouts).
- [ ] **Subjects in-frame**: every hero subject stays inside the 1920×1080 frame for its whole on-screen life (no half-off-frame model). Gate: `qa_physics` (out-of-frame).
- [ ] **Physics sanity**: no clip-through, no model passing through another; facing matches travel direction (memory `motion_direction_qa_required`). Gate: `qa_physics`.
- [ ] **Ground = themed basemap**: the diorama floor is the themed basemap/terrain (geo-groundable), not a generic gray plane.
- [ ] **LIVING CREATURES ANIMATE**: every living subject (person, horse, crowd, bird) MOVES — a walk/gallop cycle, a turn, a gesture. A static living creature reads as a cardboard cutout and is a FAIL. Gate: `qa_creature_animation`.

### Checklist — `micro_offmap` (the off-map character / cutout tier)

- [ ] **Character ≥ 30% of frame OR cutout-with-border**: the subject is either large enough to read (≥ 30% of frame height) or framed as a deliberate bordered cutout — never a tiny lost thumbnail.
- [ ] **Card bounds**: the card geometry fits inside 1920×1080, anchored from the correct frame edge (memory `card_bounds_qa_required`). Gate: `qa_card_bounds`, `qa_visual_completeness`.
- [ ] **No duplicate face**: the same portrait does not appear twice on screen at once.
- [ ] **No blank bg**: the off-map background is a real treated backdrop, not an empty fill or a dead frame. Gate: `qa_visual_completeness`.
- [ ] **Copyright assets treated**: any third-party photo/clip is run through the locked clip-treatment (frame + grade) before it goes on screen (memory `copyright_treatment_defaults`).

### Pixel/render gates (run on the rendered shot, per tier)

These inspect the rendered MP4, not the source, and are the automated half of each checklist. Run them on each shot during the loop, then again on the master:

| Gate | Catches | Tiers |
| --- | --- | --- |
| `qa_visual_contrast` | rendered text/labels below 3:1 contrast or off-canvas | macro_map, micro_offmap |
| `qa_visual_completeness` | dead/blank frame mid-timeline; a declared visible cue with no geometry | all |
| `qa_visual_alignment` | a rendered pin drifted off its declared lat/lon pixel | macro_map |
| `qa_creature_animation` | a living creature that rendered static (frozen cutout) | medium_diorama |

```bash
for g in qa_visual_contrast qa_visual_completeness qa_visual_alignment qa_creature_animation; do
  python3 -m lib.animated_history_map.gates.$g --project projects/<project_id>
done
```

Any non-zero exit → fix → re-run the FULL checklist (not just that gate).

### `qa_status` convention (the runner blocks on this)

Each shot carries a `qa_status` in its shot brief / cuelist entry:

- `pending_qa` — rendered but the self-QA loop has not produced a clean full pass. **The runner BLOCKS advancing past animation/render while any shot is `pending_qa`.**
- `self_qa_pass` — the animator completed ≥ 3 loops ending in a fully clean checklist pass AND all tier pixel gates exit 0 on the shot.
- `needs_human` — a checklist item cannot be satisfied automatically (e.g. an asset gap); escalates to the next human gate instead of silently shipping.

Set every new/edited shot to `pending_qa` on author; only the self-QA loop may promote it to `self_qa_pass`. Never hand-set `self_qa_pass` without the clean rendered pass behind it.

## Workflow per animator

1. **Validate storyboard** against schema.

2. **Resolve every beat's anchors against the chapter's Whisper transcript.** Phrase → ms timestamp. Apply drift budget.

3. **For each phase, emit GSAP timeline tweens** via the compiler library (`lib/animated_history_map/compiler.py`). The compiler enforces:
   - Motion vocabulary table (easings + duration ranges) — animator can NOT pick easings freehand
   - Layer ordering
   - Transition durations
   - `filter:brightness` ban (use opacity-overlay instead)

4. **For experimental beats**, the compiler defers to a fallback HTML+CSS+GSAP template the animator writes inline. Schema validation skipped, depth-reviewer evaluates.

5. **Just-in-time asset requests**: if a beat needs an asset not in the manifest, write to `artifacts/asset_requests.json` and proceed with a placeholder. Wait for sourcer to deliver before final render.

6. **HyperFrames lint + validate**:
   ```
   npx hyperframes lint
   npx hyperframes validate --no-contrast
   ```

7. **Emit `outgoing_state.json`** declaring final state of basemap, pins, year, UI furniture. The next chapter's animator validates this against their `incoming_state`.

## Scratch discipline — HARD RULE

`qa_no_reimplementation` scans **every** `*.html` under `hyperframes/**` for the compiler-version stamp. Any leftover un-stamped probe/preview/harness file there fails the whole project gate.

- **Never** write QA scratch (snapshot scaffolds, probe HTML, preview players, contact-sheet harnesses, `_verify/` dirs) **inside** `hyperframes/`. Put it under `renders/_scratch/` (or `/tmp`), and **delete it after capture**.
- `npx hyperframes snapshot`/`render` write into the composition dir — run them so their scratch (e.g. `snapshots/`) lands outside `hyperframes/`, or delete `snapshots/` immediately after reading the contact sheet.
- Asset paths: the render file-server roots at the **composition dir passed to `render`/`snapshot`**, and `render -c shots/x.html` roots at the chapter dir (NOT `shots/`). Provide an `assets` symlink at **both** the chapter dir and `shots/` so `url('assets/...')` resolves under either command. `../` escapes the serve root → 404 (blank). Use `assets/...`, never `../../../assets/...`.
- The only `*.html` that may live under `hyperframes/` are compiler-stamped deliverables (the per-shot shots + the chapter index).

## Master compositor — per-shot render, then ffmpeg-assemble (NOT a single master comp)

HyperFrames `data-composition-src` does **not** drive an animated sub-composition's GSAP from the parent — embedded shots render a static end-state (verified). So a single `index.html` that references each lively shot as a clip will NOT animate. Assemble instead by rendering each shot standalone and stitching on the VO timeline:

1. **Render each shot to MP4** standalone: `npx hyperframes render <chapter_dir> -c shots/<shot>.html -o renders/shots/<shot>.mp4 -w 1 -q draft` (one worker — 8GB RAM; `-w auto` OOMs). Each shot's `#root data-duration` already equals its beat window.
2. **Read the compiler chapter `index.html`** (the skeleton) for the authoritative per-beat `data-start`/`data-duration` — that is the timeline map.
3. **Fill gaps** (beats with no lively shot: short transitions, a missing action beat) with either a small authored shot or a Ken-Burns freeze-frame filler (ffmpeg `zoompan`), sized so each lively shot starts on its exact beat (resync key beats; ≤0.5s drift between contiguous shots is inaudible).
4. **Concat → silent master**, then re-encode CFR (`-fflags +genpts -vf fps=30`) to clear concat DTS jitter.
5. **Mux** the chapter VO (+ the sound pass) onto the silent master.
- Persistent UI furniture (L9) handed across chapter boundaries lives in each shot (or a constant overlay track), not a single parent comp.
- Master VO audio track + sound design muxed last (see sound-design-director).

## Gates

Every gate must pass on the master:

1. qa_asset_coverage
2. qa_gap_coverage (no black frames mid-VO)
3. qa_pin_geographic_accuracy
4. qa_projection_consistency
5. qa_location_provenance
6. qa_canonical_names
7. qa_card_bounds
8. qa_element_overlap
9. qa_label_collision
10. qa_min_hold
11. qa_motion_direction
12. qa_motion_vocabulary
13. qa_text_containment
14. qa_audio_drift
15. qa_timing_anchors
16. qa_layer_conflicts
17. qa_region_provenance + palette_binding

Any non-zero exit → fix → re-run ALL gates (per iterative QA contract).

## Quality bar

- Every primitive comes from the schema enum (or is marked experimental with rationale)
- Every easing comes from the motion vocabulary table
- No `filter: brightness()` GSAP tweens — use opacity-overlay for flashes
- Phase state contract validated cross-chapter
- HyperFrames lint passes
