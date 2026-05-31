# Storyboard Director — Animated History Map

Per chapter, emit a schema-valid `storyboard_<chapter_id>.json`. Uses per-chapter Scene Director subagents in parallel.

## Read first

- `docs/animated-history-map-design-intel.md` §2 (primitive catalog) + §9 (per-build guidance for this project) + §15 (timing contract)
- `schemas/artifacts/animated_history_map_storyboard.schema.json`
- `artifacts/script.json` (the locked VO) + Whisper transcripts in `artifacts/whisper/`
- `artifacts/theme.json` (for posture + camera_language + ui_furniture)
- `artifacts/geography.json` (for anchor IDs)

## Workflow

### 1. As the orchestrator, write the showrunner contract first

A `showrunner_contract.json` document:

```jsonc
{
  "macro_arc": {
    "tonal_contour": ["solemn_curious", "rising_stakes", "tragic_inevitability", "modern_anxiety", "open_question"],
    "chapter_runtime_budget_s": { "ch00": 45, "ch01": 70, "ch02": 100, ... },
    "spine_thread": "the next pin has not been drawn yet",
    "spine_planted_chapter": "ch00_cold_open",
    "spine_callback_chapters": ["ch05_t_roosevelt", "ch11_reagan", "ch14_closing"]
  },
  "phase_template": ["map_breath", "approach", "characters", "story_dive", "climax", "aftermath", "return_to_map", "transition"],
  "phase_durations_default_s": { "map_breath": 5, "approach": 5, "characters": 12, "story_dive": 25, "climax": 8, "aftermath": 15, "return_to_map": 6, "transition": 4 },
  "camera_language": "static_with_accents",
  "map_posture": "hybrid"
}
```

### 2. Dispatch per-chapter Scene Director subagents

One subagent per chapter, in parallel. Each receives:

- The showrunner contract
- Theme JSON
- Geography JSON (sliced to this chapter's anchors)
- Canonical names dictionary
- This chapter's VO text + Whisper transcript
- Adjacent chapters' outgoing_state (for phase state contract continuity)

Each Scene Director's deliverable: `artifacts/storyboard/storyboard_<chapter_id>.json`.

### 3. Phase state contract (cross-phase continuity)

Every chapter declares `incoming_state` (from prior chapter's outgoing_state) and `outgoing_state` (passed to next chapter). State includes:

- `basemap_tier`
- `active_pins[]` and `dimmed_pins[]`
- `year_display`
- `weather`, `time_of_day`
- `active_ui_furniture[]`
- `chapter_subject_id`

Validation script: after all storyboards land, verify each chapter's `outgoing_state` == next chapter's `incoming_state`.

### 4. Per-beat schema

Every beat has:
- `start_anchor` (Whisper word + optional ms offset)
- `end_anchor`
- `layers[]` — each layer action declares its layer (L0–L11) + primitive (enum) + anchor_id / asset_id / params
- `transitions_out[]` — explicit fade/cut/morph rules

### 5. Experimental escape hatch

Per phase, MAX 2 beats may be `experimental: true` (bypass enum) with `experimental_rationale`. Caught by depth-review, not gates.

### 6. Enhancement scout subagent (per chapter, parallel)

A separate "enhancement scout" subagent reviews each chapter's draft storyboard and proposes 3–5 enhancement opportunities:

- Etymology micro-spikes
- Period-instrument SFX moments
- Concept-stamp typography overlays
- Atmospheric breath beats between chapters

Scene Director incorporates or rejects each with rationale.

## Gates

- `qa_timing_anchors.py` — every beat has start+end anchors resolving to Whisper words in this chapter
- `qa_layer_conflicts.py` — no L8 panel overlap; clean L9 handoffs
- Schema validation per chapter

## Render Directives — HARD RULE (gate: `qa_render_directive`)

Every **hero shot** — any beat with `shot_tier: medium_diorama` or `hero: true` — MUST carry a `render_directive`: a path to a rich per-shot brief (`artifacts/shot_briefs/<beat>.md`) authored in the format at `artifacts/shot_briefs/_TEMPLATE.md`. This is the spec handed to the animator agents later, and the build **blocks** without it.

- **Three tiers**, each with its own vocabulary: `macro_map` (route draws, pin blooms, label choreography, terrain breath — NOT soldiers/boats), `medium_diorama` (cel-shaded bird's-eye 3D set, the D-Day template, geo-grounded), `micro_offmap` (panels/cards/documents).
- Every directive carries the **BINDING** facts (geo/timing/copy/assets/physics constraints), the richness sections (camera/style, environment, subject animation *with timing intent*, key moments, FX, pacing, lighting/mood), and an explicit **LOCKED / IMPROVISE** split so the animator keeps creative latitude.
- **Motion is determined per shot from the directive — there is NO canned motion library.** The agent authors the motion; `qa_physics` verifies paths/collisions/facing (physics is the gate, never left to the prompt — declare paths + planned interactions in §7).
- Author directives at storyboard time (reviewed at G2). Keep them to **hero shots only** — a pin-drop or year-card needs two lines, not 400 words.

## Human checkpoint

Present the master chapter outline + 1-paragraph synopsis per chapter + sample beat for review, **plus the human-readable storyboard (`<chapter>.human.md`) and the hero-shot Render Directives**. Wait for user approval.
