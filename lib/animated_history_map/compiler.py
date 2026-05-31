"""The compiler — storyboard JSON is the ONLY path to a HyperFrames scene.

This is the keystone of the no-monolith guarantee. A chapter storyboard (valid
against animated_history_map_storyboard.schema.json) is the sole input; the
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

CLI:  python -m lib.animated_history_map.compiler --project <dir>
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
from lib.animated_history_map import __version__  # noqa: E402

COMPILER_VERSION = "animated_history_map.compiler@{0}".format(__version__)

# --- primitive families (drive bbox + track + whether it's a visual element) ---
AUDIO_PRIMS = {"music_swell", "music_drop", "sfx_accent", "sfx_ambient_in", "sfx_ambient_out"}
CARD_PRIMS = {"character_card", "character_card_pop", "source_citation", "etymology_card", "concept_diagram"}
MAP_ANCHORED_PRIMS = {"pin_drop", "pin_dimming", "pin_pulse_breath", "map_sprite", "map_label", "label_cluster"}
FULLFRAME_PRIMS = {"story_dive", "panel_archival", "panel_illustration", "panel_quote", "document_overlay", "clip_archival"}
UI_CORNER_PRIMS = {"time_stamp", "year_card_update", "chapter_subject_badge_swap", "chapter_timeline_update"}
AUDIO_TRACK_INDEX = 20  # matches hf_coverage_qa convention (excluded from visual coverage)

# Layout slots (px, top-left origin, 1920x1080) used for bbox computation.
SLOT_LOWER_LEFT = {"x": 80, "y": 740, "w": 560, "h": 280}     # character cards
SLOT_LOWER_THIRD = {"x": 360, "y": 880, "w": 1200, "h": 160}  # source citations
SLOT_TOP_RIGHT = {"x": 1560, "y": 48, "w": 312, "h": 96}      # year/UI corner
FULL_FRAME = {"x": 0, "y": 0, "w": 1920, "h": 1080}
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
    is_light = basemap_filter in LIGHT_BASEMAP_FILTERS

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
    bg = pm.get("ui_dark", "#080c16")
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
def _whisper_index(whisper: Optional[dict]) -> List[Tuple[str, float]]:
    """Return [(word_lower, start_s), ...] from a Whisper transcript, or []."""
    if not whisper:
        return []
    words = whisper.get("words")
    out: List[Tuple[str, float]] = []
    if isinstance(words, list):
        for w in words:
            if isinstance(w, dict) and "word" in w and "start" in w:
                out.append((str(w["word"]).strip().lower(), float(w["start"])))
    return out


def _resolve_anchor(anchor: dict, words: List[Tuple[str, float]], where: str) -> float:
    """Resolve an anchor to absolute (chapter-local) seconds.

    Prefer the Whisper word time of anchor.phrase; fall back to
    anchor.fallback_absolute_s. A beat with neither is a hard CompileError —
    an un-timeable beat must never silently get t=0.
    """
    offset = float(anchor.get("offset_ms", 0)) / 1000.0
    phrase = str(anchor.get("phrase", "")).strip().lower()
    if phrase and words:
        toks = phrase.split()
        for i in range(len(words) - len(toks) + 1):
            if [w for w, _ in words[i:i + len(toks)]] == toks:
                return max(0.0, words[i][1] + offset)
    fb = anchor.get("fallback_absolute_s")
    if isinstance(fb, (int, float)) and not isinstance(fb, bool):
        return max(0.0, float(fb) + offset)
    raise CompileError(
        "{0}: anchor phrase {1!r} not found in transcript and no fallback_absolute_s".format(where, phrase)
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
    if prim in CARD_PRIMS:
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
    return None  # effects / transitions / regions / cameras / atmospherics: no bbox


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
               local_start: float, local_end: float, positions: Optional[dict]) -> dict:
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
    return cue


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
                    whisper: Optional[dict], out_html: Path) -> dict:
    """Validate + compile one chapter. Returns {chapter_id, cues, html_path, duration_s}."""
    try:
        validate_artifact("animated_history_map_storyboard", storyboard)
    except jsonschema.ValidationError as exc:
        loc = "/".join(str(p) for p in exc.absolute_path) or "<root>"
        raise CompileError("storyboard invalid at {0}: {1}".format(loc, exc.message)) from exc
    _enforce_experimental_cap(storyboard)

    chapter_id = storyboard["chapter_id"]
    duration_s = float(storyboard["duration_s"])
    words = _whisper_index(whisper)

    cues: List[dict] = []
    for ph in storyboard["phases"]:
        for beat in ph["beats"]:
            bid = beat["beat_id"]
            where = "{0}/{1}".format(chapter_id, bid)
            start = _resolve_anchor(beat["start_anchor"], words, where + ".start")
            end = _resolve_anchor(beat["end_anchor"], words, where + ".end")
            if end <= start:
                raise CompileError("{0}: end ({1}) <= start ({2})".format(where, end, start))
            for idx, la in enumerate(beat["layers"]):
                cues.append(_build_cue(chapter_id, bid, idx, la, start, end, positions))

    offsets = {c["id"]: c["local_start"] for c in cues}
    # Ground the scene on its rendered basemap (chapter HTML lives at
    # hyperframes/chapter_<id>/index.html → ../../assets/maps/<extent>.png).
    extent = ((positions or {}).get("map_info") or {}).get("extent_id")
    basemap_rel = "../../assets/maps/{0}.png".format(extent) if extent else None
    html = _render_html(chapter_id, duration_s, cues, offsets, theme, basemap_rel=basemap_rel)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html)
    return {"chapter_id": chapter_id, "cues": cues, "html_path": str(out_html), "duration_s": duration_s,
            "vo_start_offset_in_master_s": float(storyboard.get("vo_start_offset_in_master_s", 0.0))}


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

    chapters = []
    for p in sb_paths:
        sb = json.loads(p.read_text())
        out_html = project_dir / "hyperframes" / "chapter_{0}".format(sb.get("chapter_id", p.stem)) / "index.html"
        chapters.append(compile_chapter(sb, theme=theme, positions=positions, whisper=whisper, out_html=out_html))

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
    }


def _load_optional(path: Path) -> Optional[dict]:
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def _main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="animated_history_map.compiler")
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
