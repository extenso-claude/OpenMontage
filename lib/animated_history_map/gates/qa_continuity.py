"""qa_continuity — the map must not jump or lose a pin between chapters.

Catches the documented "the map jumped / a pin vanished between shots" bug.

Per the storyboard schema and the Storyboard Director skill, every chapter
storyboard (`artifacts/storyboard/storyboard_<chapter_id>.json`) declares a
cross-phase continuity contract as two top-level `phase_state` objects:

    incoming_state   — the state this chapter inherits from the prior chapter
    outgoing_state   — the state this chapter hands to the next chapter

(The schema's `phase_state` is required at `outgoing_state`; the per-phase
objects under `phases[]` carry only beats, not the continuity contract — so the
contract is evaluated at chapter boundaries, which is exactly where the camera
cuts and where a pin would visibly disappear.)

Rule (locked, per storyboard-director.md §3):
    Order chapters by `chapter_index` (chapter_id as tiebreaker). For each
    adjacent pair, the earlier chapter's `outgoing_state` MUST equal the next
    chapter's `incoming_state`, field by field, across the continuity fields:

        basemap_tier, active_pins, dimmed_pins, year_display,
        weather, time_of_day, active_ui_furniture, chapter_subject_id

    Any mismatch is a FAIL naming the field + the two chapters. A pin/furniture
    set is compared as an unordered set (draw order is not a continuity break);
    everything else is compared by value. A missing `outgoing_state` (on any but
    the last chapter) or `incoming_state` (on any but the first) is a FAIL —
    there is then nothing to hand off and the seam cannot be verified.

A single chapter cannot break continuity with itself, so a project with one
storyboard trivially passes (no adjacent pairs).

Reads:  <project>/artifacts/storyboard/*.json
Shape (per file, only the fields this gate reads):
    {"chapter_id","chapter_index"?,
     "incoming_state": <phase_state>, "outgoing_state": <phase_state>, ...}
    phase_state = {"basemap_tier","active_pins","year_display",
                   "dimmed_pins"?,"weather"?,"time_of_day"?,
                   "active_ui_furniture"?,"chapter_subject_id"?}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any, List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# Continuity fields and whether each is order-insensitive (set-compared).
# Source of truth: storyboard schema `phase_state` + storyboard-director.md §3.
SET_FIELDS = ("active_pins", "dimmed_pins", "active_ui_furniture")
SCALAR_FIELDS = (
    "basemap_tier",
    "year_display",
    "weather",
    "time_of_day",
    "chapter_subject_id",
)
CONTINUITY_FIELDS = SET_FIELDS + SCALAR_FIELDS


def _load_chapters(project_dir: Path) -> List[Tuple[str, dict]]:
    """Return [(source_name, storyboard_dict), ...]. Raises if none readable."""
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        raise GateInputError(
            "required input not found: " + str(sb_dir) + " (no storyboard directory)"
        )
    paths = sorted(sb_dir.glob("*.json"))
    if not paths:
        raise GateInputError(
            "no storyboard files in " + str(sb_dir) + " (expected one *.json per chapter)"
        )
    chapters: List[Tuple[str, dict]] = []
    for p in paths:
        data = load_json(p)  # GateInputError on unreadable/invalid JSON
        if not isinstance(data, dict):
            raise GateInputError(str(p) + ": storyboard root is not an object")
        chapters.append((p.name, data))
    return chapters


def _sort_key(item: Tuple[str, dict]) -> Tuple[int, int, str]:
    """Order by chapter_index, then chapter_id, then filename.

    Files without a numeric chapter_index sort last (they fall back to filename
    order) so a malformed/missing index can never silently reorder the timeline
    ahead of properly-indexed chapters.
    """
    name, data = item
    idx = data.get("chapter_index")
    if isinstance(idx, bool) or not isinstance(idx, int):
        return (1, 0, str(data.get("chapter_id") or name))
    return (0, idx, str(data.get("chapter_id") or name))


def _chapter_label(name: str, data: dict) -> str:
    cid = data.get("chapter_id")
    return str(cid) if isinstance(cid, str) and cid.strip() else name


def _normalize(field: str, value: Any) -> Any:
    """A comparable view of one continuity field's value.

    Set fields collapse to a frozenset (order-insensitive). Missing list fields
    normalize to the empty set so an absent `dimmed_pins` equals an explicit []."""
    if field in SET_FIELDS:
        if value is None:
            return frozenset()
        if isinstance(value, list):
            return frozenset(str(v) for v in value)
        # Wrong type — keep it distinct so a malformed shape surfaces as a mismatch.
        return ("__nonlist__", repr(value))
    return value


def _describe(field: str, value: Any) -> str:
    if field in SET_FIELDS:
        if value is None:
            return "[]"
        if isinstance(value, list):
            return "[" + ", ".join(sorted(str(v) for v in value)) + "]"
    return repr(value)


def _state_of(data: dict, key: str) -> Optional[dict]:
    st = data.get(key)
    return st if isinstance(st, dict) else None


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    chapters = _load_chapters(project_dir)
    chapters.sort(key=_sort_key)

    findings: List[Finding] = []

    # Ambiguous ordering makes "next chapter" meaningless — block it.
    seen_index: dict = {}
    for name, data in chapters:
        idx = data.get("chapter_index")
        if isinstance(idx, int) and not isinstance(idx, bool):
            if idx in seen_index:
                findings.append(Finding(
                    "fail", "duplicate_chapter_index",
                    "two storyboards share chapter_index {} ({} and {}); "
                    "chapter order is ambiguous and continuity cannot be verified".format(
                        idx, seen_index[idx], name),
                    where=name,
                ))
            else:
                seen_index[idx] = name

    # Walk adjacent chapter boundaries: prev.outgoing_state must equal next.incoming_state.
    for i in range(len(chapters) - 1):
        prev_name, prev = chapters[i]
        next_name, nxt = chapters[i + 1]
        prev_label = _chapter_label(prev_name, prev)
        next_label = _chapter_label(next_name, nxt)
        seam = prev_label + " -> " + next_label

        out_state = _state_of(prev, "outgoing_state")
        in_state = _state_of(nxt, "incoming_state")

        if out_state is None:
            findings.append(Finding(
                "fail", "missing_outgoing_state",
                "chapter {} has no outgoing_state to hand to {}; "
                "the seam cannot be verified".format(prev_label, next_label),
                where=seam,
            ))
        if in_state is None:
            findings.append(Finding(
                "fail", "missing_incoming_state",
                "chapter {} has no incoming_state to receive {}'s handoff; "
                "the seam cannot be verified".format(next_label, prev_label),
                where=seam,
            ))
        if out_state is None or in_state is None:
            continue

        for field in CONTINUITY_FIELDS:
            out_norm = _normalize(field, out_state.get(field))
            in_norm = _normalize(field, in_state.get(field))
            if out_norm != in_norm:
                findings.append(Finding(
                    "fail", "continuity_break",
                    "{} discontinuous across chapter seam: {} outgoing={} but "
                    "{} incoming={} (the map/pin/year state visibly jumps)".format(
                        field, prev_label, _describe(field, out_state.get(field)),
                        next_label, _describe(field, in_state.get(field))),
                    where=seam + " :: " + field,
                ))

    return findings


if __name__ == "__main__":
    run_cli("qa_continuity", check)
