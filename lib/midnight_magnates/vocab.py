"""Canonical Midnight Magnates primitive vocabulary + family groupings.

Single source of truth for the storyboard primitive catalog and every family /
sub-set that is currently *duplicated* across the compiler and the gates. The
duplication this module retires:

  * lib/midnight_magnates/compiler.py
        AUDIO_PRIMS, CARD_PRIMS, MAP_ANCHORED_PRIMS, FULLFRAME_PRIMS,
        UI_CORNER_PRIMS, FACE_PRIMS
  * lib/midnight_magnates/gates/qa_primitive_utilization.py
        FAMILIES (MAP_BOUND/OFF_MAP/CLIMAX/ATMOSPHERIC/TRANSITION/PERSISTENT_UI),
        REQUIRED_FAMILIES, MIN_DISTINCT
  * lib/midnight_magnates/gates/qa_beat_visual_coverage.py   OFF_MAP_VISUAL_PRIMS
  * lib/midnight_magnates/gates/qa_emotion_face_coverage.py  FACE_PRIMITIVES
  * lib/midnight_magnates/gates/qa_spatial_anchor.py         CHROME_KINDS,
                                                             EVENT_FX_KINDS,
                                                             _AUDIO_KINDS
  * lib/midnight_magnates/gates/qa_cue_lifecycle.py          PERSISTENT_KINDS
  * lib/midnight_magnates/gates/qa_visual_alignment.py       _PIN_KINDS

PRIMITIVES is the ordered catalog and is IDENTICAL (members + order) to the
``layer_action.properties.primitive.enum`` in
``schemas/artifacts/midnight_magnates_storyboard.schema.json`` — the schema is
the source of truth, this is a verbatim mirror for code that cannot conveniently
load the JSON. Every other name below reproduces EXACTLY the current value at its
site, so the later consumer refactors are pure 1:1 substitutions (no semantic
change). A module-level self-consistency check (run at import) guarantees every
member of every family / named set is a real primitive; a stray member raises
AssertionError naming it.

This module deliberately has NO consumers yet — it must simply EXIST and import
cleanly so the nine sites above can later switch to it. Do not change any value
here without changing the corresponding site in the same commit.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Tuple

# ---------------------------------------------------------------------------
# PRIMITIVES — the ordered storyboard primitive catalog.
# IDENTICAL (members + order) to midnight_magnates_storyboard.schema.json
#   definitions.layer_action.properties.primitive.enum
# Grouped here only by visual block for readability; the FLAT order is the
# schema's enum order and is the contract (the import-time check asserts the set
# equality against the schema is the consumer's job; this tuple is the mirror).
# ---------------------------------------------------------------------------
PRIMITIVES: Tuple[str, ...] = (
    # pins / cards
    "pin_drop", "pin_dimming", "pin_pulse_breath", "all_presidents_pins",
    "map_sprite", "character_card", "character_card_pop",
    # map-bound vectors / labels
    "migration_arrow", "front_line_curve", "glow_region", "territory_wash",
    "trench_line", "concept_stamp", "label_cluster", "time_stamp", "map_label",
    # atmosphere
    "weather_overlay", "cloud_drift", "idle_atmosphere", "time_of_day",
    "paper_texture", "vignette_pulse",
    # camera
    "camera_push_in", "camera_pull_out", "camera_pan", "camera_orbit",
    "camera_hold",
    # transitions
    "basemap_swap", "panel_to_pin_morph", "chapter_wipe", "time_shift",
    "year_sweep", "connection_line",
    # off-map / story
    "story_dive", "panel_archival", "panel_illustration", "panel_quote",
    "parallax_layers", "clip_archival", "document_overlay",
    "source_citation", "etymology_card", "concept_diagram",
    # climax FX
    "flash_burst", "bullet_trail", "slow_zoom_terror", "clock_freeze",
    "gunshot_freeze", "mournful_hold", "dust_settle",
    # persistent UI
    "chapter_subject_badge_swap", "year_card_update", "chapter_timeline_update",
    "structure_tree_node_fill", "vignette_breath",
    # polygon / region labels
    "polygon_fill", "polygon_clear", "region_label_in", "region_label_out",
    # audio
    "music_swell", "music_drop", "sfx_accent", "sfx_ambient_in",
    "sfx_ambient_out",
    # faces
    "face_closeup", "face_reaction", "face_medium", "reaction_cut",
    # spine / catch-all
    "spine_panel",
    "experimental",
)

# Fast membership set (kept private; PRIMITIVES is the ordered public contract).
_PRIMITIVE_SET: FrozenSet[str] = frozenset(PRIMITIVES)


# ---------------------------------------------------------------------------
# PRIMITIVE_FAMILIES — the six storyboard families.
# IDENTICAL to qa_primitive_utilization.FAMILIES (values as frozensets; family
# ORDER preserved for human diffing, though a frozenset itself is unordered).
# Their union is intentionally NOT all of PRIMITIVES: audio (music_*/sfx_*),
# faces (face_*/reaction_cut), all_presidents_pins, spine_panel and the catch-all
# `experimental` are members of NO content family (a soundtrack/face/spine does
# not satisfy a REQUIRED content family).
# ---------------------------------------------------------------------------
PRIMITIVE_FAMILIES: Dict[str, FrozenSet[str]] = {
    "MAP_BOUND": frozenset({
        "pin_drop", "pin_dimming", "pin_pulse_breath", "map_sprite",
        "migration_arrow", "front_line_curve", "glow_region", "territory_wash",
        "trench_line", "map_label", "label_cluster", "concept_stamp",
        "time_stamp", "polygon_fill", "polygon_clear", "region_label_in",
        "region_label_out",
    }),
    "OFF_MAP": frozenset({
        "story_dive", "panel_archival", "panel_illustration", "panel_quote",
        "parallax_layers", "clip_archival", "document_overlay",
        "source_citation", "etymology_card", "concept_diagram",
        "character_card", "character_card_pop",
    }),
    "CLIMAX": frozenset({
        "flash_burst", "bullet_trail", "slow_zoom_terror", "clock_freeze",
        "gunshot_freeze", "mournful_hold", "dust_settle",
    }),
    "ATMOSPHERIC": frozenset({
        "weather_overlay", "cloud_drift", "idle_atmosphere", "time_of_day",
        "paper_texture", "vignette_pulse",
    }),
    "TRANSITION": frozenset({
        "basemap_swap", "panel_to_pin_morph", "chapter_wipe", "time_shift",
        "year_sweep", "connection_line", "camera_push_in", "camera_pull_out",
        "camera_pan", "camera_orbit", "camera_hold",
    }),
    "PERSISTENT_UI": frozenset({
        "chapter_subject_badge_swap", "year_card_update",
        "chapter_timeline_update", "structure_tree_node_fill", "vignette_breath",
    }),
}

# The three families a finished chapter MUST exercise + the breadth floor.
# IDENTICAL to qa_primitive_utilization.REQUIRED_FAMILIES / MIN_DISTINCT.
REQUIRED_FAMILIES: Tuple[str, ...] = ("MAP_BOUND", "OFF_MAP", "PERSISTENT_UI")
MIN_DISTINCT: int = 12


# ---------------------------------------------------------------------------
# compiler.py primitive families (lib/midnight_magnates/compiler.py ~L52-57).
# These drive bbox / track / "is this a visual element". Verbatim values.
# ---------------------------------------------------------------------------
AUDIO_PRIMS: FrozenSet[str] = frozenset({
    "music_swell", "music_drop", "sfx_accent", "sfx_ambient_in",
    "sfx_ambient_out",
})
CARD_PRIMS: FrozenSet[str] = frozenset({
    "character_card", "character_card_pop", "source_citation", "etymology_card",
    "concept_diagram",
})
# The character members of CARD_PRIMS (those whose name starts with
# "character_card"). character_treatment.CHARACTER_PRIMITIVES was a hand-copy of
# exactly these — it now binds to this. Ordered tuple (sorted) so the public
# shape matches the literal the consumer used: ("character_card",
# "character_card_pop").
CHARACTER_CARD_PRIMS: Tuple[str, ...] = tuple(
    p for p in sorted(CARD_PRIMS) if p.startswith("character_card")
)
MAP_ANCHORED_PRIMS: FrozenSet[str] = frozenset({
    "pin_drop", "pin_dimming", "pin_pulse_breath", "map_sprite", "map_label",
    "label_cluster",
})
FULLFRAME_PRIMS: FrozenSet[str] = frozenset({
    "story_dive", "panel_archival", "panel_illustration", "panel_quote",
    "document_overlay", "clip_archival",
})
# Full-frame scene primitives whose presence in a character beat's window means a
# LOWER_CORNER card is composited over real content (scene-anchored), not floating
# on empty parchment. character_treatment.SCENE_ANCHOR_PRIMITIVES was an INEXACT
# hand-mirror — its comment said "FULLFRAME_PRIMS plus map_sprite" but the literal
# also carried "parallax_layers". This is the exact set it meant.
#
# It is an ORDERED tuple (not a frozenset) on purpose: the membership is exactly
# ``frozenset(FULLFRAME_PRIMS) | {"map_sprite", "parallax_layers"}`` (asserted
# below), but qa_character_presence binds SCENE_ANCHOR_PRIMITIVES to this and
# SLICES it (``SCENE_ANCHOR_PRIMITIVES[:4]`` for a hint string), which a frozenset
# cannot do — so the canonical form preserves the consumer's original tuple order.
SCENE_ANCHOR_PRIMS: Tuple[str, ...] = (
    "story_dive", "panel_archival", "panel_illustration", "panel_quote",
    "document_overlay", "clip_archival", "map_sprite", "parallax_layers",
)
# Membership contract: exactly FULLFRAME_PRIMS plus the two placed-scene additions.
assert frozenset(SCENE_ANCHOR_PRIMS) == (
    frozenset(FULLFRAME_PRIMS) | {"map_sprite", "parallax_layers"}
), "vocab.SCENE_ANCHOR_PRIMS membership drifted from FULLFRAME_PRIMS | {map_sprite, parallax_layers}"
assert len(SCENE_ANCHOR_PRIMS) == len(frozenset(SCENE_ANCHOR_PRIMS)), (
    "vocab.SCENE_ANCHOR_PRIMS has duplicate entries"
)
UI_CORNER_PRIMS: FrozenSet[str] = frozenset({
    "time_stamp", "year_card_update", "chapter_subject_badge_swap",
    "chapter_timeline_update",
})
# RULE 4 — emotional faces. Same membership the schema's emotion_face allOf
# requires. Exposed under both names the duplicated sites use:
#   compiler.py            -> FACE_PRIMS
#   qa_emotion_face_coverage -> FACE_PRIMITIVES
FACE_PRIMS: FrozenSet[str] = frozenset({
    "face_closeup", "face_reaction", "face_medium", "reaction_cut",
})
FACE_PRIMITIVES: FrozenSet[str] = FACE_PRIMS  # alias (qa_emotion_face_coverage)


# ---------------------------------------------------------------------------
# qa_beat_visual_coverage.OFF_MAP_VISUAL_PRIMS — verbatim. (Currently identical
# in membership to PRIMITIVE_FAMILIES["OFF_MAP"], but kept as its own named
# constant so that gate's 1:1 substitution stays exact and independent.)
# ---------------------------------------------------------------------------
OFF_MAP_VISUAL_PRIMS: FrozenSet[str] = frozenset({
    "story_dive", "panel_archival", "panel_illustration", "panel_quote",
    "parallax_layers", "clip_archival", "document_overlay",
    "source_citation", "etymology_card", "concept_diagram",
    "character_card", "character_card_pop",
})


# ---------------------------------------------------------------------------
# qa_spatial_anchor "kind" sets — verbatim.
#   CHROME_KINDS    — action-independent UI exempt from a spatial_target.
#   EVENT_FX_KINDS  — react to a place, so MUST carry a spatial_target.
#   AUDIO_KINDS     — sound primitives (= compiler's AUDIO_PRIMS membership);
#                     exposed un-underscored as the canonical name (the gate's
#                     local was _AUDIO_KINDS).
# ---------------------------------------------------------------------------
CHROME_KINDS: FrozenSet[str] = frozenset({
    "year_card_update",
    "chapter_subject_badge_swap",
    "source_citation",
    "time_stamp",
})
EVENT_FX_KINDS: FrozenSet[str] = frozenset({
    "flash_burst",
    "bullet_trail",
    "gunshot_freeze",
    "glow_region",
    "connection_line",
    "dust_settle",
    "slow_zoom_terror",
    "clock_freeze",
    "concept_stamp",
    "mournful_hold",
    "vignette_pulse",
    "time_shift",
    "year_sweep",
    "panel_to_pin_morph",
    "chapter_wipe",
    "structure_tree_node_fill",
})
AUDIO_KINDS: FrozenSet[str] = frozenset({
    "music_swell", "music_drop",
    "sfx_accent", "sfx_ambient_in", "sfx_ambient_out",
})


# ---------------------------------------------------------------------------
# qa_cue_lifecycle.PERSISTENT_KINDS — verbatim. Persistent UI exempt from the
# linger ceiling. NOTE: this is the PERSISTENT_UI family PLUS "paper_texture"
# (which the family files under ATMOSPHERIC) — the two are deliberately not the
# same set, so this is its own constant.
# ---------------------------------------------------------------------------
PERSISTENT_KINDS: FrozenSet[str] = frozenset({
    "chapter_subject_badge_swap",
    "year_card_update",
    "chapter_timeline_update",
    "structure_tree_node_fill",
    "vignette_breath",
    "paper_texture",
})


# ---------------------------------------------------------------------------
# qa_visual_alignment._PIN_KINDS — verbatim (cue kinds that own a point marker
# verified against its declared pixel). Exposed un-underscored as PIN_KINDS.
# ---------------------------------------------------------------------------
PIN_KINDS: FrozenSet[str] = frozenset({
    "pin_drop", "pin_pulse_breath", "pin_dimming", "map_sprite",
})


# ---------------------------------------------------------------------------
# qa_visual_completeness._NON_VISIBLE_KINDS — verbatim. Cue kinds that are NOT
# visible objects on the canvas (audio, camera moves, whole-frame
# transitions/atmosphere/time); exempt from the "visible cue must declare
# geometry" rule. Exposed un-underscored as NON_VISIBLE_KINDS.
# ---------------------------------------------------------------------------
NON_VISIBLE_KINDS: FrozenSet[str] = frozenset({
    # audio
    "music_swell", "music_drop", "sfx_accent", "sfx_ambient_in", "sfx_ambient_out",
    # camera (move the whole frame, not an object placed at coords)
    "camera_push_in", "camera_pull_out", "camera_pan", "camera_orbit", "camera_hold",
    # whole-frame transitions / atmosphere / time
    "basemap_swap", "chapter_wipe", "time_shift", "time_of_day", "year_sweep",
    "weather_overlay", "cloud_drift", "idle_atmosphere", "paper_texture",
    "vignette_pulse", "vignette_breath", "parallax_layers",
})


# ---------------------------------------------------------------------------
# qa_visual_contrast._TEXT_KINDS — verbatim. Cue kinds that paint on-screen words
# even when no literal text/label string is carried, so the contrast gate must
# inspect their region. Exposed as TEXT_PAINTING_KINDS.
# ---------------------------------------------------------------------------
TEXT_PAINTING_KINDS: FrozenSet[str] = frozenset({
    "map_label", "label_cluster", "time_stamp", "concept_stamp",
    "source_citation", "etymology_card", "region_label_in", "region_label_out",
    "year_card_update", "chapter_timeline_update", "year_sweep", "panel_quote",
    "concept_diagram",
})


# ---------------------------------------------------------------------------
# Self-consistency check (runs at import).
# Every member of every family / named set MUST be a real primitive in
# PRIMITIVES. A stray member is a hard AssertionError that NAMES it, so a typo or
# a drift between this module and the schema can never pass silently.
# ---------------------------------------------------------------------------
def _check_subset(name: str, members: FrozenSet[str]) -> None:
    stray = sorted(members - _PRIMITIVE_SET)
    assert not stray, (
        "vocab.{0} contains member(s) not in PRIMITIVES: {1}".format(name, stray)
    )


# PRIMITIVES itself must have no accidental duplicates (ordered tuple -> set).
assert len(PRIMITIVES) == len(_PRIMITIVE_SET), (
    "vocab.PRIMITIVES has duplicate entries: "
    + repr(sorted({p for p in PRIMITIVES if PRIMITIVES.count(p) > 1}))
)

for _fam_name, _fam_members in PRIMITIVE_FAMILIES.items():
    _check_subset("PRIMITIVE_FAMILIES[{0!r}]".format(_fam_name), _fam_members)

for _set_name in (
    "AUDIO_PRIMS", "CARD_PRIMS", "MAP_ANCHORED_PRIMS", "FULLFRAME_PRIMS",
    "UI_CORNER_PRIMS", "FACE_PRIMS", "OFF_MAP_VISUAL_PRIMS",
    "CHROME_KINDS", "EVENT_FX_KINDS", "AUDIO_KINDS", "PERSISTENT_KINDS",
    "PIN_KINDS", "NON_VISIBLE_KINDS", "TEXT_PAINTING_KINDS",
):
    _check_subset(_set_name, globals()[_set_name])

# CHARACTER_CARD_PRIMS and SCENE_ANCHOR_PRIMS are ordered tuples (their public
# shape is a tuple — a consumer slices SCENE_ANCHOR_PRIMS); wrap each in a
# frozenset for the same "every member is a real primitive" check.
_check_subset("CHARACTER_CARD_PRIMS", frozenset(CHARACTER_CARD_PRIMS))
_check_subset("SCENE_ANCHOR_PRIMS", frozenset(SCENE_ANCHOR_PRIMS))

# Every REQUIRED family must be a real family key.
for _rf in REQUIRED_FAMILIES:
    assert _rf in PRIMITIVE_FAMILIES, (
        "vocab.REQUIRED_FAMILIES names a non-existent family: {0!r}".format(_rf)
    )

# Clean up loop temporaries so they are not exported as module attributes.
del _fam_name, _fam_members, _set_name, _rf


__all__ = [
    "PRIMITIVES",
    "PRIMITIVE_FAMILIES",
    "REQUIRED_FAMILIES",
    "MIN_DISTINCT",
    "AUDIO_PRIMS",
    "CARD_PRIMS",
    "CHARACTER_CARD_PRIMS",
    "MAP_ANCHORED_PRIMS",
    "FULLFRAME_PRIMS",
    "SCENE_ANCHOR_PRIMS",
    "UI_CORNER_PRIMS",
    "FACE_PRIMS",
    "FACE_PRIMITIVES",
    "OFF_MAP_VISUAL_PRIMS",
    "CHROME_KINDS",
    "EVENT_FX_KINDS",
    "AUDIO_KINDS",
    "PERSISTENT_KINDS",
    "PIN_KINDS",
    "NON_VISIBLE_KINDS",
    "TEXT_PAINTING_KINDS",
]
