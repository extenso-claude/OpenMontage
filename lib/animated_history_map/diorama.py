"""Diorama engine — the medium-tier "simple 3D bird's-eye with action".

The channel's signature: zoom from the macro map into a simple HTML/CSS/GSAP
2.5D scene where sprite "actors" move along paths past buildings, under a virtual
camera. Built in HTML (the proven strength), NOT Three.js. A diorama can be
GEO-GROUNDED on a real, factually-correct map shape (actor paths + building
footprints given as lat/lon and projected to pixels via the same mapkit
projection the basemap uses) OR stand on its own terrain.

This module emits TWO things, both load-bearing:
  1. render_html(scene)  -> a HyperFrames-valid composition (tilted ground plane,
     billboarded props/actors, GSAP-animated motion + virtual camera). Same
     clip/timeline contract as the compiler, so it slots into the render path.
  2. build_scene_graph(scene) -> a physics-checkable model: every actor's bbox
     sampled over time along its path (+ heading + net travel), every prop's
     footprint, the frame bounds. THIS is what qa_physics consumes to guarantee
     "objects don't pass through each other / off the map unless intended."

We don't simulate physics; we make geometry explicit and checkable.

Scene spec (input) shape:
    {"scene_id","duration_s","fps"?:12,
     "ground":{"tilt_deg"?:55,"width"?:1920,"height"?:1080,"bg"?:"#hex"|path,
               "geo"?:{"map_info":{...mapkit projection...}}},
     "props":[{"id","kind","layer"?:int,"label"?,"walkable"?:false,
               "footprint":{"x","y","w","h"} | "geo_footprint":{"lat","lon","w","h"}}],
     "actors":[{"id","kind","size":{"w","h"},"layer"?:int,"facing"?:"left"|"right",
                "facing_follows_path"?:true,"can_overlap"?:[ids],"sprite"?:path,
                "path":[{"t","x","y"}] | "geo_path":[{"t","lat","lon"}]}],
     "camera"?:[{"t","x"?,"y"?,"zoom"?}]}

CLI:
    python -m lib.animated_history_map.diorama --scene s.json --out-html out.html --out-graph g.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lib.animated_history_map import __version__  # noqa: E402

DIORAMA_VERSION = "animated_history_map.diorama@{0}".format(__version__)
DEFAULT_FPS = 12
DEFAULT_TILT = 55.0


class DioramaError(Exception):
    """A diorama scene cannot be built (bad geometry / unresolvable geo)."""


# --------------------------------------------------------------------------- #
# geo grounding
# --------------------------------------------------------------------------- #
def _geo_to_px(lat: float, lon: float, map_info: dict) -> Tuple[float, float]:
    from lib import mapkit_subjects  # local import: only needed for geo-grounded scenes
    x, y = mapkit_subjects.latlon_to_local_pixel(lat, lon, map_info)
    return float(x), float(y)


def _resolve_path(actor: dict, map_info: Optional[dict]) -> List[dict]:
    if "path" in actor:
        pts = actor["path"]
    elif "geo_path" in actor:
        if not map_info:
            raise DioramaError("actor {0!r} has geo_path but ground.geo.map_info is missing".format(actor.get("id")))
        pts = []
        for wp in actor["geo_path"]:
            x, y = _geo_to_px(wp["lat"], wp["lon"], map_info)
            pts.append({"t": wp["t"], "x": x, "y": y})
    else:
        raise DioramaError("actor {0!r} has neither path nor geo_path".format(actor.get("id")))
    pts = sorted(pts, key=lambda p: p["t"])
    if len(pts) < 2:
        raise DioramaError("actor {0!r} path needs >= 2 waypoints".format(actor.get("id")))
    return pts


def _resolve_footprint(prop: dict, map_info: Optional[dict]) -> dict:
    if "footprint" in prop:
        return dict(prop["footprint"])
    if "geo_footprint" in prop:
        if not map_info:
            raise DioramaError("prop {0!r} has geo_footprint but no map_info".format(prop.get("id")))
        gf = prop["geo_footprint"]
        cx, cy = _geo_to_px(gf["lat"], gf["lon"], map_info)
        w, h = float(gf["w"]), float(gf["h"])
        return {"x": cx - w / 2.0, "y": cy - h / 2.0, "w": w, "h": h}
    raise DioramaError("prop {0!r} has neither footprint nor geo_footprint".format(prop.get("id")))


# --------------------------------------------------------------------------- #
# scene graph (physics-checkable)
# --------------------------------------------------------------------------- #
def _interp(pts: List[dict], t: float) -> Tuple[float, float]:
    if t <= pts[0]["t"]:
        return pts[0]["x"], pts[0]["y"]
    if t >= pts[-1]["t"]:
        return pts[-1]["x"], pts[-1]["y"]
    for a, b in zip(pts, pts[1:]):
        if a["t"] <= t <= b["t"]:
            span = (b["t"] - a["t"]) or 1e-9
            f = (t - a["t"]) / span
            return a["x"] + f * (b["x"] - a["x"]), a["y"] + f * (b["y"] - a["y"])
    return pts[-1]["x"], pts[-1]["y"]


def _layer(obj: dict, default: int) -> int:
    v = obj.get("layer", default)
    return int(v) if isinstance(v, int) and not isinstance(v, bool) else default


def build_scene_graph(scene: dict) -> dict:
    ground = scene.get("ground", {}) or {}
    map_info = (ground.get("geo") or {}).get("map_info")
    bounds = {"w": int(ground.get("width", 1920)), "h": int(ground.get("height", 1080))}
    fps = int(scene.get("fps", DEFAULT_FPS))
    dt = 1.0 / fps

    props_out = []
    for prop in scene.get("props", []) or []:
        props_out.append({
            "id": prop["id"],
            "layer": _layer(prop, 1),
            "walkable": bool(prop.get("walkable", False)),
            "footprint": _resolve_footprint(prop, map_info),
        })

    actors_out = []
    for actor in scene.get("actors", []) or []:
        pts = _resolve_path(actor, map_info)
        size = actor.get("size", {"w": 80, "h": 80})
        w, h = float(size["w"]), float(size["h"])
        t0, t1 = pts[0]["t"], pts[-1]["t"]
        samples = []
        n = max(2, int(round((t1 - t0) * fps)) + 1)
        prev = None
        for i in range(n):
            t = min(t1, t0 + i * dt)
            cx, cy = _interp(pts, t)
            heading = None
            if prev is not None:
                dx, dy = cx - prev[0], cy - prev[1]
                if abs(dx) > 1e-6 or abs(dy) > 1e-6:
                    heading = math.degrees(math.atan2(dy, dx))
            samples.append({
                "t": round(t, 3),
                "cx": round(cx, 2), "cy": round(cy, 2),
                "bbox": {"x": round(cx - w / 2, 2), "y": round(cy - h / 2, 2), "w": w, "h": h},
                "heading_deg": (round(heading, 1) if heading is not None else None),
            })
            prev = (cx, cy)
        actors_out.append({
            "id": actor["id"],
            "layer": _layer(actor, 2),
            "facing": actor.get("facing"),
            "facing_follows_path": bool(actor.get("facing_follows_path", True)),
            "can_overlap": list(actor.get("can_overlap", []) or []),
            "net_dx": round(pts[-1]["x"] - pts[0]["x"], 2),
            "net_dy": round(pts[-1]["y"] - pts[0]["y"], 2),
            "samples": samples,
        })

    return {
        "scene_id": scene["scene_id"],
        "diorama_version": DIORAMA_VERSION,
        "bounds": bounds,
        "fps": fps,
        "props": props_out,
        "actors": actors_out,
    }


# --------------------------------------------------------------------------- #
# HTML render (HyperFrames-valid 2.5D)
# --------------------------------------------------------------------------- #
def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


_HEAD = """<!doctype html>
<html lang="en" data-resolution="landscape">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<meta name="compiler-version" content="{ver}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  html,body {{ width:1920px; height:1080px; margin:0; padding:0; overflow:hidden; background:{bg}; }}
  #stage {{ position:absolute; inset:0; perspective:1200px; perspective-origin:50% 38%; }}
  #camera {{ position:absolute; inset:0; transform-style:preserve-3d; }}
  #ground {{ position:absolute; left:0; top:0; transform-origin:50% 50%;
             transform: rotateX({tilt}deg); transform-style:preserve-3d; }}
  .billboard {{ position:absolute; transform: rotateX(-{tilt}deg); transform-origin:50% 100%; }}
  .prop {{ background:rgba(20,26,40,0.92); border:1px solid var(--accent); border-radius:3px;
           box-shadow:0 14px 26px rgba(0,0,0,0.55); color:#cfc59a; font:13px Georgia,serif;
           display:flex; align-items:flex-end; justify-content:center; padding-bottom:4px; }}
  .actor {{ background:radial-gradient(circle at 50% 40%, var(--accent), #6a5320);
            border-radius:50% 50% 45% 45%; box-shadow:0 8px 14px rgba(0,0,0,0.5); }}
  .actor::after {{ content:""; position:absolute; left:10%; right:10%; bottom:-10px; height:8px;
                   background:rgba(0,0,0,0.35); border-radius:50%; filter:blur(3px); }}
</style>
</head>
<body>
<div id="stage" class="clip" data-composition-id="{cid}" data-start="0" data-duration="{dur:.3f}"
     data-width="1920" data-height="1080" data-track-index="0" style="--accent:{accent};">
  <div id="camera">
    <div id="ground" class="clip" data-start="0" data-duration="{dur:.3f}" data-track-index="1"
         style="width:{gw}px; height:{gh}px; background:{ground_bg};">
{scene_html}
    </div>
  </div>
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


def render_html(scene: dict, theme: Optional[dict] = None) -> str:
    theme = theme or {}
    palette = theme.get("palette_master") or {}
    accent = palette.get("primary_accent", "#c9a84c")
    ground = scene.get("ground", {}) or {}
    tilt = float(ground.get("tilt_deg", DEFAULT_TILT))
    gw, gh = int(ground.get("width", 1920)), int(ground.get("height", 1080))
    ground_bg = ground.get("bg", "#10151f")
    dur = float(scene["duration_s"])
    graph = build_scene_graph(scene)

    html_parts: List[str] = []
    tl_parts: List[str] = []

    for prop in graph["props"]:
        fp = prop["footprint"]
        label = next((p.get("label", "") for p in scene.get("props", []) if p["id"] == prop["id"]), "")
        html_parts.append(
            '      <div class="clip prop billboard" id="prop_{id}" data-start="0" data-duration="{d:.3f}" '
            'data-track-index="{t}" style="left:{x}px; top:{y}px; width:{w}px; height:{h}px;">{lbl}</div>'.format(
                id=_esc(prop["id"]), d=dur, t=prop["layer"] + 2,
                x=round(fp["x"]), y=round(fp["y"]), w=round(fp["w"]), h=round(fp["h"]), lbl=_esc(label)))

    for actor in graph["actors"]:
        samples = actor["samples"]
        s0, s1 = samples[0], samples[-1]
        span = max(0.001, s1["t"] - s0["t"])
        w, h = s0["bbox"]["w"], s0["bbox"]["h"]
        face = -1 if (actor.get("facing") == "left" or (actor["facing"] is None and actor["net_dx"] < 0)) else 1
        aid = "actor_{0}".format(_esc(actor["id"]))
        html_parts.append(
            '      <div class="clip actor billboard" id="{id}" data-start="{s:.3f}" data-duration="{d:.3f}" '
            'data-track-index="{t}" style="left:{x}px; top:{y}px; width:{w}px; height:{h}px; '
            'transform: rotateX(-{tilt}deg) scaleX({f});"></div>'.format(
                id=aid, s=s0["t"], d=span, t=actor["layer"] + 2,
                x=round(s0["bbox"]["x"]), y=round(s0["bbox"]["y"]), w=round(w), h=round(h), tilt=tilt, f=face))
        # Author the motion as left/top keyframes (compiler-authored easing — no freehand).
        tl_parts.append('  gsap.set("#{id}", {{left:{x}, top:{y}}});'.format(
            id=aid, x=round(s0["bbox"]["x"]), y=round(s0["bbox"]["y"])))
        # one tween per source waypoint segment, linear (constant speed)
        src = _resolve_path(next(a for a in scene["actors"] if a["id"] == actor["id"]),
                            (ground.get("geo") or {}).get("map_info"))
        for a, b in zip(src, src[1:]):
            seg = max(0.001, b["t"] - a["t"])
            tl_parts.append('  tl.to("#{id}", {{left:{x}, top:{y}, duration:{dd:.3f}, ease:"none"}}, {at:.3f});'.format(
                id=aid, x=round(b["x"] - w / 2), y=round(b["y"] - h / 2), dd=seg, at=a["t"]))

    # Virtual camera keyframes (pan/zoom).
    cam = scene.get("camera") or []
    for kf in cam:
        x = -float(kf.get("x", 0))
        y = -float(kf.get("y", 0))
        zoom = float(kf.get("zoom", 1))
        tl_parts.append('  tl.to("#camera", {{x:{x}, y:{y}, scale:{z}, duration:0.8, ease:"power2.inOut"}}, {at:.3f});'.format(
            x=round(x), y=round(y), z=zoom, at=float(kf.get("t", 0))))

    return _HEAD.format(
        ver=DIORAMA_VERSION, bg="#05080f", tilt=tilt, cid=_esc(scene["scene_id"]),
        dur=dur, accent=accent, gw=gw, gh=gh, ground_bg=ground_bg,
        scene_html="\n".join(html_parts), tl_js="\n".join(tl_parts))


def emit(scene: dict, out_html: Path, out_graph: Path, theme: Optional[dict] = None) -> dict:
    out_html = Path(out_html)
    out_graph = Path(out_graph)
    graph = build_scene_graph(scene)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_graph.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(render_html(scene, theme))
    out_graph.write_text(json.dumps(graph, indent=2))
    return {"scene_id": scene["scene_id"], "html": str(out_html), "scene_graph": str(out_graph),
            "actors": len(graph["actors"]), "props": len(graph["props"]),
            "geo_grounded": bool((scene.get("ground", {}).get("geo") or {}).get("map_info"))}


def _main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="animated_history_map.diorama")
    ap.add_argument("--scene", required=True)
    ap.add_argument("--out-html", required=True)
    ap.add_argument("--out-graph", required=True)
    args = ap.parse_args(argv)
    scene = json.loads(Path(args.scene).read_text())
    try:
        summary = emit(scene, Path(args.out_html), Path(args.out_graph))
    except DioramaError as exc:
        print("DIORAMA FAILED: {0}".format(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
