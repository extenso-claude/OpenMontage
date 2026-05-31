# Animated History Map — Rebuild Plan v2.1

**Status:** for human review. A doc has no enforcement power (that was the prior failure) — so the plan's first milestone is to build the load-bearing enforcement spine in CODE before any creative work. **Test video:** "Every Presidential Assassination + Attempt on a Map."

### Revisions in v2.1 (this review round)
1. **Physics by construction** — compiler authors a scene-graph (colliders + z-layers + timed paths); new `qa_physics` gate (§3, §6).
2. **SFX audibility** — new `qa_sfx_audibility` gate catches SFX too quiet to hear (§3, §8).
3. **Sound `sound_intent` seeds** at storyboard time — non-binding, adapt-hard-rule (§8).
4. **Voice QA→fix subsystem** — researched stack + loop (§7).
5. **G-voice human gate** + audio-review tool — review/flag words before storyboarding (§7).
6. **Shot spec split BINDING vs INTENT** + continuity from neighbor shots; physics paths mapped by the agent, verified by gate (§6).
7. **OTIO handoff is human-triggered after final review**, not automatic (§5, §9).
8. **InWorld line breaks ARE the natural-pause mechanism** (user-tested) — preserve them; `<break>` reserved for *ensuring* hard pauses. Tool newline-strip bug is now the top fix (§7, §9).
9. **Nano Banana cap → 50/video** (incl. revisions) — a runaway guard, not a budget; agents are explicitly empowered to use it creatively (§9).
10. **Self-anneal = a retro stage that mints regression-tested gates** from each video's findings (§11).

---

## 0. The one idea that fixes everything

The last build had a great framework and **bypassed all of it** — a 3,830-line monolith, 0 framework primitives, 0 sourced clips, and a `COMPLETION_SUMMARY.md` claiming a `28:13 final.mp4` **that does not exist on disk**. The audit found the only thing in the repo that *never* gets bypassed:

> **`animation_catalog.py` runs its QA INSIDE the tool's `execute()` and returns `success=False` on failure** — un-bypassable because there is no other path to output. Every other gate is a loose `qa_*.py` an agent must remember to run, and a repo-wide grep proves **no orchestrator ever runs them.**

**The whole rebuild generalizes that pattern:** gates live *inside the only sanctioned path to output*, and "done" is produced by a deterministic runner the agent does not control — because you are not in the production loop to catch drift.

---

## 1. Keep / Fix / Kill (grounded in the audit)

| Component | Verdict | Why |
|---|---|---|
| `lib/mapkit_subjects.py` | **KEEP** | Real macro/medium map engine. Web-Mercator, 10 tile providers, 4 filters, `compute_anchor_pixels`, `write_positions_json`. |
| `tools/find_assets.py` | **KEEP** | Real license filter — non-monetizable assets never reach output. |
| `tools/clip_treatment/` | **KEEP** | Real (22 filters, 17 audio, 8 frames). The copyright-defeat toolkit the monolith ignored. |
| `tools/animation/animation_catalog.py` + `composer.py` | **KEEP** | Real, and the **model pattern** (embedded blocking QA). |
| `lib/asset_sourcing/portraits.py` | **KEEP** | Real PD sourcing + credit sidecar. |
| `lib/hf_coverage_qa.py` | **KEEP + harden** | Real gap gate; add rendered-luma sampling to defeat the invisible-cover-clip cheat. |
| `lib/render_placement_qa.py` | **KEEP + fix** | Add `sys.exit`, multi-timestamp sampling, widen to any low-variance band. |
| 4 JSON schemas | **KEEP + fix** | Good contracts but **all UNREGISTERED** — nothing validates against them. `canonical_names` allows an empty dict. |
| 12 director skills + design-intel doc | **KEEP as content** | Strong creative content; relabel false "gate" claims as CRAFT. |
| `inworld_tts` tool | **FIX (top priority)** | **Silently strips line breaks** (joins chunks with a space) — and per your testing line breaks ARE the pause mechanism, so this nullifies your pause strategy. Also SSML-unaware chunking can cut a `<break>` / exceed 20/request. |
| `pipeline_loader.check_extension_permitted()` | **FIX — wire in** | The one real guardrail is **called nowhere.** Wiring it would have blocked the monolith. |
| `qa_asset_coverage.py` (vatican) | **FIX — generalize** | Real gate but hardcoded literals + checks PLAN not pixels + unaudited free-text scrap escape. |
| 17 named "hard gates" | **BUILD** | No `scripts/` dir; **zero** exist for this pipeline. |
| `lib/animated_history_map/` ("the compiler") | **BUILD — empty directory** | The "compiler that bans freehand easings" never existed. Highest leverage. |
| `projects/presidential-assassinations-map/` | **KILL — exhibit only** | Monolith, fabricated completion. |
| `projects/presidential-assassinations-v2/` | **CONTINUE** | Framework-aligned rebuild already here. |
| Review-tool fork | **Use canonical** | `framework-videos/execution/review/`; retire `lib/review_tool/` (crash bug). |

---

## 2. Enforcement spine — three structural inventions

**2.1 The Runner + manifest gates.** Add `hard_gates:[{name,cmd,expect_exit:0}]` + `requires_human_approval` to the manifest schema. `scripts/run_stage.py` runs each gate and **refuses to advance** on any non-zero exit or missing approval artifact. Free-text `success_criteria` become executable walls.

**2.2 The Compiler** (`lib/animated_history_map/compiler.py`). **Storyboard JSON → HyperFrames HTML is the ONLY emitter.** Freehand becomes impossible: (1) the compiler schema-validates first (off-enum primitive = hard error); (2) `check_extension_permitted()` is **wired in** (a project-level `.py` while `custom_scripts:false` raises); (3) an **anti-bypass lint** fails the build on re-implemented engine logic (hand-rolled Mercator, inline ffmpeg, hardcoded map CSS %). *Offering a better engine didn't stop the last monolith — it wrote its own; the gate must forbid re-implementation.*

**2.3 The Gate-runner writes "done", not the agent.** `scripts/run_gates.py` shells every gate, captures **real exit codes**, writes machine-authored `qa_report.json` (schema *requires* `exit_code:0` per gate + runner signature + input hashes). Final render is **physically blocked** unless the report is all-green AND fresh. Kills the self-asserted "clean" report and the fabricated-`final.mp4` at once.

---

## 3. The gate suite — every documented failure → one un-bypassable gate

| Gate | Catches | How |
|---|---|---|
| **Schema-validation** | "rolled its own vocabulary, 0 framework primitives" | Validate storyboard/theme/geo/canonical; existence-check **every** asset path → dangling refs hard-fail. |
| **VO-content-unchanged** | "don't change VO content when adding tags" | Strip tags/breaks/CAPS/whitespace; assert it equals the human-approved script word-for-word. |
| **Voice-markup** | flat VO; dropped pauses; wrong voice | **Line breaks preserved to the API** (never stripped); `<break>` ≤20/request, beats 500–850ms, big turns 1.2–2.0s; steering tags before-text only; `deliveryMode=CREATIVE`, `voiceId` locked; request LINEAR16/48k. |
| **Voice-QA (per segment)** | mispronounced names, rushed beats, robotic reads, dropped words, artifacts | The §7 subsystem (faster-whisper WER + UTMOSv2/Distill-MOS + ffmpeg). Blocks the voice lock. |
| **Primitive-utilization** | "7 of 64 = 16%" | Per-family floor + **diff declared-vs-rendered against compiler output** (list-but-don't-render faking fails). |
| **Asset-reference-closure** | "9 clips/16 stock/22 floorplans sourced, ~0 used" | Every `*_manifest.json` entry referenced ≥1× in the compiled HTML; scrap needs structured `{asset,reason,evidence_url}`; >30% scrapped = fail. |
| **Geo-accuracy** | "pins on wrong continent" | Anchor lat/lon must fall in its map_extent; `positions.json` px must match a recompute (catches hand-edited CSS %). OOB patch moved into `render_basemap`. |
| **`qa_physics`** | "objects pass through each other / clip / overlap" | Sample the timeline ~12fps; interpolate every object's bbox/polygon along its path; flag same/adjacent-layer intersections (unless `interaction:true`), paths crossing building footprints, occlusion of labels/faces, facing≠direction, out-of-bounds. |
| **`qa_continuity`** | "map jumped / pin vanished between shots" | Each shot's outgoing state == next shot's incoming state (basemap tier, active pins, year, camera, persistent UI). |
| **Cue-lifecycle** | "objects left awkwardly on screen — missed exit" | Every cue needs start AND end anchor on a Whisper word; on-screen cue with no exit = fail. |
| **Drift** | "animations drifting / wrong timestamp" | Every `anchor_phrase` matches a Whisper word (NOT_FOUND = fail); per-cue-type budgets. |
| **Overlap + Min-hold** | "text overlapping"; "on screen too briefly" | bbox intersection on overlapping cues; `hold ≥ max(2.5, ceil(words/3)+2)`. |
| **Face-visibility** | "card face cut off" | Face detector on every portrait/cutout; fail on no-face or clipped bbox. |
| **No-monolith + Subagent ledger** | "one script for all chapters; swarm never ran" | `count(storyboard_*.json)==count(chapter_*/index.html)==N_chapters`; each shot agent appends a signed `{chapter,id,sha256}` entry; gate asserts ≥N matching entries. |
| **`qa_sfx_audibility`** | "SFX too quiet to hear" | Per SFX cue, measure short-term loudness vs the simultaneous VO+music bed; flag if masked (not ≥X LU above bed) or below an absolute floor. Mirror of the alarming/too-loud deny-list. |
| **Sound-design** | "alarming SFX after 10:00"; loudness drift | Deny-list regex on SFX for `t_in>600s`; −15 LUFS gate; music-density coverage. |
| **Render-existence + duration** | "fabricated 28:13 that doesn't exist" | `final.mp4` exists AND ffprobe duration ≈ VO AND frames == duration×fps. |
| **Black-frame / placement** | "hero in a letterbox band"; black frames | `hf_coverage_qa` (+luma) and `render_placement_qa` (multi-timestamp, exit-code). |
| **Brief-manifesto alignment** | "the brief got lost; QA was technical, never creative" | Required-set harvested **from the transcript/canonical_names — never a hand dict**; every figure/place/year/moment needs a cue. Plus a fresh-context depth reviewer naming "first thing you'd notice missing." |

---

## 4. Your nine anti-slop mechanisms → where each lives

1. Brief manifesto = `artifacts/brief_manifesto.json` (verbatim), approved at **G0**; alignment gate checks against THIS. 2. Primitive-util → §3. 3. Asset-util → §3 (manifest-driven). 4. No-monolith → §2.2 + count + ledger + wired guardrail. 5. Brief-alignment → §3. 6. Scope-lock first → G0. 7. Structural check-ins → batched at the nearest human gate. 8. "First thing missing" review → fresh-context depth reviewer. 9. Output can't call itself done → §2.3 gate-runner + render-lock — **the linchpin.**

**Human gates (your only touchpoints):** **G0** scope/theme · **G1** script text · **G-voice** voiceover (new) · **G2** storyboard+assets · **G3** preview · **G4** final render (+ post-render ask: OTIO handoff?).

---

## 5. The pipeline — your 8 phases, mapped

Two-layer defense, aligned: **machine gates run continuously & un-bypassably between your touchpoints; your human gates sit exactly where the machine can't judge (creative truth, story quality).**

| Your phase | Canonical artifact | Key hard gates | Human gate |
|---|---|---|---|
| **1. Research** | `research_brief`, `geography`, `canonical_names` (incl. name→IPA map) | multi-source fact-check swarm; provenance non-empty; canonical closure | — |
| **2. Script + TTS format** | `theme.json`, `script.json` | schema-validate; **VO-content-unchanged**; voice-markup | **G1: approve final script** |
| **3. Voice + QA→fix + timestamping** | VO PCM segments, `whisper/*.json`, `voicespec.json`, segment table | per-segment Voice-QA loop (§7); track loudness/gap | **G-voice: review + flag words** |
| **4. Storyboard + asset research** | `storyboard_*.json` (per chapter, w/ `sound_intent`), `asset_manifest` | binding-vs-intent shot schema (§6); breadth+depth QA; sourcing swarm + JIT requests | **G2: approve storyboard+assets** |
| **5. Generate visuals + stitch** | `hyperframes/chapter_*/index.html` + master | compiler-only; ledger; no-monolith; primitive-util; asset-closure; geo; **physics**; **continuity**; cue-lifecycle; overlap; min-hold; face | — |
| **6. Sound design** | `music_mix.wav`, `sfx_mix.wav` | swarm **must listen**; drift; alarming-SFX deny-list; **`qa_sfx_audibility`**; −15 LUFS | — |
| **7. HTML preview → review loop** | `review/` + `submitted_comments/latest.json` | preview built; comments mapped to concrete edits | **G3: scrub + comment on frames** |
| **8. Final render (+ optional handoff)** | `master.mov/.mp4`; **OTIO only if you ask** | render-exists+duration; **all gates green & fresh**; OTIO conform check *(if requested)* | **G4: initiate final render**, then I ask if you want the editor handoff |

**3-tier shot system → engines:** **Macro** = `mapkit` Carto basemaps. **Medium** = the **geo-grounded diorama engine** (built on a real factually-correct map shape OR standalone terrain, agent's choice; inherits geo + physics gates). **Micro** = off-map story dives / panels / treated clips / character cutouts. **Transitions** = `basemap_swap` (anchored center), `panel_to_pin_morph`, `camera_*`, `year_sweep`.

**QA loop rule:** each shot agent QAs ≥10 issues + improvements, fixes, re-QAs — **3×**; remaining issues on round 3 are fixed by the **master agent (me), not you.** Master-level QA covers ≥15 on the stitched master, same 3-loop rule.

---

## 6. Shot-prompt contract — BINDING vs INTENT (+ continuity, + physics by construction)

Your D-Day example is the bar, but pixel-exact specs at plan time would violate "finalize motion after the image lands" and would be impossible (geometry isn't known until assets are placed). So the spec is split:

**BINDING at storyboard (animator MUST honor — facts & continuity):** map tier + geo anchor (lat/lon) · z-order/layer · VO anchor phrase + timing window · overlay text copy (canonical names) · asset list + provenance · transition type + **boundary state** · which entities/events must appear · physics **constraints** (obstacles that must not be crossed, intended interactions).

**INTENT at storyboard → animator FINALIZES (craft, image-dependent):** exact motion paths/easings/coordinates · camera-move specifics · lighting/atmosphere · secondary animations · color specifics · `sound_intent` (non-binding seed for the sound stage).

**Physics by construction (answers "paths mapped before or by the agent?"):** the **agent maps the actual collision-free path** (only it knows real asset bboxes + basemap geometry), but the storyboard declares **intent + constraints**, and **`qa_physics` verifies**. The compiler authors every scene as a **scene-graph** — each object a node with a bbox/polygon collider + z-layer + timed motion path — so collisions, occlusion, clipping, and out-of-bounds are deterministic math, not eyeballing. We don't *simulate* physics; we make geometry *explicit and checkable*. (Parabolic eased paths give "physical-looking" motion without a simulator.)

**Continuity (yes, neighbors matter):** each Tier-3 animator receives the **previous shot's outgoing state** and the **next shot's incoming requirements** (boundary slices only), and `qa_continuity` enforces that the seams match.

---

## 7. Voice QA→fix subsystem + G-voice (researched; free/local/commercial-safe)

**Principle:** synthesize **per sentence**, detect objectively, **regenerate only the bad segment** (neighbors' pauses live as timeline metadata, never baked in, so a swap disturbs nothing), re-evaluate, loop ≤3×, then escalate to **you**. Voiceover is the timing foundation, so it's fully locked (machine + human) **before** storyboarding.

**InWorld facts that shape it:** word timestamps are **native** (use them; ASR only cross-checks what was *said*); **no seed & `temperature` ignored** → best-of-N = resampling stochasticity + varying `deliveryMode`; **pronunciation = inline English IPA `/…/`** (one word/slash-pair; no `<phoneme>`/lexicon) → build a reusable per-video name→IPA map; **QA on LINEAR16/PCM @48 kHz**, never MP3; `<break>` ≤20/request, ≤10s each.

**Stack (all installs free; gate only on MIT-licensed):** `faster-whisper large-v3` (round-trip WER + per-word `.probability`, VAD) · `WhisperX` (pause/rate alignment) · **UTMOSv2** + **Distill-MOS** (MIT naturalness MOS) · `ffmpeg`+`pyloudnorm`+`librosa` (clipping/dropout/LUFS/seams). NISQA per-artifact diagnostics are **non-commercial** → advisory only.

**Detect thresholds (flag if any trips):** WER >5% (>15% hard-fail; any missing content word flags); word prob <0.40 or `avg_logprob` <−0.55; `compression_ratio` >2.4 / `no_speech_prob` >0.6 (hallucination); UTMOSv2 <3.6 (<3.2 hard-fail); rate >3.6 w/s (too fast) / <1.8 (drag); realized pause <80ms where ≥180ms expected (rushed beat); true-peak ≥−0.1 dBFS (clip); ≥400ms silence inside (dropout); ±2 LU off target / seam jump >6 dB.

**Fix tree (cheapest-deterministic first; re-eval each step):** mispronounced name → inline IPA then respelling · dropped word → re-call once, then split sentence · rushed beat → insert `<break 250–600ms>` (split if >20) · too fast → `speakingRate` 0.5–1.5 + `[measured]` · wrong emphasis → CAPS + `[emphasize…]` · robotic/hallucination → **best-of-N** (N=3, →5; vary `deliveryMode`; composite score 0.40·(1−WER)+0.20·MOS+0.15·conf+0.15·prosody+0.10·clean−0.10·hallucination) · clip/dropout/level/seam → trim/limit/normalize/crossfade, never regenerate. **Cap 3 iterations/segment → escalate.**

**G-voice human tool (new):** a transcript synced to the waveform + word-timeline (from InWorld `wordAlignment`); you **click a word or drag a range** and tag "regenerate" + note; the bundle also shows the N candidate takes + scorecards + which fixes were tried + editable IPA/break/steering/rate fields. Submit → I regenerate just those → re-present → loop until you approve (`approvals/voice.json`). Built on the canonical local-review-tool JSON pattern.

---

## 8. Sound design — audibility + the `sound_intent` middle ground

- **`sound_intent` seeds (your #3):** storyboard captures *intent only* per beat (mood/energy, opportunity tags like `accent_on:<anchor>`, `silence_for_impact`, `ambient:<env>`) — never tracks/files. **HARD RULE:** the sound stage treats it as a *seed*, must independently re-derive from the locked visuals and adapt/optimize/improve. **Zero human burden at storyboard** — you review sound only after it's applied (G3).
- **The swarm must LISTEN** (analyze the actual audio, not filenames), rank/rate, choose; QA loops 3×.
- **`qa_sfx_audibility` (your #2):** every SFX that should be heard is checked against the simultaneous VO+music bed — flagged if masked or below floor. Bounds SFX on both ends (audible enough / never alarming).

---

## 9. New capabilities to build

| # | Capability | What | Gate |
|---|---|---|---|
| 1 | **Diorama engine** (medium-tier 3D) — *biggest new build* | HTML/CSS 3D-transform + GSAP + sprite "actors" + parallax + virtual camera, as a **scene-graph** (colliders/z-layers/paths). Geo-grounded on a `mapkit` basemap **or** standalone terrain. Reuses `composer.py` + `positions.json`. | geo + **physics** + min-hold + placement. |
| 2 | **Cutout + border tool** | Background removal (`rembg`/U²-Net) + white/gray stroke → transparent PNG sprite for maps/dioramas. | Face-visibility + alpha-edge QA. |
| 3 | **Nano Banana (Google) gen** | JIT. **Cap 50/video (incl. revisions)** as a runaway guard. **HARD RULE: agents are empowered to use it creatively** when it makes a shot better; free/procedural is the default preference, not a restriction. Lightly logged for the retro. | Never generate text; spell-check/edit hallucinations. |
| 4 | **OTIO handoff (conditional)** | After **G4** I **ask** if you want it; only then export a conformed OTIO timeline → DaVinci + Premiere/FCPXML (needs per-scene/layer assets). | OTIO conform check (every clip ref resolves) — only when requested. |
| 5 | **`inworld_tts` fixes (top priority)** | **Preserve line breaks verbatim** (they're your pause mechanism); SSML-aware chunking (never cut a `<break>`, ≤20/request); lock `CREATIVE` + `voiceId`; request PCM@48k; drop the no-op `temperature`. | Voice-markup gate = CLI twin of the in-tool preflight. |
| 6 | **Voice-QA stack** | Install + wrap the §7 tools as one `voice_qa` step embedded in the voice tool path. | The §7 detect/fix loop. |

---

## 10. Agent org — tiers + context isolation

- **Tier 0 — Orchestrator (me):** thin; dispatches, runs the runner, never holds all shots, does round-3 fixes. *Cannot* declare done.
- **Tier 1 — Stage directors** (one per stage, read fresh).
- **Tier 2 — Scene Directors** (one per chapter).
- **Tier 3 — Shot/phase animators (the swarm):** one shot each; sees ONLY its beat JSON + theme + adjacent boundary state; writes a ledger entry.
- **QA swarm:** breadth sweepers (single-issue-class each) + a fresh-context depth reviewer.

---

## 11. Self-anneal — a retro stage that mints regression-tested gates (your #10)

The evolution mechanism is itself load-bearing: **every bug we ever see becomes a permanent regression-tested gate.**
1. **Findings captured as data** — every QA finding + every human comment (voice + preview tools) appends to `findings_ledger.jsonl` (what, where, which gate should've caught it).
2. **Retro stage (mandatory)** classifies each: caught ✓ / **missed but gateable** (→ propose new/extended gate) / subjective (→ update a skill + the catalog enum, which grows by addition).
3. **A new gate ships only with a fixture** — the actual failing artifact as the *known-bad* fixture + a known-good one + a CI assertion (non-zero on bad / zero on good). **A fixed bug can never silently return.**
4. **Gate registry + spine-integrity check** — gates are version-controlled with fixtures; each video re-runs every fixture, so a gate can't be silently weakened (it'd fail its own known-bad case).
5. **Cheap batched sign-off** — the retro hands you `gate_proposals.json` (scannable); you approve which become permanent.

Result: the system gets *stricter and smarter every video* without you babysitting.

---

## 12. Build order — GATES BEFORE CREATIVE

**Milestone A — Enforcement spine (no video work until green):**
- [x] **(1) DONE+verified** — 5 AHM schemas registered in `schemas/artifacts/__init__.py`; `validate_artifact.py` CLI exits non-zero on invalid.
- [x] **(2) DONE+verified** — `hard_gates[]`/`requires_human_approval` added to the manifest schema; AHM manifest rewritten to conform (it *failed* validation before); `lib/animated_history_map/runner.py` (run-gates / run-stage / **render-lock** `assert_green_and_fresh`) + `scripts/run_gates.py`/`run_stage.py`; machine-written `qa_report.json` + its schema. Render-lock verified to block on red AND on stale inputs.
- [x] **(3) PARTIAL** — `check_extension_permitted` wired in via `gates/qa_no_custom_scripts.py` (the anti-monolith guard, verified fail-on-`.py`). TODO: the broader anti-bypass lint (hand-rolled Mercator / inline ffmpeg strings / hardcoded map CSS %).
- [x] **(4) DONE+verified** — **11 gates live, wired, and spot-checked** (22/22 in `test_gates.py`, each good→0/bad→1; a real 5-gate `qa_visual` run proven green→red→stale): `qa_no_custom_scripts`, `qa_min_hold`, `qa_element_overlap`, `qa_card_bounds`, `qa_vo_content_unchanged`, `qa_voice_markup`, `qa_asset_reference_closure`, `qa_render_existence_duration`, `qa_continuity`, `qa_geo`, `qa_schema_validate`. (9 built by a verification swarm, 2 by me; `qa_geo` spot-checked against the real mapkit key names, `qa_continuity` against the real storyboard schema.) Remaining lib hardening: `render_placement_qa` (add `sys.exit` + multi-timestamp) and `hf_coverage_qa` (+rendered-luma sampling). `qa_card_bounds` was rebuilt fresh in-spine, so the non-exiting framework-videos copy is moot here.
- [x] **(5) DONE+verified** — `lib/animated_history_map/compiler.py`: storyboard JSON → per-chapter + master HF HTML (clip divs + paused GSAP timeline + `compiler-version` stamp) and emits `artifacts/cuelist.json`. Schema-validates (an off-enum `primitive` = hard compile error → the 64-primitive catalog is finally load-bearing), enforces the ≤2-experimental-per-phase cap, resolves timing from Whisper / `fallback_absolute_s`. **Verified: the storyboard→HTML→cuelist→gates loop closes** — the real `qa_visual` 5-gate suite runs GREEN on the compiler's own output (sample at `lib/animated_history_map/fixtures/sample_project/`). En route I **fixed a latent storyboard-schema bug**: its `experimental` `if/then` required `experimental_rationale` on *every* beat (the `if` matched when `experimental` was absent); now correctly gated on `required:["experimental"]`.
- [x] **(6) DONE+verified** — **`qa_physics`** built + wired (qa_visual): reads the diorama engine's motion-path scene-graphs and fails on clip-through (actor↔prop / actor↔actor on same/adjacent layer, honoring `can_overlap`/`walkable`), out-of-frame, and facing-vs-travel mismatch. Verified good→pass / bad→fail (the bad fixture caught both a building clip-through *and* a facing mismatch). Passes (with a note) for chapters that have no diorama.

**Deferred gate swarm — DONE+verified** (7 built in parallel, each good→0/bad→1, spot-checked, wired): `qa_cue_lifecycle` (qa_visual), `qa_drift` (storyboard), `qa_primitive_utilization` (qa_visual), `qa_black_frame` (render, ffmpeg luma), `qa_face_visibility` (assets, optional cv2), `qa_alarming_sfx` + `qa_sfx_audibility` (sound_design). Plus the final batch (built + verified + wired): `qa_placement` (render), `qa_loudness` (final_render, ffmpeg ebur128), `qa_audio_drift` (sound_design), and `qa_no_reimplementation` (qa_visual — the anti-bypass lint: every HF composition must be compiler-stamped + no hand-rolled Mercator). **Gate suite is now 24 gates / 48-case harness, all green; manifest = 25 hard_gate entries across 13 stages.**

Every gate ships with good/bad fixtures + a row in `lib/animated_history_map/gates/test_gates.py` (the regression harness — a gate that can't fail is forbidden). New gates minted from real bugs add their failing artifact here (§11).

**Milestone B — New engines:**
- [x] **diorama engine — vertical slice DONE+verified** (`lib/animated_history_map/diorama.py`): geo-grounded 2.5D (lat/lon→px via mapkit), tilted ground + billboarded actors on GSAP motion paths + virtual camera; emits HF-valid HTML **and** a physics scene-graph `qa_physics` consumes. Remaining (iterative): visual richness — textures, lighting, multi-actor choreography, environment FX, basemap-image grounding.
- [x] **`inworld_tts` fixes DONE+verified** — newline-preserving + SSML-tag-safe chunking (your line-break pauses survive; `<break>` never severed), ≤20-break/request guard, `speaking_rate` capped at 1.5.
- [x] **Voice lock gate DONE+verified** — `qa_voice_segments` (voice stage hard gate): every VO segment must pass (WER ≤0.15 / MOS ≥3.2 / rate / no clipping/dropout + track loudness) **or** be human-approved at G-voice; an unfixed+unapproved segment blocks the build. Defines the `voice_report.json` contract the loop will produce.
- [x] **Voice-QA→fix loop architecture DONE+verified** (`voice_qa.py`): markup fixes, detect thresholds, best-of-N composite scoring (+ hard-reject), the fix-decision tree, and the synth→detect→fix→loop≤3→escalate orchestration — verified via a deterministic StubBackend (s1 passes, s2 fixed via best-of-N re-roll, s3 escalates) and the **loop↔gate↔human contract closes** (the escalated segment blocks `qa_voice_segments` until human-approved). The REAL **evaluation** pipeline (`RealBackend.evaluate` / `evaluate_audio`) is now installed + **run-verified on real speech**: `faster-whisper` (ASR round-trip) + `distillmos` (MOS) + `pyloudnorm`/`soundfile` (loudness/clip), verified via macOS `say` → **WER 0.091 / MOS 4.25 / wps 3.65**. Only InWorld **synthesis** stays gated (`RealBackend.synthesize` is wired to the fixed `inworld_tts` tool; paid, needs per-run approval). NB: HF model downloads on this machine require `urllib3<2` (LibreSSL).
- [ ] TODO: the **G-voice audio-review TOOL** (transcript+waveform UI to click words for re-gen). The approval-artifact enforcement already works via the runner; only the UI remains.
- [x] **G-voice audio-review UI DONE+verified** — `lib/animated_history_map/gvoice/` (`serve.py` + `review.html`): scrub the VO, per-segment approve / regenerate-with-note + fix-hints; submit writes `artifacts/approvals/voice.json`. Verified the runner passes the voice stage only when the gate passes AND the human approved via the UI (and blocks without approval).
- [x] **OTIO editor handoff DONE+verified** — `lib/animated_history_map/otio_export.py`: emits an `.otio` timeline (video + VO/Music/SFX audio tracks + chapter markers from the cuelist) referencing real media, with a conform check. Round-trips; DaVinci imports `.otio` natively. (Human-triggered after final render.)
- [x] **Cutout+border tool DONE+verified** — `lib/animated_history_map/cutout.py` (`rembg` installed): background-removes a photo + adds a white/gray silhouette outline → transparent PNG sprite for maps/dioramas. Verified on a real PD portrait.
- [ ] TODO: a paid **InWorld synthesis** run (per-run approval) to exercise the full voice loop on real VO; **Nano Banana** generation (cap 50; `GOOGLE_API_KEY` in .env); optional CLI-exit hardening of `render_placement_qa`/`hf_coverage_qa`. **Then Milestone C: the real 1-chapter slice.**

**Milestone C — Test video:** run **one chapter end-to-end** through every stage + gate (incl. G-voice) → **you review** → then scale to all chapters in `projects/presidential-assassinations-v2/`.

---

## 13. Decisions — RESOLVED

- **Sequencing:** spine → 1-chapter slice for your review → scale.
- **Editor handoff:** OTIO, **human-triggered after final review** (default deliverable is the .mov/.mp4).
- **Voice:** line breaks preserved as the natural-pause mechanism; `<break>` only for ensured hard pauses; voice locked at **G-voice** before storyboarding.
- **Nano Banana:** cap 50/video, creativity explicitly protected.
- Defaults (object if wrong): continue in `presidential-assassinations-v2/`; adopt canonical `framework-videos/execution/review/`.
- **Open for your eye:** the §7 detect thresholds, the 16-aspect→binding/intent split, and the `sound_intent` tag list.
