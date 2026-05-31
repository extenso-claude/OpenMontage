# Local Review Tool

A lightweight Frame.io-like local annotation workflow for any HF master render.
Promoted from `experiments/iran-hook-shotplan/proof/master/review/` (May 2026).

## Quickstart

```bash
# 1. From your project's master folder, copy these two files into review/
cp lib/review_tool/review.html  projects/<my-project>/master/review/
cp lib/review_tool/serve_review.py projects/<my-project>/master/review/

# 2. Make sure the rendered MP4 is at ../renders/master_draft.mp4 relative to review/
ls projects/<my-project>/master/renders/master_draft.mp4

# 3. Launch the server
cd projects/<my-project>/master/review
python3 serve_review.py
# Studio at http://localhost:3010
```

## How users review

- Scrub the video, press **K** at any moment to drop a note
- The tool auto-captures the timestamp + a JPG snapshot of that exact frame
- Type the note, set severity (optional)
- When done, hit **Submit All to Claude** — bundle lands in `submissions/<ts>_review.json` + per-comment frame JPGs in `submissions/<ts>_frames/`

## How Claude reads submissions

```bash
ls projects/<my-project>/master/review/submissions/
cat projects/<my-project>/master/review/submissions/<ts>_review.json
# Read each frame JPG via the Read tool — multimodal context
```

## Customization

The `review.html` has a `SHOT_MAP` constant near the top — update it with your project's shot timestamps + names so the auto-detected `shot_id` on each comment is accurate.

`REVIEW_PORT` env var overrides the default port 3010. Run two instances on different ports for v1/v2 review with independent localStorage.

## Why this exists

Frame.io requires uploading the MP4 and switching to a different app. This pattern stays local: no cloud roundtrip, no API keys, no quota. The trade-off is no multi-user collaboration — for solo review it's strictly better.

See memory: `local_review_tool`.
