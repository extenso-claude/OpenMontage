# Voice Director — Midnight Magnates

The voice stage for Midnight Magnates is **ingest-and-validate**, NOT generate-and-self-heal.

In this pipeline the VO is **user-provided finished audio** (the user hands you MP3/WAV
files per project — there is no Inworld voice ID, no TTS run, no RVC pass). Your job is to:
**ingest** the provided files in narrative order → **build the timing spine** (Whisper word
timestamps) → **normalize loudness** → **validate quality** → present the **G-voice** human
gate → emit `artifacts/voice_report.json`. The voiceover is the timing foundation every
downstream visual/audio cue anchors against, so the spine and the validation are load-bearing.

This stage **never generates the voiceover.** If a segment is bad, you cannot "regenerate" a
voice you don't own — you flag it for the human at G-voice (who can re-record / re-supply that
section). The script stage already produced the planned narration text for storyboarding; this
stage works from the audio the user delivers.

## Read first

- `[[project_mm_voice_provided_files]]` (memory) — the canonical reason this stage is
  ingest-only: user supplies finished voice files; no Inworld generation for MM-maps.
- `[[inworld_tts2_facts]]` (memory) — the **QA + timestamp-extraction** stack
  (faster-whisper / WhisperX for word timestamps, UTMOSv2 / Distill-MOS for naturalness MOS,
  ffmpeg / pyloudnorm for loudness + clipping/dropout). Use the **validation** half only — the
  generation / IPA-markup half is dormant here.
- `lib/midnight_magnates/voice_qa.py` — its QA/scoring + timestamp-extraction path is what you
  reuse; its synthesize/RVC/best-of-N generation path is **dormant** for provided files.
- `lib/midnight_magnates/gates/qa_voice_segments.py` and `…/qa_voice_timestamps.py` — the two
  blocking gates; their code IS the contract for the JSON you must produce (shapes below).
- `lib/midnight_magnates/gvoice/__init__.py` — the sanctioned G-voice review UI; submitting it
  writes `artifacts/approvals/voice.json`, the exact artifact the runner requires to advance.

## Manifest contract (pipeline_defs/midnight-magnates-doc.yaml, stage `voice`)

- **produces:** `voice_report` → `artifacts/voice_report.json`
- **requires_human_approval: true** → G-voice (review + flag any words to fix)
- **hard_gates (BOTH block):**
  - `qa_voice_segments` — every segment passes (WER/MOS/rate/clipping/dropout + track loudness)
    or is human-approved at G-voice.
  - `qa_voice_timestamps` — `artifacts/whisper/full.json` exists with a non-empty `words[]`.
- **review_focus:** `per_segment_qa_loop_ran`, `track_loudness_minus_16_lufs`.
- Note: the manifest lists `qa_voice_markup` only on the **script** stage (a generation-time
  Inworld-markup gate). It is **NOT** a voice-stage gate and does **NOT** apply to provided
  files — do not run it or author any Inworld-markup steps here.

## Enforcement model (the runner decides "done", not you)

A deterministic runner — not the agent — shells the gates and writes the machine-authored
`artifacts/qa_report.json`. You never hand-author that report or claim a gate passed. Run:

```bash
# the voice stage's two gates + the human-approval check, in one call:
python3 -m lib.midnight_magnates.runner run-stage  --pipeline midnight-magnates-doc --project <project_dir> --stage voice

# (or just the gates, no approval check — use while iterating before G-voice:)
python3 -m lib.midnight_magnates.runner run-gates  --pipeline midnight-magnates-doc --project <project_dir> --stage voice
```

`run-stage voice` BLOCKS until `artifacts/approvals/voice.json` exists with `approved: true`
**and** both gates exit 0. Iterate with `run-gates` until green, then collect G-voice.

## HARD RULES

1. **NEVER generate the VO. There is no Inworld/TTS/RVC synthesis in this stage.** The audio
   is user-provided. If you cannot find the provided files, **STOP and ask the user** for
   them — do not synthesize a substitute, do not fall back to Inworld, do not proceed on
   placeholder audio. ("Provide the finished voice files" is the locked channel decision.)
2. **Ingest in narrative order.** Copy the provided files into `assets/audio/vo/` named so
   sort order = narrative order (e.g. `s01_*.wav`, `s02_*.wav`). For each section record:
   `filename`, `duration_s`, and `start_offset_s` = the **cumulative** start of that section
   in the assembled master (section 1 starts at 0.0; each next section's offset = prior
   offset + prior duration). If sections are separate files, **concatenate them to a single
   continuous VO track** `assets/audio/vo_full.wav` (the spine + every drift gate resolve
   against one continuous master timeline, not per-file clocks). Record offsets in the report's
   `sections[]`.
3. **Build the timing spine — this is the non-negotiable product of the stage.** Run WhisperX /
   faster-whisper on the assembled `assets/audio/vo_full.wav` and write
   `artifacts/whisper/full.json` with a **non-empty `words[]`**, each entry
   `{"word": <str>, "start": <number>, "end": <number>}` on the **master** timeline (a word's
   `start` is its absolute second in `vo_full.wav`, NOT relative to its source section). Every
   downstream gate (`qa_drift`, `qa_audio_drift`, `qa_cue_drift`, `qa_sfx_event_sync`,
   `qa_scene_sync`, `qa_master_offset`) resolves anchor phrases against this file.
   `qa_voice_timestamps` BLOCKS the build if it is missing, unreadable, or has an empty/wordless
   `words[]`. An empty transcript is treated as "no narration" — a hard fail, never a pass.
4. **Machine gotcha (the spine fails to build → it looks like "no network" but isn't):**
   faster-whisper / Hugging Face model fetch fails on this machine with an SSL handshake error
   (LibreSSL). If the download/handshake fails, run `pip install --user 'urllib3<2'` and retry
   — pip itself uses a different SSL path so it works, masking the real cause. Do NOT conclude
   "offline" and skip the spine; the spine is mandatory.
5. **Normalize VO loudness toward the manifest target.** Normalize `vo_full.wav` to
   **integrated ~ -16 LUFS** (track loudness review_focus) with **true-peak ≤ -1.0 dBFS**, and
   QA on PCM/WAV, never on a re-compressed MP3. `qa_voice_segments` reads
   `track.lufs` and FAILS outside **[-17, -13] LUFS**, and FAILS `track.true_peak_db` > -1.0 dB.
   Measure with ffmpeg `ebur128` / pyloudnorm and write the **measured** values (never guess).
6. **Validate every segment, then write `artifacts/voice_report.json` in the exact gate shape.**
   Segment the master per narrative section (or finer if the user delivered sub-clips). For each
   segment compute the metrics via the QA stack (ASR round-trip WER, naturalness MOS,
   words/sec, clipping, dropout) and set `status` honestly. The gate re-checks the numbers, so a
   green `status` with red metrics still FAILS. Thresholds the gate enforces on any
   non-approved segment: **WER ≤ 0.15**, **MOS ≥ 3.2**, **1.8 ≤ wps ≤ 3.6**, `clipping` not true,
   `dropout` not true.
7. **A flagged segment's ONLY sanctioned override is human approval at G-voice.** Because you
   cannot regenerate the audio, any segment that fails the metrics must be marked
   `status: "approved"` **only after** the human listened and accepted it at G-voice (or be
   re-supplied by the user and re-validated). Setting `status: "approved"` / `human_approved:
   true` without an actual G-voice acceptance is a falsified pass — never do it.
8. **Flag the `voice` block as user-provided — that is what the gate keys off, and NO schema is
   involved.** Set `voice.source: "user_provided"`, `voice.generated: false`, and a non-empty
   `voice.voice_id` (the channel/provider voice label the user supplied, e.g. the file/voice
   name). `qa_voice_segments` (`_is_user_provided`, ~L56-77) **skips** the generator-identity
   checks — `model_id == "inworld-tts-2"` and `delivery_mode == "CREATIVE"` — on the
   user-provided path (`source == "user_provided"` OR `generated == false`); only the QUALITY
   checks (per-segment WER/MOS/rate/clipping/dropout + track loudness) and the non-empty
   `voice_id` still apply. You therefore do **not** need `model_id` or `delivery_mode`; omit them
   (or, if present, they are ignored on this path). There is **no `voice_report` schema** —
   `qa_schema_validate` validates only theme/geography/canonical_names/storyboard, so nothing
   requires these fields. (`voice_id` is the one `voice` field still enforced — keep it
   non-empty.)
9. **Do NOT author or run `qa_voice_markup` / any Inworld-TTS markup step here.** It is a
   script-stage generation gate (≤20 breaks/segment, steering tags lead, locked voice/model) and
   is irrelevant to provided audio. Authoring IPA/break/steering markup in this stage is wrong.
10. **The runner owns the verdict.** Do not declare the voice stage done on your own say-so. It
    is done only when `run-stage … --stage voice` reports `ok: true` (both gates exit 0 AND
    `artifacts/approvals/voice.json` has `approved: true`).

## `artifacts/voice_report.json` — required shape

`qa_voice_segments` reads this exact structure (extra keys are fine; the named ones are required):

```json
{
  "voice": {
    "voice_id": "<provider/voice label the user supplied — non-empty>",
    "source": "user_provided",
    "generated": false
  },
  "sections": [
    { "id": "s01", "filename": "s01_intro.wav", "duration_s": 92.4, "start_offset_s": 0.0 },
    { "id": "s02", "filename": "s02_rise.wav",  "duration_s": 140.1, "start_offset_s": 92.4 }
  ],
  "segments": [
    {
      "id": "s01",
      "status": "pass",
      "human_approved": false,
      "metrics": { "wer": 0.03, "min_word_prob": 0.71, "mos": 3.9, "wps": 2.6,
                   "clipping": false, "dropout": false }
    }
  ],
  "track": { "lufs": -16.0, "true_peak_db": -1.4 }
}
```

- `segments[].status` ∈ `{"pass","fail","approved"}`. Use `"approved"` (or `human_approved:
  true`) ONLY after a real G-voice acceptance (HARD RULE 7).
- `track.lufs` ∈ [-17, -13] (aim -16); `track.true_peak_db` ≤ -1.0 — both **measured**.
- `sections[].start_offset_s` is cumulative (HARD RULE 2); the spine in `whisper/full.json` uses
  the same continuous master clock.

## Workflow

1. **Locate the provided VO files.** Confirm the user-supplied MP3/WAV set (per section or one
   file). If absent → STOP and ask (HARD RULE 1). Copy into `assets/audio/vo/` with
   sort-order = narrative-order names; record filename + duration per section.
2. **Assemble the master.** If multiple files, concat (ffmpeg) to one continuous
   `assets/audio/vo_full.wav`; compute each section's cumulative `start_offset_s`.
3. **Normalize loudness.** Loudnorm `vo_full.wav` to ~ -16 LUFS / true-peak ≤ -1.0 dBFS; re-run
   `ebur128` to capture the **measured** integrated LUFS + true peak for `track`.
4. **Build the timing spine.** WhisperX / faster-whisper on `vo_full.wav` →
   `artifacts/whisper/full.json` with master-clock word timestamps (HARD RULE 3). If the model
   fetch fails, apply the urllib3<2 fix (HARD RULE 4) and retry — the spine is mandatory.
5. **Validate per segment.** Run the QA scoring (reuse the `voice_qa.py` evaluate path: ASR
   round-trip WER, MOS, wps, clipping, dropout) per section; set honest `status` + `metrics`.
6. **Write `artifacts/voice_report.json`** in the shape above (`voice` block flagged
   user-provided per HARD RULE 8 — `source`/`generated`/non-empty `voice_id`; plus `sections`,
   `segments`, `track`).
7. **Run the gates while iterating** until both exit 0:
   ```bash
   python3 -m lib.midnight_magnates.runner run-gates --pipeline midnight-magnates-doc --project <project_dir> --stage voice
   ```
   - `qa_voice_timestamps` red → fix the spine (exists? non-empty `words[]` with numeric
     `start`?). Re-run Whisper; apply the urllib3<2 fix if the fetch failed.
   - `qa_voice_segments` red → fix loudness/normalization, correct a falsely-green segment's
     metrics, or route a genuinely-bad segment to G-voice for approval / re-supply.
8. **Present the G-voice human gate.** Launch the review UI; the human scrubs the VO, reads
   per-segment metrics, and for any segment APPROVEs it (override the gate accepts) or flags it
   to re-supply with a note:
   ```bash
   python3 -m lib.midnight_magnates.gvoice.serve --project <project_dir>
   ```
   Submitting writes `artifacts/approvals/voice.json`. For any human-approved segment, set its
   `status: "approved"` in the report (HARD RULE 7) and re-run the gates. For any flag-to-fix,
   obtain the corrected audio from the user, re-ingest that section, rebuild the spine + metrics,
   and re-validate.
9. **Confirm the stage is done via the runner** (not your judgment):
   ```bash
   python3 -m lib.midnight_magnates.runner run-stage --pipeline midnight-magnates-doc --project <project_dir> --stage voice
   ```
   Done only when it reports `ok: true` (both gates green AND approval present).

## Outputs

- `assets/audio/vo/` — ingested user-provided section files (narrative-ordered).
- `assets/audio/vo_full.wav` — the single normalized (~ -16 LUFS) master VO track.
- `artifacts/whisper/full.json` — the **timing spine** (non-empty `words[]`, master clock).
- `artifacts/voice_report.json` — the `voice_report` artifact (shape above).
- `artifacts/approvals/voice.json` — G-voice approval (written by the gvoice UI).
