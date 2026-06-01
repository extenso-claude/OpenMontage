"""qa_spatial_anchor — the action-location contract. Every visible action cue
lands on a resolvable place.

The MM synchrony model splits a cue's TIME (qa_cue_drift / qa_audio_drift anchor
it to a narrated word) from its PLACE (this gate). A flash_burst, a glow_region,
a connection_line that fires at the right instant but has no WHERE drifts to the
frame's top-left (or wherever the compiler defaults) and stamps an event over
empty parchment — visually unmotivated, off the thing it is reacting to. The
companion gate qa_visual_alignment proves a DECLARED pixel rendered where it was
declared; this gate proves a visible action cue DECLARED a pixel-resolvable
target at all (and that the target actually resolves to a pixel/region). It is
the upstream half: no unplaced action cue can reach the renderer, so
qa_visual_alignment always has a pixel to verify.

Scope: every VISIBLE cue in cuelist.json. A cue is "chrome" (action-independent
UI — year card, subject badge, citation, time stamp) and EXEMPT when
placement == "chrome" OR its kind is a known chrome kind. Everything else is an
"action cue" and MUST carry a resolvable spatial_target.

A spatial_target resolves when it declares EXACTLY ONE of:
    * anchor_id  — an id present in positions.json anchors (a map/geo pixel);
    * region_id  — a region_id present in some chapter's setting.scene_anchors
                   (a named on-screen region/actor for an off-map 2D/3D scene);
    * target_px  — an authored [x,y] (or [x,y,w,h]) pixel INSIDE 1920x1080.
Zero keys, two-or-more keys, or a declared key that does not resolve (unknown
anchor_id / unknown region_id / off-canvas or malformed target_px) is an
unresolved target.

The ~19 event-FX kinds (flash_burst, bullet_trail, gunshot_freeze, glow_region,
connection_line, dust_settle, slow_zoom_terror, clock_freeze, concept_stamp, …)
are NOT chrome — they react to a place and so MUST carry a spatial_target. A
flash_burst with no spatial_target and placement on_action is the canonical bug.

Rules (severity "fail"):
    * cue_unplaced     — a visible, non-chrome cue has no spatial_target and is
                         not placement:"chrome". (Includes an event-FX cue that
                         forgot its target.)
    * unresolved_target— a declared spatial_target cannot resolve to a pixel/
                         region: not exactly one of anchor_id/region_id/target_px,
                         an unknown anchor_id, an unknown region_id, or a
                         target_px that is malformed / outside 1920x1080.

A gate that cannot run must never silently pass:
    * no cuelist.json / unreadable / no 'cues' array      -> GateInputError (blocks)
    * a present-but-unreadable positions.json / storyboard -> GateInputError (blocks)
    (positions.json and the storyboard directory are OPTIONAL inputs — their
     ABSENCE is not a failure, but if a cue then references an anchor_id /
     region_id there is nothing to resolve against, so the cue fails as
     unresolved_target. Missing context never silently passes an unplaced cue.)

Reads:
    <project>/artifacts/cuelist.json            (REQUIRED)
    <project>/artifacts/positions.json          (optional — anchor_id resolution)
    <project>/artifacts/storyboard/*.json        (optional — region_id resolution)
Shapes (only the fields this gate reads):
    cuelist    = {"cues": [{"id","kind","layer"?,"start_s"?,"end_s"?,
                            "placement"?:"on_action"|"chrome",
                            "spatial_target"?:{"anchor_id"?|"region_id"?|"target_px"?},
                            ...}, ...]}
    positions  = {"anchors": [{"id", ...}, ...]}
    storyboard = {"chapter_id"?, "setting": {"scene_anchors": [{"region_id"}, ...]}}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Set, Tuple

from .. import vocab
from ._contract import Finding, GateInputError, load_json, run_cli

# Authored-pixel canvas. A target_px must fall inside this frame; a coordinate
# outside it is the literal "placed off-canvas" symptom.
FRAME_W = 1920
FRAME_H = 1080

# Action-independent UI that legitimately ignores the narrated thing. These own
# their own fixed screen real-estate (a corner badge, a citation strip) and so
# are EXEMPT from needing a spatial_target. A cue may also opt in to this
# exemption explicitly via placement:"chrome" regardless of kind.
# Canonical vocabulary — see lib/midnight_magnates/vocab.py.
CHROME_KINDS = vocab.CHROME_KINDS

# Event-FX kinds: they REACT to a place on the frame, so they MUST carry a
# spatial_target (a flash over empty parchment is the bug). Listed for the
# message + a belt-and-suspenders presence check; the general rule already
# requires a target for every non-chrome cue, but naming these makes the FX
# contract explicit and the failure message precise.
EVENT_FX_KINDS = vocab.EVENT_FX_KINDS

# Sound primitives (from the storyboard schema) — these never occupy a pixel,
# so they are out of scope for a WHERE check. (vocab exports this un-underscored
# as AUDIO_KINDS; the local alias keeps the rest of this module unchanged.)
_AUDIO_KINDS = vocab.AUDIO_KINDS


def _is_number(v) -> bool:
    # bool is an int subclass; True/False is not a real coordinate.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _load_anchor_ids(project_dir: Path) -> Set[str]:
    """Set of anchor ids from positions.json (for anchor_id resolution).

    ABSENCE is allowed (returns an empty set) — not every MM project paints a
    map. A present-but-unreadable file is a BLOCKING fail (load_json raises),
    because a gate that cannot read a declared input must not silently pass.
    """
    path = project_dir / "artifacts" / "positions.json"
    if not path.exists():
        return set()
    data = load_json(path)  # present-but-unreadable -> GateInputError (blocks)
    anchors = data.get("anchors")
    if not isinstance(anchors, list):
        raise GateInputError(
            "positions.json present but has no 'anchors' array (cannot resolve "
            "anchor_id targets)"
        )
    ids: Set[str] = set()
    for a in anchors:
        if isinstance(a, dict):
            aid = a.get("id")
            if isinstance(aid, str) and aid.strip():
                ids.add(aid)
    return ids


def _load_region_ids(project_dir: Path) -> Set[str]:
    """Union of setting.scene_anchors[].region_id across every chapter storyboard
    (for region_id resolution).

    The storyboard directory is OPTIONAL here (returns an empty set if absent) —
    a project may be all-map. A present storyboard *.json that cannot be read is
    a BLOCKING fail; a readable one whose root is not an object is too (the
    contract: a malformed declared input never silently passes).
    """
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        return set()
    regions: Set[str] = set()
    for p in sorted(sb_dir.glob("*.json")):
        data = load_json(p)  # present-but-unreadable -> GateInputError (blocks)
        if not isinstance(data, dict):
            raise GateInputError(
                str(p) + ": storyboard root is not an object (cannot index "
                "setting.scene_anchors for region_id resolution)"
            )
        setting = data.get("setting")
        if not isinstance(setting, dict):
            continue
        scene_anchors = setting.get("scene_anchors")
        if not isinstance(scene_anchors, list):
            continue
        for sa in scene_anchors:
            if isinstance(sa, dict):
                rid = sa.get("region_id")
                if isinstance(rid, str) and rid.strip():
                    regions.add(rid)
    return regions


def _target_px_ok(value) -> bool:
    """True iff value is [x,y] or [x,y,w,h] with x,y numeric and INSIDE the frame.

    Only x,y (the placement point) are bounds-checked; an optional w,h merely
    has to be numeric. A non-list, a too-short list, non-numeric coords, or an
    x/y outside 1920x1080 all make the target unresolvable.
    """
    if not isinstance(value, (list, tuple)) or len(value) < 2 or len(value) > 4:
        return False
    x, y = value[0], value[1]
    if not _is_number(x) or not _is_number(y):
        return False
    if len(value) > 2 and not all(_is_number(v) for v in value[2:]):
        return False
    return 0 <= float(x) <= FRAME_W and 0 <= float(y) <= FRAME_H


def _resolve_target(
    target: dict, anchor_ids: Set[str], region_ids: Set[str]
) -> Tuple[bool, str]:
    """Return (resolved, reason). resolved=True means exactly one of
    anchor_id / region_id / target_px is present AND it resolves to a
    pixel/region. Otherwise (False, human-readable reason)."""
    present = [
        k for k in ("anchor_id", "region_id", "target_px")
        if target.get(k) is not None
    ]
    if len(present) == 0:
        return False, (
            "spatial_target declares none of anchor_id / region_id / target_px"
        )
    if len(present) > 1:
        return False, (
            "spatial_target declares more than one of anchor_id/region_id/"
            "target_px ({0}) — provide exactly one".format(", ".join(present))
        )

    key = present[0]
    val = target.get(key)
    if key == "anchor_id":
        if not isinstance(val, str) or not val.strip():
            return False, "anchor_id must be a non-empty string"
        if val not in anchor_ids:
            return False, (
                "anchor_id {0!r} is not in positions.json anchors — it does not "
                "resolve to a map pixel".format(val)
            )
        return True, ""
    if key == "region_id":
        if not isinstance(val, str) or not val.strip():
            return False, "region_id must be a non-empty string"
        if val not in region_ids:
            return False, (
                "region_id {0!r} is not in any chapter setting.scene_anchors — "
                "it does not resolve to a named on-screen region".format(val)
            )
        return True, ""
    # target_px
    if not _target_px_ok(val):
        return False, (
            "target_px {0!r} is not an [x,y]/[x,y,w,h] pixel inside "
            "{1}x{2}".format(val, FRAME_W, FRAME_H)
        )
    return True, ""


def _is_visible(cue: dict) -> bool:
    """A cue is a visible VISUAL cue (vs an audio-only cue) for this gate.

    Audio cues carry no on-screen position to anchor, so they are out of scope.
    We treat a cue as audio-only when it is explicitly flagged is_audio:true or
    its kind is a known sound primitive. Everything else is on-screen.
    """
    if cue.get("is_audio") is True:
        return False
    kind = cue.get("kind")
    if isinstance(kind, str) and kind in _AUDIO_KINDS:
        return False
    return True


def _has_top_level_placement(cue: dict, anchor_ids: Set[str]) -> bool:
    """True if the cue carries a resolvable PLACEMENT the compiler stamps at the TOP
    LEVEL (not inside a spatial_target dict).

    The compiler places map-anchored cues (pin_drop / pin_pulse_breath / pin_dimming /
    map_sprite / map_label / migration_arrow / all_presidents_pins) via a top-level
    anchor_id resolved to anchor_px/anchor_py, a route polyline (path_px), or a resolved
    pin roster (pins_px) — NOT a spatial_target dict. Those cues ARE placed; recognizing
    the compiler's real placement contract stops the gate false-failing every pin /
    label / arrow / roster as cue_unplaced (it flagged 44 cues on the reference project).
    """
    apx, apy = cue.get("anchor_px"), cue.get("anchor_py")
    if (_is_number(apx) and _is_number(apy)
            and 0 <= float(apx) <= FRAME_W and 0 <= float(apy) <= FRAME_H):
        return True
    aid = cue.get("anchor_id")
    if isinstance(aid, str) and aid.strip() and aid in anchor_ids:
        return True
    path_px = cue.get("path_px")
    if isinstance(path_px, list) and len(path_px) >= 1:
        return True
    pins_px = cue.get("pins_px")
    if isinstance(pins_px, list) and len(pins_px) >= 1:
        return True
    return False


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    anchor_ids = _load_anchor_ids(project_dir)
    region_ids = _load_region_ids(project_dir)

    findings: List[Finding] = []
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            findings.append(Finding(
                "fail", "malformed_cue", "cue is not an object",
                where="cue[{0}]".format(i)))
            continue

        cid = str(cue.get("id") or "cue[{0}]".format(i))
        kind = cue.get("kind")
        kind_str = kind if isinstance(kind, str) else ""

        # Audio-only cues have no on-screen position to anchor — out of scope.
        if not _is_visible(cue):
            continue

        placement = cue.get("placement")
        placement_str = placement if isinstance(placement, str) else ""

        # Chrome is exempt: action-independent UI by placement OR by known kind.
        if placement_str == "chrome" or kind_str in CHROME_KINDS:
            continue

        target = cue.get("spatial_target")

        # A declared spatial_target must resolve to a pixel/region.
        if isinstance(target, dict):
            resolved, reason = _resolve_target(target, anchor_ids, region_ids)
            if not resolved:
                findings.append(Finding(
                    "fail", "unresolved_target",
                    "spatial_target does not resolve: {0}".format(reason),
                    where=cid))
            continue

        # No spatial_target dict — but the compiler places map-anchored cues
        # (pins / labels / arrows / rosters) via TOP-LEVEL anchor_id -> anchor_px/py,
        # path_px, or pins_px. Accept that as a resolved placement.
        if _has_top_level_placement(cue, anchor_ids):
            continue

        # A top-level anchor_id that does NOT resolve is an unresolved target.
        aid = cue.get("anchor_id")
        if isinstance(aid, str) and aid.strip():
            findings.append(Finding(
                "fail", "unresolved_target",
                "top-level anchor_id {0!r} is not in positions.json anchors — it does "
                "not resolve to a map pixel".format(aid),
                where=cid))
            continue

        # Nothing places it. Event-FX kinds get a sharper message.
        if kind_str in EVENT_FX_KINDS:
            findings.append(Finding(
                "fail", "cue_unplaced",
                "event-FX cue {0!r} has no spatial_target and is not "
                "placement:\"chrome\" — it would fire over empty frame "
                "(must declare anchor_id / region_id / target_px)".format(
                    kind_str or "?"),
                where=cid))
        else:
            findings.append(Finding(
                "fail", "cue_unplaced",
                "visible action cue (kind={0!r}, placement={1!r}) has no resolvable "
                "placement (no spatial_target, no top-level anchor_id/anchor_px, no "
                "path_px/pins_px) — nothing tells the renderer WHERE it lands".format(
                    kind_str or "?", placement_str or "on_action"),
                where=cid))

    return findings


if __name__ == "__main__":
    run_cli("qa_spatial_anchor", check)
