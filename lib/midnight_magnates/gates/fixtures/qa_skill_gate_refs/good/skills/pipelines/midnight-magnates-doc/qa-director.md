# QA Director — Midnight Magnates Doc

Iterative QA with no round cap. Hard gates run first; any non-zero exit means
fix and re-run ALL gates. Every gate named here is a real module under
lib/midnight_magnates/gates/ and runs in import form, never as a scripts/ path.

## Layer A — Hard gates (mandatory)

Every cited gate resolves to lib/midnight_magnates/gates/<name>.py:

- qa_min_hold — text-bearing cues stay on screen long enough to read.
- qa_card_bounds — every cue bbox lies fully within the 1920x1080 frame.
- qa_element_overlap — no two same/adjacent-layer cues collide in time and space.
- qa_drift — every beat anchor resolves to a Whisper word or a fallback time.
- qa_geo — pin pixels are derived from lat/lon via mapkit, not hand-edited CSS.
- qa_visual_alignment — a rendered pin lands within tolerance of its declared pixel.
- qa_audio_drift — sound cues anchored to the VO stay inside their drift budget.

Each is invoked as:

    python3 -m lib.midnight_magnates.gates.qa_min_hold --project {project_dir}

## Layer B — Breadth swarm

After all gates pass, dispatch the breadth sweepers (cross-chapter consistency,
pacing, tone, map continuity). Any finding → fix → re-run every gate above.

## Output

Writes artifacts/qa_report.json with the round count and the list of gates that
passed. (The "qa_report.json" filename here is data, not a gate citation.)
