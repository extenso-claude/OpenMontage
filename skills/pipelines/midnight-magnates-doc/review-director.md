# Review Director — Midnight Magnates

Set up the local review tool for human feedback on the draft render.

## Read first

- `skills/core/local-review-tool.md` — canonical bootstrap pattern
- Canonical review tool: `lib/review_tool/` (`review.html`, `serve_review.py`, `README.md`)

## Workflow

1. Copy the canonical reviewer into this project:
   ```bash
   cp lib/review_tool/review.html      projects/<project_id>/review/
   cp lib/review_tool/serve_review.py  projects/<project_id>/review/
   ```

2. Point the reviewer at the draft render and shot map:
   - Rendered MP4 at `../renders/master_draft.mp4` relative to `review/` (the path `serve_review.py` serves)
   - Update the `SHOT_MAP` constant near the top of `review.html` with per-chapter timestamps from `script.json` + per-cue markers from the storyboard

3. Tell the user to run `python3 serve_review.py` from `review/` and open the studio at `http://localhost:3010` (override with `REVIEW_PORT`).

4. Wait for user to submit comments via the tool (writes to `review/submitted_comments/latest.json`).

5. Map each comment to a concrete cuelist edit. Re-render. Repeat until user approves.

## Output

`review.html` + `serve_review.py` copied in with `SHOT_MAP` set; serve_review.py running; user can scrub + comment.
