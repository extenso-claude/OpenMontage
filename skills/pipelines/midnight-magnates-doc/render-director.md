# Render Director — Midnight Magnates

Render the per-shot **noir** scenes (2D and 3D co-equally) to MP4, ffmpeg-assemble
them on the VO timing spine, and produce a 1080p `renders/<chapter>_preview.mp4` whose
**rendered pixels** pass the `render` stage's blocking gates. You render each shot
standalone, self-QA what actually rendered, and stitch — you do NOT drive a single
master composition (embedded sub-comps freeze at an end-state). Audio (music + SFX) is
baked later by `final-render-director.md`; this stage muxes the chapter VO only.

## Read first

- `skills/pipelines/midnight-magnates-doc/animation-director.md` — the per-shot
  render → ffmpeg-assemble mechanics, the shot self-QA status (`shot_status.json`) convention,
  and the scratch-discipline rules. This stage executes the render half of that loop.
- Memory: `[[hyperframes_render_workers_ram]]` (8GB single-worker), `[[video_resolution_rule]]`
  (1080p floor), `[[render_self_qa_required]]` (extract frames + inspect before "done"),
  `[[ahm_assembly_per_shot_render]]` (why per-shot, not one master comp),
  `[[gap_coverage_qa_required]]` (a black frame mid-VO is a bug).

## HARD RULES (non-skippable)

1. **8GB single-worker render.** ALWAYS `-w 1` (`-q draft` for QA iterations, `-q standard`
   for the final pass). `-w auto` OOM-kills silently with exit 144 on this machine
   (`[[hyperframes_render_workers_ram]]`). This is correct for every shot, 2D or 3D.

2. **1080p floor, no exceptions.** Final output is **1920×1080** (`[[video_resolution_rule]]`).

3. **Self-QA the rendered pixels before "done"** (`[[render_self_qa_required]]`). `lint` /
   `validate` read the source; they never see what rendered. A shot is finished only when
   its sampled frames pass the visual scan AND the `render` stage's pixel gates exit 0 via
   the runner. Fix → re-render at draft → re-scan, looping until one fully clean pass.

4. **Per-shot render → ffmpeg-assemble — NOT a single master comp.** HyperFrames
   `data-composition-src` does not drive an animated sub-composition's GSAP from the
   parent (embedded shots render a static end-state — verified, `[[ahm_assembly_per_shot_render]]`).
   So a single `index.html` referencing each lively shot will NOT animate. Render each
   shot standalone and stitch on the VO timeline.

5. **No black frame mid-VO.** A dead/blank frame inside the timeline (timeline gap,
   dropped basemap, brightness glitch) is a shippable bug (`[[gap_coverage_qa_required]]`).
   `qa_black_frame` + `qa_visual_completeness` block on it.

## Architecture — per-shot render, then assemble

The lively shots are separate compositions; render each standalone and stitch on the VO
timeline (see animation-director "Master compositor"). Both MM render modes flow through
the same assembly — **2D noir** shots render via `npx hyperframes render`; **3D bird's-eye
diorama** shots render via `lib/midnight_magnates/threejs_diorama.py` (off-screen WebGL
capture → ffmpeg → MP4). The render mode for each shot is the per-shot decision in
`artifacts/render_modes.json`; do not re-decide it here — render what the animator chose.

```bash
# 1. render every 2D noir shot standalone (single worker — 8GB RAM; assets symlink at
#    chapter dir AND shots/). 3D shots are rendered via threejs_diorama.py.
for s in shots/*.html; do
  npx hyperframes render <chapter_dir> -c "$s" -o "renders/shots/$(basename "$s" .html).mp4" -w 1 -q draft
done
# 2. gap-fillers (beats with no shot) via ffmpeg zoompan on a freeze-frame or the bare scene
# 3. concat in the compiler skeleton's beat order; size fillers so each shot starts on its exact beat
# 4. CFR re-encode to clear concat DTS jitter, then mux the chapter VO:
ffmpeg -fflags +genpts -i renders/_master_silent.mp4 -i artifacts/.../vo_full.wav \
  -vf "fps=30,setsar=1" -c:v libx264 -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -map 0:v -map 1:a -shortest renders/<chapter>_preview.mp4
```

Keep render scratch (frames, fillers, silent master) under `renders/_scratch/` or
`renders/_assembly/` — **never inside** `hyperframes/` (trips `qa_no_reimplementation`).
Read the compiler chapter `index.html` for the authoritative per-beat `data-start` /
`data-duration` — that is the timeline map. Mux the chapter VO only; music + SFX are baked
later by `final-render-director.md`.

## Workflow

1. **Render each shot for self-QA** (`-w 1 -q draft`) — 2D noir via `npx hyperframes
   render`, 3D bird's-eye via `threejs_diorama.py` — then assemble per the block above
   into `renders/<chapter>_preview.mp4`.

2. **Extract frames at 15 FPS for visual inspection**:
   ```bash
   ffmpeg -i renders/<chapter>_preview.mp4 -vf "fps=15" renders/_scratch/qa/f_%04d.jpg
   ```
   Keep these under `renders/_scratch/` (outside `hyperframes/`); delete after capture.

3. **Scan the frame sequence** for (mode-aware — most MM shots are 2D noir medium/micro):
   - Noir look broken (a daylight-bright wash, a generic-AI gradient — this is an authored
     scene, never a Recraft image and never a clip grade)
   - Sprite/overlay collisions (a face or card covering a label)
   - Invisible elements (a label too dark to read, a subject lost on empty canvas)
   - Off-frame elements (a card or cutout clipped by the 1920×1080 edge)
   - 3D bird's-eye misses: a living creature rendered frozen, a model clipped through
     another, a too-close push-in on a low-poly figure
   - Camera/transition glitches between shots
   - Bad easings (a subject warping during a transition)
   - **Black frames mid-VO** (HARD RULE 5)

4. **Run the rendered-pixel gates via the runner** (the automated half of the per-shot
   self-QA loop — see animation-director "Per-shot self-QA loop"). These read the MP4, not
   the source. **Run them through the runner** — it shells the real gate modules, captures
   actual exit codes, and writes the machine-authored `artifacts/qa_report.json`; you never
   invoke a gate by path and you never hand-author that report:
   ```bash
   python3 -m lib.midnight_magnates.runner run-gates \
     --pipeline midnight-magnates-doc --project projects/<id> --stage render
   ```
   Then read `artifacts/qa_report.json`. The `render` stage's blocking pixel gates are:
   - `qa_black_frame` — any black/near-black frame mid-timeline (gap / dropped basemap / brightness glitch)
   - `qa_placement` — a hero/image rendered into a letterbox band instead of filling the canvas
   - `qa_visual_contrast` — labels below WCAG 3:1 contrast, or off-canvas text
   - `qa_visual_completeness` — a dead/blank frame mid-timeline, or a declared visible cue with no geometry
   - `qa_visual_alignment` — a map-scale pin that rendered off its declared lat/lon pixel
   - `qa_creature_animation` — a living creature that rendered static (frozen cutout)
   - `qa_rendered_sync` — a cue whose sampled frame at its anchor time doesn't show its content on its target pixel (data-correct but render-drifted)

   Never invoke a gate by a bare per-gate module path, a `scripts/`-directory Python path, or
   another pipeline package's gate module — those legacy forms are exactly what the build blocks
   for. The only real gates live at `lib/midnight_magnates/gates/`, and the only sanctioned way
   to run them is the runner above. (`ls lib/midnight_magnates/gates/` if you need to confirm a
   name; the manifest's `render` stage is the source of truth for which ones block here.)

5. **Fix + re-render at draft until visually clean AND all pixel gates exit 0.** A fix can
   break another item (moving a label off a dark patch can push it into a face; brightening
   a scene can crush a coastline label; adding a walk cycle can drift a creature out of
   frame) — re-run the FULL scan + the runner gate pass, looping ≥ 3 times until one clean
   pass (per the iterative self-QA contract). Only then promote each shot to
   `self_qa_pass` in `artifacts/shot_status.json`, with its rendered-frame evidence
   attached (the animation-director shot-status convention — `qa_shot_status_clean` fails a
   `self_qa_pass` with empty evidence).

6. **Final render at standard quality** (single worker; 1080p):
   ```bash
   npx hyperframes render <chapter_dir> -c shots/<shot>.html \
     -o renders/shots/<shot>.mp4 -q standard -w 1
   ```
   Re-assemble the chapter at standard quality into `renders/<chapter>_preview.mp4`.

7. **Confirm the render-lock is green AND fresh** before declaring the stage done. The
   runner — not you — decides "done":
   ```bash
   python3 -m lib.midnight_magnates.runner check-lock \
     --pipeline midnight-magnates-doc --project projects/<id>
   ```
   A stale or non-green lock means a gate input changed after the last green pass — re-run
   the render-stage gates and fix before advancing.

8. **VO sync check** — extract the rendered audio and verify the muxed chapter VO stays in
   sync (no drift introduced by concat/CFR re-encode). Cue-level synchrony to VO words is
   gate-enforced upstream (`qa_rendered_sync` at this stage; the `qa_cue_drift` / `qa_drift`
   drift gates on the assembled master); music/SFX sync is handled in `sound-design-director.md`.

## Output

- `renders/<chapter>_preview.mp4` — 1080p, h264, chapter VO muxed (no music/SFX yet)
- `renders/shots/<shot>.mp4` — the per-shot renders behind it
- `artifacts/shot_status.json` updated: every rendered shot `self_qa_pass` with evidence
- `artifacts/render_report.json` — output paths, encoding profile, frame-scan + gate notes
- Frame scans kept under `renders/_scratch/` for record (outside `hyperframes/`)
