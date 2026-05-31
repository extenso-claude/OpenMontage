---
name: local-review-tool
description: Sleep Network's canonical local HTML video review tool. Provides A/B toggle (source vs composite), 4+ kind cue timeline with zoom + horizontal scroll, comment system with severity tags + persistence + per-comment cue context + submit-to-disk endpoint. Use this for every overlay-postproduction preview so the user can scrub, comment, and submit feedback in one place — Claude reads submitted comments at `review/submitted_comments/latest.json` and applies fixes before re-rendering.
layer: 2
status: production
applies_to_channels: [midnight_magnates, grandpa_huxley, sleepy_biographer, sleep_network_*]
applies_to_pipelines: [hybrid, documentary-montage, clip-factory]
companion_files:
  - framework-videos/execution/review/index.html
  - framework-videos/execution/review/serve.py
  - framework-videos/execution/review/setup_review.py
  - framework-videos/execution/review/config.example.json
memory_anchors:
  - local_review_tool
  - overlay_coverage_gate_mandatory
created: 2026-05-21
---

# Local Review Tool — Sleep Network Canonical

A zero-dependency local-server + HTML reviewer for any Sleep Network overlay-postproduction project. Same HTML works for every project — the project-specific values live in a small `config.json` the HTML loads on boot.

## What it does

| Feature | Behavior |
|---|---|
| **A/B mode toggle** | `A` key (or button) switches between source and composite videos with the same playhead time so the user can flip-flop to see exactly what the overlay layer adds. |
| **Multi-lane timeline** | 7 visible lanes: avatar / card / map / animation / clip / music / sfx + a comments lane below. Each cue is a colored bar; SFX shows as narrow markers. Color-coded by kind. |
| **Timeline zoom** | Z / X keys (or ＋/− buttons) zoom in/out. `0` fits all. Timeline expands inside a horizontally scrollable frame; rest of page stays fixed (grid column constrained via `minmax(0, 1fr)` + `overflow: hidden`). Tick density auto-adapts to zoom level (5-min → 5-sec ticks). |
| **Comment system** | `C` key (or button) opens composer with current timestamp pre-filled. Severity: 🔴 Fix · 🟡 Tweak · 🟢 Like · 🔵 Note. Comments persist in browser localStorage across refreshes. Sidebar shows running list; red dots on timeline mark each. Click any timestamp to jump there. `N` jumps to next comment. |
| **Submit to disk** | "Submit to Claude" button POSTs all comments + each comment's active-cue context to the local server, which writes `review/submitted_comments/<timestamp>__<N>_comments.json` + a `latest.json` pointer. Claude reads from `latest.json` after the user submits. |
| **Cue sidebar** | Full cuelist with filter tabs (All / Avatar / Cards / Map / Animation / Clip / Music / SFX). Click any cue to jump to its t_in. |
| **HTTP Range support** | Server supports byte-range requests so `<video>` seeking works on large ProRes/H.264 MOVs. |

## How to set up for a new project

```bash
python3 /Users/ryanodreher/Desktop/Claude\ code/framework-videos/execution/review/setup_review.py \
    /path/to/projects/<project-slug> \
    --title "My Project (full edit v1)" \
    --duration 3424.0 \
    --cuelist artifacts/cuelist_v1.json \
    --source-mov deliverables_v1/01_source_vo.mov \
    --composite-mov deliverables_v1/02_composite_preview.mov
```

The setup script copies `index.html` + `serve.py` into `<project-slug>/review/` and writes a `config.json` with the per-project values. After that:

```bash
cd /path/to/projects/<project-slug>
python3 review/serve.py
```

Browser opens at `http://localhost:8765/review/index.html`.

## What Claude reads after the user submits

```
projects/<project-slug>/review/submitted_comments/latest.json
```

Shape:
```json
{
  "project": "<slug>",
  "cuelist_version": 4,
  "submitted_at": "2026-05-21T12:34:56.789Z",
  "comments": [
    {
      "id": "cm_1716302400000_4242",
      "t": 320.0,                                   // video time the user was at
      "text": "Avatar lip-sync looks 0.5s late.",
      "sev": "fix",                                 // fix | tweak | like | note
      "created": "2026-05-21T12:34:56.789Z",
      "active_cue_id": "clip_calvi_blackfriars",    // which cue was on screen
      "active_cue_kind": "clip",
      "active_cue_t_in": 320.0,
      "active_cue_t_out": 326.5
    },
    ...sorted by t...
  ]
}
```

Use the `active_cue_*` fields to know exactly which cue the user is flagging. Each `fix`-severity comment is a required change; `tweak` is preference; `like` is keep-as-is feedback; `note` is informational.

## Why this exists

Without a structured review tool, feedback comes back as free-form chat ("the avatar at minute 12 feels off") and Claude has to guess what cue is involved. With this tool:

- The user pins the EXACT video time
- The active cue at that time is auto-attached
- Severity makes priority obvious
- Submit is one click → one file Claude can parse

It also makes review faster because the user has zoom + scrub-to-cue + filter, instead of dragging a generic browser video scrubber.

## Required behavior for Claude

1. **For every overlay-postproduction preview**, run `setup_review.py` against the project, then start the server. Direct the user to the URL.
2. **Tell the user about the C / Z / X / A / N shortcuts** in the same message as the URL. Discoverability matters.
3. **After the user clicks "Submit to Claude"**, read `<project>/review/submitted_comments/latest.json` and write a fix plan that maps each `fix`/`tweak` comment to a concrete cuelist edit.
4. **Do not re-render** anything until either (a) all fixes are mapped to specific edits and confirmed, or (b) the user says "render anyway."

## File map

```
framework-videos/execution/review/
├── index.html              # canonical UI (universal; loads config.json on boot)
├── serve.py                # canonical server (Range support + /submit-comments)
├── config.example.json     # template config
└── setup_review.py         # bootstrap script for a new project

<project>/review/           # created by setup_review.py
├── index.html              # copied from canonical
├── serve.py                # copied from canonical
├── config.json             # project-specific values
└── submitted_comments/     # user comment submissions land here
    ├── 2026-05-21_12-34-56__7_comments.json
    └── latest.json         # symlink to most recent submission (Claude reads this)
```

## Self-Annealing Notes

- **2026-05-21**: First documented after the Vatican Entity v4 run, where the user asked for zoom + comments + submit on the review HTML and we built it inline. Promoted to canonical workflow so every future Sleep Network overlay run uses it. Memory anchor `local_review_tool` already existed (per `memory/MEMORY.md`); this skill formalizes it.
- **CSS gotcha**: timeline zoom requires `grid-template-columns: minmax(0, 1fr) <sidebar-width>` on the `<main>` grid AND `min-width: 0; overflow: hidden` on the stage column, otherwise the timeline's expanded width pushes the whole grid column wider and the page becomes horizontally scrollable instead of just the timeline frame. Don't drop those CSS rules.
- **Keyboard shortcuts**: `Z` / `X` for zoom (not `+` / `−` — those collide with Chrome's browser zoom). `C` for comment. `N` for next comment. `0` for fit-all. `A` for A/B toggle. Plus the standard `Space` / `← →` / `J L` / `, .` for play/scrub.
