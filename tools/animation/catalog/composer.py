"""Composition writer — emits unique HTML per format using MM motion primitives.

Each format has a `scene_recipe` (a small Python function) that takes the
manifest entry, the base-image path (or None for procedural), the version
(hyperframes|recraft), and a duration. It returns:
    {"scene_css": "...", "scene_html": "...", "tl_js": "...", "deco": {...}}

The composer then wraps that with HF-compatible <html>/<head>/<body>/<script>
boilerplate and writes the HTML.

Each recipe SHOULD:
  - Build a unique HTML stage tailored to the format's narrative.
  - Use MM.* primitives in `tl_js` to author the timeline.
  - Specify decorative overlays (light_shaft, vignette, grain, etc.).
  - Provide a #title and optional #subtitle if appropriate.
  - Add a `.fmt-label` so renders are self-identifying.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional


HEAD_TMPL = """<!doctype html>
<html lang="en" data-resolution="landscape">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Georgia&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/tokens.css" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/MotionPathPlugin.min.js"></script>
<script src="../assets/shared/mm_motion.js"></script>
<style>
  html, body {{ width:1920px; height:1080px; margin:0; padding:0; background:#080c16; overflow:hidden; font-family:Georgia,serif; color:#f5f0e4; }}
  #root {{ position:absolute; inset:0; }}
  .clip {{ position:absolute; }}

  /* Universal title styling */
  .title {{ position:absolute; left:50%; transform:translateX(-50%); top:6.5%;
            font-family:'Playfair Display',Georgia,serif; font-weight:700;
            color:#c9a84c; font-size:42px; letter-spacing:6px;
            text-shadow:0 0 18px rgba(8,12,22,0.85), 0 0 4px rgba(0,0,0,0.9);
            opacity:0; z-index:80; }}
  .subtitle {{ position:absolute; left:50%; transform:translateX(-50%); top:12%;
               font-family:Georgia,serif; font-style:italic;
               color:#e8d6a8; font-size:20px; letter-spacing:1.5px;
               opacity:0; text-shadow:0 0 12px rgba(8,12,22,0.85); z-index:80; }}
  .fmt-label {{ position:absolute; left:42px; bottom:36px; z-index:100;
                font-family:'Courier New',monospace; font-size:13px; letter-spacing:2px;
                color:#c9a84c; opacity:0.55; text-shadow:0 0 8px rgba(0,0,0,0.95); }}

  /* Universal Hero (for image-led formats) — anchored at 0,0 with 100%x100% + cover,
     so the image always fills the canvas with center crop. Ken-burns wraps it. */
  .hero {{ position:absolute; top:0; left:0; width:100%; height:100%;
           object-fit:cover; object-position:center center;
           transform-origin:center center;
           filter: brightness(0.78) saturate(0.85) contrast(1.10) hue-rotate(-6deg); }}

  /* Star + comet defaults */
  .star {{ fill:#f5f0e4; }}
  .star-bright {{ fill:#fff7d9; filter: drop-shadow(0 0 4px rgba(255,247,217,0.7)); }}
  .comet-path {{ fill:none; stroke:#fff7d9; stroke-width:2; stroke-linecap:round;
                 filter: drop-shadow(0 0 6px rgba(255,247,217,0.9)); }}
  .comet-head {{ fill:#fff7d9; filter: drop-shadow(0 0 8px rgba(255,247,217,1)); }}

  /* Generic particle (firefly / dust / mote) */
  .firefly {{ position:absolute; width:6px; height:6px; border-radius:50%;
              background:#f5e0a8; box-shadow:0 0 16px 5px rgba(245,224,168,0.7);
              opacity:0; z-index:50; }}
  .dust-mote {{ position:absolute; width:4px; height:4px; border-radius:50%;
                background:#e8d6a8; box-shadow:0 0 10px 3px rgba(232,214,168,0.55);
                opacity:0; z-index:50; }}

  /* Generic glow patch */
  .glow {{ position:absolute; border-radius:8px; pointer-events:none;
           mix-blend-mode:screen; opacity:0; z-index:30; }}

  /* Per-scene CSS injected here */
{scene_css}
</style>
</head>
<body>
"""

ROOT_OPEN = """<div id="root" class="clip" data-composition-id="{cid}"
     data-start="0" data-duration="{dur}" data-width="1920" data-height="1080" data-track-index="0">
"""

ROOT_CLOSE = """
  <!-- Decorative overlays -->
{deco_html}

  <div class="fmt-label">{label}</div>
</div>

<script>
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused: true }});
  const D = {dur};
  MM.sceneFade(tl, {{ duration: D }});
{tl_js}
  window.__timelines["{cid}"] = tl;
</script>
</body>
</html>
"""


# Default starfield SVG markup — 37 stars across the upper canvas
STARFIELD_SVG = '''<svg class="clip" id="starfield" width="1920" height="540" viewBox="0 0 1920 540" style="left:0; top:0; opacity:0;">
  <g>
    <circle class="star" cx="80" cy="60" r="1.1"/><circle class="star" cx="170" cy="130" r="1.4"/>
    <circle class="star-bright" cx="240" cy="80" r="1.6"/><circle class="star" cx="310" cy="220" r="1.0"/>
    <circle class="star" cx="395" cy="50" r="1.3"/><circle class="star-bright" cx="450" cy="160" r="1.8"/>
    <circle class="star" cx="525" cy="100" r="1.1"/><circle class="star" cx="600" cy="200" r="1.2"/>
    <circle class="star-bright" cx="690" cy="40" r="1.5"/><circle class="star" cx="760" cy="180" r="1.1"/>
    <circle class="star" cx="830" cy="80" r="1.3"/><circle class="star-bright" cx="910" cy="140" r="1.7"/>
    <circle class="star" cx="990" cy="60" r="1.0"/><circle class="star" cx="1060" cy="220" r="1.2"/>
    <circle class="star-bright" cx="1140" cy="110" r="1.6"/><circle class="star" cx="1220" cy="40" r="1.1"/>
    <circle class="star" cx="1290" cy="170" r="1.4"/><circle class="star" cx="1370" cy="90" r="1.2"/>
    <circle class="star-bright" cx="1450" cy="200" r="1.8"/><circle class="star" cx="1530" cy="120" r="1.1"/>
    <circle class="star" cx="1610" cy="60" r="1.3"/><circle class="star" cx="1690" cy="180" r="1.2"/>
    <circle class="star-bright" cx="1770" cy="100" r="1.6"/><circle class="star" cx="1850" cy="40" r="1.0"/>
    <circle class="star" cx="125" cy="280" r="1.2"/><circle class="star" cx="380" cy="320" r="1.1"/>
    <circle class="star" cx="640" cy="380" r="1.3"/><circle class="star-bright" cx="900" cy="300" r="1.5"/>
    <circle class="star" cx="1180" cy="350" r="1.1"/><circle class="star" cx="1450" cy="320" r="1.2"/>
    <circle class="star" cx="1720" cy="280" r="1.3"/>
  </g>
</svg>'''

COMET_SVG = '''<svg class="clip" id="comet" width="1920" height="500" viewBox="0 0 1920 500" style="left:0; top:0; pointer-events:none;">
  <path id="comet-trail" class="comet-path" d="M -50 -50 Q 400 50 900 200 T 2000 450" stroke-dasharray="800" stroke-dashoffset="800"/>
  <circle id="comet-dot" class="comet-head" cx="-50" cy="-50" r="3.5"/>
</svg>'''


def particles(class_name: str, count: int, area: tuple[float, float, float, float] = (10, 50, 90, 95), seed: int = 1) -> str:
    """Generate N particle divs deterministically inside area (lx, ty, rx, by) in %.

    Returns HTML with class="firefly" (or class_name). Caller animates via MM.particleDrift.
    """
    lx, ty, rx, by = area
    out = []
    # Mulberry32 (Python port)
    s = seed * 9999 + 7
    def rng():
        nonlocal s
        s = (s + 0x6D2B79F5) & 0xFFFFFFFF
        t = s
        t = (t ^ (t >> 15)) * (t | 1) & 0xFFFFFFFF
        t ^= t + (t ^ (t >> 7)) * (t | 61) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 0xFFFFFFFF
    for i in range(count):
        px = lx + rng() * (rx - lx)
        py = ty + rng() * (by - ty)
        out.append(f'<div class="{class_name}" id="{class_name}-{i}" style="left:{px:.2f}%; top:{py:.2f}%;"></div>')
    return "\n  ".join(out)


def vignette_html(grain: bool = True, shaft: bool = True) -> str:
    parts = []
    if shaft:
        parts.append('  <div class="light-shaft"></div>')
    parts.append('  <div class="vignette"></div>')
    if grain:
        parts.append('  <div class="grain"></div>')
    return "\n".join(parts)


def write_composition(
    out_path: Path,
    *,
    cid: str,
    label: str,
    dur: float,
    scene_css: str,
    scene_html: str,
    tl_js: str,
    deco_html: Optional[str] = None,
) -> Path:
    """Write a complete HTML composition with universal scaffolding."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deco_html = deco_html if deco_html is not None else vignette_html()
    parts = [
        HEAD_TMPL.format(scene_css=scene_css),
        ROOT_OPEN.format(cid=cid, dur=dur),
        scene_html,
        ROOT_CLOSE.format(cid=cid, dur=dur, tl_js=tl_js, deco_html=deco_html, label=label),
    ]
    out_path.write_text("\n".join(parts))
    return out_path
