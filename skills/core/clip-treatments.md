---
name: clip-treatments
description: When using potentially copyrighted third-party clips, images, or audio in a video, apply the LOCKED transformative treatment defaults. Covers identification, sourcing (≤5 min cap), audio role tagging, the filter + frame wrap rule, and copyright-specific QA additions. Read before sourcing any non-PD media for a Sleep Network channel edit.
layer: 2
status: production
applies_to_channels: [midnight_magnates, grandpa_huxley, sleep_network_*]
applies_to_pipelines: [hybrid, documentary-montage, clip-factory]
companion_files:
  - projects/iran-us-history-clip-toolkit-v1/toolkit/approved_toolkit.json   # canonical config
  - projects/iran-us-history-clip-toolkit-v1/toolkit/filters/filter_library.py
  - projects/iran-us-history-clip-toolkit-v1/toolkit/audio_treatments/audio_library.py
  - projects/iran-us-history-clip-toolkit-v1/hyperframes_project/compositions/frame-*.html
  - styles/sleep-network-base.yaml  (clip_treatment block)
  - shared sheet 1v1pI_x1s7ermhkG1ryNxhNxelDQuliCM6l-3hHRwwY8  (Animation Library, rows 22-33)
memory_anchors:
  - copyright_treatment_defaults
  - clip_vo_dialogue_handling
  - clip_source_download_strategy
  - internet_archive_partial_fetch
  - hyperframes_render_workers_ram
---

# Clip Treatments — Transformative Use of Third-Party Material

Used for moments where the iconic source IS the content (specific broadcast, on-camera figure, news photo) and free stock won't carry it. **None of this material publishes raw.** Identify, clip, then apply the locked transformation.

## Locked defaults (DO NOT substitute)

| Media | Filter / treatment | Frame wrap |
|---|---|---|
| Copyrighted **video** | `grade_cyan_orange` on video track + `pitch_up_1st` on audio if kept (vo-pause) | one of 8 approved frames |
| Copyrighted **image** | `grade_crushed_warm` (after Ken Burns) | one of 8 approved frames |
| Copyrighted **audio** (standalone or kept-from-clip) | `pitch_up_1st` (loudnorm I=-14 auto-appended) | n/a |
| **Character image** | EXEMPT — route to existing character cards in the main flow | n/a |

User locked these defaults on 2026-05-20 (filter+frame for video/image) and 2026-05-21 (audio = pitch_up_1st after sampling pitch_down 1-2st and pitch_up 1-3st).

## The 8 approved frames

| Frame | Channel affinity | Best situation |
|---|---|---|
| `tv-vintage` | both | retro broadcast / archival news |
| `dossier` | Midnight Magnates | classified document reveal |
| `newspaper` | both | breaking news / headline moment |
| `fireside` | Grandpa Huxley | cozy storytelling / mantel photograph |
| `surveillance` | Midnight Magnates | spy / intelligence / "we're watching" |
| `boardroom` | Midnight Magnates | power-meeting / executive reveal |
| `magnifier` | both | investigation / evidence detail |
| `library` | Grandpa Huxley | historical knowledge / quiet reflection |

Source: `projects/iran-us-history-clip-toolkit-v1/hyperframes_project/compositions/frame-<name>.html`
Render: `npx hyperframes render -c compositions/frame-<name>.html -o out.mp4 -q draft -w 1`

**Other frames** in the same directory (telex, ledger, projector, photo-album, candlelight, train-window, pocket-watch, radio-broadcast, globe, wax-letter, map-route, magnifier variants) are experimental — usable when no approved frame fits, but the production default must use one of the 8.

## Sourcing (priority order)

1. **Internet Archive first** — `archive.org/advancedsearch.php?q=<query>&output=json`. ffmpeg HTTP-range stream-fetch is the right way to grab a partial:
   ```
   ffmpeg -y -ss <start> -i "https://archive.org/download/<id>/<filename>.mp4" -t <duration> \
          -c:v libx264 -preset fast -crf 23 -c:a aac out.mp4
   ```
   Universal Newsreels (`collection:"universal_newsreels"`) is fully PD.
2. **yt-dlp** as fallback — `--download-sections "*HH:MM:SS-HH:MM:SS"` with ±10s padding. YouTube SABR may 403; log and try another upload.
3. **Hard cap:** never store a single source clip longer than **5 minutes** on disk.

## Required workflow gates

**Before any transformation:** frame-by-frame fit check. Sample candidate frames every ~10s via ffmpeg. Modern docs often mix archival with talking heads — the archival sections may be only seconds. Reject misfits.

**Audio role tag per clip:**
- `vo-pause` → VO breaks around the clip; treated clip audio plays. (See memory `clip_vo_dialogue_handling`.)
- `vo-over` → VO plays through; clip audio muted or ducked.
- `mixed` → VO speaks AND clip audio plays, ducked ≥ -8 dB.

## NO-EXTRA-CHYRON rule (LOCKED 2026-05-21)

**A clip composited inside an approved frame already IS the chyron.** Adding a lower-third like "ARCHIVE FOOTAGE", "1942 — Wehrmacht parade", or "Vatican Bank press conference" ON TOP of a frame-wrapped clip is forbidden.

The 2026-05-21 Vatican Entity review found 4 clip cues had stacked lower-thirds saying "ARCHIVE FOOTAGE" — redundant with the dossier / surveillance / tv-vintage frame wrap, and read as cluttered.

**Rule:** The clip + grade + frame + audio-role tag IS the treatment. Anything that needs to be SAID about the clip (year, location, context) goes into the FRAME's built-in caption slot (each approved frame has one), not a separate lower-third stacked over it.

| Approved frame | Built-in caption slot location |
|---|---|
| `tv-vintage` | Bottom-bar headline, mid-frame |
| `dossier` | Top-right "CLASSIFIED" stamp + bottom-left handwritten file label |
| `newspaper` | Headline at top, subhead below |
| `fireside` | Mantel placard at top |
| `surveillance` | Bottom-left timestamp + top-right "CAM 1" label |
| `boardroom` | Bottom name plate |
| `magnifier` | Outside the lens — caption to the right |
| `library` | Spine label, mid-frame |

When sourcing a frame for a clip, identify which caption slot to use and inject the year / context there. Do not add a separate cuelist entry for a chyron over the same window.

QA: `qa_clip_no_extra_chyron.py` reads the cuelist, finds every `clip_*` cue, checks no `lt_*` / `card_*` cue overlaps its window. Fails compose on violation.

## Reference: Google Sheet animation library (frame catalog)

The shared business Google Sheet at ID `1v1pI_x1s7ermhkG1ryNxhNxelDQuliCM6l-3hHRwwY8` (rows 22-33) catalogs all frame compositions — the 8 production-approved ones plus the experimental ones. When picking a frame:

1. **Default first to the 8 approved frames** per the table above.
2. **Consult the sheet's "Best Fit" column** if none of the 8 obviously fits — there may be a period-specific frame (Renaissance ledger, WWII telex, 1980s VHS scan-line) that the 8 don't cover.
3. **Propose new frames** when the story / time period demands them. New frames live at `projects/iran-us-history-clip-toolkit-v1/hyperframes_project/compositions/frame-<slug>.html`. Render with `npx hyperframes render -c compositions/frame-<slug>.html -o out.mp4 -q draft -w 1`.

To read the sheet programmatically (OAuth flow per `feedback_google_drive_oauth` memory):

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/spreadsheets.readonly'])
sheets = build('sheets', 'v4', credentials=creds)
result = sheets.spreadsheets().values().get(
    spreadsheetId='1v1pI_x1s7ermhkG1ryNxhNxelDQuliCM6l-3hHRwwY8',
    range='Frames!A22:F33'
).execute()
for row in result.get('values', []):
    print(row)  # [slug, name, channel_affinity, best_situation, time_period, status]
```

## Period-appropriate frame selection (NEW 2026-05-21)

Match the frame to the clip's TIME PERIOD, not just the channel default:

| Clip period | Suggested frames |
|---|---|
| Pre-1700 (engravings, paintings) | `library` (bookshelves + globes), `dossier` (vellum-feel), `newspaper` (period broadsheet variant if available) |
| 1700–1899 | `dossier`, `library`, `magnifier` (investigative period) |
| 1900–1945 | `tv-vintage` (only if pre-broadcast era is OK as stylization), `dossier`, `newspaper` |
| 1945–1989 | `tv-vintage` (perfect fit), `surveillance`, `boardroom`, `magnifier` |
| 1989–present | `tv-vintage` (broadcast news), `surveillance`, `boardroom` |

For pre-photography periods, **never use `tv-vintage` for a clip-of-a-painting** — the CRT scanlines on a Renaissance painting reads as anachronistic / AI-slop. Use `library` or `dossier` instead.

## QA additions for transformed clips

Runs alongside the standard pipeline QA loop:

- Filter applied per the locked rule — no substitute
- Output composited inside an approved frame — never bare
- **No stacked lower-third over the frame-wrapped clip** (NEW 2026-05-21)
- **Period-appropriate frame chosen** for the clip's source decade (NEW 2026-05-21)
- Source watermark detection (network bugs, chyrons, channel logos) → cropped, masked, or hidden by the frame
- Audio-role tag recorded; VO timeline has matching silence gap if `vo-pause`
- Mean luma 25–50 (qa_pass.py `brightness_in_band`); dark-source × dim-filter combos flagged for editor review
- No identifiable private individuals in compromising framing
- Provenance row in `sources_manifest/sources.json` — URL, title, accessed date, license claim

## How to invoke

From any pipeline stage that has clip_treatment available in `tools_available`:

```python
from tools.clip_treatment import ClipTreatment
ct = ClipTreatment()

# Apply locked video filter
ct.execute({"operation": "apply_filter", "input_path": clip, "output_path": out,
            "recipe": "grade_cyan_orange"})

# Apply locked audio treatment
ct.execute({"operation": "apply_audio", "input_path": clip, "output_path": out,
            "recipe": "pitch_up_1st"})

# Wrap inside an approved frame
ct.execute({"operation": "wrap_in_frame", "input_path": treated_clip,
            "frame": "dossier", "output_path": final})
```

## What to read next

- For the full recipe catalog (22 filters, 13 audio recipes, 19 frame compositions): browse `projects/iran-us-history-clip-toolkit-v1/toolkit/` and `hyperframes_project/compositions/`.
- For QA tooling: `projects/iran-us-history-clip-toolkit-v1/scripts/qa_pass.py` (17-check pass) and `qa_loop_5_rounds.py`.
- For the master comparison reel (every variation back-to-back, 12:17): `projects/iran-us-history-clip-toolkit-v1/renders/comparison_reel_v2/99_master_reel_v2.mp4`.
- Memory anchors are listed in this file's frontmatter — read them when in doubt.
