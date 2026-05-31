# Asset Director — Animated History Map

Source every asset the storyboard references. Parallel sourcer swarm. ALL FREE except TTS (already done in script stage).

## Read first

- `docs/animated-history-map-design-intel.md` §9.7 (asset sourcing approach for this project)
- `skills/core/asset-coverage-gates.md` — the coverage gate enforcement
- `skills/core/clip-treatments.md` — transformative-use workflow for copyrighted clips

## NO-NO list (no exceptions)

- No Recraft (per user instruction)
- No Flux / Imagen / DALL-E / any AI image generation
- No ElevenLabs Music API
- No paid stock services

## Sourcer swarm

Dispatch in parallel:

### Portrait sourcer
- Tool: `lib/asset_sourcing/portraits.py` (existing)
- Sources: Wikimedia Commons + Library of Congress
- Per named person in canonical_names, fetch ≥1 PD photo
- Output: `assets/portraits/<person_id>/portrait.png` + `manifest.json` with license + source URL

### Archival video sourcer
- Sources: Internet Archive (Universal Newsreels, Prelinger Archives, government films)
- Per event, search for period footage matching the event
- For copyrighted modern footage (JFK Zapruder, Reagan news clips, Trump 2024), route through `tools/clip_treatment/` — transformative-use with locked filter + approved frame
- Output: `assets/archival_video/<event_id>_<n>.mp4` + treated variants `_treated.mp4`

### Stock B-roll sourcer
- Sources: Pexels + Pixabay free tier
- Per chapter, source atmospheric establishers (rainy DC, smoke, flags, crowds)
- Output: `assets/stock/<chapter_id>_<n>.mp4`

### Procedural SVG sprite sourcer
- In-repo generation
- Per landmark/instrument needed: theatre, capitol, depository, hotel, hospital, expo grounds, train station, gun (period-appropriate), briefcase, clock
- Output: `assets/sprites/<sprite_id>.svg`

### PD floorplan sourcer
- Sources: Library of Congress, FBI archives, Sanborn Maps
- Per building-tier event, find period floorplan
- Procedural fallback if no PD source available
- Output: `assets/floorplans/<building_id>.png`

### Music sourcer
- Check `music_library/` first
- Then YouTube Audio Library + Free Music Archive
- Per chapter mood (somber / tense / mournful / urgent / quiet / climactic), source ≥2 candidates
- Output: `assets/music/<mood_tag>_<n>.mp3` + manifest

### SFX sourcer
- Freesound CC0/CC-BY
- Per cue type (gunshot, crowd, period instrument, clock, etc.), source ≥1 candidate
- Output: `assets/sfx/<cue_id>.wav`

## Asset request channel (just-in-time)

During animation stage, animator subagents may write to `artifacts/asset_requests.json` requesting new assets. A sourcer subagent picks these up and delivers. The animator may proceed with a placeholder; final compile blocks until requested assets land.

## Gates

- `qa_asset_coverage.py` — every storyboard `asset_id` resolves to an existing file in asset_manifest.json
- Every asset has a license + source URL in manifest

## Output

`artifacts/asset_manifest.json`:

```jsonc
{
  "assets": [
    {
      "asset_id": "abraham_lincoln_1865_portrait",
      "category": "portrait",
      "path": "assets/portraits/abraham_lincoln/portrait.png",
      "license": "PD",
      "source_url": "https://www.loc.gov/...",
      "person_id": "abraham_lincoln"
    },
    {
      "asset_id": "zapruder_frame_313_treated",
      "category": "archival_video",
      "path": "assets/archival_video/jfk_1963_zapruder_treated.mp4",
      "license": "transformative_use",
      "original_source": "Abraham Zapruder, 1963",
      "treatment": "grade_cyan_orange + frame_03",
      "audio_role": "vo_over"
    }
  ]
}
```
