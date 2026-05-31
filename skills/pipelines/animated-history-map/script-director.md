# Script Director — Animated History Map

Write `artifacts/script.json` — the VO script with Inworld TTS-2 markup. Then generate the VO MP3s.

## Read first

- `docs/animated-history-map-design-intel.md` §3 (pacing), §4 (hook architecture), §6 (production tells)
- `artifacts/theme.json` — for pacing_target, hook_engine, voice_persona
- `artifacts/research_brief.json` — for facts
- `artifacts/canonical_names.json` — **use ONLY these names + spellings**
- Reference 5 brief in `docs/animated-history-map-references/ref5_script_*.md` — the script-craft canon

## Writing rules (locked from Ref 5)

1. **Open with ostensive opener.** `"This is..."` or `"It's [year], and [person] is [doing X] here, in [place]."` First sentence ≤12 words. Map carries the deixis.

2. **Per `hook_engine`:**
   - `rolling_payoff`: First named-figure payoff lands by 0:20. Then ordinal countdown ("first", "next", "then") with rolling small payoffs every ~15s.
   - `deep_mystery`: Triple-nested cliffhanger before 90s. First open loop in sentence 2 ("you've probably heard X but get [Y] WRONG"). Second nested loop ~0:55 ("a [shocking thing] that will [strong consequence]"). Drop into context with "But before I share, you first need to understand..."

3. **Stack open loops every 60–120s.** Use: *"something would happen that would [strong consequence verb]"*, *"more shocking than most people realize"*, *"Most people don't realize this, but..."*

4. **Reserve short sentences (≤8 words) for emotional landings only.** ~5% of total sentences. Examples: `"He was DIVINE."`, `"But they were wrong."`, `"She was anointing him for burial."`

5. **"But" pivot** ~14% of sentences. ZERO sentence-start anaphora — vary openings.

6. **Anchor every map move with named place + named person + specific number.** Density: ~25 capitalized proper-noun tokens per minute, ≥1 concrete number per 60s. NEVER say "many" when a number exists.

7. **Quote dialogue at climactic moments only.** ~1 quote per 2 minutes. Quotes are set-pieces.

8. **Plant 2–3 etymology / "we still call this today" micro-spikes in the middle act.** Highest-engagement spots in Ref 5's heatmap.

9. **Build a spine thread.** Plant in first 60s, callback at climax + closing. For Presidential Assassinations: *"the next pin on this map has not been drawn yet."*

10. **CTA welded to geography.** Pivot to CTA from a place name in the final act, not a fixed timestamp.

11. **WPM at theme.voice_persona.wpm_target ±5%.** No acceleration/deceleration — all drama in word choice.

## Inworld TTS-2 markup rules

The script uses inline markup that the `inworld_tts` tool understands:

- **Emotion tags** `[curious]`, `[wry]`, `[suspenseful]`, `[hushed]`, `[awed]`, `[reverent]`, `[grave]`, `[warm]`. Place ONLY at topic pivots / change-of-pace beats. ~1 tag-change per 90–120s.
- **CAPS** on a single critical word per climactic reveal. Never on common words. Never more than once per paragraph.
- **Em-dash** for long pauses (≥0.5s perceived). Place at colon-pivots where the speaker withholds a noun: `"...defeat a much greater enemy — death."`
- **Line breaks** for natural sentence-clause breath.
- **`<break time="1000ms" />`** after act-ending short sentences and climactic reveals. Also between chapters.

### Concrete markup example (for the assassinations opener)

```
[curious] This is a map of every man who tried to KILL an American president.

There have been seventeen attempts — across nineteen states, two centuries, and seven assassins who succeeded.

Some you remember.

Some — most people have never heard of.
<break time="1000ms" />

[suspenseful] And the next pin on this map — has not been drawn yet.
<break time="1000ms" />
```

## Workflow

1. **Plan the chapter list.** Allocate runtime budget per chapter (typically ~90s for major events, ~30s for minor ones, ~45s for cold open + closing).

2. **Write the cold open + closing first.** These set the spine thread and the tone.

3. **Write each chapter** using the 8-phase template (map_breath → approach → characters → story_dive → climax → aftermath → return_to_map → transition). Tag VO per phase so the storyboard director can sync.

4. **Cross-check names against `canonical_names.json`.** Run `qa_canonical_names.py` (or a quick manual scan) before submitting.

5. **Generate VO MP3s via the `inworld_tts` tool.** Tyler, more_creative mode. One MP3 per chapter (chunked at 2000-char limit if needed).

6. **Transcribe each chapter's VO via Whisper** (using `video-understand` or `speech-to-text` skill) to get word-level timestamps. Save to `artifacts/whisper/chapter_<n>.json`. **This is what storyboard anchors will reference.**

7. **Concatenate VO MP3s** in chapter order into `assets/audio/vo_full.mp3` for the master comp.

## Output format

`artifacts/script.json`:

```jsonc
{
  "project_id": "...",
  "total_duration_target_s": 1200,
  "wpm_actual": 164,
  "chapters": [
    {
      "chapter_id": "ch00_cold_open",
      "chapter_index": 0,
      "year_range": [2024, 2024],
      "vo_text_with_markup": "[curious] This is a map of every man who tried to KILL an American president.\n\n...",
      "vo_text_plain": "This is a map of every man who tried to kill an American president...",
      "phase_segments": [
        { "phase_kind": "cold_open", "vo_start_word": 0, "vo_end_word": 87 }
      ],
      "estimated_duration_s": 45,
      "named_entities_used": ["donald_trump_2024", "butler_pa_2024", ...]
    },
    ...
  ]
}
```

## Quality bar

- Hook earns the next 60s (first payoff per engine type)
- WPM within ±5% of target
- Canonical names dictionary respected (zero rejected variations)
- Every paragraph break feels intentional, not arbitrary
- Inworld markup present and well-formed
- All VO MP3s generated + Whisper transcripts in place

## Anti-patterns

- "In this video, we'll explore..." — banned. Use ostensive opener.
- "Imagine a world where..." — banned. Use diegetic anchor.
- "Many", "a lot of" when a number exists — banned. Use the number.
- Three sentences in a row starting with "And" — anaphora ban.
- CAPS on common words like "really", "so" — emphasis must be earned.
- Sponsor break in middle of dramatic arc — if there's a CTA, weld to geography.
