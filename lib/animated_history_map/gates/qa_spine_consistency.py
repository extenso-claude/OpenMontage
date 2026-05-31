"""qa_spine_consistency — the recurring all-presidents spine map (A12).

The series' spine is a single recurring map ("the next pin on this map has not
been drawn yet"): at each chapter close the camera returns to a map of ALL the
presidents' pins, with the chapter's own subject IN COLOR and every other pin
DIMMED. The documented failure is two-fold:
  (a) a chapter closes on a bespoke one-off map instead of the shared spine map,
      so the recurring callback never lands; and
  (b) the spine map's pin roster / pin POSITIONS drift between chapters — a pin
      appears in one chapter and vanishes in the next, or the same president sits
      at a different spot — so the "same map, one more pin" illusion breaks.

This gate enforces the `all_presidents_pins` primitive as that shared spine:

  1. CLOSE PLACEMENT (fail). Every chapter that HAS a close phase
     (phase_kind in CLOSE_PHASES) MUST carry an `all_presidents_pins` layer in
     that close phase. A close phase with no spine map is a FAIL.

  2. WELL-FORMED (fail). Each `all_presidents_pins` usage must declare a non-empty
     `params.pins` roster where every pin has an `id` and a resolvable POSITION
     (an `anchor_id`, OR numeric `lat` + `lon`), plus a `params.current` pin id
     that is a member of the roster (the one shown in color). Anything missing is
     a FAIL — a spine map you can't place or can't color is not a spine map.

  3. CROSS-CHAPTER CONSISTENCY (fail). Across every `all_presidents_pins` usage in
     the project, the pin-id SET must be identical and each pin's POSITION must be
     identical (same anchor_id, or same lat/lon). A roster that adds/drops a pin
     or moves a pin between chapters is a FAIL.

Reads:  <project>/artifacts/storyboard/*.json
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

PRIMITIVE = "all_presidents_pins"

# Phases that constitute a "chapter close" — where the spine map must appear.
CLOSE_PHASES = frozenset({"return_to_map", "chapter_outro"})


def _storyboards(project_dir: Path) -> List[Tuple[str, dict]]:
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        raise GateInputError("required input not found: " + str(sb_dir) + " (no storyboard directory)")
    paths = sorted(sb_dir.glob("*.json"))
    if not paths:
        raise GateInputError("no storyboard files in " + str(sb_dir) + " (expected one *.json per chapter)")
    out: List[Tuple[str, dict]] = []
    for p in paths:
        data = load_json(p)
        if not isinstance(data, dict):
            raise GateInputError(str(p) + ": storyboard root is not an object")
        out.append((p.name, data))
    return out


def _position_of(pin: dict) -> Optional[Tuple]:
    """A comparable, hashable position key for a pin, or None if unresolvable.

    Prefer an anchor_id (geography resolves it to lat/lon); else accept inline
    numeric lat+lon. Returned as a tuple so it can be set-compared across chapters.
    """
    aid = pin.get("anchor_id")
    if isinstance(aid, str) and aid.strip():
        return ("anchor", aid.strip())
    lat, lon = pin.get("lat"), pin.get("lon")
    if (isinstance(lat, (int, float)) and not isinstance(lat, bool)
            and isinstance(lon, (int, float)) and not isinstance(lon, bool)):
        return ("latlon", round(float(lat), 6), round(float(lon), 6))
    return None


def _describe_pos(pos: Optional[Tuple]) -> str:
    if pos is None:
        return "<unresolved>"
    if pos[0] == "anchor":
        return "anchor:{0}".format(pos[1])
    return "latlon:{0},{1}".format(pos[1], pos[2])


def _validate_roster(la: dict, where: str, findings: List[Finding]) -> Dict[str, Tuple]:
    """Validate one all_presidents_pins layer's roster. Returns {pin_id: position}
    for the cross-chapter pass (only well-formed pins are included)."""
    params = la.get("params") or {}
    pins = params.get("pins")
    roster: Dict[str, Tuple] = {}
    if not isinstance(pins, list) or not pins:
        findings.append(Finding(
            "fail", "spine_roster_empty",
            "all_presidents_pins declares no params.pins roster — the recurring "
            "all-presidents map has nothing to draw",
            where=where,
        ))
        return roster

    for pi, pin in enumerate(pins):
        if not isinstance(pin, dict):
            findings.append(Finding(
                "fail", "spine_pin_malformed",
                "pins[{0}] is not an object".format(pi), where=where))
            continue
        pid = pin.get("id")
        if not (isinstance(pid, str) and pid.strip()):
            findings.append(Finding(
                "fail", "spine_pin_no_id",
                "pins[{0}] has no string 'id'".format(pi), where=where))
            continue
        pid = pid.strip()
        pos = _position_of(pin)
        if pos is None:
            findings.append(Finding(
                "fail", "spine_pin_no_position",
                "pin {0!r} has no resolvable position (needs an anchor_id or numeric "
                "lat+lon) — it cannot be placed on the map".format(pid),
                where=where))
            continue
        if pid in roster and roster[pid] != pos:
            findings.append(Finding(
                "fail", "spine_pin_duplicate_conflict",
                "pin {0!r} appears twice in the same roster with different positions "
                "({1} vs {2})".format(pid, _describe_pos(roster[pid]), _describe_pos(pos)),
                where=where))
        roster[pid] = pos

    current = params.get("current")
    if not (isinstance(current, str) and current.strip()):
        findings.append(Finding(
            "fail", "spine_no_current",
            "all_presidents_pins has no params.current — no pin is marked as the "
            "in-color (active) president; the rest cannot be dimmed against it",
            where=where))
    elif current.strip() not in roster:
        findings.append(Finding(
            "fail", "spine_current_not_in_roster",
            "params.current={0!r} is not a pin id in the roster {1}".format(
                current.strip(), sorted(roster)),
            where=where))
    return roster


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    storyboards = _storyboards(project_dir)
    findings: List[Finding] = []

    # (chapter_label, position-map) for every well-formed spine usage, for the
    # cross-chapter consistency pass.
    rosters: List[Tuple[str, Dict[str, Tuple]]] = []

    for name, sb in storyboards:
        cid = str(sb.get("chapter_id") or name)
        phases = sb.get("phases")
        if not isinstance(phases, list):
            continue
        for ph in phases:
            if not isinstance(ph, dict):
                continue
            phase_kind = ph.get("phase_kind")
            phase_id = str(ph.get("phase_id") or phase_kind or "phase")
            beats = ph.get("beats")
            beats = beats if isinstance(beats, list) else []

            spine_layers: List[Tuple[str, dict]] = []
            for beat in beats:
                if not isinstance(beat, dict):
                    continue
                bid = str(beat.get("beat_id") or "beat")
                layers = beat.get("layers")
                if not isinstance(layers, list):
                    continue
                for la in layers:
                    if isinstance(la, dict) and la.get("primitive") == PRIMITIVE:
                        spine_layers.append((bid, la))

            # 1) A close phase must carry the spine map.
            if phase_kind in CLOSE_PHASES and not spine_layers:
                findings.append(Finding(
                    "fail", "close_missing_spine_map",
                    "chapter-close phase (phase_kind={0!r}) has no all_presidents_pins "
                    "beat — the chapter must return to the recurring all-presidents "
                    "spine map (subject in color, others dimmed)".format(phase_kind),
                    where="{0} :: {1}".format(cid, phase_id)))

            # 2) Validate every spine usage found in this phase.
            for bid, la in spine_layers:
                where = "{0} :: {1} :: {2}".format(cid, phase_id, bid)
                roster = _validate_roster(la, where, findings)
                if roster:
                    rosters.append((cid + " :: " + bid, roster))

    # 3) Cross-chapter consistency: same pin-id set, same positions everywhere.
    if len(rosters) >= 2:
        ref_label, ref = rosters[0]
        ref_ids = set(ref)
        for label, roster in rosters[1:]:
            ids = set(roster)
            missing = ref_ids - ids
            extra = ids - ref_ids
            if missing or extra:
                findings.append(Finding(
                    "fail", "spine_roster_drift",
                    "all-presidents pin roster differs from {0}: missing {1}, extra {2} "
                    "(the recurring spine map must carry the SAME president pin set in "
                    "every chapter)".format(ref_label, sorted(missing) or "none", sorted(extra) or "none"),
                    where=label))
            for pid in sorted(ref_ids & ids):
                if ref[pid] != roster[pid]:
                    findings.append(Finding(
                        "fail", "spine_position_drift",
                        "pin {0!r} moved between chapters: {1} in {2} but {3} here "
                        "(a president's pin must sit at the same position in every "
                        "chapter)".format(pid, _describe_pos(ref[pid]), ref_label, _describe_pos(roster[pid])),
                        where=label))

    return findings


if __name__ == "__main__":
    run_cli("qa_spine_consistency", check)
