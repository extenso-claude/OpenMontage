"""G-voice — the human voice-review gate UI.

After the automated Voice-QA->fix loop (voice_qa.py) runs and writes
artifacts/voice_report.json, the human reviews the voiceover here: scrub the VO,
read the per-segment metrics, and for any segment either APPROVE it (a human
override the gate accepts) or flag it REGENERATE with a note + optional fix hint
(IPA / break / steering / rate) that the loop consumes on the next pass.

Submitting writes artifacts/approvals/voice.json — the exact artifact
lib/animated_history_map/runner.py's run_stage() requires before the pipeline may
advance past the voice stage. So this UI IS the G-voice gate, not a courtesy.

    python -m lib.animated_history_map.gvoice.serve --project <project_dir> [--port 3011]
"""
