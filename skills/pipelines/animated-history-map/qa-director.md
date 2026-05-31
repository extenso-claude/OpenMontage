# QA Director — Animated History Map

Iterative QA with no round cap. Three layers: hard gates → breadth swarm → depth review. Steady-state detection prevents infinite loops.

## Layer A — Hard gates (mandatory)

All 17 gates run. Any non-zero exit → fix → re-run **ALL gates**. Loop until clean.

```
scripts/qa_asset_coverage.py
scripts/qa_gap_coverage.py
scripts/qa_pin_geographic_accuracy.py
scripts/qa_projection_consistency.py
scripts/qa_location_provenance.py
scripts/qa_canonical_names.py
scripts/qa_card_bounds.py
scripts/qa_element_overlap.py
scripts/qa_label_collision.py
scripts/qa_min_hold.py
scripts/qa_motion_direction.py
scripts/qa_motion_vocabulary.py
scripts/qa_text_containment.py
scripts/qa_audio_drift.py
scripts/qa_timing_anchors.py
scripts/qa_layer_conflicts.py
scripts/qa_region_provenance.py
```

## Layer B — Breadth swarm (after all gates pass)

Dispatch 6 parallel sweeper subagents:

1. **Cross-chapter consistency** — Jackson's portrait appears identically when re-cued in chapter 14? Year card increments monotonically? Theme palette consistent?
2. **Pacing audit** — Three consecutive chapters share the same arc shape? Camera-move frequency varies?
3. **Tone drift** — Does the VO voice stay measured across 20 min? Any chapter overheats / cools off?
4. **Map continuity** — Pin set grows monotonically (no resurrected past chapters)? Dimmed pins stay dimmed?
5. **Sensitive-content sweep** — Per `youtube_ai_slop_signals` memory + per-era sensitivities (lone-gunman conspiracy framing? graphic violence?)
6. **Source-citation completeness** — Every claim in script has a `source_ref` in research_brief? Every quote attributed?

Any finding → fix → re-run ALL gates AND breadth swarm.

## Layer C — Depth review (after breadth swarm passes)

ONE reviewer subagent. Reads the draft render at 2× speed + reads the master comp HTML. Looks for:

- Subjective quality issues
- Enhancement opportunities
- Pacing problems gates can't catch
- Visual fatigue / monotony
- Missed opportunities for ref-1/3/4/5 primitives

Outputs findings + proposed fixes. Animator fixes. Re-run gates + breadth + depth.

**Loop until reviewer returns "no new improvements found."**

## Stop conditions

1. **Clean** — reviewer returns no findings AND all gates pass AND breadth swarm is empty.
2. **Steady-state** — round N produces same findings as round N-1. Escalate to user with "stable but imperfect" status.
3. **Resource cap** (safety) — if total fix-time exceeds 4 hours of wall clock without clean, escalate.

## Output

`artifacts/qa_report.json`:
```jsonc
{
  "round_count": 3,
  "final_outcome": "clean",
  "gates_passed": ["qa_asset_coverage", ...],
  "breadth_findings": [],
  "depth_findings": [],
  "experimental_beats_evaluated": [{ "beat_id": "...", "outcome": "accepted" }]
}
```
