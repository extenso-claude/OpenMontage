"""Regression harness for the gate suite.

The plan's rule: every gate must PASS its known-good fixture (exit 0) and FAIL
its known-bad fixture (exit 1). A gate that cannot fail manufactures false
confidence (qa_card_bounds was exactly that). When a new gate is minted from a
real bug, add the failing artifact here as its bad fixture so the bug can never
silently return.

Run:  python -m lib.midnight_magnates.gates.test_gates
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FIX = Path(__file__).resolve().parent / "fixtures"

# (gate_module, project_fixture, expected_exit)
# Original two gates use shared proj_* fixtures; the swarm-built gates each own
# gate-namespaced fixtures/<gate>/{good,bad}.
CASES = [
    # sleep-network-overlay gates (built/promoted 2026-06-01)
    ("qa_asset_coverage", "qa_asset_coverage/good", 0),
    ("qa_asset_coverage", "qa_asset_coverage/bad", 1),
    ("qa_avatar_sync", "qa_avatar_sync/good", 0),
    ("qa_avatar_sync", "qa_avatar_sync/bad", 1),
    ("qa_card_timing", "qa_card_timing/good", 0),
    ("qa_card_timing", "qa_card_timing/bad", 1),
    ("qa_source_collision", "qa_source_collision/good", 0),
    ("qa_source_collision", "qa_source_collision/bad", 1),
    ("qa_clip_no_extra_chyron", "qa_clip_no_extra_chyron/good", 0),
    ("qa_clip_no_extra_chyron", "qa_clip_no_extra_chyron/bad", 1),
    ("qa_channel_fingerprint", "qa_channel_fingerprint/good", 0),
    ("qa_channel_fingerprint", "qa_channel_fingerprint/bad", 1),
    ("qa_generation_budget", "qa_generation_budget/good", 0),
    ("qa_generation_budget", "qa_generation_budget/bad", 1),
    ("qa_min_hold", "proj_good", 0),
    ("qa_min_hold", "proj_bad_min_hold", 1),
    ("qa_no_custom_scripts", "proj_good", 0),
    ("qa_no_custom_scripts", "proj_monolith", 1),
    ("qa_element_overlap", "qa_element_overlap/good", 0),
    ("qa_element_overlap", "qa_element_overlap/bad", 1),
    ("qa_card_bounds", "qa_card_bounds/good", 0),
    ("qa_card_bounds", "qa_card_bounds/bad", 1),
    ("qa_vo_content_unchanged", "qa_vo_content_unchanged/good", 0),
    ("qa_vo_content_unchanged", "qa_vo_content_unchanged/bad", 1),
    ("qa_voice_markup", "qa_voice_markup/good", 0),
    ("qa_voice_markup", "qa_voice_markup/bad", 1),
    ("qa_asset_reference_closure", "qa_asset_reference_closure/good", 0),
    ("qa_asset_reference_closure", "qa_asset_reference_closure/bad", 1),
    ("qa_render_existence_duration", "qa_render_existence_duration/good", 0),
    ("qa_render_existence_duration", "qa_render_existence_duration/bad", 1),
    ("qa_continuity", "qa_continuity/good", 0),
    ("qa_continuity", "qa_continuity/bad", 1),
    ("qa_geo", "qa_geo/good", 0),
    ("qa_geo", "qa_geo/bad", 1),
    ("qa_schema_validate", "qa_schema_validate/good", 0),
    ("qa_schema_validate", "qa_schema_validate/bad", 1),
    ("qa_physics", "qa_physics/good", 0),
    ("qa_physics", "qa_physics/bad", 1),
    ("qa_physics", "qa_physics/bad_no_graph", 1),  # 2d/3d beats declared but no scene-graph emitted
    ("qa_physics", "qa_physics/stub", 0),  # compile-time stub graph (no actors/props) -> non-blocking stub_graph_no_geometry warn
    ("qa_voice_segments", "qa_voice_segments/good", 0),
    ("qa_voice_segments", "qa_voice_segments/bad", 1),
    ("qa_cue_lifecycle", "qa_cue_lifecycle/good", 0),
    ("qa_cue_lifecycle", "qa_cue_lifecycle/bad", 1),
    ("qa_drift", "qa_drift/good", 0),
    ("qa_drift", "qa_drift/bad", 1),
    ("qa_render_directive", "qa_render_directive/good", 0),
    ("qa_render_directive", "qa_render_directive/bad", 1),
    ("qa_primitive_utilization", "qa_primitive_utilization/good", 0),
    ("qa_primitive_utilization", "qa_primitive_utilization/bad", 1),
    ("qa_black_frame", "qa_black_frame/good", 0),
    ("qa_black_frame", "qa_black_frame/bad", 1),
    ("qa_face_visibility", "qa_face_visibility/good", 0),
    ("qa_face_visibility", "qa_face_visibility/bad", 1),
    ("qa_alarming_sfx", "qa_alarming_sfx/good", 0),
    ("qa_alarming_sfx", "qa_alarming_sfx/bad", 1),
    ("qa_sfx_audibility", "qa_sfx_audibility/good", 0),
    ("qa_sfx_audibility", "qa_sfx_audibility/bad", 1),
    ("qa_no_reimplementation", "qa_no_reimplementation/good", 0),
    ("qa_no_reimplementation", "qa_no_reimplementation/bad", 1),
    ("qa_loudness", "qa_loudness/good", 0),
    ("qa_loudness", "qa_loudness/bad", 1),
    ("qa_audio_drift", "qa_audio_drift/good", 0),
    ("qa_audio_drift", "qa_audio_drift/bad", 1),
    ("qa_placement", "qa_placement/good", 0),
    ("qa_placement", "qa_placement/bad", 1),
    # --- swarm rails build (A1, A3, A4, A5/A6, A7/A8/A9, A10/A11/A12, A13) ---
    ("qa_map_contrast", "qa_map_contrast/good", 0),
    ("qa_map_contrast", "qa_map_contrast/bad", 1),
    ("qa_asset_sourcing", "qa_asset_sourcing/good", 0),
    ("qa_asset_sourcing", "qa_asset_sourcing/bad", 1),
    ("qa_clip_treatment", "qa_clip_treatment/good", 0),
    ("qa_clip_treatment", "qa_clip_treatment/bad", 1),
    ("qa_character_presence", "qa_character_presence/good", 0),
    ("qa_character_presence", "qa_character_presence/bad", 1),
    ("qa_chapter_ui", "qa_chapter_ui/good", 0),
    ("qa_chapter_ui", "qa_chapter_ui/bad", 1),
    ("qa_duplicate_face", "qa_duplicate_face/good", 0),
    ("qa_duplicate_face", "qa_duplicate_face/bad", 1),
    ("qa_pin_label_pulse_align", "qa_pin_label_pulse_align/good", 0),
    ("qa_pin_label_pulse_align", "qa_pin_label_pulse_align/bad", 1),
    ("qa_basemap_present", "qa_basemap_present/good", 0),
    ("qa_basemap_present", "qa_basemap_present/bad", 1),
    ("qa_stray_mover", "qa_stray_mover/good", 0),
    ("qa_stray_mover", "qa_stray_mover/bad", 1),
    ("qa_ui_sfx_coverage", "qa_ui_sfx_coverage/good", 0),
    ("qa_ui_sfx_coverage", "qa_ui_sfx_coverage/bad", 1),
    ("qa_visual_contrast", "qa_visual_contrast/good", 0),
    ("qa_visual_contrast", "qa_visual_contrast/bad", 1),
    ("qa_visual_completeness", "qa_visual_completeness/good", 0),
    ("qa_visual_completeness", "qa_visual_completeness/bad", 1),
    ("qa_visual_alignment", "qa_visual_alignment/good", 0),
    ("qa_visual_alignment", "qa_visual_alignment/bad", 1),
    ("qa_creature_animation", "qa_creature_animation/good", 0),
    ("qa_creature_animation", "qa_creature_animation/bad", 1),
    ("qa_beat_visual_coverage", "qa_beat_visual_coverage/good", 0),
    ("qa_beat_visual_coverage", "qa_beat_visual_coverage/bad", 1),
    ("qa_migration_icon", "qa_migration_icon/good", 0),
    ("qa_migration_icon", "qa_migration_icon/bad", 1),
    ("qa_spine_consistency", "qa_spine_consistency/good", 0),
    ("qa_spine_consistency", "qa_spine_consistency/bad", 1),
    # --- MM synchrony + enforcement gates (swarm fan-out, 2026-05-31) ---
    ("qa_cue_drift", "qa_cue_drift/good", 0),
    ("qa_cue_drift", "qa_cue_drift/bad", 1),
    ("qa_spatial_anchor", "qa_spatial_anchor/good", 0),
    ("qa_spatial_anchor", "qa_spatial_anchor/bad", 1),
    ("qa_emotion_face_coverage", "qa_emotion_face_coverage/good", 0),
    ("qa_emotion_face_coverage", "qa_emotion_face_coverage/bad", 1),
    ("qa_sfx_event_sync", "qa_sfx_event_sync/good", 0),
    ("qa_sfx_event_sync", "qa_sfx_event_sync/bad", 1),
    ("qa_scene_sync", "qa_scene_sync/good", 0),
    ("qa_scene_sync", "qa_scene_sync/bad", 1),
    ("qa_master_offset", "qa_master_offset/good", 0),
    ("qa_master_offset", "qa_master_offset/bad", 1),
    ("qa_voice_timestamps", "qa_voice_timestamps/good", 0),
    ("qa_voice_timestamps", "qa_voice_timestamps/bad", 1),
    ("qa_shot_status_clean", "qa_shot_status_clean/good", 0),
    ("qa_shot_status_clean", "qa_shot_status_clean/bad", 1),
    ("qa_image_gen_policy", "qa_image_gen_policy/good", 0),
    ("qa_image_gen_policy", "qa_image_gen_policy/bad", 1),
    ("qa_skill_gate_refs", "qa_skill_gate_refs/good", 0),
    ("qa_skill_gate_refs", "qa_skill_gate_refs/bad", 1),
    ("qa_rendered_sync", "qa_rendered_sync/good", 0),
    ("qa_rendered_sync", "qa_rendered_sync/bad", 1),
]


def _run(gate: str, project: Path) -> int:
    return subprocess.run(
        [sys.executable, "-m", f"lib.midnight_magnates.gates.{gate}",
         "--project", str(project)],
        cwd=str(REPO), capture_output=True, text=True,
    ).returncode


def main() -> int:
    failures = []
    for gate, proj_name, expect in CASES:
        rc = _run(gate, FIX / proj_name)
        ok = rc == expect
        print(f"[{'PASS' if ok else 'FAIL'}] {gate} on {proj_name}: exit {rc} (expected {expect})")
        if not ok:
            failures.append((gate, proj_name, rc, expect))
    if failures:
        print(f"\n{len(failures)} fixture assertion(s) FAILED")
        return 1
    print("\nAll gate fixtures behaved correctly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
