# Asset & Clip Director — Midnight Magnates

Companion to `asset-director.md`. The asset-director skill tells you WHAT to source per storyboard beat. THIS skill governs the **copyright posture** of every imagery beat: the Midnight Magnates transformative-use workflow — copyright-search-first, transform-then-frame any third-party media, Nano-Banana fallback for faces, NO-EXTRA-CHYRON.

The single most important thing to get right: **the Midnight Magnates LOOK is noir, and that noir comes from first-party HyperFrames scenes — NEVER from a clip grade.** Clip grades exist for exactly one job: to push third-party copyright / potential-copyright assets AWAY from their original (defeat copyright + audio fingerprinting) so they can ride inside one of the 8 approved noir frames. A grade is never the channel style.

## Read first

- `skills/pipelines/midnight-magnates-doc/mm_treatments.json` — the locked noir copyright-transform presets (video → `grade_cyan_orange`, image → `grade_crushed_warm`, kept audio → `pitch_up_1st`, wrap in one of the 8 approved noir frames; character images → character cards; Nano-Banana faces EXEMPT). Every recipe + frame named there is REAL in the shared engine. **This is the only treatment table for this channel.**
- `skills/core/clip-treatments.md` — the shared transformative-use engine, the 8 approved frames, the NO-EXTRA-CHYRON rule, period-appropriate frame selection by source decade.
- memory `copyright_treatment_defaults` — the locked filter+frame recipes (video → `grade_cyan_orange`; image → `grade_crushed_warm`; kept audio → `pitch_up_1st`; character images → character cards).
- memory `feedback_mm_noir_look_vs_grades` — **the reason this skill exists**: the noir LOOK is HyperFrames-generated scenes (no Recraft); clip grades are copyright-transform-only and never the channel style; Nano Banana is the faces / fallback path.
- `tools/clip_treatment/` — the engine. **Reuse it. Never duplicate it.**

## HARD RULES (the channel identity — do not drift, skip, or reinterpret)

1. **NOIR LOOK = HyperFrames, NOT a clip grade.** The Midnight Magnates channel look (`"night colors, noir atmosphere, moonlit, flat segmented color illustration"`) is produced by first-party HyperFrames-generated flat-segmented noir scenes. It is NOT Recraft/Flux/Imagen/DALLE, and it is NOT a clip grade. The clip grades in `mm_treatments.json` (`grade_cyan_orange` / `grade_crushed_warm` / `pitch_up_1st`) transform THIRD-PARTY COPYRIGHT assets away from copyright ONLY. Never run a clip grade over a first-party HyperFrames scene or a Nano-Banana face.

2. **COPYRIGHT-SEARCH-FIRST, for images AND video.** For every imagery beat you ALWAYS also search the copyright / potential-copyright space — not only PD/free. Copyright-free is not always the best material to carry the story. You are hunting the BEST asset for the beat, then deciding how to clear it — not stopping at the first PD hit. A beat whose asset record shows only a PD/free search, with no copyright search and no documented generation reason, is a **`qa_asset_sourcing` FAIL.**

3. **TRANSFORM-THEN-FRAME any third-party copyright / potential-copyright media.** Route it through the shared engine (`tools/clip_treatment/`, `ClipTreatment`) using the `mm_treatments.json` defaults: VIDEO → `grade_cyan_orange`, IMAGE → `grade_crushed_warm`, then wrap the graded output inside ONE of the 8 approved noir frames (frame chosen by source decade + situation, per `clip-treatments.md`). If the clip's own audio is kept, ALSO apply `pitch_up_1st`. Raw, ungraded, unframed third-party copyright media in the manifest = **`qa_clip_treatment` FAIL.**

4. **NANO BANANA is the ONLY allowed AI image generator, and it is the FALLBACK — not the default.** Recraft / Flux / Imagen / DALLE are FORBIDDEN (`qa_image_gen_policy`). When no good real asset clears, generate with Google Nano Banana — paid, **per-run user approval required** (announce tool + provider + cost before the call, per AGENT_GUIDE Decision Communication Contract), under the per-video generation cap (`qa_generation_budget`), and with **NO baked text** in the image (memory `feedback_ai_image_no_text` — all text via HF/Remotion overlay). The generated asset's record carries `copyright_status: "generated"` + a non-empty `sourcing.generation_reason`. A generated asset with no documented reason = **`qa_asset_sourcing` FAIL.**

5. **EMOTIONAL beats are FACES — real first, Nano Banana second.** Emotional medium/close-up beats want a human face: a real still or clip FIRST (sourced + transformed per rule 3 if it's copyright), else a Nano-Banana face. The same FORBIDDEN list (Recraft/Flux/Imagen/DALLE) applies; Nano Banana is the only AI face path. Face beats route to the main flow's character cards / cutouts (see rule 6), not the inline copyright-frame wrap.

6. **CHARACTER images are EXEMPT from the frame-wrap rule.** A portrait of a person we are introducing / telling a story about is a character CARD, not third-party B-roll — it routes to the main flow's **character cards / cutouts**, NOT the noir copyright-frame wrap (a face in a gilt oval is a character card). Mark these `category: "portrait"` / `"character_cutout"` or `is_character: true`. `qa_clip_treatment` skips them. **Nano-Banana-generated faces are likewise exempt** from grade+frame: they are the channel's own first-party art (`copyright_status: "generated"`), not a copyright asset.

## Applying the noir transform — the locked default

Pull the recipe from `mm_treatments.json`; do not hand-pick grades. The defaults (LOCKED — filter+frame 2026-05-20, audio `pitch_up_1st` 2026-05-21):

| Asset kind | Grade (copyright-transform) | Frame | Audio (only if kept) |
|---|---|---|---|
| VIDEO (copyright / potential_copyright, non-character) | `grade_cyan_orange` | one of the 8 noir frames (by source decade + situation) | `pitch_up_1st` if `audio_role` is kept/mixed/vo_pause |
| IMAGE (copyright / potential_copyright, non-character) | `grade_crushed_warm` (after any Ken Burns move) | one of the 8 noir frames | — |
| Character / portrait / Nano-Banana face | — (EXEMPT) | route to character card | — |
| PD / free_license | — (EXEMPT) | — | — |

The 8 approved noir frames are the first 8 of `ClipTreatment.APPROVED_FRAMES`: `tv-vintage`, `dossier`, `newspaper`, `fireside`, `surveillance`, `boardroom`, `magnifier`, `library`. Each has a built-in caption slot that carries the year/context — **do NOT stack a separate lower-third over a frame-wrapped clip** (NO-EXTRA-CHYRON, locked 2026-05-21). Pick the frame by the source's decade + situation (e.g. `tv-vintage`/`newspaper` for 1945+ broadcast and headline moments; `surveillance`/`dossier`/`boardroom` for intelligence / classified / power-reveal beats) per `skills/core/clip-treatments.md`. The 6 warm frames now in `APPROVED_FRAMES` (`candlelight`, `wax-letter`, `pocket-watch`, `train-window`, `dossier-warm`, `magnifier-warm`) belong to the Grandpa Huxley channel — Midnight Magnates keeps its noir frames.

Apply it exactly like any clip treatment — reuse the engine, never duplicate it:

```python
from tools.clip_treatment import ClipTreatment
ct = ClipTreatment()

# VIDEO: copyright-transform grade, NOT the channel look
ct.execute({"operation": "apply_filter", "input_path": raw, "output_path": graded,
            "recipe": "grade_cyan_orange"})
# (IMAGE would use recipe="grade_crushed_warm")

# wrap inside one of the 8 noir frames (frame chosen by source decade + situation)
ct.execute({"operation": "wrap_in_frame", "input_path": graded,
            "frame": "surveillance", "output_path": final, "clip_duration": 6})

# kept clip audio only: defeat audio fingerprinting
ct.execute({"operation": "apply_audio", "input_path": kept_audio,
            "output_path": treated_audio, "recipe": "pitch_up_1st"})
```

## Asset record contract (what the gates read)

Extend each `artifacts/asset_manifest.json` asset with a copyright posture. Backward compatible with the existing shape (`asset_id`, `category`, `path`, `license`, `source_url`).

```jsonc
{
  "asset_id": "boardroom_meeting_clip",
  "category": "clip",                  // imagery categories the gates scan; character cats are exempt
  "path": "assets/scenes/boardroom_treated.mp4",
  "copyright_status": "potential_copyright",  // pd | free_license | copyright | potential_copyright | generated
  "treatment": "grade_cyan_orange",    // REQUIRED for copyright/potential_copyright (non-character): video=grade_cyan_orange, image=grade_crushed_warm
  "frame": "surveillance",             // REQUIRED for copyright/potential_copyright (non-character): one of the 8 noir frames
  "audio_role": "vo_pause",            // if a kept-audio clip: also record pitch_up_1st was applied
  "original_source": "broadcast news, 1981",
  "sourcing": {
    "searched_free": true,             // PD/CC tier searched (find_assets.py)
    "searched_copyright": true,        // copyright/potential-copyright space ALSO searched  <-- qa_asset_sourcing
    "queries": ["reagan attempt 1981 broadcast", "1981 hinkley press footage"],
    "generation_reason": ""            // non-empty ONLY when copyright_status == "generated"
  }
}
```

- **`pd` / `free_license`** imagery: no treatment/frame required. `sourcing.searched_free` must be true.
- **`copyright` / `potential_copyright`** non-character imagery: `treatment` (`grade_cyan_orange` video / `grade_crushed_warm` image) + `frame` (one of the 8 noir frames) REQUIRED (`qa_clip_treatment`), and `sourcing.searched_copyright` true (`qa_asset_sourcing`). Kept-audio clips also record `pitch_up_1st`.
- **`generated`** imagery (Nano Banana): `sourcing.generation_reason` REQUIRED and non-empty (`qa_asset_sourcing`); EXEMPT from grade+frame.
- **Character** assets (`category` in the character set — `portrait` / `character` / `character_card` / `character_cutout` / `cutout` — or `is_character: true`): exempt from `qa_clip_treatment`; still need a `sourcing` block.

## Gates this skill is enforced by

This stage's gates are REAL and live in `lib/midnight_magnates/gates/`. **Run them through the deterministic runner — never hand-certify, and never invoke a gate by an ad-hoc path.** The runner decides "done":

```bash
python3 -m lib.midnight_magnates.runner run-gates --pipeline midnight-magnates-doc --project <dir>
# then read artifacts/qa_report.json, and confirm the render-lock:
python3 -m lib.midnight_magnates.runner check-lock --pipeline midnight-magnates-doc --project <dir>
```

The asset-stage gates relevant to THIS skill (the runner runs the full set; these are the ones this skill governs):

- **`qa_clip_treatment`** — every third-party copyright/potential-copyright IMAGE or VIDEO asset has a real `treatment` recipe applied AND a `frame`. Raw third-party media = FAIL. Character-card images and Nano-Banana faces are exempt.
- **`qa_asset_sourcing`** — every imagery beat's asset record proves the copyright/potential-copyright space was searched (`sourcing.searched_copyright`) OR carries a documented `sourcing.generation_reason`.
- **`qa_image_gen_policy`** — every asset's generator must be permitted; Recraft / Flux / DALLE / Imagen are FORBIDDEN; `nano_banana` is the only allowed AI image generator and must stay under the per-video cap.

`qa_clip_treatment` and `qa_asset_sourcing` ship good/bad fixtures and are wired into `lib/midnight_magnates/gates/test_gates.py`. To see the full set of real gate modules: `ls lib/midnight_magnates/gates/qa_*.py`.
