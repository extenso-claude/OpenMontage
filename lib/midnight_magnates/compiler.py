"""The compiler — storyboard JSON is the ONLY path to a HyperFrames scene.

This is the keystone of the no-monolith guarantee. A chapter storyboard (valid
against midnight_magnates_storyboard.schema.json) is the sole input; the
compiler:

  1. VALIDATES the storyboard against its schema -> an off-enum `primitive` is a
     hard error (the 64-primitive catalog is now load-bearing, not documentation).
  2. Enforces the experimental cap (<= 2 experimental beats per phase) that the
     schema cannot express.
  3. Resolves each beat's start/end timing from the Whisper transcript
     (anchor.phrase + offset_ms), falling back to anchor.fallback_absolute_s so a
     storyboard is compilable standalone (no VO needed for a structural test).
  4. Emits HyperFrames-valid HTML (clip divs with data-start/data-duration/
     data-track-index + a paused GSAP timeline registered to window.__timelines)
     per chapter AND a master, stamping <meta name="compiler-version"> so
     qa_no_custom_scripts/no-monolith can prove provenance.
  5. Emits artifacts/cuelist.json — the flattened, gate-facing timeline that
     qa_min_hold / qa_element_overlap / qa_card_bounds / qa_asset_reference_closure
     consume. This is how the gates verify the COMPILER's real output.

Motion is uniform (compiler-authored fades) by design — the animator cannot pick
easings freehand. Richer per-primitive motion + the geo-grounded diorama engine
are Milestone B; this compiler renders a real, correctly-timed, gapless scene for
a core primitive set and emits an honest cuelist for the rest.

CLI:  python -m lib.midnight_magnates.compiler --project <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import jsonschema  # noqa: E402
from schemas.artifacts import validate_artifact  # noqa: E402
from lib.midnight_magnates import __version__  # noqa: E402
from lib.midnight_magnates import vocab  # noqa: E402  (single-source primitive vocabulary)
from lib.midnight_magnates.character_treatment import (  # noqa: E402
    bbox_for_treatment, HERO_CUTOUT, FULL_SCREEN_CARD,
)

COMPILER_VERSION = "midnight_magnates.compiler@{0}".format(__version__)

# --- primitive families (drive bbox + track + whether it's a visual element) ---
# Single-sourced from lib.midnight_magnates.vocab — these were 6 hand-maintained
# literals that could drift from the schema enum and the gates' copies; vocab is now
# the one source every consumer imports (membership is identical, verified by vocab's
# import-time self-check).
AUDIO_PRIMS = vocab.AUDIO_PRIMS
CARD_PRIMS = vocab.CARD_PRIMS
MAP_ANCHORED_PRIMS = vocab.MAP_ANCHORED_PRIMS
FULLFRAME_PRIMS = vocab.FULLFRAME_PRIMS
UI_CORNER_PRIMS = vocab.UI_CORNER_PRIMS
FACE_PRIMS = vocab.FACE_PRIMS  # RULE 4: emotional faces
AUDIO_TRACK_INDEX = 20  # matches hf_coverage_qa convention (excluded from visual coverage)

# Layout slots (px, top-left origin, 1920x1080) used for bbox computation.
SLOT_LOWER_LEFT = {"x": 80, "y": 740, "w": 560, "h": 280}     # character cards
SLOT_LOWER_THIRD = {"x": 360, "y": 880, "w": 1200, "h": 160}  # source citations
SLOT_TOP_RIGHT = {"x": 1560, "y": 48, "w": 312, "h": 96}      # year/UI corner
FULL_FRAME = {"x": 0, "y": 0, "w": 1920, "h": 1080}
SLOT_FACE_CLOSEUP = {"x": 460, "y": 60, "w": 1000, "h": 960}   # RULE 4: large centered emotional face
SLOT_FACE_MEDIUM = {"x": 610, "y": 170, "w": 700, "h": 780}    # RULE 4: medium face shot
ANCHOR_BOX_W, ANCHOR_BOX_H = 220, 64  # small box around a map-anchored pin/label

# Compiler-authored fade timing (the animator cannot override these).
FADE_S = 0.3

# Theme palettes whose basemap is LIGHT/warm rather than noir. On these the
# legible-history rule flips: cue text must be INK (dark) on the parchment, and
# card / map-label backings must be CREAM with an ink/brass border — the
# hardcoded dark rgba(10,15,26,...) chrome from the noir path would be invisible
# (dark-on-dark text the user can't read) over an aged-parchment map.
LIGHT_BASEMAP_FILTERS = {"warm", "illuminated", "light_minimal"}


def _hex_to_rgb(value: str, fallback: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Parse '#rrggbb' (or 'rrggbb') to an (r,g,b) tuple; fall back on garbage."""
    if isinstance(value, str):
        s = value.strip().lstrip("#")
        if len(s) == 6:
            try:
                return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
            except ValueError:
                pass
    return fallback


def _theme_palette(theme: dict) -> dict:
    """Resolve the render palette from theme.palette_master.

    Returns a flat dict of the colors the emitter needs. The branch is driven by
    palette_master.basemap_filter:
      * LIGHT/warm/illuminated/light_minimal -> ink text on cream backings with
        an ink/brass border (aged-parchment look);
      * anything else (noir / dark) -> the original light-text-on-dark chrome.

    All values trace back to palette_master (paper / ink / accents) so a theme
    swap re-skins the chapter without touching this code.
    """
    pm = theme.get("palette_master") or {}
    basemap_filter = str(pm.get("basemap_filter", "")).strip().lower()
    # MM RULE 1: noir is the LOCKED channel look. The theme schema rejects
    # warm/illuminated/light_minimal, so the parchment branch below is dead for the
    # MM pipeline; we also force noir here as defense-in-depth so an AHM theme can't
    # sneak a light basemap in and render unreadable dark-on-cream chrome.
    is_light = False
    _ = basemap_filter in LIGHT_BASEMAP_FILTERS  # (retained for traceability; not used)

    accent = pm.get("primary_accent", "#c9a84c")          # brass (venues / pins)
    accent_2 = pm.get("secondary_accent", accent)         # oxblood (route / assassination)
    paper_rgb = _hex_to_rgb(pm.get("paper", "#efe6cf"), (239, 230, 207))
    ink_rgb = _hex_to_rgb(pm.get("ink", "#2b2015"), (43, 32, 21))

    if is_light:
        bg = pm.get("ui_dark", pm.get("paper", "#efe6cf"))    # page color (cream)
        fg = pm.get("ui_light", pm.get("ink", "#2b2015"))     # body text color (ink)
        ink = "rgb({0},{1},{2})".format(*ink_rgb)
        # Cream backing on a light map keeps a label/card legible without a black
        # plate; an ink/brass hairline separates it from the parchment.
        backing = "rgba({0},{1},{2},0.9)".format(*paper_rgb)
        border = accent                                       # brass hairline
        # Soft paper-toned shadows (a 0,0,0 glow looks like a hole on cream).
        text_shadow = "0 1px 2px rgba({0},{1},{2},0.35)".format(*ink_rgb)
        backing_shadow = "0 2px 10px rgba({0},{1},{2},0.30)".format(*ink_rgb)
        # Pin halo in the accent itself rather than a brass-on-dark glow.
        pin_halo = accent_2
        return {
            "is_light": True, "bg": bg, "fg": fg, "text_color": ink,
            "card_backing": backing, "card_border": border,
            "label_backing": backing, "label_border": ink,
            "text_shadow": text_shadow, "backing_shadow": backing_shadow,
            "pin_halo": pin_halo, "accent": accent,
        }

    # Noir / dark default — preserve the original chrome exactly.
    NOIR_BG = "#080c16"
    bg = pm.get("ui_dark", NOIR_BG)
    # RULE 1: the page background must READ as noir. basemap_filter is locked to
    # 'noir' by the theme schema, but ui_dark is only constrained to be a hex color —
    # a theme that (mis)set ui_dark to a light value would emit a cream html,body
    # background under the dark cards. Clamp a light ui_dark back to the noir navy.
    _bgr, _bgg, _bgb = _hex_to_rgb(bg, (8, 12, 22))
    if (0.299 * _bgr + 0.587 * _bgg + 0.114 * _bgb) > 110:
        bg = NOIR_BG
    fg = pm.get("ui_light", "#f5f0e4")
    return {
        "is_light": False, "bg": bg, "fg": fg, "text_color": fg,
        "card_backing": "rgba(10,15,26,0.82)", "card_border": "var(--accent)",
        "label_backing": "rgba(10,15,26,0.72)", "label_border": None,
        "text_shadow": "0 0 12px rgba(0,0,0,0.9)",
        "backing_shadow": "0 0 12px rgba(0,0,0,0.85)",
        "pin_halo": "rgba(201,168,76,0.22)", "accent": accent,
    }


def _marker_css(pal: dict) -> str:
    """Rich CSS for map-tier primitives (Milestone B), themed from `pal`.

    The compiler stays the sole, stamped emitter (anti-monolith intact) while the
    theme drives the look. Inserted into the {scene_css} slot, so literal CSS
    braces are safe here (this value is substituted, not re-formatted).
    """
    label_extra = ""
    if pal.get("label_border"):
        label_extra = "border:1px solid {0}; ".format(pal["label_border"])
    return (
        "#root { background-size:cover; background-position:center; }\n"
        ".cue-pin_drop, .cue-pin_pulse_breath, .cue-pin_dimming, .cue-map_sprite "
        "{ display:flex; align-items:center; justify-content:center; }\n"
        ".cue-pin_drop::before, .cue-pin_pulse_breath::before, .cue-pin_dimming::before "
        "{ content:''; width:18px; height:18px; border-radius:50%; background:var(--accent); "
        "box-shadow:0 0 0 6px " + pal["pin_halo"] + ", 0 0 18px var(--accent); }\n"
        ".cue-map_label .cue-text, .cue-label_cluster .cue-text { font-family:'Cinzel',Georgia,serif; "
        "text-transform:uppercase; letter-spacing:1px; font-size:22px; line-height:1.35; color:"
        + pal["text_color"] + "; background:" + pal["label_backing"] + "; " + label_extra
        + "padding:5px 12px; border-radius:3px; box-shadow:" + pal["backing_shadow"] + "; }\n"
        ".route-svg { position:absolute; inset:0; width:1920px; height:1080px; pointer-events:none; overflow:visible; }\n"
        ".route-path { fill:none; stroke:var(--accent); stroke-width:3; stroke-dasharray:9 6; "
        "filter:drop-shadow(0 0 6px var(--accent)); }\n"
        ".route-icon { position:absolute; transform:translate(-50%,-50%); font-size:26px; line-height:1; "
        "filter:drop-shadow(0 0 6px rgba(0,0,0,0.8)); pointer-events:none; }\n"
        ".pres-pins { position:absolute; inset:0; pointer-events:none; }\n"
        ".pres-pin { position:absolute; width:14px; height:14px; border-radius:50%; "
        "transform:translate(-50%,-50%); }\n"
        ".pres-pin.pin-dimmed { background:" + pal["label_backing"] + "; opacity:0.35; "
        "box-shadow:0 0 0 2px rgba(0,0,0,0.4); }\n"
        ".pres-pin.pin-current { background:var(--accent); opacity:1; "
        "box-shadow:0 0 0 6px " + pal["pin_halo"] + ", 0 0 18px var(--accent); }\n"
    )


class CompileError(Exception):
    """A storyboard cannot be compiled (invalid, off-enum, or unresolvable timing)."""


# --------------------------------------------------------------------------- #
# timing
# --------------------------------------------------------------------------- #
# Mirror qa_scene_sync / qa_drift / qa_audio_drift token normalization EXACTLY so a
# phrase resolves to the same word here (compiler) and there (gates) — a stray comma
# must not make the compiler and the drift audit disagree about where a beat lands.
# Strip only edge punctuation; keep internal apostrophes/hyphens ("nation's", "thirty-five").
_EDGE_PUNCT = ".,!?;:\"'`()[]{}<>—–…“”‘’"


def _is_number(v) -> bool:
    """True for a real number (a bool is not a time/coordinate)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _norm_token(tok: str) -> str:
    return tok.lower().strip().strip(_EDGE_PUNCT)


def _whisper_index(whisper: Optional[dict]) -> List[Tuple[str, float]]:
    """Return [(normalized_token, start_s), ...] from a Whisper transcript, or [].

    Normalization mirrors the drift gates so the compiler and the gates resolve a
    phrase to the same word.
    """
    if not whisper:
        return []
    words = whisper.get("words")
    out: List[Tuple[str, float]] = []
    if isinstance(words, list):
        for w in words:
            if isinstance(w, dict) and "word" in w and "start" in w:
                t = _norm_token(str(w["word"]))
                if t:
                    out.append((t, float(w["start"])))
    return out


def _resolve_anchor(anchor: dict, words: List[Tuple[str, float]], where: str) -> Tuple[float, str]:
    """Resolve an anchor to seconds on the master VO clock + its source.

    Returns (time_s, source) where source is 'whisper' (matched a real word run) or
    'fallback' (used anchor.fallback_absolute_s). Prefer the Whisper word time of
    anchor.phrase; fall back to anchor.fallback_absolute_s. A beat with neither is a
    hard CompileError — an un-timeable beat must never silently get t=0.

    Carrying the source lets _build_cue stamp anchor_source so a drift gate can reject
    a cue that only resolved via a structural fallback on a real VO run (the loophole).
    """
    offset = float(anchor.get("offset_ms", 0)) / 1000.0
    toks = [t for t in (_norm_token(x) for x in str(anchor.get("phrase", "")).split()) if t]
    if toks and words:
        n = len(toks)
        for i in range(len(words) - n + 1):
            if [w for w, _ in words[i:i + n]] == toks:
                return max(0.0, words[i][1] + offset), "whisper"
    fb = anchor.get("fallback_absolute_s")
    if _is_number(fb):
        return max(0.0, float(fb) + offset), "fallback"
    raise CompileError(
        "{0}: anchor phrase {1!r} not found in transcript and no fallback_absolute_s".format(
            where, str(anchor.get("phrase", "")))
    )


# --------------------------------------------------------------------------- #
# cues
# --------------------------------------------------------------------------- #
def _layer_int(layer: str) -> int:
    return int(layer[1:]) if isinstance(layer, str) and layer.startswith("L") else 0


def _anchor_pixel(anchor_id: Optional[str], positions: Optional[dict]) -> Optional[Tuple[float, float]]:
    if not anchor_id or not positions:
        return None
    for a in positions.get("anchors", []) or []:
        if isinstance(a, dict) and a.get("id") == anchor_id:
            px, py = a.get("px"), a.get("py")
            if isinstance(px, (int, float)) and isinstance(py, (int, float)):
                return float(px), float(py)
    return None


def _clamp_box(x: float, y: float, w: float, h: float) -> dict:
    """Keep a derived anchor box inside the frame (so legitimate map pins don't
    spuriously fail qa_card_bounds at the edges)."""
    x = max(0.0, min(x, 1920.0 - w))
    y = max(0.0, min(y, 1080.0 - h))
    return {"x": round(x), "y": round(y), "w": w, "h": h}


def _bbox_for(prim: str, la: dict, positions: Optional[dict]) -> Optional[dict]:
    # RULE 4 — emotional faces get a large centered slot (NOT a lower-third card).
    if prim in FACE_PRIMS:
        return dict(SLOT_FACE_MEDIUM if prim == "face_medium" else SLOT_FACE_CLOSEUP)
    if prim in CARD_PRIMS:
        # Character cards honor an explicit treatment (HERO_CUTOUT / FULL_SCREEN_CARD)
        # instead of always collapsing to the tiny lower-left card — the A4 / postage-
        # stamp bug: character_treatment was defined but never wired into the compiler.
        if prim in ("character_card", "character_card_pop"):
            treat = (la.get("treatment") or (la.get("params") or {}).get("treatment"))
            if isinstance(treat, str):
                t = treat.strip().lower()
                if t == HERO_CUTOUT:
                    side = (la.get("params") or {}).get("side")
                    return bbox_for_treatment(HERO_CUTOUT, side=side if side in ("left", "right") else "right")
                if t == FULL_SCREEN_CARD:
                    return bbox_for_treatment(FULL_SCREEN_CARD)
        return dict(SLOT_LOWER_THIRD if prim == "source_citation" else SLOT_LOWER_LEFT)
    if prim in UI_CORNER_PRIMS:
        return dict(SLOT_TOP_RIGHT)
    if prim in FULLFRAME_PRIMS:
        return dict(FULL_FRAME)
    if prim in MAP_ANCHORED_PRIMS:
        px = _anchor_pixel(la.get("anchor_id"), positions)
        if px is None:
            return None  # no resolved pixel -> not a bounds/overlap candidate
        return _clamp_box(px[0] - ANCHOR_BOX_W / 2, px[1] - ANCHOR_BOX_H / 2, ANCHOR_BOX_W, ANCHOR_BOX_H)
    # Off-map action cues (FX, 2D/3D scene elements): a spatial_target gives them a
    # real box so bounds/overlap/placement gates can see them (RULE 3 + spatial sync).
    st = la.get("spatial_target")
    if isinstance(st, dict):
        tp = st.get("target_px")
        if isinstance(tp, list) and len(tp) >= 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in tp[:4]):
            if len(tp) >= 4:
                return _clamp_box(float(tp[0]), float(tp[1]), float(tp[2]), float(tp[3]))
            return _clamp_box(float(tp[0]) - ANCHOR_BOX_W / 2, float(tp[1]) - ANCHOR_BOX_H / 2, ANCHOR_BOX_W, ANCHOR_BOX_H)
        aid = st.get("anchor_id")
        if aid:
            px = _anchor_pixel(aid, positions)
            if px is not None:
                return _clamp_box(px[0] - ANCHOR_BOX_W / 2, px[1] - ANCHOR_BOX_H / 2, ANCHOR_BOX_W, ANCHOR_BOX_H)
    return None  # transitions / regions / cameras / atmospherics: no bbox


def _cue_text(la: dict) -> Optional[str]:
    p = la.get("params") or {}
    for k in ("text", "label", "name", "caption", "quote"):
        v = p.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _label_count(la: dict) -> Optional[int]:
    p = la.get("params") or {}
    labels = p.get("labels")
    if isinstance(labels, list):
        return len(labels)
    return None


def _build_cue(chapter_id: str, beat_id: str, idx: int, la: dict,
               local_start: float, local_end: float, positions: Optional[dict],
               anchor_phrase: Optional[str] = None, anchor_time_s: Optional[float] = None,
               anchor_source: Optional[str] = None) -> dict:
    prim = la["primitive"]
    layer = _layer_int(la.get("layer", "L0"))
    is_audio = prim in AUDIO_PRIMS
    cue = {
        "id": "{0}.{1}.{2}.{3}".format(chapter_id, beat_id, prim, idx),
        "kind": prim,
        "layer": layer,
        "track": AUDIO_TRACK_INDEX if is_audio else (layer + 1),
        "is_audio": is_audio,
        "local_start": round(local_start, 3),
        "local_end": round(local_end, 3),
    }
    text = _cue_text(la)
    if text is not None:
        cue["text"] = text
    if not is_audio:
        bbox = _bbox_for(prim, la, positions)
        if bbox is not None:
            cue["bbox"] = bbox
    if la.get("anchor_id"):
        cue["anchor_id"] = la["anchor_id"]
    if la.get("asset_id"):
        cue["asset_id"] = la["asset_id"]
    lc = _label_count(la)
    if lc is not None:
        cue["label_count"] = lc
    # RULE 4 / treatment: carry the declared treatment so qa_character_presence's
    # declaration branch is reachable (it used to be silently dropped — the A4 bug).
    treat = la.get("treatment") or (la.get("params") or {}).get("treatment")
    if isinstance(treat, str) and treat.strip():
        cue["treatment"] = treat.strip().lower()
    # Spatial-sync: carry placement + the focal pixel so qa_spatial_anchor and
    # qa_visual_alignment have real data (the dead-gate fix — qa_visual_alignment
    # read anchor_px the compiler never emitted, so it verified nothing).
    if la.get("placement"):
        cue["placement"] = la["placement"]
    if la.get("time_distinct"):
        cue["time_distinct"] = True
    if isinstance(la.get("anchor_color"), list):
        cue["anchor_color"] = la["anchor_color"]
    st = la.get("spatial_target")
    if isinstance(st, dict):
        cue["spatial_target"] = st
        tp = st.get("target_px")
        if isinstance(tp, list) and len(tp) >= 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in tp[:2]):
            cue["anchor_px"], cue["anchor_py"] = round(float(tp[0])), round(float(tp[1]))
        elif st.get("anchor_id"):
            pxy = _anchor_pixel(st.get("anchor_id"), positions)
            if pxy is not None:
                cue["anchor_px"], cue["anchor_py"] = round(pxy[0]), round(pxy[1])
    # Map-anchored cues: stamp the resolved pixel (computed to center the bbox but
    # previously discarded) so qa_visual_alignment can verify the rendered pin.
    if prim in MAP_ANCHORED_PRIMS and la.get("anchor_id") and "anchor_px" not in cue:
        pxy = _anchor_pixel(la["anchor_id"], positions)
        if pxy is not None:
            cue["anchor_px"], cue["anchor_py"] = round(pxy[0]), round(pxy[1])
    params = la.get("params") or {}
    if "interaction_with" in params:
        cue["interaction_with"] = params["interaction_with"]
    if "min_hold_override" in params:
        cue["min_hold_override"] = params["min_hold_override"]
    # Route geometry for migration_arrow: resolve the path's anchor ids to pixels
    # (purely from positions.json — no Mercator in the HTML) so it can draw on a map.
    if prim == "migration_arrow":
        pts = []
        for aid in (params.get("path") or []):
            pxy = _anchor_pixel(aid, positions)
            if pxy:
                pts.append([round(pxy[0]), round(pxy[1])])
        if len(pts) >= 2:
            cue["path_px"] = pts
        # A transportation/character icon (e.g. Booth on horseback) rides the
        # polyline. Pass its label/asset through so the HTML can place + travel a
        # marker along path_px (qa_migration_icon requires this on travel routes).
        icon = params.get("character_icon")
        if isinstance(icon, dict):
            label = next((icon[k] for k in ("label", "asset_id", "icon", "sprite",
                                            "character_id", "emoji")
                          if isinstance(icon.get(k), str) and icon.get(k).strip()), None)
            if label:
                cue["route_icon"] = {"label": label.strip(),
                                     "asset_id": icon.get("asset_id")}
    # The recurring all-presidents spine map: resolve every pin to a pixel and
    # record which one is `current` (drawn in color; the rest dimmed).
    if prim == "all_presidents_pins":
        # Geo pixels come only from positions.json anchors (no Mercator in the
        # compiler/HTML — geography.py pre-resolves lat/lon to anchor px/py).
        pins_px = []
        for pin in (params.get("pins") or []):
            if not isinstance(pin, dict):
                continue
            pid = pin.get("id")
            pxy = _anchor_pixel(pin.get("anchor_id"), positions)
            if isinstance(pid, str) and pid.strip() and pxy is not None:
                pins_px.append({"id": pid.strip(),
                                "px": round(pxy[0]), "py": round(pxy[1]),
                                "current": pid.strip() == params.get("current")})
        if pins_px:
            cue["pins_px"] = pins_px
            if isinstance(params.get("current"), str):
                cue["current_pin"] = params["current"]
    # Drift spine: every cue carries the VO word it hangs off + the resolved master
    # time + whether that came from Whisper or a structural fallback. The cross-cue
    # drift audit (memory drift_audit_all_cue_types) resolves against these; a
    # fallback source on a real VO run is what a drift gate rejects.
    if anchor_phrase:
        cue["anchor_phrase"] = anchor_phrase
    if anchor_time_s is not None:
        cue["anchor_time_s"] = round(float(anchor_time_s), 3)
    if anchor_source:
        cue["anchor_source"] = anchor_source
    return cue


def _build_scene_graph(chapter_id: str, beat_id: str, beat: dict,
                       start_master_s: float, end_master_s: float) -> dict:
    """Synthesize the VO-reconciled scene graph for an animated (2d/3d) beat.

    qa_scene_sync requires every animation_tier 2d/3d beat to carry a scene graph
    with scene_t0_master_s + key_moments[{local_t, vo_anchor_phrase, ...}] that hang
    on real Whisper words. We derive it from the beat's own start/end anchors (already
    resolved against the master VO), so scene_t0 + local_t == the narrated word time
    by construction (zero drift). Richer per-action key moments can be authored later;
    this guarantees the animated beat is genuinely VO-anchored, not a dead hold.

    A FACE beat (carries emotion_face) marks its moment face=True so qa_scene_sync
    applies the tighter 0.4s face budget.
    """
    is_face = isinstance(beat.get("emotion_face"), dict)
    key_moments: List[dict] = []
    sa = beat.get("start_anchor") or {}
    sp = str(sa.get("phrase", "")).strip()
    if sp:
        m = {"local_t": 0.0, "vo_anchor_phrase": sp}
        if _is_number(sa.get("fallback_absolute_s")):
            m["fallback_absolute_s"] = float(sa["fallback_absolute_s"])
        if is_face:
            m["face"] = True
        key_moments.append(m)
    ea = beat.get("end_anchor") or {}
    ep = str(ea.get("phrase", "")).strip()
    if ep:
        m = {"local_t": round(max(0.0, end_master_s - start_master_s), 3),
             "vo_anchor_phrase": ep}
        if _is_number(ea.get("fallback_absolute_s")):
            m["fallback_absolute_s"] = float(ea["fallback_absolute_s"])
        key_moments.append(m)
    return {
        "scene_t0_master_s": round(start_master_s, 3),
        "beat_id": beat_id,
        "chapter_id": chapter_id,
        "animation_tier": beat.get("animation_tier"),
        "key_moments": key_moments,
    }


# --------------------------------------------------------------------------- #
# HTML emission (HyperFrames-valid, self-contained)
# --------------------------------------------------------------------------- #
def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _clip_div(cue: dict, start: float, dur: float, theme: dict) -> str:
    """One HyperFrames clip div for a cue, positioned at absolute `start`."""
    kind = cue["kind"]
    if cue["is_audio"]:
        # Audio cues carry no pixels; track 20 keeps them out of visual coverage.
        return ('<div class="clip cue-audio cue-{k}" id="{id}" data-start="{s:.3f}" '
                'data-duration="{d:.3f}" data-track-index="{t}" style="display:none"></div>').format(
            k=kind, id=_esc(cue["id"]), s=start, d=dur, t=cue["track"])

    bbox = cue.get("bbox")
    if bbox:
        style = "left:{x}px; top:{y}px; width:{w}px; height:{h}px;".format(**bbox)
    else:
        style = "inset:0;"  # effect/overlay spans the stage
    accent = (theme.get("palette_master") or {}).get("primary_accent", "#c9a84c")
    text = cue.get("text")
    inner = ('<span class="cue-text">{0}</span>'.format(_esc(text)) if text else "")
    if cue.get("path_px"):
        pts = " ".join("{0},{1}".format(int(x), int(y)) for x, y in cue["path_px"])
        inner = ('<svg class="route-svg" viewBox="0 0 1920 1080" preserveAspectRatio="none">'
                 '<polyline class="route-path" points="{0}" /></svg>'.format(pts)) + inner
        # The character/transportation icon rides the polyline (starts at its head).
        ic = cue.get("route_icon")
        if ic and cue["path_px"]:
            hx, hy = cue["path_px"][0]
            inner += ('<span class="route-icon" data-route-icon="1" '
                      'style="left:{x}px; top:{y}px;">{lbl}</span>').format(
                x=int(hx), y=int(hy), lbl=_esc(ic.get("label", "")))
    if cue.get("pins_px"):
        # The recurring all-presidents map: a dot per president; the `current`
        # one is rendered in color (.pin-current), the rest dimmed (.pin-dimmed).
        dots = "".join(
            ('<span class="pres-pin {cls}" data-pin-id="{pid}" '
             'style="left:{x}px; top:{y}px;"></span>').format(
                cls=("pin-current" if p.get("current") else "pin-dimmed"),
                pid=_esc(str(p.get("id", ""))), x=int(p["px"]), y=int(p["py"]))
            for p in cue["pins_px"] if "px" in p and "py" in p)
        inner = ('<div class="pres-pins" data-current="{cur}">{dots}</div>'.format(
            cur=_esc(str(cue.get("current_pin", ""))), dots=dots)) + inner
    return ('<div class="clip cue-{k}" id="{id}" data-start="{s:.3f}" data-duration="{d:.3f}" '
            'data-track-index="{t}" style="{style} opacity:0; --accent:{a};">{inner}</div>').format(
        k=kind, id=_esc(cue["id"]), s=start, d=dur, t=cue["track"], style=style, a=accent, inner=inner)


def _clip_tween(cue: dict, start: float, dur: float) -> str:
    """Compiler-authored fade in/out for one visual clip (no freehand easing)."""
    if cue["is_audio"]:
        return ""
    sel = "#" + cue["id"]
    fade = min(FADE_S, dur / 2.0)
    out_at = max(start, start + dur - fade)
    return ('  tl.to("{sel}", {{opacity:1, duration:{f:.3f}, ease:"power1.out"}}, {s:.3f});\n'
            '  tl.to("{sel}", {{opacity:0, duration:{f:.3f}, ease:"power1.in"}}, {o:.3f});').format(
        sel=sel, f=fade, s=start, o=out_at)


_HEAD = """<!doctype html>
<html lang="en" data-resolution="landscape">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<meta name="compiler-version" content="{ver}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  html,body {{ width:1920px; height:1080px; margin:0; padding:0; overflow:hidden;
               background:{bg}; color:{fg}; font-family:Georgia,serif; }}
  #root {{ position:absolute; inset:0; }}
  .clip {{ position:absolute; box-sizing:border-box; }}
  .cue-text {{ display:block; padding:14px 18px; font-size:30px; line-height:1.25;
               color:{text_color}; text-shadow:{text_shadow}; }}
  .cue-character_card .cue-text, .cue-character_card_pop .cue-text {{
        background:{card_backing}; border-left:4px solid {card_border};
        box-shadow:{backing_shadow}; }}
  .cue-source_citation .cue-text {{ font-style:italic; text-align:center; }}
{scene_css}
</style>
</head>
<body>
<div id="root" class="clip" data-composition-id="{cid}" data-start="0" data-duration="{dur:.3f}"
     data-width="1920" data-height="1080" data-track-index="0">
{scene_html}
</div>
<script>
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused: true }});
{tl_js}
  window.__timelines["{cid}"] = tl;
</script>
</body>
</html>
"""


def _render_html(cid: str, dur: float, cues: List[dict], offsets: Dict[str, float],
                 theme: dict, basemap_rel: Optional[str] = None) -> str:
    pal = _theme_palette(theme)
    scene_css = _marker_css(pal)
    if basemap_rel:
        scene_css += "#root {{ background-image:url('{0}'); }}\n".format(basemap_rel).replace("{{", "{").replace("}}", "}")
    scene_html = "\n".join(
        _clip_div(c, offsets[c["id"]], c["local_end"] - c["local_start"], theme) for c in cues
    )
    tl_js = "\n".join(
        t for t in (_clip_tween(c, offsets[c["id"]], c["local_end"] - c["local_start"]) for c in cues) if t
    )
    return _HEAD.format(ver=COMPILER_VERSION, bg=pal["bg"], fg=pal["fg"],
                        text_color=pal["text_color"], text_shadow=pal["text_shadow"],
                        card_backing=pal["card_backing"], card_border=pal["card_border"],
                        backing_shadow=pal["backing_shadow"],
                        scene_css=scene_css, cid=_esc(cid),
                        dur=dur, scene_html=scene_html, tl_js=tl_js)


# --------------------------------------------------------------------------- #
# chapter + project compile
# --------------------------------------------------------------------------- #
def _enforce_experimental_cap(storyboard: dict) -> None:
    for ph in storyboard.get("phases", []):
        n = sum(1 for b in ph.get("beats", []) if b.get("experimental") is True)
        if n > 2:
            raise CompileError(
                "phase {0!r} has {1} experimental beats (max 2)".format(ph.get("phase_id"), n)
            )


def compile_chapter(storyboard: dict, *, theme: dict, positions: Optional[dict],
                    whisper: Optional[dict], out_html: Path,
                    scene_graph_dir: Optional[Path] = None) -> dict:
    """Validate + compile one chapter. Returns {chapter_id, cues, html_path, duration_s}.

    Timing model: whisper/full.json is the MASTER VO transcript (absolute seconds
    over the whole video). _resolve_anchor returns that master time; we subtract the
    chapter's vo_start_offset_in_master_s to get chapter-local clip times for the
    per-chapter HTML, and compile_project re-adds the offset for the master cuelist
    (net: master == resolved, no double-count). For a single-section slice the offset
    is 0 and the subtraction is a no-op.
    """
    try:
        validate_artifact("midnight_magnates_storyboard", storyboard)
    except jsonschema.ValidationError as exc:
        loc = "/".join(str(p) for p in exc.absolute_path) or "<root>"
        raise CompileError("storyboard invalid at {0}: {1}".format(loc, exc.message)) from exc
    _enforce_experimental_cap(storyboard)

    chapter_id = storyboard["chapter_id"]
    duration_s = float(storyboard["duration_s"])
    chapter_offset = float(storyboard.get("vo_start_offset_in_master_s", 0.0))
    words = _whisper_index(whisper)
    # Scope phrase resolution to THIS chapter's master-time window so a phrase that
    # recurs across chapters binds to the occurrence INSIDE its own chapter (not the
    # first one anywhere in the video). With one master full.json this is what keeps
    # the compiler's resolution consistent with the chapter-scoped drift gates; an
    # empty window (mis-set offset/duration — caught by qa_master_offset) falls back
    # to the full list rather than failing to resolve.
    if words:
        _lo, _hi = chapter_offset, chapter_offset + duration_s
        scoped_words = [(w, t) for (w, t) in words if _lo <= t < _hi] or words
    else:
        scoped_words = words

    cues: List[dict] = []
    scene_graphs: List[Tuple[str, dict]] = []
    seen_beat_ids: set = set()
    for ph in storyboard["phases"]:
        for beat in ph["beats"]:
            bid = beat["beat_id"]
            # A duplicate (chapter, beat_id) would clobber the beat's scene-graph file
            # AND collide its cue ids — silent data-loss the gates can't see. Fail loud.
            if bid in seen_beat_ids:
                raise CompileError(
                    "{0}: duplicate beat_id {1!r} in chapter — beat ids must be unique "
                    "within a chapter (a dup overwrites the first beat's scene graph and "
                    "produces colliding cue ids)".format(chapter_id, bid))
            seen_beat_ids.add(bid)
            where = "{0}/{1}".format(chapter_id, bid)
            start_m, start_src = _resolve_anchor(beat["start_anchor"], scoped_words, where + ".start")
            end_m, _end_src = _resolve_anchor(beat["end_anchor"], scoped_words, where + ".end")
            if end_m <= start_m:
                raise CompileError("{0}: end ({1}) <= start ({2})".format(where, end_m, start_m))
            # Master -> chapter-local for the per-chapter HTML clock.
            local_start = max(0.0, start_m - chapter_offset)
            local_end = max(0.0, end_m - chapter_offset)
            start_phrase = str(beat["start_anchor"].get("phrase", "")).strip() or None
            for idx, la in enumerate(beat["layers"]):
                # A layer may carry its own cue_anchor (the schema REQUIRES it for the
                # 2nd+ time-distinct action in a beat) — that action fires on its OWN
                # word, not the beat start, so time this cue from the cue_anchor. Else
                # the layer inherits the beat's start_anchor.
                l_start_m, l_src, l_phrase = start_m, start_src, start_phrase
                ca = la.get("cue_anchor")
                if isinstance(ca, dict) and str(ca.get("phrase", "")).strip():
                    l_start_m, l_src = _resolve_anchor(ca, scoped_words, where + ".cue_anchor")
                    l_phrase = str(ca.get("phrase", "")).strip() or None
                l_local_start = max(0.0, l_start_m - chapter_offset)
                l_local_end = max(local_end, l_local_start + 0.1)  # hold at least to the beat end
                cues.append(_build_cue(chapter_id, bid, idx, la, l_local_start, l_local_end, positions,
                                       anchor_phrase=l_phrase, anchor_time_s=l_start_m,
                                       anchor_source=l_src))
            # RULE 2: an animated (2d/3d) beat must emit a VO-reconciled scene graph so
            # qa_scene_sync can verify it is anchored to the narration, not a dead hold.
            if beat.get("animation_tier") in ("2d", "3d"):
                scene_graphs.append((bid, _build_scene_graph(chapter_id, bid, beat, start_m, end_m)))

    offsets = {c["id"]: c["local_start"] for c in cues}
    # Ground the scene on its rendered basemap (chapter HTML lives at
    # hyperframes/chapter_<id>/index.html → ../../assets/maps/<extent>.png).
    extent = ((positions or {}).get("map_info") or {}).get("extent_id")
    basemap_rel = "../../assets/maps/{0}.png".format(extent) if extent else None
    html = _render_html(chapter_id, duration_s, cues, offsets, theme, basemap_rel=basemap_rel)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html)

    # Write each animated beat's scene graph to
    # artifacts/diorama/<chapter>.<beat>.scene_graph.json (qa_scene_sync's input).
    if scene_graph_dir is not None and scene_graphs:
        scene_graph_dir.mkdir(parents=True, exist_ok=True)
        for bid, graph in scene_graphs:
            (scene_graph_dir / "{0}.{1}.scene_graph.json".format(chapter_id, bid)).write_text(
                json.dumps(graph, indent=2))

    return {"chapter_id": chapter_id, "cues": cues, "html_path": str(out_html), "duration_s": duration_s,
            "vo_start_offset_in_master_s": chapter_offset,
            "scene_graphs": [bid for bid, _ in scene_graphs]}


def compile_project(project_dir: Path) -> dict:
    """Compile every chapter storyboard -> per-chapter HTML + master + cuelist.json."""
    project_dir = Path(project_dir).resolve()
    art = project_dir / "artifacts"
    sb_dir = art / "storyboard"
    if not sb_dir.is_dir():
        raise CompileError("no artifacts/storyboard/ directory in {0}".format(project_dir))
    sb_paths = sorted(sb_dir.glob("*.json"))
    if not sb_paths:
        raise CompileError("no storyboard *.json files in {0}".format(sb_dir))

    theme = _load_optional(art / "theme.json") or {}
    positions = _load_optional(art / "positions.json")
    whisper = _load_optional(art / "whisper" / "full.json")
    scene_graph_dir = art / "diorama"

    chapters = []
    for p in sb_paths:
        sb = json.loads(p.read_text())
        out_html = project_dir / "hyperframes" / "chapter_{0}".format(sb.get("chapter_id", p.stem)) / "index.html"
        chapters.append(compile_chapter(sb, theme=theme, positions=positions, whisper=whisper,
                                        out_html=out_html, scene_graph_dir=scene_graph_dir))

    chapters.sort(key=lambda c: c["vo_start_offset_in_master_s"])

    # Global cuelist + master HTML.
    global_cues: List[dict] = []
    master_offsets: Dict[str, float] = {}
    for ch in chapters:
        off = ch["vo_start_offset_in_master_s"]
        for c in ch["cues"]:
            gc = dict(c)
            gc["start_s"] = round(c["local_start"] + off, 3)
            gc["end_s"] = round(c["local_end"] + off, 3)
            global_cues.append(gc)
            master_offsets[c["id"]] = gc["start_s"]

    master_dur = max((c["end_s"] for c in global_cues), default=0.0)
    master_html = _render_html("master", master_dur, [
        {**c, "local_start": c["start_s"], "local_end": c["end_s"]} for c in global_cues
    ], master_offsets, theme)
    master_path = project_dir / "hyperframes" / "index.html"
    master_path.parent.mkdir(parents=True, exist_ok=True)
    master_path.write_text(master_html)

    # The gate-facing contract. Strip the html-only local_* fields.
    cuelist = {"cues": [
        {k: v for k, v in c.items() if k not in ("local_start", "local_end")}
        for c in global_cues
    ]}
    (art).mkdir(parents=True, exist_ok=True)
    (art / "cuelist.json").write_text(json.dumps(cuelist, indent=2))

    return {
        "compiler_version": COMPILER_VERSION,
        "chapters": len(chapters),
        "chapter_html": [c["html_path"] for c in chapters],
        "master_html": str(master_path),
        "cuelist": str(art / "cuelist.json"),
        "cue_count": len(global_cues),
        "primitives_used": sorted({c["kind"] for c in global_cues}),
        "scene_graphs": sorted({bid for ch in chapters for bid in ch.get("scene_graphs", [])}),
    }


def _load_optional(path: Path) -> Optional[dict]:
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def _main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="midnight_magnates.compiler")
    ap.add_argument("--project", required=True)
    args = ap.parse_args(argv)
    try:
        summary = compile_project(Path(args.project))
    except CompileError as exc:
        print("COMPILE FAILED: {0}".format(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
