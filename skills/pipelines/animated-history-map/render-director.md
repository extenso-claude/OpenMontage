# Render Director — Animated History Map

Render the master HyperFrames composition to 1080p MP4.

## Hard rules (from memory)

- `hyperframes_render_workers_ram` — 8GB RAM machine: ALWAYS use `-w 1 -q standard` (or `-q draft` for QA iterations). `-w auto` OOMs silently with exit 144.
- `video_resolution_rule` — final output 1920x1080 (no exceptions)
- `render_self_qa_required` — extract frames + visually inspect before declaring done

## Architecture — per-shot render, then assemble (NOT one master render)

The lively shots are separate HyperFrames compositions; `data-composition-src` does not drive their GSAP from a parent (embedded sub-comps freeze at an end-state). So render each shot standalone and stitch on the VO timeline (see animation-director "Master compositor"):

```bash
# 1. render every shot standalone (single worker — 8GB RAM; assets symlink at chapter dir AND shots/)
for s in shots/*.html; do
  npx hyperframes render <chapter_dir> -c "$s" -o "renders/shots/$(basename "$s" .html).mp4" -w 1 -q draft
done
# 2. gap-fillers (beats with no shot) via ffmpeg zoompan on a freeze-frame or the bare basemap
# 3. concat in the compiler skeleton's beat order; size fillers so each shot starts on its exact beat
# 4. CFR re-encode to clear concat DTS jitter, then mux the chapter VO:
ffmpeg -fflags +genpts -i renders/_master_silent.mp4 -i artifacts/.../vo_full.wav \
  -vf "fps=30,setsar=1" -c:v libx264 -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -map 0:v -map 1:a -shortest renders/<chapter>_preview.mp4
```

Keep render scratch (frames, fillers, silent master) under `renders/_scratch/` or `renders/_assembly/` — never inside `hyperframes/` (trips qa_no_reimplementation).

## Workflow

1. **Render each shot for self-QA** (`-w 1 -q draft`), then assemble per the block above into `renders/<chapter>_preview.mp4`.

2. **Extract frames at 15 FPS for visual inspection**:
   ```bash
   ffmpeg -i renders/draft.mp4 -vf "fps=15" qa/draft_frames/f_%04d.jpg
   ```

3. **Scan frame sequence** for:
   - Sprite collisions (someone's portrait covering a label)
   - Invisible elements (dust too small, sea labels too dark)
   - Off-frame elements
   - Camera glitches at basemap_swap transitions
   - Bad easings (subjects warping during transitions)
   - Black frames mid-VO

4. **Run the rendered-pixel gates** (the automated half of the per-shot self-QA loop — see animation-director "Per-shot self-QA loop"). These read the MP4, not the source:
   ```bash
   for g in qa_visual_contrast qa_visual_completeness qa_visual_alignment qa_creature_animation; do
     python3 -m lib.animated_history_map.gates.$g --project projects/<id>
   done
   ```
   - `qa_visual_contrast` — labels below 3:1 contrast / off-canvas text
   - `qa_visual_completeness` — dead/blank frame mid-timeline; a declared visible cue with no geometry
   - `qa_visual_alignment` — a pin that rendered off its declared lat/lon pixel
   - `qa_creature_animation` — a living creature that rendered static (frozen cutout)

5. **Fix + re-render at draft until visually clean AND all pixel gates exit 0.** A fix can break another item — re-run the full scan + gates, looping ≥ 3 times until one clean pass (per the iterative self-QA contract). Only then promote each shot's `qa_status` to `self_qa_pass`.

6. **Final render at standard quality**:
   ```bash
   npx hyperframes render --output projects/<id>/renders/final.mp4 \
     --quality standard --fps 24 --workers 1
   ```

7. **Audio sync check** — extract rendered audio, find SFX/music peak windows, verify within ±100ms of scripted timestamps.

## Output

- `renders/final.mp4` (1080p, 24fps, h264)
- `qa/final_frames/` (extracted at 15 FPS for record)
- `artifacts/render_report.json` with stats
