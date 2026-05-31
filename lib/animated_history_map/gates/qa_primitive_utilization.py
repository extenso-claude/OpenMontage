"""qa_primitive_utilization — the storyboard must actually USE its vocabulary.

Catches the documented "7-of-64 / 16% utilization" collapse: a chapter that
nominally has ~64 storyboard primitives available but renders out as five kinds
of pin on a map, with no off-map dives and no persistent on-screen UI. The video
reads as a slideshow of dots, not an animated documentary.

The storyboard primitive enum
(schemas/artifacts/animated_history_map_storyboard.schema.json -> layer_action
.primitive) is grouped into six families. Three of them are non-negotiable: a
finished chapter must spend pixels on the map itself (MAP_BOUND), step off the
map to show people/documents/archival (OFF_MAP), and keep continuity furniture
alive on screen (PERSISTENT_UI). The other three (CLIMAX, ATMOSPHERIC,
TRANSITION) enrich but are not individually mandatory here.

Rule (fail):
    * fewer than MIN_DISTINCT (=12) distinct primitive kinds across all cues, OR
    * any REQUIRED family ({MAP_BOUND, OFF_MAP, PERSISTENT_UI}) with zero usage.

Reads:  <project>/artifacts/cuelist.json
Shape:  {"cues": [{"id","kind"(a storyboard primitive name),"start_s","end_s",
                   "layer", ...}, ...]}

Note: audio primitives (music_*, sfx_*) and the catch-all "experimental" are not
members of any of the six content families. They still count toward the distinct
-kind total (they are real distinct kinds) but can never satisfy a REQUIRED
content family — exactly right, since a soundtrack does not make a map.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

MIN_DISTINCT = 12

# Families mirror the storyboard schema's primitive enum. Kept as tuples so the
# mapping is obviously exhaustive and easy to diff against the schema.
FAMILIES: Dict[str, Tuple[str, ...]] = {
    "MAP_BOUND": (
        "pin_drop", "pin_dimming", "pin_pulse_breath", "map_sprite",
        "migration_arrow", "front_line_curve", "glow_region", "territory_wash",
        "trench_line", "map_label", "label_cluster", "concept_stamp",
        "time_stamp", "polygon_fill", "polygon_clear", "region_label_in",
        "region_label_out",
    ),
    "OFF_MAP": (
        "story_dive", "panel_archival", "panel_illustration", "panel_quote",
        "parallax_layers", "clip_archival", "document_overlay",
        "source_citation", "etymology_card", "concept_diagram",
        "character_card", "character_card_pop",
    ),
    "CLIMAX": (
        "flash_burst", "bullet_trail", "slow_zoom_terror", "clock_freeze",
        "gunshot_freeze", "mournful_hold", "dust_settle",
    ),
    "ATMOSPHERIC": (
        "weather_overlay", "cloud_drift", "idle_atmosphere", "time_of_day",
        "paper_texture", "vignette_pulse",
    ),
    "TRANSITION": (
        "basemap_swap", "panel_to_pin_morph", "chapter_wipe", "time_shift",
        "year_sweep", "connection_line", "camera_push_in", "camera_pull_out",
        "camera_pan", "camera_orbit", "camera_hold",
    ),
    "PERSISTENT_UI": (
        "chapter_subject_badge_swap", "year_card_update",
        "chapter_timeline_update", "structure_tree_node_fill", "vignette_breath",
    ),
}

REQUIRED_FAMILIES = ("MAP_BOUND", "OFF_MAP", "PERSISTENT_UI")

# Reverse index: primitive kind -> family name (built once at import).
_KIND_TO_FAMILY: Dict[str, str] = {
    kind: family for family, kinds in FAMILIES.items() for kind in kinds
}


def _kind(cue: dict) -> Optional[str]:
    """Return the cue's primitive kind as a non-empty string, else None."""
    val = cue.get("kind")
    if isinstance(val, str):
        val = val.strip()
        if val:
            return val
    return None


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    distinct_kinds = set()              # every distinct primitive kind seen
    families_used = set()               # families with >=1 usage
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError(f"cuelist.json cue #{i} is not an object")
        kind = _kind(cue)
        if kind is None:
            continue  # un-kinded cue contributes nothing to the vocabulary
        distinct_kinds.add(kind)
        family = _KIND_TO_FAMILY.get(kind)
        if family is not None:
            families_used.add(family)

    n_distinct = len(distinct_kinds)
    empty_required = [f for f in REQUIRED_FAMILIES if f not in families_used]
    unused_families = [f for f in FAMILIES if f not in families_used]

    findings: List[Finding] = []

    # 1) Raw vocabulary breadth.
    if n_distinct < MIN_DISTINCT:
        findings.append(Finding(
            "fail", "low_primitive_utilization",
            f"only {n_distinct} distinct primitive kinds used across all cues; "
            f"need >= {MIN_DISTINCT} (the '7-of-64 / 16%' collapse). "
            f"Used: {sorted(distinct_kinds) or 'none'}. "
            f"Unused families: {unused_families or 'none'}.",
            where="cuelist.json",
        ))

    # 2) Each required content family must appear at least once.
    if empty_required:
        findings.append(Finding(
            "fail", "required_family_unused",
            f"REQUIRED families with zero usage: {empty_required}. "
            f"A finished chapter must use the map (MAP_BOUND), step off the map "
            f"(OFF_MAP), and keep persistent UI (PERSISTENT_UI). "
            f"Distinct kinds = {n_distinct}; all unused families: {unused_families}.",
            where="cuelist.json",
        ))

    return findings


if __name__ == "__main__":
    run_cli("qa_primitive_utilization", check)
