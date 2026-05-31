# Final Render Director — Animated History Map

Bake VO + music + SFX into the master HF render. Final 1080p deliverable.

## Workflow

1. Mix `sfx_mix.wav` + `music_mix.wav` + `vo_full.mp3` via ffmpeg `amix` with VO leading.
2. Mux audio onto `renders/final.mp4` from animation stage. Output `renders/master.mp4`.
3. Verify: 1920x1080, 24fps, h264, audio -15 LUFS, no clipping.
4. Extract final-render frames at 1 FPS for record. Visual sanity check.
5. Set up the local review tool one last time so user can verify the audio mix.

## Output

`renders/master.mp4` — the deliverable. 1080p @ 24fps. Audio mixed and mastered.
