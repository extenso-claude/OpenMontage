# Final Render Director — Midnight Magnates

Bake VO + music + SFX into the master render. Final 1080p deliverable.

## Workflow

1. Mix `sfx_mix.wav` + `music_mix.wav` + `vo_full.wav` via ffmpeg `amix` with VO leading.
2. Mux the combined audio onto the assembled `renders/final.mp4` from the render stage. Output `renders/master.mp4`.
3. **Verify the container**: 1920x1080, 24fps, h264. Re-encode to CFR if concat left DTS jitter.
4. **Verify loudness** (must match what the final loudness gate measures — see "Loudness target" below): integrated LUFS inside **[-17, -13]** (aim **~ -16**, consistent with the VO master), true-peak **≤ -1.0 dBFS**, no clipping. Capture the measured values with `ffmpeg ... -af ebur128` (or `loudnorm` measurement pass).
5. Extract final-render frames at 1 FPS for record. Visual sanity check.
6. Set up the local review tool one last time so the user can verify the audio mix.

## Loudness target

The VO master arrived from the voice stage normalized to **~ -16 LUFS** with true-peak **≤ -1.0 dBFS**. Mixing music + SFX under a VO-leading bed must NOT push the muxed master out of the channel's broadcast window. The final loudness gate measures the muxed `master.mp4` and FAILS on:

- integrated loudness outside **[-17.0, -13.0] LUFS** (target ~ -15/-16), OR
- true-peak **> -1.0 dBFS** (no inter-sample headroom).

So normalize the muxed master toward **~ -16 LUFS / true-peak ≤ -1.0 dBFS** and re-measure before you declare done. If the mix lands hot (e.g. SFX accents stacking over VO), trim the bed and re-measure — do not ship at -15 against the older spec; the window is [-17, -13].

## Gate routing — the runner decides "done"

Do not hand-certify the mix. Run the gates through the runner, then read the machine-authored report:

```bash
python3 -m lib.midnight_magnates.runner run-gates --pipeline midnight-magnates-doc --project <dir>
# then read artifacts/qa_report.json (all-green required) and verify freshness:
python3 -m lib.midnight_magnates.runner check-lock --pipeline midnight-magnates-doc --project <dir>
```

At this final stage the runner exercises the loudness gate (and the SFX audibility/sync + audio-drift gates) over the muxed master via ffmpeg's `ebur128`. A non-zero exit blocks the deliverable; the render-lock refuses to certify a master unless `qa_report.json` is all-green AND its input hashes are still fresh. If you must name the final loudness gate, it lives at `lib/midnight_magnates/gates/qa_loudness.py` — run `ls lib/midnight_magnates/gates/qa_*.py` for the real set, and prefer "run the runner, read qa_report.json" over enumerating gate names.

## Output

`renders/master.mp4` — the deliverable. 1080p @ 24fps. Audio mixed and mastered to ~ -16 LUFS (gate window [-17, -13]), true-peak ≤ -1.0 dBFS.
