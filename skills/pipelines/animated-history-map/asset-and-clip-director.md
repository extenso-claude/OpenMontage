# Asset & Clip Director — Animated History Map

Companion to `asset-director.md`. The asset-director skill tells you WHAT to source per storyboard. THIS skill governs the **copyright posture** of every imagery beat: it ports the Midnight-Magnates transformative-use workflow to the maps channel, with one hard difference — **the maps channel grades to the SUBJECT'S era, never to MM noir.**

## Read first

- `skills/core/clip-treatments.md` — the shared transformative-use engine, the 8 approved frames, the NO-EXTRA-CHYRON rule, period-appropriate frame selection.
- memory `copyright_treatment_defaults` — the locked filter+frame recipes.
- memory `video_specific_coloring` — **the reason this skill exists**: maps-channel palette derives from each video's subject/era/culture (parchment + Civil-War for Lincoln 1865), NOT the noir lock.
- `skills/pipelines/animated-history-map/era_treatments.json` — the era→(filter, audio, frame) presets. Every recipe named there is REAL in the shared engine.
- `tools/clip_treatment/` — the engine. **Reuse it. Never duplicate it.**

## THE HARD RULE (gates: `qa_asset_sourcing`, `qa_clip_treatment`)

For **every visual beat** in the storyboard, in this exact order:

1. **ALWAYS search copyright + potential-copyright sources too — not only PD/free.**
   For every imagery beat, run `tools/find_assets.py` for the free/PD/CC tiers AND additionally scan the copyright / potential-copyright space (the iconic news photo, the specific broadcast clip, the famous painting still under reproduction claim, modern reenactment footage). You are looking for the BEST asset for the beat, then deciding how to clear it — not stopping at the first PD hit. Record that the copyright space was searched in the asset's `sourcing` block (see contract below). A beat whose asset record shows only a PD search, with no copyright search and no documented generation reason, is a **`qa_asset_sourcing` FAIL.**

2. **Transform any third-party copyright / potential-copyright media before use.**
   Route it through the shared engine (`tools/clip_treatment/`, `ClipTreatment`) with an **ERA-APPROPRIATE** grade + frame from `era_treatments.json` — **NOT** MM noir. For Lincoln 1865 that means `sepia_archive` + the `civil-war-portrait` parchment frame, never `grade_cyan_orange` + `tv-vintage` (CRT scanlines on an 1865 engraving read anachronistic / AI-slop — see `clip-treatments.md` period rule). Raw, ungraded, unframed third-party copyright media in the manifest = **`qa_clip_treatment` FAIL.**

3. **Character images are EXEMPT from the wrap-in-frame rule.**
   A portrait of a person we are introducing/telling a story about routes to the main flow's **character cards / cutouts**, NOT the copyright frame wrap (a face in an oval gilt mat is a character card, not "third-party B-roll"). Mark these `category: "portrait"` / `"character_cutout"` or `is_character: true`. Both gates skip them.

4. **If no good asset is found, generate with Google Nano Banana — and document why.**
   Paid, **per-run user approval required** (announce tool + provider + cost before the call, per AGENT_GUIDE Decision Communication Contract). **No baked text** in the generated image (memory `feedback_ai_image_no_text` — all text via HF/Remotion overlay). The generated asset's record MUST carry `copyright_status: "generated"` + a `sourcing.generation_reason` explaining what was searched and why nothing cleared. A generated asset with no documented reason = **`qa_asset_sourcing` FAIL.**

## Era-appropriate treatment — Lincoln 1865 (authored preset)

`era_treatments.json → presets.lincoln_1865`:

| Field | Value | Why |
|---|---|---|
| `image_filter` / `video_filter` | `sepia_archive` | Desaturated, warm-shifted, grainy — period-true for 1865 print/engraving culture. |
| `audio` | `pitch_up_1st` | Only relevant for a modern reenactment clip whose audio is kept; 1865 itself has no recorded audio. |
| `frame` | `civil-war-portrait` | New era frame at `tools/clip_treatment/frames/frame-civil-war-portrait.html`: oval gilt mat, foxed parchment, **telegraph-bar caption slot** (the chyron — no stacked lower-third). |

This preset REUSES the engine. Apply it exactly like any clip treatment:

```python
from tools.clip_treatment import ClipTreatment
ct = ClipTreatment()
ct.execute({"operation": "apply_filter", "input_path": raw, "output_path": graded,
            "recipe": "sepia_archive"})                                   # era grade, not noir
ct.execute({"operation": "wrap_in_frame", "input_path": graded,
            "frame": "civil-war-portrait", "output_path": final, "clip_duration": 6})
```

> The `civil-war-portrait` frame ships in the engine's `frames/` dir so the engine resolves it by filename. It is an **era frame**, not one of the 8 noir-approved frames; the orchestrator selects it via `era_treatments.json`, and `qa_clip_treatment` accepts it as a valid frame. (Integrator note: add `"civil-war-portrait"` to `ClipTreatment.APPROVED_FRAMES` if you want `wrap_in_frame` to accept it without the era-frame allowlist.)

When the story moves to a later era (Garfield 1881, McKinley 1901, JFK 1963, Reagan 1981) pick that era's preset — `tv-vintage` is period-true ONLY for the 1945–1989 broadcast preset.

## Asset record contract (what the gates read)

Extend each `artifacts/asset_manifest.json` asset with a copyright posture. Backward compatible with the existing maps shape (`asset_id`, `category`, `path`, `license`, `source_url`).

```jsonc
{
  "asset_id": "booth_leap_engraving",
  "category": "illustration",          // imagery categories the gates scan; character cats are exempt
  "path": "assets/scenes/booth_leap_treated.mp4",
  "copyright_status": "potential_copyright",  // pd | free_license | copyright | potential_copyright | generated
  "treatment": "sepia_archive",        // REQUIRED for copyright/potential_copyright (non-character)
  "frame": "civil-war-portrait",       // REQUIRED for copyright/potential_copyright (non-character)
  "audio_role": "vo_over",             // if a clip with kept audio: also record the audio recipe used
  "original_source": "Currier & Ives, 1865",
  "sourcing": {
    "searched_free": true,             // PD/CC tier searched (find_assets.py)
    "searched_copyright": true,        // copyright/potential-copyright space ALSO searched  <-- qa_asset_sourcing
    "queries": ["booth leap ford's theatre 1865", "currier ives lincoln assassination"],
    "generation_reason": ""            // non-empty ONLY when copyright_status == "generated"
  }
}
```

- **`pd` / `free_license`** imagery: no treatment/frame required. `sourcing.searched_free` must be true.
- **`copyright` / `potential_copyright`** non-character imagery: `treatment` + `frame` REQUIRED (`qa_clip_treatment`), and `sourcing.searched_copyright` true (`qa_asset_sourcing`).
- **`generated`** imagery: `sourcing.generation_reason` REQUIRED and non-empty (`qa_asset_sourcing`).
- **Character** assets (`category` in the character set, or `is_character: true`): exempt from `qa_clip_treatment`; still need a `sourcing` block.

## Gates this skill is enforced by

- `qa_clip_treatment.py` — every third-party copyright/potential-copyright IMAGE or VIDEO asset has a real `treatment` recipe applied AND a `frame`. Raw third-party media = FAIL. Character-card images exempt.
- `qa_asset_sourcing.py` — every imagery beat's asset record shows the copyright space was searched (`sourcing.searched_copyright`) OR carries a documented `generation_reason`.

Both ship good/bad fixtures and are wired into `test_gates.py`.
