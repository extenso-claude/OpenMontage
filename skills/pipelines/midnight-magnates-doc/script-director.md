# Script Director — Midnight Magnates

The script stage **approves the VO TEXT** for a Midnight Magnates documentary and authors its
**Inworld TTS-2 delivery markup**. It produces two artifacts:

- `artifacts/script_approved.json` — the **plain, human-approved spoken script**, one entry per
  `segments[].text`. This is the G1 deliverable: the exact words the video will say, in order.
- `artifacts/script.json` — the **same words** with Inworld TTS-2 presentation markup
  (`segments[].text_markup`) plus a `voice` block. Markup may ONLY add `[steering tags]`,
  `<break .../>` pauses, line breaks, and CAPS — it may **not** add, drop, or change a single
  spoken word.

**This stage does NOT generate audio and does NOT run Whisper.** Midnight Magnates voice is
**user-provided finished audio** — there is no Inworld/TTS/RVC synthesis anywhere in this
pipeline. The Inworld markup you author here is the **narration-delivery spec** (the channel's
craft layer and what `qa_voice_markup` validates) — the desired delivery the recording honors —
**not** an instruction to synthesize. Ingestion of the user's audio, loudness normalization, and
the Whisper **timing spine** are the next stage's job — see
[`skills/pipelines/midnight-magnates-doc/voice-director.md`](voice-director.md). Do not produce
MP3s, do not transcribe, do not concatenate a master track here.

## Read first

- `artifacts/theme.json` — `voice_persona` (provider, `wpm_target`, `emotion_tag_frequency`,
  `break_tags_after`), `hook_engine` (`rolling_payoff` | `deep_mystery`), `pacing_target`
  (`broadcast` | `cliffhanger` | `explainer`). These set the pacing and hook architecture you
  write to.
- `artifacts/research_brief.json` — the facts, dates, quotes, and the **`through_line_candidates`**
  block (the research stage surfaces candidate recurring devices; the **storyboard** director
  picks the actual `through_line`). You write VO that lets a recurring device pay off — see
  "Plant the spine thread" below.
- `artifacts/canonical_names.json` — **use ONLY these names + spellings.** Zero variations.
- `lib/midnight_magnates/gates/qa_vo_content_unchanged.py` and `…/qa_voice_markup.py` — the two
  blocking gates; **their code is the contract** for the two JSON files you produce (shapes below).
- [`skills/pipelines/midnight-magnates-doc/voice-director.md`](voice-director.md) — the next stage.
  Read it so you understand the handoff: it ingests user audio and builds the
  `artifacts/whisper/full.json` timing spine. You hand it approved TEXT, not audio.

## What this channel is (so the writing fits the visuals)

A Midnight Magnates video is a **noir documentary told in shots** — most of them medium scenes
and close-ups of faces, objects, and documents. **Maps are supporting evidence used by a minority
of beats, never the default canvas.** Write prose that gives the storyboard those shots: name the
**place AND the person AND a specific number** so a medium scene or a face close-up has something
concrete to render, and reserve a real map only for the moments where geography itself is the
evidence. Do not write "and then we move across the map to…"; the visuals are scenes, not a map
tour.

## Writing rules

1. **Open with an ostensive, diegetic opener.** `"This is…"` or
   `"It's [year], and [person] is [doing X] here, in [place]."` First sentence ≤ 12 words. The
   opening shot (a face, a room, an object) carries the deixis — not a map.

2. **Per `theme.json` `hook_engine`:**
   - `rolling_payoff`: first named-figure payoff lands by **0:20**. Then a rolling cadence of small
     payoffs every ~15s ("first… next… then…").
   - `deep_mystery`: a triple-nested cliffhanger before **90s**. First open loop in sentence 2
     ("you've probably heard X but get [Y] WRONG"). Second nested loop ~0:55 ("a [shocking thing]
     that will [strong consequence]"). Drop into context with "But before I share, you first need
     to understand…".

3. **Stack open loops every 60–120s.** e.g. *"something would happen that would [strong
   consequence verb]"*, *"more shocking than most people realize"*, *"Most people don't realize
   this, but…"*.

4. **Reserve short sentences (≤ 8 words) for emotional landings only** (~5% of total sentences):
   `"He was already dead."`, `"But they were wrong."`, `"No one came."`.

5. **"But" pivot** ~14% of sentences. **Vary openings — ZERO sentence-start anaphora.**

6. **Anchor every beat with a named place + named person + specific number.** Density ~25
   capitalized proper-noun tokens per minute, ≥ 1 concrete number per 60s. NEVER say "many" /
   "a lot of" when a number exists.

7. **Quote dialogue at climactic moments only** (~1 quote per 2 minutes). Quotes are set-pieces —
   the storyboard renders them as a `panel_quote` or over the speaker's face.

8. **Plant 2–3 etymology / "we still call this today" micro-spikes in the middle act.** These are
   high-engagement beats.

9. **Plant the spine thread — but do NOT name or hardcode the through-line.** The video has ONE
   recurring device it returns to at each chapter close (a dossier that grows, a timeline that
   fills, a board of players, occasionally a map). The **storyboard** director chooses it (from the
   research brief's `through_line_candidates`) and renders it. Your job is to write VO that **lets
   that device pay off**: plant the recurring idea in the first 60s and **call it back at the
   climax and the close** so each chapter's ending has a line the storyboard can land the spine
   beat on. Keep the thread **device-agnostic** in the prose ("one more name for the file",
   "another date on the record") rather than welding it to a specific visual — never assume a map,
   a roster of figures, or any fixed canvas.

10. **CTA welded to context, not a fixed timestamp.** If there's a CTA, pivot to it from a place,
    a name, or the spine thread in the final act — not from a hard-coded clock position.

11. **WPM at `theme.voice_persona.wpm_target` ± 5%.** No acceleration/deceleration — all drama is
    in word choice, not read speed. (The user records the real audio; write to a length the target
    WPM can deliver inside the runtime budget.)

## Inworld TTS-2 markup craft (validated by `qa_voice_markup`)

`script.json` carries one `text_markup` string per segment plus a `voice` block. This markup is
the **delivery spec** — the channel's narration craft. `qa_voice_markup` enforces Inworld's real
limits, so author to them exactly:

- **`voice` block (required, all three or the gate FAILS):** `delivery_mode: "CREATIVE"`,
  `model_id: "inworld-tts-2"`, and a non-empty `voice_id` (the channel/provider voice label).
- **Steering tags** `[curious]`, `[wry]`, `[suspenseful]`, `[hushed]`, `[awed]`, `[reverent]`,
  `[grave]`, `[warm]` — a `[bracketed]` delivery instruction. **A steering tag only takes effect
  as the FIRST non-whitespace token of its segment** (Inworld speaks or ignores a mid-text steering
  tag — a bug either way). So **lead the segment with the tag**; a steering tag anywhere else is a
  hard FAIL. Place a tag-change only at topic pivots / change-of-pace beats (~1 per 90–120s, per
  `voice_persona.emotion_tag_frequency: topic_pivots_only`). Inline **non-verbals** (`[laugh]`,
  `[breathe]`, `[sigh]`, `[cough]`, `[yawn]`, `[clear throat]`) are the exception — those may
  appear anywhere inline.
- **CAPS** on a single critical word per climactic reveal. Never on common words ("really", "so").
  Never more than once per paragraph. (CAPS is compared case-insensitively by
  `qa_vo_content_unchanged`, so it does not count as changing a word.)
- **Em-dash** for a long pause (≥ 0.5s perceived) — place at colon-pivots where the speaker
  withholds a noun: `"…the one thing he never expected — a witness."`
- **`<break time="… ms" />`** for an explicit pause. Inworld limits: **≤ 20 breaks per segment**,
  each break time **> 0 and ≤ 10000ms**, recommended **500–2000ms** (outside that band is a WARN).
  Use a break after an act-ending short sentence, after a climactic reveal, and between chapters.
- **Line breaks** for natural sentence-clause breath — line breaks are the channel's intended
  natural-pause mechanism and are **never penalized**. Preserve them; the voice-director's spine
  treats them as pause cues too.

### Concrete markup example (segment-leading steering tag, words unchanged from the approved text)

```
[suspenseful] It's the autumn of 1931, and Salvatore Maranzano is dead in his own office — in MIDTOWN Manhattan.

Forty assassins moved through the city that afternoon.

Most people have never heard a single one of their names.
<break time="1000ms" />
```

## Workflow

1. **Plan the chapter / segment list.** Allocate runtime budget per segment (typically ~90s for
   major events, ~30s for minor ones, ~45s for the cold open and the closing). Each segment gets a
   stable `id` (e.g. `s00_cold_open`, `s01_rise`, …) — the SAME id is used in both
   `script_approved.json` and `script.json`, because `qa_vo_content_unchanged` matches by id.

2. **Write the cold open + closing first.** These set the spine thread (rule 9) and the tone.

3. **Write each segment's plain spoken text** to the writing rules above. This is the
   `script_approved.json` `text` — the words the user will record.

4. **Cross-check every proper noun against `canonical_names.json`.** Zero variations. A name not in
   the dictionary is a rewrite, not a judgment call.

5. **Present the plain script for G1 human approval** (the manifest sets
   `requires_human_approval: true` on this stage). The human signs off on the WORDS. Save the
   approved text to `artifacts/script_approved.json`.

6. **Author the Inworld markup over the approved words** → `artifacts/script.json`. For each
   segment, copy the approved `text` verbatim into `text_markup`, then add ONLY steering
   tags / breaks / line breaks / CAPS (the four allowed presentation additions). Lead each segment
   with its steering tag. Add the `voice` block. **Do not change any word** — `qa_vo_content_unchanged`
   diffs the two files word-for-word and FAILS on the first divergence.

7. **Hand off to the voice stage.** You produce TEXT only. The user supplies the finished audio;
   [`voice-director.md`](voice-director.md) ingests it, normalizes loudness, and builds the
   `artifacts/whisper/full.json` timing spine the storyboard anchors against. **You do not run
   `inworld_tts`, you do not transcribe, you do not concat a master track.**

## Enforcement model (the runner decides "done", not you)

A deterministic runner — not the agent — shells the gates and writes the machine-authored
`artifacts/qa_report.json`. You never hand-author that report or claim a gate passed. Run the
script-stage gates through the runner and read the report:

```bash
# run the script stage's blocking gates, then read artifacts/qa_report.json:
python3 -m lib.midnight_magnates.runner run-gates --pipeline midnight-magnates-doc --project <project_dir> --stage script

# the gates + the G1 human-approval check, in one call:
python3 -m lib.midnight_magnates.runner run-stage  --pipeline midnight-magnates-doc --project <project_dir> --stage script
```

The script stage's two blocking gates are `qa_vo_content_unchanged` (words unchanged from the
approved VO) and `qa_voice_markup` (Inworld markup limits + `voice` block). Iterate with
`run-gates` until `artifacts/qa_report.json` is all-green, then collect G1 with `run-stage`. If you
ever need the exact set of gates that exist, run `ls lib/midnight_magnates/gates/qa_*.py` — never
assume a gate name, never cite a per-project `qa_*.py` script path, and never invoke a gate file by
hand (only the runner under `lib/midnight_magnates/` decides "done").

## Artifact shapes (the gate contract)

`artifacts/script_approved.json` — the plain, human-approved VO:

```jsonc
{
  "segments": [
    { "id": "s00_cold_open", "text": "It's the autumn of 1931, and Salvatore Maranzano is dead in his own office, in midtown Manhattan. Forty assassins moved through the city that afternoon. Most people have never heard a single one of their names." }
  ]
}
```

`artifacts/script.json` — the SAME words with Inworld markup + the `voice` block:

```jsonc
{
  "voice": {
    "voice_id": "<channel/provider voice label — non-empty>",
    "delivery_mode": "CREATIVE",
    "model_id": "inworld-tts-2"
  },
  "segments": [
    {
      "id": "s00_cold_open",
      "text_markup": "[suspenseful] It's the autumn of 1931, and Salvatore Maranzano is dead in his own office — in MIDTOWN Manhattan.\n\nForty assassins moved through the city that afternoon.\n\nMost people have never heard a single one of their names.\n<break time=\"1000ms\" />"
    }
  ]
}
```

- Segment `id`s MUST match across both files (the content gate compares by id; a segment present in
  only one file FAILS).
- `text_markup` minus `[tags]` and `<break/>` tags, normalized, must equal `text` word-for-word.
- `voice.delivery_mode == "CREATIVE"`, `voice.model_id == "inworld-tts-2"`, `voice.voice_id`
  non-empty.

## Quality bar

- Hook earns the next 60s (first payoff per `hook_engine`).
- WPM within ±5% of `theme.voice_persona.wpm_target` (write to a deliverable length).
- Canonical-names dictionary respected — zero rejected variations.
- Spine thread planted in the first 60s and called back at climax + close, **device-agnostic**
  (no hardcoded recurring canvas — the storyboard picks the through-line).
- Every paragraph break intentional; Inworld markup present, segment-leading steering tags,
  ≤ 20 breaks/segment, well-formed.
- Both artifacts present; `qa_vo_content_unchanged` and `qa_voice_markup` green via the runner.

## Anti-patterns

- "In this video, we'll explore…" — banned. Use the ostensive, diegetic opener.
- "Imagine a world where…" — banned. Use a diegetic anchor (a year, a place, a person).
- "Many" / "a lot of" when a number exists — banned. Use the number.
- Three sentences in a row starting with "And" (or any repeated sentence-start) — anaphora ban.
- CAPS on common words ("really", "so") — emphasis must be earned.
- A steering tag placed mid-segment — Inworld only honors it as the FIRST token; `qa_voice_markup`
  FAILS it. Lead the segment with the tag.
- Changing a word while "formatting" — the markup adds presentation only;
  `qa_vo_content_unchanged` FAILS the first altered word.
- **Generating VO audio here** — wrong stage and wrong channel. MM voice is user-provided; this
  stage approves TEXT, and [`voice-director.md`](voice-director.md) ingests the audio + builds the
  Whisper spine. Do not call `inworld_tts`, do not transcribe, do not concat a master track.
- Welding the spine thread to a fixed canvas (a presidents map, a fixed roster) — the through-line
  is agent-selected at the storyboard stage from the research candidates; keep the prose thread
  device-agnostic.
