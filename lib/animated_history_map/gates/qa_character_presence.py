"""qa_character_presence — a named figure must be PRESENT, not a postage stamp.

The bug (A4): every character beat compiled to the same tiny lower-left card on
empty parchment (the compiler's SLOT_LOWER_LEFT is 560x280 ~= 26% of frame
height). A 26%-tall portrait floating on a blank page does not put the figure in
the story. The cut-out treatment the channel was supposed to use — background
removed, white-gray border, placed LARGE on the live scene — was never wired in.

This gate enforces the character-treatment system
(lib.animated_history_map.character_treatment). A character beat (a cue whose
kind is character_card / character_card_pop) must resolve to ONE of:

  HERO_CUTOUT       a bordered cut-out standing ON the scene: bbox height
                    >= 30% of the frame (>= 324px on 1080) AND backed by a real
                    sprite (asset_id). A tall lone TEXT card with no art does not
                    count as a cutout.
  FULL_SCREEN_CARD  a near-full-frame card (>= 85% W and >= 85% H), carried by a
                    camera move.
  LOWER_CORNER      a small lower card is allowed ONLY when it is scene-anchored:
                    a full-frame scene primitive (panel_archival /
                    panel_illustration / story_dive / clip_archival /
                    document_overlay / parallax_layers / map_sprite) OR a map
                    basemap is live in the SAME time window, so the card sits
                    over real content — not empty background.

A character beat that is a small lone card with nothing under it FAILS
(small_lone_character_card). An explicit, mismatched treatment declaration also
FAILS (e.g. treatment=hero_cutout but the bbox is only 26% tall).

A cue may declare its treatment explicitly via cue["treatment"] or
cue["params"]["treatment"] (one of hero_cutout / full_screen_card /
lower_corner); otherwise the gate infers it from geometry + scene-window overlap.

Map basemap: if the project has a positions.json / geography.json with a
map_info.extent_id (the compiler grounds chapters on a rendered basemap), the
whole timeline is considered to have a live map under it, so a lower-corner
name-tag over the map is scene-anchored. Projects with no basemap get no such
credit — a lone card on parchment must earn a HERO_CUTOUT / FULL_SCREEN / panel.

This gate PASSES a project with zero character beats (nothing to check).

Reads:  <project>/artifacts/cuelist.json   (required)
        <project>/artifacts/positions.json (optional, for basemap detection)
        <project>/artifacts/geography.json (optional, fallback basemap detection)
Shape:  {"cues": [{"id","kind","start_s","end_s","bbox"?,"asset_id"?,
                   "treatment"?, "params"?:{"treatment"?}, ...}, ...]}
"""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli
from ..character_treatment import (
    CHARACTER_PRIMITIVES,
    SCENE_ANCHOR_PRIMITIVES,
    CAMERA_PRIMITIVES,
    HERO_CUTOUT,
    FULL_SCREEN_CARD,
    LOWER_CORNER,
    TREATMENTS,
    HERO_MIN_H,
    HERO_MIN_FRAME_HEIGHT_FRAC,
    FULLSCREEN_MIN_W,
    FULLSCREEN_MIN_H,
    is_hero_height,
    is_full_screen,
)


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def _num(value) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _kind(cue: dict) -> str:
    v = cue.get("kind")
    return v.strip() if isinstance(v, str) else ""


def _window(cue: dict) -> Optional[Tuple[float, float]]:
    """(start_s, end_s) for a cue, or None if either is missing/garbage."""
    s = _num(cue.get("start_s"))
    e = _num(cue.get("end_s"))
    if s is None or e is None:
        return None
    return (s, e)


def _overlaps(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
    """True if two [start,end] windows share any time (touching edges don't)."""
    return a[0] < b[1] and b[0] < a[1]


def _declared_treatment(cue: dict) -> Optional[str]:
    """Explicit treatment from cue['treatment'] or cue['params']['treatment']."""
    for src in (cue.get("treatment"),
                (cue.get("params") or {}).get("treatment")
                if isinstance(cue.get("params"), dict) else None):
        if isinstance(src, str) and src.strip():
            return src.strip().lower()
    return None


def _project_has_basemap(project_dir: Path) -> bool:
    """True if a rendered map basemap underlies the timeline.

    The compiler grounds a chapter on assets/maps/<extent>.png when
    positions.json (or geography.json) carries map_info.extent_id. When a basemap
    is live for the whole scene, a small lower-corner name-tag is composited over
    real content (the map), so it is scene-anchored.
    """
    for name in ("positions.json", "geography.json"):
        p = project_dir / "artifacts" / name
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        info = data.get("map_info")
        if isinstance(info, dict) and str(info.get("extent_id") or "").strip():
            return True
    return False


# --------------------------------------------------------------------------- #
# per-beat verdict
# --------------------------------------------------------------------------- #
def _scene_anchor_in_window(beat_win: Tuple[float, float], cues: List[dict],
                            self_id) -> Optional[str]:
    """Return the kind of the first full-frame scene primitive whose window
    overlaps this beat (so a lower card sits over real content), else None."""
    for c in cues:
        if c.get("id") == self_id:
            continue
        if _kind(c) not in SCENE_ANCHOR_PRIMITIVES:
            continue
        w = _window(c)
        if w is not None and _overlaps(beat_win, w):
            return _kind(c)
    return None


def _camera_in_window(beat_win: Tuple[float, float], cues: List[dict]) -> bool:
    for c in cues:
        if _kind(c) in CAMERA_PRIMITIVES:
            w = _window(c)
            if w is not None and _overlaps(beat_win, w):
                return True
    return False


def _check_beat(cue: dict, cues: List[dict], has_basemap: bool) -> Optional[Finding]:
    """Return a fail Finding if this character beat is a postage-stamp, else None."""
    cid = cue.get("id", "<character beat>")
    bbox = cue.get("bbox") if isinstance(cue.get("bbox"), dict) else None
    has_asset = isinstance(cue.get("asset_id"), str) and cue["asset_id"].strip()
    declared = _declared_treatment(cue)
    win = _window(cue)

    hero_geom = is_hero_height(bbox)
    full_geom = is_full_screen(bbox)
    h = (bbox or {}).get("h")
    h_str = "{:.0f}px".format(float(h)) if isinstance(h, (int, float)) and not isinstance(h, bool) else "unknown"

    # 1) Explicit declaration must be honored by the geometry/assets.
    if declared is not None:
        if declared not in TREATMENTS:
            return Finding(
                "fail", "unknown_treatment",
                "character beat declares treatment={0!r}, not one of {1}."
                .format(declared, list(TREATMENTS)),
                where=str(cid),
            )
        if declared == HERO_CUTOUT:
            if not hero_geom:
                return Finding(
                    "fail", "hero_cutout_too_small",
                    "declares HERO_CUTOUT but its bbox is only {0} tall "
                    "(< {1}px / {2:.0%} of frame) — a hero cutout must stand "
                    "LARGE on the scene.".format(h_str, HERO_MIN_H, HERO_MIN_FRAME_HEIGHT_FRAC),
                    where=str(cid),
                )
            if not has_asset:
                return Finding(
                    "fail", "hero_cutout_no_sprite",
                    "declares HERO_CUTOUT but carries no asset_id — a cutout is a "
                    "bordered transparent sprite (resolve via "
                    "character_treatment.resolve_hero_cutout), not a bare text card.",
                    where=str(cid),
                )
            return None  # valid hero cutout
        if declared == FULL_SCREEN_CARD:
            if not full_geom:
                return Finding(
                    "fail", "full_screen_too_small",
                    "declares FULL_SCREEN_CARD but its bbox does not fill the "
                    "frame (need >= {0}x{1}px).".format(FULLSCREEN_MIN_W, FULLSCREEN_MIN_H),
                    where=str(cid),
                )
            return None  # valid full-screen card
        # declared == LOWER_CORNER: fall through to the scene-anchor requirement.

    # 2) Inferred HERO_CUTOUT: tall bordered sprite on the scene.
    if hero_geom and has_asset:
        return None
    # A tall card with NO sprite is just an oversized text card, not a cutout.
    if hero_geom and not has_asset:
        return Finding(
            "fail", "tall_card_no_sprite",
            "character beat is {0} tall but carries no asset_id — a tall TEXT "
            "card is not a HERO_CUTOUT. Either attach a bordered cutout sprite "
            "(asset_id) or use a real scene/panel under it.".format(h_str),
            where=str(cid),
        )

    # 3) Inferred FULL_SCREEN_CARD.
    if full_geom:
        return None  # camera move is recommended but a full-frame portrait reads on its own

    # 4) LOWER_CORNER must be scene-anchored: real content under it.
    if win is None:
        # No window -> cannot prove scene-anchoring; treat as a lone card.
        return Finding(
            "fail", "small_lone_character_card",
            "small character card ({0} tall) has no start_s/end_s, so it cannot "
            "be shown to sit over any scene — it reads as a lone card on an empty "
            "background. Make it a HERO_CUTOUT (>= {1}px), full-screen, or anchor "
            "it over a panel/map.".format(h_str, HERO_MIN_H),
            where=str(cid),
        )
    anchor_kind = _scene_anchor_in_window(win, cues, cue.get("id"))
    if anchor_kind is not None:
        return None  # composited over a real scene panel/illustration/dive/clip/map_sprite
    if has_basemap:
        return None  # a live map basemap underlies the whole timeline

    # Nothing under it: the bug.
    return Finding(
        "fail", "small_lone_character_card",
        "small character card ({0} tall) sits on an EMPTY background — no "
        "full-frame scene primitive ({1}) overlaps {2}, and the project has no "
        "map basemap. A lone postage-stamp portrait on a blank page does not put "
        "the figure in the story. Use HERO_CUTOUT (cutout sprite >= {3}px tall), "
        "FULL_SCREEN_CARD, or place a panel/map under it.".format(
            h_str, "/".join(SCENE_ANCHOR_PRIMITIVES[:4]) + "/…",
            "[{:.1f},{:.1f}]s".format(win[0], win[1]), HERO_MIN_H),
        where=str(cid),
    )


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")
    for i, c in enumerate(cues):
        if not isinstance(c, dict):
            raise GateInputError("cuelist.json cue #{0} is not an object".format(i))

    has_basemap = _project_has_basemap(project_dir)

    findings: List[Finding] = []
    character_beats = [c for c in cues if _kind(c) in CHARACTER_PRIMITIVES]
    for cue in character_beats:
        bad = _check_beat(cue, cues, has_basemap)
        if bad is not None:
            findings.append(bad)

    return findings


if __name__ == "__main__":
    run_cli("qa_character_presence", check)
