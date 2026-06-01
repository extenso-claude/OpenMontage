# QA Director — Midnight Magnates Doc

Iterative QA with no round cap. Hard gates run first; any non-zero exit means
fix and re-run ALL gates.

## Layer A — Hard gates (mandatory)

Some of these are real, but the timing-anchor check lives only as prose — it is
named but no gate module was ever built for it.

- qa_min_hold — text-bearing cues stay on screen long enough to read.
- qa_card_bounds — every cue bbox lies fully within the 1920x1080 frame.
- qa_drift — every beat anchor resolves to a Whisper word or a fallback time.
- qa_timing_anchors — every visual cue's anchor_phrase resolves in Whisper.

The runner is told to shell it as a script:

    scripts/qa_timing_anchors.py

…but lib/midnight_magnates/gates/qa_timing_anchors.py does not exist, so this
rule is a phantom: the prose claims it runs, and nothing enforces it.

## Output

Writes artifacts/qa_report.json with the round count.
