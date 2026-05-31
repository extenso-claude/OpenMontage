"""Character-treatment system — how a named figure is put on screen.

The failure this fixes (A4): every character beat compiled to the SAME tiny
lower-left card on empty parchment (compiler SLOT_LOWER_LEFT == 560x280, i.e.
~26% of frame height) — a postage-stamp portrait floating on a blank page. The
cut-out treatment (background removed, white-gray border, placed LARGE on the
actual scene) that the channel was supposed to use was never wired in.

This module is the compiler-side support for three sanctioned treatments plus a
helper that turns a portrait into the bordered transparent sprite a HERO_CUTOUT
needs (delegating the pixel work to lib.animated_history_map.cutout). The
matching gate (qa_character_presence) reads the emitted cuelist and FAILS a
character beat that is none of the three.

THE THREE TREATMENTS
--------------------
HERO_CUTOUT      Background removed + white-gray border (cutout.py), composited
                 LARGE onto the live scene/map. Frame height >= 30% (>= 324px on
                 1080). The figure stands IN the scene; it does not sit in a box.
FULL_SCREEN_CARD A framed portrait that fills (nearly) the whole frame, carried
                 by a camera move (push-in / pull-out / pan). >= 85% of width AND
                 height. The card IS the shot.
LOWER_CORNER     The existing small lower-corner card — only legitimate when it
                 is composited OVER real scene content (a full-frame panel /
                 archival / dive / clip, or a map basemap) in the same time
                 window. A lower-corner card on an EMPTY background is the bug.

WHEN TO USE WHICH (documented in skills/core/character-treatments.md):
  * First/important reveal of a figure, or a figure who IS the moment (the
    assassin named, the victim introduced)      -> HERO_CUTOUT.
  * A held portrait beat with a slow camera move, no competing scene -> FULL_SCREEN_CARD.
  * A name-tag while the scene itself carries the frame (figure already shown,
    or an establishing panel/map underneath)     -> LOWER_CORNER (scene-anchored).

This module is import-only support: it owns the treatment vocabulary, the slot
geometry per treatment, the >=30% threshold, and the cutout-resolution helper.
The compiler imports `bbox_for_treatment` / `resolve_hero_cutout`; the gate
imports the same constants so the rule and the renderer can never drift.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

# Frame is locked at 1920x1080 everywhere in this pipeline.
FRAME_W = 1920
FRAME_H = 1080

# Treatment names (the cue/param vocabulary the gate enforces).
HERO_CUTOUT = "hero_cutout"
FULL_SCREEN_CARD = "full_screen_card"
LOWER_CORNER = "lower_corner"
TREATMENTS = (HERO_CUTOUT, FULL_SCREEN_CARD, LOWER_CORNER)

# A HERO_CUTOUT must own real vertical real estate — at least 30% of frame
# height. Below this it reads as another postage stamp, which is the bug.
HERO_MIN_FRAME_HEIGHT_FRAC = 0.30
HERO_MIN_H = int(round(FRAME_H * HERO_MIN_FRAME_HEIGHT_FRAC))  # 324 px on 1080

# A FULL_SCREEN_CARD must (nearly) fill the frame so the portrait IS the shot.
FULLSCREEN_MIN_FRAC = 0.85
FULLSCREEN_MIN_W = int(round(FRAME_W * FULLSCREEN_MIN_FRAC))   # 1632 px
FULLSCREEN_MIN_H = int(round(FRAME_H * FULLSCREEN_MIN_FRAC))   # 918 px

# Character primitives (mirror the compiler's CARD_PRIMS character members).
CHARACTER_PRIMITIVES = ("character_card", "character_card_pop")

# Full-frame scene primitives whose presence in a character beat's time window
# means a LOWER_CORNER card is composited over real content (scene-anchored),
# not floating on empty parchment. Mirrors the compiler's FULLFRAME_PRIMS that
# carry scene imagery, plus map_sprite (a placed scene illustration on the map).
SCENE_ANCHOR_PRIMITIVES = (
    "story_dive", "panel_archival", "panel_illustration", "panel_quote",
    "document_overlay", "clip_archival", "map_sprite", "parallax_layers",
)

# Camera primitives that satisfy the FULL_SCREEN_CARD "with a camera move" rule.
CAMERA_PRIMITIVES = (
    "camera_push_in", "camera_pull_out", "camera_pan", "camera_orbit",
    "story_dive",
)

# Hero-cutout slot: a tall sprite standing on the scene. Right-anchored by
# default (subject faces into frame); ~46% frame height, comfortably above the
# 30% floor, fully inside 1920x1080.
SLOT_HERO_CUTOUT = {"x": 1180, "y": 200, "w": 620, "h": 840}
# Full-screen framed portrait: a near-full-frame card with a thin safe margin.
SLOT_FULL_SCREEN = {"x": 96, "y": 54, "w": 1728, "h": 972}


def bbox_for_treatment(treatment: str, side: str = "right") -> Dict[str, float]:
    """Return the compiler bbox (px, top-left origin, 1920x1080) for a treatment.

    `side` ('left'|'right') mirrors a HERO_CUTOUT horizontally so the subject can
    be placed on the side it faces away from (so it looks INTO the frame). For
    LOWER_CORNER the caller keeps using the compiler's existing lower slot — this
    helper only supplies the two NEW (large) treatments.
    """
    if treatment == HERO_CUTOUT:
        box = dict(SLOT_HERO_CUTOUT)
        if side == "left":
            box["x"] = FRAME_W - box["x"] - box["w"]
        return box
    if treatment == FULL_SCREEN_CARD:
        return dict(SLOT_FULL_SCREEN)
    raise ValueError(
        "bbox_for_treatment only supplies the large treatments "
        "({0!r}, {1!r}); LOWER_CORNER uses the compiler's existing lower slot."
        .format(HERO_CUTOUT, FULL_SCREEN_CARD)
    )


def is_hero_height(bbox: Optional[dict]) -> bool:
    """True if a bbox is tall enough (>= 30% frame height) to be a hero cutout."""
    if not isinstance(bbox, dict):
        return False
    h = bbox.get("h")
    if isinstance(h, bool) or not isinstance(h, (int, float)):
        return False
    return float(h) >= HERO_MIN_H


def is_full_screen(bbox: Optional[dict]) -> bool:
    """True if a bbox (nearly) fills the frame — a full-screen card."""
    if not isinstance(bbox, dict):
        return False
    w, h = bbox.get("w"), bbox.get("h")
    if isinstance(w, bool) or isinstance(h, bool):
        return False
    if not isinstance(w, (int, float)) or not isinstance(h, (int, float)):
        return False
    return float(w) >= FULLSCREEN_MIN_W and float(h) >= FULLSCREEN_MIN_H


def resolve_hero_cutout(
    portrait_path: str,
    out_path: str,
    *,
    stroke_px: int = 6,
    gray_border: bool = False,
) -> dict:
    """Turn a portrait into a bordered transparent sprite for a HERO_CUTOUT.

    Delegates the actual background-removal + outline to
    lib.animated_history_map.cutout.cutout (rembg / U2Net), so there is exactly
    one cutout implementation. Returns cutout()'s result dict (output path, size,
    pixel counts, stroke), augmented with the resolved treatment + frame-height
    fraction so the caller/compiler can assert the sprite clears the hero floor.

    This is the single integration point the compiler calls when a character
    beat declares treatment == HERO_CUTOUT.
    """
    from .cutout import cutout  # local import: rembg/onnxruntime is heavy

    color = (200, 200, 200, 255) if gray_border else (235, 235, 235, 255)
    res = cutout(portrait_path, out_path, stroke_px=stroke_px, stroke_color=color)
    res["treatment"] = HERO_CUTOUT
    size = res.get("size") or [0, 0]
    sprite_h = size[1] if len(size) > 1 else 0
    res["sprite_height_px"] = sprite_h
    # The sprite's own pixel height is informational; the ON-SCREEN height is the
    # bbox the compiler places it at (SLOT_HERO_CUTOUT), which clears the floor.
    res["placed_bbox"] = bbox_for_treatment(HERO_CUTOUT)
    res["clears_hero_floor"] = is_hero_height(res["placed_bbox"])
    return res


def classify_bbox(bbox: Optional[dict]) -> Optional[str]:
    """Best-effort: name the treatment a bbox's GEOMETRY satisfies (or None).

    full_screen wins over hero (a full-frame box is also >=30% tall). Used by the
    gate to report what a character beat's geometry actually is.
    """
    if is_full_screen(bbox):
        return FULL_SCREEN_CARD
    if is_hero_height(bbox):
        return HERO_CUTOUT
    return None


__all__ = [
    "FRAME_W", "FRAME_H",
    "HERO_CUTOUT", "FULL_SCREEN_CARD", "LOWER_CORNER", "TREATMENTS",
    "HERO_MIN_FRAME_HEIGHT_FRAC", "HERO_MIN_H",
    "FULLSCREEN_MIN_FRAC", "FULLSCREEN_MIN_W", "FULLSCREEN_MIN_H",
    "CHARACTER_PRIMITIVES", "SCENE_ANCHOR_PRIMITIVES", "CAMERA_PRIMITIVES",
    "SLOT_HERO_CUTOUT", "SLOT_FULL_SCREEN",
    "bbox_for_treatment", "is_hero_height", "is_full_screen",
    "classify_bbox", "resolve_hero_cutout",
]
