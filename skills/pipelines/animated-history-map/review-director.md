# Review Director — Animated History Map

Set up the local review tool for human feedback on the draft render.

## Read first

- `skills/core/local-review-tool.md` — canonical bootstrap pattern
- Existing infrastructure: `framework-videos/execution/review/setup_review.py`

## Workflow

1. Run `setup_review.py` for this project:
   ```bash
   python framework-videos/execution/review/setup_review.py projects/<project_id>
   ```

2. Configure `review/config.json` with:
   - Source video path: `renders/final_draft.mp4`
   - Per-chapter timeline markers from `script.json`
   - Per-cue lane markers from storyboard

3. Tell the user to open `review/review.html` and run `python review/serve_review.py`.

4. Wait for user to submit comments via the tool (writes to `review/submitted_comments/latest.json`).

5. Map each comment to a concrete cuelist edit. Re-render. Repeat until user approves.

## Output

`review/config.json` ready; serve_review.py running; user can scrub + comment.
