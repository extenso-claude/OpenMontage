# Asset Director — Midnight Magnates

The assets stage sources (or generates) **every** asset the storyboard references and emits the
`asset_manifest` — `artifacts/asset_manifest.json`. This skill is the **governing skill for
Midnight Magnates sourcing POLICY**: where each asset may come from, when AI generation is
allowed, and what provenance + coverage every record must carry so the assets-stage gates pass.

**Scope split (do not duplicate):** this skill OWNS *sourcing policy* (search order, the
copyright-search obligation, the image-gen allow/deny list, manifest provenance + coverage). It
**DEFERS the clip transformative-use specifics** — which grade recipe, which approved frame, the
no-extra-chyron rule, the kept-audio recipe, per-era treatment — to
[`asset-and-clip-director.md`](asset-and-clip-director.md), the companion skill. When a beat needs
a third-party copyright clip *treated*, source it here per policy, then hand the treatment recipe
to that skill. Two gates straddle the boundary: `qa_asset_sourcing` (mine — was the copyright
space searched?) and `qa_clip_treatment` (theirs — is the copyright media actually graded +
framed?).

## Read first

- `[[feedback_mm_noir_look_vs_grades]]` (memory) — the channel-identity split this skill turns on:
  the **noir LOOK** is HyperFrames-generated scenes (no Recraft); **clip grades** are
  copyright-transform-only and are NEVER the channel style. Sourcing must not confuse the two.
- `[[midnight_magnates_style_locked_v2]]` (memory) — the locked noir look string
  (`"night colors, noir atmosphere, moonlit, flat segmented color illustration"`). The asset
  manifest never carries Recraft/Flux/etc. art; bespoke noir visuals are authored in the
  animation stage via HyperFrames, not sourced here.
- `[[feedback_ai_image_no_text]]` (memory) — any generated image (Nano Banana) must contain **no
  baked text**; all text lands via HF/Remotion overlay downstream.
- [`asset-and-clip-director.md`](asset-and-clip-director.md) — the **companion** skill this one
  defers to for clip transformative-use (grade + frame + kept-audio + the manifest copyright
  posture fields). Read it before treating any third-party clip.
- `skills/core/asset-coverage-gates.md` — the cross-channel coverage-gate doctrine (every named
  entity resolves to the treatment that carries it; documented drops, not silent holes).
- `tools/find_assets.py` — the sourcing tool (free/PD/CC tiers **and** the copyright /
  potential-copyright space). Exposed to this stage as the `find_assets` tool.
- `tools/clip_treatment/` — the shared transformative-use **engine** (do not duplicate it). Policy
  lives here; recipe selection lives in `asset-and-clip-director.md`.

## HARD RULES

These are the channel identity for sourcing. They are **non-skippable** — each maps to a real gate
on the assets stage (see *Enforcement model*). Do not drift, reinterpret, or "simplify" them.

1. **The noir LOOK is generated in the animation stage via HyperFrames — never sourced, never
   Recraft, never a clip grade.** Bespoke Midnight Magnates scenes
   (`"night colors, noir atmosphere, moonlit, flat segmented color illustration"`) are authored as
   HyperFrames SVG/GSAP downstream. Do **not** put illustrated "noir scene" art in the asset
   manifest, and do **not** treat the clip grades (`grade_cyan_orange` / `grade_crushed_warm` /
   `pitch_up_1st`) as the channel style — those grades exist ONLY to transform **third-party
   copyright** media away from copyright, and their selection belongs to
   `asset-and-clip-director.md`. (`[[feedback_mm_noir_look_vs_grades]]`,
   `[[midnight_magnates_style_locked_v2]]`)

2. **Copyright-search-FIRST for BOTH images AND video.** For every imagery beat the storyboard
   declares, search the free/PD/CC tiers **and additionally scan the copyright /
   potential-copyright space** — the iconic news still, the specific broadcast clip, the famous
   photograph under a reproduction claim, modern reenactment footage. You are hunting the BEST
   asset for the beat, then deciding how to clear it (transform it, or generate a replacement) —
   not stopping at the first PD hit. Record the searched queries and set
   `sourcing.searched_copyright: true` on the asset record. **A PD/free-only sourcing decision with
   no copyright search and no documented generation reason FAILS `qa_asset_sourcing`.** (Treating
   any copyright media you then choose to use is `asset-and-clip-director.md`'s job.)

3. **Nano Banana is the ONLY permitted AI image generator — and only when free/cleared assets are
   insufficient (especially emotional faces).** When no good real asset exists for an emotional
   medium/close-up FACE beat (real still or clip preferred FIRST), or for any beat free sourcing
   can't fill, generate with **Google Nano Banana**. It is **paid + per-run user-approved**:
   announce tool + provider + cost before the call (AGENT_GUIDE Decision Communication Contract),
   stay under the **per-video cap** (the channel `nano_banana_cap_per_video` quality_rule), and
   bake **no text** into the image (`[[feedback_ai_image_no_text]]`). Set
   `provenance.generator: "nano_banana"`, `copyright_status: "generated"`, and a non-empty
   `sourcing.generation_reason` (what was searched, why nothing cleared).

4. **Recraft / Flux / Imagen / DALL·E / Midjourney / SDXL are FORBIDDEN — outright.** No asset's
   `provenance.generator` may name any of them. `qa_image_gen_policy` reads provenance and refuses
   a single banned-generator asset (and refuses Nano Banana over the cap). Real, non-AI provenance
   — wikimedia, pexels, pixabay, loc, internet_archive, hand-authored sprites — is fine and not
   policed.

5. **Every imagery asset record must be self-documenting for provenance + coverage.** Each carries
   a `copyright_status`, a `sourcing` block (what was searched), a `license` + source URL for
   sourced assets, and `provenance.generator` for generated ones. The manifest is the audit trail
   the gates read; an undocumented sourcing decision is a hard fail.

6. **No silent orphans, no silent holes.** Every asset you put in the manifest must be wired into a
   cue (or formally scrapped with `{reason, evidence_url}`), and every storyboard beat that needs
   an asset must resolve to one. Bookkeeping is gated (`qa_asset_reference_closure`,
   `qa_asset_coverage` — both run at the `qa-visual` stage), so source to the cuelist, not into a
   void.

## What this stage sources (and what it does NOT)

**SOURCE / generate per policy (these land in the manifest):**

- **Real stills & portraits** — Wikimedia Commons, Library of Congress, and (per rule 2) the
  copyright / potential-copyright space for the better image. Named people get a real PD/cleared
  portrait FIRST; route portraits to character cards/cutouts (they are exempt from the clip-frame
  wrap — see below). `category: "portrait"` / `"character_cutout"`.
- **Real video / archival footage / stock B-roll** — Internet Archive (Universal Newsreels,
  Prelinger, government film), Pexels/Pixabay free tier, **and** the copyright space for the
  iconic clip. Any third-party copyright clip you choose is transformed downstream per
  `asset-and-clip-director.md` (grade + frame + kept-audio recipe).
- **Generated faces / fill** — Nano Banana only, under the cap, when rules 3 governs (real asset
  insufficient). Emotional medium/close-up faces are the canonical use.
- **Music** — channel/library music first, then YouTube Audio Library / Free Music Archive per
  chapter mood; record license + source. (Music sourcing is unchanged by the SFX library rule.)
- **SFX** — **library-only** (HARD RULE per `skills/core/sound-design-rules.md`): query the curated
  Sleep Documentaries SFX library via `search_sfx.py`; a needed sound absent from the library =
  **STOP and raise a Missing-SFX proposal** (free-SFX candidates for review, or an ElevenLabs
  prompt to approve → then `ingest_sfx.py` → `normalize_sfx.py` → `add_clap_embeddings.py`). Never
  substitute or silently generate. Reference approved library SFX by `cue_id`.

**Do NOT source / generate here:**

- **The noir LOOK** — bespoke noir scenes are HyperFrames-authored in the animation stage, not
  asset files (rule 1). No "noir illustration" art in the manifest.
- **Recraft/Flux/Imagen/DALL·E/Midjourney/SDXL** — forbidden outright (rule 4).
- **Map-channel furniture** — this is NOT the maps channel: maps are supporting, not central, and
  there is no presidents/depository/hotel/expo-sprite sourcing program. Source only the props an
  actual storyboard beat declares. (Procedural SVG sprites a beat genuinely needs are
  hand-authored in-repo, `category: "sprite"`; they are non-imagery and not policed by
  `qa_asset_sourcing`.)

## Character images are exempt from the clip-frame wrap

A portrait of a person we are introducing/telling a story about routes to the main flow's
**character cards / cutouts**, NOT the copyright-frame wrap. Mark these `category: "portrait"` /
`"character_cutout"` (or `is_character: true`). `qa_clip_treatment` skips them. They still need a
`sourcing` block (rule 5), still pass `qa_face_visibility` (real image ≥ 200×200, face in-bounds —
never a placeholder), and a Nano-Banana-generated face still records `copyright_status:
"generated"` + `provenance.generator: "nano_banana"` + `generation_reason`.

## The asset record contract (what the gates read)

`artifacts/asset_manifest.json` for this channel uses the **gate-shaped** record below (this is the
same shape `asset-and-clip-director.md` documents — the two skills share one manifest). Note: the
runner's `qa_schema_validate` does **not** validate this manifest against the legacy registered
`asset_manifest.schema.json`; for the manifest it only **existence-checks every `path`** (a path
that points at a nonexistent file is a `qa_schema_validate` fail). The operative contract is the
fields the MM gates read, not the legacy schema:

```jsonc
{
  "version": "1.0",
  "assets": [
    {
      "asset_id": "lincoln_portrait",          // canonical key; cue.asset_id references it
      "category": "portrait",                    // character cats are exempt from the clip-frame wrap
      "path": "assets/portraits/lincoln/portrait.png",  // MUST exist on disk (qa_schema_validate)
      "license": "PD",
      "source_url": "https://www.loc.gov/...",
      "copyright_status": "pd",                  // pd | free_license | copyright | potential_copyright | generated
      "provenance": { "generator": "loc" },      // real source OR "nano_banana"; never a forbidden generator
      "sourcing": {
        "searched_free": true,                   // PD/CC tier searched (find_assets.py)
        "searched_copyright": true,              // copyright/potential-copyright ALSO searched  <-- qa_asset_sourcing
        "queries": ["abraham lincoln 1865 portrait", "lincoln gardner photograph"],
        "generation_reason": ""                  // non-empty ONLY when copyright_status == "generated"
      }
    },
    {
      "asset_id": "grieving_widow_face",
      "category": "image",
      "path": "assets/faces/grieving_widow.png",
      "copyright_status": "generated",
      "provenance": { "generator": "nano_banana" },   // the ONLY permitted AI image generator (rule 3/4)
      "sourcing": {
        "searched_free": true,
        "searched_copyright": true,
        "queries": ["widow mourning period photograph", "grieving woman 1860s"],
        "generation_reason": "No PD/cleared close-up grief face for this emotional beat; generated with Nano Banana (approved, no baked text)."
      }
    }
  ]
}
```

Per-status obligations the gates enforce:

- **`pd` / `free_license`** imagery: `sourcing.searched_copyright: true` (rule 2). No treatment
  required by this skill.
- **`copyright` / `potential_copyright`** non-character imagery: `sourcing.searched_copyright:
  true` here, **and** a real grade + frame applied downstream (`qa_clip_treatment`, owned by
  `asset-and-clip-director.md`).
- **`generated`** imagery: `provenance.generator: "nano_banana"` + non-empty
  `sourcing.generation_reason` (rules 3/5); under the per-video cap (rule 4).
- **Character** assets (character category or `is_character: true`): exempt from
  `qa_clip_treatment`; still need a `sourcing` block and must pass `qa_face_visibility`.
- **Every** manifest `path` must resolve on disk (`qa_schema_validate`); **every** asset must be
  referenced by a cue or carry a valid `scrap {reason, evidence_url}` (`qa_asset_reference_closure`
  at the `qa-visual` stage).

## Asset request channel (just-in-time)

During the animation stage, animator subagents may write to `artifacts/asset_requests.json`
requesting a new asset. A sourcer picks it up and delivers under this same policy (copyright-search
first; Nano Banana only when free is insufficient; provenance + `sourcing` block on the new
record). The animator may proceed on a placeholder, but the final compile blocks until the
requested asset lands and closes against its cue.

## Enforcement model (the runner decides "done", not you)

A deterministic runner — not the agent — shells the gates and writes the machine-authored
`artifacts/qa_report.json`. **Never** hand-author that report, cite a `scripts/qa_*.py` path, or
claim a gate passed on your own say-so. Run the runner and read the report:

```bash
# run THIS stage's gates (assets) + read the result:
python3 -m lib.midnight_magnates.runner run-gates --pipeline midnight-magnates-doc --project <project_dir> --stage assets
# then read artifacts/qa_report.json  (and `check-lock` before any later render)
```

If you must name a gate, it MUST exist as `lib/midnight_magnates/gates/<name>.py`
(`ls lib/midnight_magnates/gates/qa_*.py` for the real set). **Prefer "run the runner, read
qa_report.json" over enumerating gate names.** The assets-stage hard gates the runner applies to
this manifest are:

- **`qa_asset_sourcing`** — every imagery beat proves the copyright space was searched
  (`sourcing.searched_copyright`) OR carries a documented `generation_reason`. *(This skill's
  central rule — rule 2/3.)*
- **`qa_image_gen_policy`** — no forbidden `provenance.generator`; Nano Banana under the per-video
  cap. *(Rule 3/4.)*
- **`qa_clip_treatment`** — third-party copyright image/video is graded + framed (kept audio
  carries a recipe); character cards exempt. *(Deferred to `asset-and-clip-director.md` for recipe
  selection; listed here because it gates the same manifest.)*
- **`qa_face_visibility`** — character portraits/cutouts are real images ≥ 200×200 with the face
  in-bounds (no placeholders / cropped faces).
- **`qa_map_contrast`** — any rendered basemap PNG under `assets/maps/` has real land/water
  contrast (maps are supporting evidence; when a beat uses one it must read).
- **`qa_schema_validate`** — every declared artifact validates against its schema **and every
  asset `path` exists** (catches a dangling manifest reference).

Bookkeeping/coverage gates that read this manifest but run later, at the **`qa-visual`** stage
(source to satisfy them now): **`qa_asset_reference_closure`** (no orphan, no dangling ref, ≤ 30 %
scrapped) and **`qa_asset_coverage`** (every named entity resolves to the treatment that carries
it — `[[skills/core/asset-coverage-gates.md]]`). The paid-generation bill is surfaced by
**`qa_generation_budget`** (Nano Banana stills counted at $0.04 each via
`sourcing.generation_reason`).

## Workflow

1. **Read the storyboard's imagery beats + the declared named entities** (canonical_names) so you
   source to the cuelist, not into a void (rule 6).
2. **For each imagery beat, search BOTH tiers** with `find_assets.py` — free/PD/CC **and** the
   copyright / potential-copyright space (rule 2). Record the queries; pick the BEST asset.
3. **Decide how to clear the chosen asset:** PD/free → use as-is; third-party copyright → keep it
   and hand the grade+frame recipe to `asset-and-clip-director.md`; nothing good → generate (rule
   3) with **Nano Banana only**, under the cap, no baked text, with an announced cost and a
   documented `generation_reason`.
4. **Route portraits to character cards/cutouts** (exempt from the clip-frame wrap); ensure each is
   a real, face-visible image (never a placeholder).
5. **Write each record in the gate-shaped contract** — `copyright_status`, `provenance.generator`,
   the `sourcing` block, `license` + `source_url` (sourced) or `generation_reason` (generated).
   Confirm every `path` exists on disk.
6. **Source music + SFX** — music per chapter mood (library first); SFX **library-only** via
   `search_sfx.py` (STOP + Missing-SFX proposal on any miss).
7. **Close the books** — every asset wired to a cue or formally scrapped `{reason, evidence_url}`.
8. **Run the runner, read `qa_report.json`** (command above) until the assets-stage gates are
   green. The runner — not you — declares the stage done.

## Outputs

- `assets/portraits/<id>/…`, `assets/faces/<id>.png` (Nano Banana), `assets/stock/…`,
  `assets/archival_video/…`, `assets/music/…`, `assets/sprites/…`, `assets/maps/…` — the sourced /
  generated files (every path referenced by the manifest must exist).
- `artifacts/asset_manifest.json` — the `asset_manifest` artifact in the gate-shaped contract
  above (provenance + `sourcing` per asset; shared with `asset-and-clip-director.md`).
