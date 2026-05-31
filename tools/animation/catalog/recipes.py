"""Lean per-format composition builder for the 99-format test.

Each builder returns: dict with scene_html, tl_js, scene_css(optional), deco_html(optional).

Format dispatch happens in `build_format(entry, version, image_path)`.
Each format has an entry in BUILDERS that maps format number → builder function.

Heavy reuse of:
  - MM.* primitives (in assets/shared/mm_motion.js)
  - Procedural scene helpers (proc_night_sky, proc_paper_backdrop, etc.)
  - particles() generator
"""
from __future__ import annotations
from typing import Optional, Callable
from tools.animation.catalog.composer import STARFIELD_SVG, COMET_SVG, particles


# ===========================================================
# Reusable procedural scene parts
# ===========================================================

def night_sky() -> str:
    return '''<div class="sky" style="position:absolute; inset:0;
      background:
        radial-gradient(ellipse 1800px 700px at 50% 95%, rgba(201,168,76,0.18), transparent 70%),
        linear-gradient(180deg, #050913 0%, #0a1024 38%, #0e1530 72%, #1a1820 100%);"></div>'''


def night_ground() -> str:
    return '''<div class="mountains" style="position:absolute; left:-2%; right:-2%; bottom:18%; height:14%;
      background: linear-gradient(180deg, transparent 0%, #0a0e1d 60%, #0a0e1d 100%);
      clip-path: polygon(0% 100%, 0% 60%, 6% 45%, 12% 55%, 19% 30%, 26% 45%, 33% 25%, 40% 40%, 50% 18%, 60% 32%, 68% 50%, 76% 35%, 84% 50%, 92% 30%, 100% 50%, 100% 100%);"></div>
      <div class="ground" style="position:absolute; left:0; right:0; bottom:0; height:18%;
      background: linear-gradient(180deg, #1a1410 0%, #0e0a08 80%, #060403 100%);
      box-shadow: inset 0 24px 60px rgba(0,0,0,0.7);"></div>'''


def velvet_table() -> str:
    return '''<div style="position:absolute; inset:0;
      background:
        radial-gradient(ellipse 1400px 1000px at 50% 50%, #1a0e10 0%, #0c0608 60%, #050203 100%),
        linear-gradient(180deg, #100608, #050203);"></div>
      <div style="position:absolute; inset:0; opacity:0.16; mix-blend-mode:overlay;
      background-image: url(&quot;data:image/svg+xml;utf8,&lt;svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'&gt;&lt;filter id='v'&gt;&lt;feTurbulence type='fractalNoise' baseFrequency='1.2' numOctaves='2'/&gt;&lt;/filter&gt;&lt;rect width='100%' height='100%' filter='url(%23v)' opacity='0.4'/&gt;&lt;/svg&gt;&quot;);"></div>'''


def desk_top() -> str:
    return '''<div style="position:absolute; inset:0;
      background: radial-gradient(ellipse 1700px 800px at 50% 55%, #1c1612 0%, #0c0a09 70%, #060911 100%);"></div>'''


def parchment_paper(left="14%", right="14%", top="16%", bottom="14%",
                    headline="LAST WILL & TESTAMENT", body_lines=None) -> str:
    """Cream parchment with a headline + ruled body lines + signature line + wax seal.

    body_lines: list of strings; if None, uses three lorem-ipsum-style scribble lines.
    Includes a faint signature scribble and a red wax seal at bottom-right.
    """
    body_lines = body_lines or [
        "I, EZEKIEL P. ASHFORD, being of sound mind",
        "do hereby bequeath the entirety of my estate",
        "to the trustees herein named — in perpetuity.",
    ]
    body_html = "".join(
        f'<div style="position:absolute; left:8%; right:8%; top:{38+i*9}%; '
        f'border-bottom:1px solid #5a4830; height:2.2em; '
        f'font-family:Georgia,serif; font-style:italic; font-size:28px; color:#3a2410; '
        f'overflow:hidden; white-space:nowrap;">{line}</div>'
        for i, line in enumerate(body_lines)
    )
    return f'''<div id="doc" class="clip" style="position:absolute; left:{left}; right:{right}; top:{top}; bottom:{bottom};
      background: radial-gradient(ellipse at 30% 30%, rgba(255,255,255,0.06), transparent 60%),
                  linear-gradient(180deg, #e0d4ac 0%, #c4b387 50%, #a89461 100%);
      border-radius:4px; box-shadow:0 24px 60px rgba(0,0,0,0.7);
      transform: rotateX(5deg); overflow:hidden;">
      <!-- Aging texture -->
      <div style="position:absolute; inset:0; opacity:0.4; mix-blend-mode:multiply; pointer-events:none;
        background-image: url(&quot;data:image/svg+xml;utf8,&lt;svg xmlns='http://www.w3.org/2000/svg' width='400' height='400'&gt;&lt;filter id='r'&gt;&lt;feTurbulence type='fractalNoise' baseFrequency='0.6' numOctaves='3'/&gt;&lt;feColorMatrix values='0 0 0 0 0.55  0 0 0 0 0.48  0 0 0 0 0.30  0 0 0 0.30 0'/&gt;&lt;/filter&gt;&lt;rect width='100%' height='100%' filter='url(%23r)'/&gt;&lt;/svg&gt;&quot;);"></div>
      <!-- Headline -->
      <div style="position:absolute; left:0; right:0; top:10%; text-align:center;
        font-family:Playfair Display,serif; font-weight:900; font-size:46px; color:#1a0e08;
        letter-spacing:6px; text-shadow:0 1px 0 rgba(255,255,255,0.2);">{headline}</div>
      <div style="position:absolute; left:0; right:0; top:24%; text-align:center;
        font-family:Georgia,serif; font-style:italic; font-size:18px; color:#3a2410;">~~~</div>
      <!-- Body lines -->
      {body_html}
      <!-- Signature -->
      <svg style="position:absolute; left:48%; bottom:14%; width:280px; height:60px;" viewBox="0 0 280 60">
        <path d="M 10 40 Q 30 12 60 30 T 110 25 Q 140 18 160 40 T 220 30 Q 240 15 270 30" fill="none" stroke="#1a0e08" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <div style="position:absolute; left:10%; bottom:11%; width:30%; border-top:1px solid #5a4830;
        font-family:Georgia,serif; font-style:italic; font-size:14px; color:#5a4830; padding-top:4px;">signature, witness</div>
      <!-- Wax seal -->
      <div style="position:absolute; right:9%; bottom:8%; width:80px; height:80px;
        background: radial-gradient(circle at 35% 35%, #a82424 0%, #6a1010 60%, #3a0808 100%);
        border-radius:50%; box-shadow: 0 4px 12px rgba(0,0,0,0.6); transform: rotate(-12deg);
        display:flex; align-items:center; justify-content:center;
        font-family:Playfair Display,serif; font-weight:900; font-size:18px; color:#3a0808;">★</div>
      </div>'''


def mansion_silhouette(scale=1.0, bottom="18%") -> str:
    return f'''<svg style="position:absolute; left:50%; bottom:{bottom}; transform:translateX(-50%) scale({scale});
      width:760px; height:340px; filter:drop-shadow(0 20px 40px rgba(0,0,0,0.6));"
    viewBox="0 0 760 340">
    <rect x="80" y="120" width="600" height="200" fill="#0e0a08"/>
    <polygon points="60,120 380,40 700,120" fill="#1a0f08"/>
    <rect x="180" y="50" width="22" height="60" fill="#1a0f08"/>
    <rect x="560" y="50" width="22" height="60" fill="#1a0f08"/>
    <rect x="0" y="180" width="80" height="140" fill="#0e0a08"/>
    <rect x="680" y="180" width="80" height="140" fill="#0e0a08"/>
    <g fill="#e9b045" filter="drop-shadow(0 0 18px rgba(233,176,69,0.85))" class="mansion-window">
      <rect x="160" y="160" width="36" height="50"/>
      <rect x="240" y="160" width="36" height="50"/>
      <rect x="360" y="160" width="36" height="50"/>
      <rect x="440" y="160" width="36" height="50"/>
      <rect x="540" y="160" width="36" height="50"/>
    </g>
    <g fill="#1d130e">
      <rect x="160" y="230" width="36" height="50"/>
      <rect x="240" y="230" width="36" height="50"/>
      <rect x="360" y="230" width="36" height="50"/>
      <rect x="440" y="230" width="36" height="50"/>
      <rect x="540" y="230" width="36" height="50"/>
    </g>
    <rect x="350" y="240" width="60" height="80" fill="#d8a138"
      filter="drop-shadow(0 0 28px rgba(216,161,56,0.95))" class="mansion-door"/>
    </svg>'''


def train_silhouette() -> str:
    """Train + 3 men silhouettes for archival photo formats."""
    return '''<svg style="position:absolute; left:50%; bottom:14%; transform:translateX(-50%);
      width:1200px; height:520px; filter:drop-shadow(0 24px 40px rgba(0,0,0,0.6));"
      viewBox="0 0 1200 520">
      <!-- Train body -->
      <rect x="60" y="280" width="900" height="160" fill="#0e0a08"/>
      <!-- Smoke stack -->
      <rect x="180" y="180" width="60" height="100" fill="#0a0706"/>
      <ellipse cx="210" cy="200" rx="60" ry="14" fill="#0a0706"/>
      <!-- Cab -->
      <rect x="120" y="230" width="200" height="50" fill="#0e0a08"/>
      <rect x="160" y="240" width="40" height="30" fill="#e9b045" filter="drop-shadow(0 0 12px rgba(233,176,69,0.7))"/>
      <!-- Boiler -->
      <rect x="280" y="280" width="500" height="100" fill="#0e0a08"/>
      <circle cx="340" cy="330" r="30" fill="#1a0e08"/>
      <!-- Wheels -->
      <circle cx="200" cy="440" r="46" fill="#1a0e08" stroke="#0a0706" stroke-width="3"/>
      <circle cx="200" cy="440" r="20" fill="#0a0706"/>
      <circle cx="320" cy="440" r="46" fill="#1a0e08" stroke="#0a0706" stroke-width="3"/>
      <circle cx="320" cy="440" r="20" fill="#0a0706"/>
      <circle cx="600" cy="440" r="40" fill="#1a0e08" stroke="#0a0706" stroke-width="3"/>
      <circle cx="600" cy="440" r="18" fill="#0a0706"/>
      <circle cx="800" cy="440" r="40" fill="#1a0e08" stroke="#0a0706" stroke-width="3"/>
      <circle cx="800" cy="440" r="18" fill="#0a0706"/>
      <!-- Cowcatcher -->
      <polygon points="60,280 60,420 20,440 0,300" fill="#0a0706"/>
      <!-- Three men silhouettes in front -->
      <g fill="#050302">
        <!-- Man 1 (left) -->
        <ellipse cx="900" cy="360" rx="22" ry="28"/>
        <path d="M 870 460 L 870 380 Q 900 370 930 380 L 930 460 Z"/>
        <!-- Man 2 (middle) -->
        <ellipse cx="980" cy="350" rx="24" ry="30"/>
        <path d="M 944 460 L 944 374 Q 980 364 1016 374 L 1016 460 Z"/>
        <!-- Hat -->
        <rect x="958" y="316" width="44" height="14" rx="3"/>
        <ellipse cx="980" cy="330" rx="32" ry="6"/>
        <!-- Man 3 (right) -->
        <ellipse cx="1060" cy="360" rx="22" ry="28"/>
        <path d="M 1030 460 L 1030 380 Q 1060 370 1090 380 L 1090 460 Z"/>
      </g>
    </svg>'''


def record_player_silhouette() -> str:
    """Record player on a velvet shelf."""
    return '''<svg style="position:absolute; left:50%; bottom:18%; transform:translateX(-50%);
      width:720px; height:520px;" viewBox="0 0 720 520">
      <!-- Wooden base -->
      <rect x="80" y="320" width="560" height="160" fill="#3a2410" rx="6"/>
      <rect x="80" y="320" width="560" height="20" fill="#5a3820"/>
      <!-- Record turntable -->
      <circle cx="240" cy="400" r="100" fill="#1a0e08"/>
      <circle cx="240" cy="400" r="92" fill="#0e0606"/>
      <circle cx="240" cy="400" r="34" fill="#c9a84c"/>
      <circle cx="240" cy="400" r="6" fill="#1a0e08"/>
      <!-- Tonearm -->
      <line x1="380" y1="320" x2="280" y2="380" stroke="#c9a84c" stroke-width="6"/>
      <circle cx="380" cy="320" r="14" fill="#c9a84c"/>
      <!-- Horn -->
      <path d="M 400 250 Q 480 240 540 200 L 600 130 L 700 80 L 700 280 L 600 250 L 540 240 Q 480 270 400 280 Z" fill="#c9a84c"/>
      <path d="M 700 80 L 700 280 L 660 260 L 660 100 Z" fill="#8a6e23"/>
      <!-- Highlights -->
      <ellipse cx="200" cy="370" rx="40" ry="6" fill="rgba(255,255,255,0.05)"/>
    </svg>'''


def stained_glass_silhouette() -> str:
    """Gothic stained glass window."""
    return '''<svg style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
      width:560px; height:840px;" viewBox="0 0 560 840">
      <!-- Frame outer -->
      <path d="M 60 280 Q 280 40 500 280 L 500 800 L 60 800 Z" fill="#0a0706" stroke="#c9a84c" stroke-width="6"/>
      <!-- Glass panels -->
      <g stroke="#3a2410" stroke-width="2">
        <path d="M 80 280 Q 280 70 480 280 L 480 780 L 80 780 Z" fill="#4a6fa5"/>
        <path d="M 280 90 L 280 780" stroke-width="4"/>
        <path d="M 80 460 L 480 460" stroke-width="4"/>
        <!-- Top arch detail -->
        <path d="M 200 280 Q 280 200 360 280" fill="none"/>
        <!-- Central figure (silhouetted industrialist) -->
        <ellipse cx="280" cy="380" rx="40" ry="50" fill="#c9a84c" opacity="0.85"/>
        <path d="M 240 580 L 240 430 Q 280 410 320 430 L 320 580 Z" fill="#c9a84c" opacity="0.85"/>
        <!-- Scales of justice -->
        <line x1="240" y1="500" x2="320" y2="500" stroke="#c9a84c" stroke-width="3"/>
        <circle cx="240" cy="520" r="14" fill="#c9a84c" opacity="0.7"/>
        <circle cx="320" cy="540" r="14" fill="#c9a84c" opacity="0.9"/>
      </g>
    </svg>'''


def lecture_hall_silhouette() -> str:
    """Lecture hall with chalkboard."""
    return '''<svg style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
      width:1400px; height:720px;" viewBox="0 0 1400 720">
      <!-- Side walls (perspective) -->
      <path d="M 0 0 L 280 200 L 280 520 L 0 720 Z" fill="#0e0a08"/>
      <path d="M 1400 0 L 1120 200 L 1120 520 L 1400 720 Z" fill="#0e0a08"/>
      <!-- Floor -->
      <path d="M 280 520 L 1120 520 L 1400 720 L 0 720 Z" fill="#1a0e08"/>
      <!-- Chalkboard -->
      <rect x="320" y="80" width="760" height="380" fill="#1a201c" stroke="#1a0e08" stroke-width="14"/>
      <!-- Gas lamps on sides -->
      <rect x="240" y="240" width="14" height="60" fill="#c9a84c"/>
      <circle cx="247" cy="230" r="18" fill="#e9b045" filter="drop-shadow(0 0 14px rgba(233,176,69,0.7))"/>
      <rect x="1146" y="240" width="14" height="60" fill="#c9a84c"/>
      <circle cx="1153" cy="230" r="18" fill="#e9b045" filter="drop-shadow(0 0 14px rgba(233,176,69,0.7))"/>
      <!-- Desks (out-of-focus suggestion via shapes in foreground) -->
      <rect x="80" y="600" width="200" height="60" fill="#3a2410" opacity="0.5"/>
      <rect x="1120" y="600" width="200" height="60" fill="#3a2410" opacity="0.5"/>
    </svg>'''


def ballroom_silhouette() -> str:
    """Ballroom dance silhouettes."""
    return '''<svg style="position:absolute; left:50%; bottom:18%; transform:translateX(-50%);
      width:1400px; height:560px;" viewBox="0 0 1400 560">
      <!-- Floor (art-deco pattern) -->
      <rect x="0" y="400" width="1400" height="160" fill="#1a0e08"/>
      <pattern id="deco" patternUnits="userSpaceOnUse" width="80" height="80">
        <path d="M 0 0 L 40 40 L 80 0 M 0 80 L 40 40 L 80 80" stroke="#3a2410" stroke-width="1" fill="none"/>
      </pattern>
      <rect x="0" y="400" width="1400" height="160" fill="url(#deco)" opacity="0.3"/>
      <!-- Chandelier -->
      <line x1="700" y1="0" x2="700" y2="60" stroke="#c9a84c" stroke-width="3"/>
      <circle cx="700" cy="80" r="50" fill="#c9a84c" filter="drop-shadow(0 0 26px rgba(233,176,69,0.7))"/>
      <!-- Dance couples (silhouettes) -->
      <g fill="#050302">
        <!-- Couple 1 -->
        <ellipse cx="350" cy="260" rx="18" ry="22"/>
        <path d="M 320 400 L 320 280 Q 350 270 380 280 L 380 400 Z"/>
        <ellipse cx="410" cy="270" rx="16" ry="20"/>
        <path d="M 380 400 L 380 290 Q 410 282 440 290 L 440 400 L 460 400 L 460 420 L 360 420 L 360 400 Z"/>
        <!-- Couple 2 -->
        <ellipse cx="700" cy="250" rx="18" ry="22"/>
        <path d="M 670 400 L 670 270 Q 700 260 730 270 L 730 400 Z"/>
        <ellipse cx="760" cy="260" rx="16" ry="20"/>
        <path d="M 730 400 L 730 280 Q 760 272 790 280 L 790 400 L 810 400 L 810 420 L 710 420 L 710 400 Z"/>
        <!-- Couple 3 -->
        <ellipse cx="1050" cy="260" rx="18" ry="22"/>
        <path d="M 1020 400 L 1020 280 Q 1050 270 1080 280 L 1080 400 Z"/>
        <ellipse cx="1110" cy="270" rx="16" ry="20"/>
        <path d="M 1080 400 L 1080 290 Q 1110 282 1140 290 L 1140 400 L 1160 400 L 1160 420 L 1060 420 L 1060 400 Z"/>
      </g>
    </svg>'''


def saloon_silhouette() -> str:
    """Used for HF-only versions of saloon-themed formats."""
    return '''<svg style="position:absolute; left:50%; bottom:14%; transform:translateX(-50%);
      width:1140px; height:520px; filter:drop-shadow(0 24px 40px rgba(0,0,0,0.55));"
      viewBox="0 0 1140 520">
      <rect x="60" y="120" width="1020" height="360" fill="#16110c" stroke="#2a1f15" stroke-width="2"/>
      <polygon points="40,140 1100,140 1100,180 40,180" fill="#0e0a08"/>
      <rect x="50" y="280" width="1040" height="14" fill="#221710"/>
      <rect x="280" y="60" width="580" height="80" fill="#2a1d12" stroke="#4a3320" stroke-width="1.4"/>
      <text x="570" y="112" text-anchor="middle"
        style="font-family:'Playfair Display',Georgia,serif; font-weight:900; fill:#c9a84c; font-size:24px; letter-spacing:1.2px;">DIAMOND LIL'S SALOON</text>
      <g class="window" fill="#e9b045" filter="drop-shadow(0 0 18px rgba(233,176,69,0.85))">
        <rect x="130" y="200" width="80" height="70"/>
        <rect x="260" y="200" width="80" height="70"/>
        <rect x="800" y="200" width="80" height="70"/>
        <rect x="930" y="200" width="80" height="70"/>
      </g>
      <rect class="window-door" x="470" y="200" width="200" height="180" fill="#d8a138"
        filter="drop-shadow(0 0 28px rgba(216,161,56,0.95))"/>
    </svg>'''


def derrick_silhouette() -> str:
    """Oil derrick — used for derrick/oil-rig themed scenes."""
    return '''<svg style="position:absolute; left:50%; bottom:18%; transform:translateX(-50%);
      width:400px; height:600px; filter:drop-shadow(0 24px 40px rgba(0,0,0,0.6));"
      viewBox="0 0 400 600">
      <!-- Lattice frame -->
      <g stroke="#1a1610" stroke-width="3" fill="none">
        <line x1="160" y1="0" x2="120" y2="600"/>
        <line x1="240" y1="0" x2="280" y2="600"/>
        <line x1="160" y1="0" x2="240" y2="0"/>
      </g>
      <g stroke="#1a1610" stroke-width="2" fill="none">
        <line x1="155" y1="60" x2="245" y2="60"/>
        <line x1="148" y1="120" x2="252" y2="120"/>
        <line x1="142" y1="180" x2="258" y2="180"/>
        <line x1="135" y1="240" x2="265" y2="240"/>
        <line x1="128" y1="300" x2="272" y2="300"/>
        <line x1="120" y1="360" x2="280" y2="360"/>
      </g>
      <!-- Diagonal braces -->
      <g stroke="#0d0a08" stroke-width="1.5" fill="none">
        <line x1="156" y1="60" x2="248" y2="120"/>
        <line x1="244" y1="60" x2="152" y2="120"/>
        <line x1="148" y1="120" x2="252" y2="180"/>
        <line x1="252" y1="120" x2="148" y2="180"/>
        <line x1="142" y1="180" x2="258" y2="240"/>
        <line x1="258" y1="180" x2="142" y2="240"/>
        <line x1="135" y1="240" x2="265" y2="300"/>
        <line x1="265" y1="240" x2="135" y2="300"/>
        <line x1="128" y1="300" x2="272" y2="360"/>
        <line x1="272" y1="300" x2="128" y2="360"/>
      </g>
      <!-- Crown block at top -->
      <rect x="150" y="-8" width="100" height="16" fill="#c9a84c" filter="drop-shadow(0 0 8px rgba(201,168,76,0.5))"/>
    </svg>'''


def vault_door() -> str:
    return '''<div style="position:absolute; left:50%; bottom:12%; transform:translateX(-50%);
      width:540px; height:540px; border-radius:50%;
      background: radial-gradient(circle at 35% 35%, #4a4036 0%, #2a221c 45%, #14100c 100%);
      box-shadow: 0 0 60px rgba(0,0,0,0.7), inset 0 0 80px rgba(0,0,0,0.5);">
      <div style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
        width:160px; height:160px; border-radius:50%;
        background: radial-gradient(circle at 35% 35%, #c9a84c, #7a5e1d 70%);
        box-shadow: 0 0 25px rgba(201,168,76,0.4), inset 0 0 12px rgba(0,0,0,0.4);">
      </div>
      <!-- 4 bolts -->
      <div style="position:absolute; left:8%; top:8%; width:30px; height:30px; border-radius:50%; background:#3a302a;"></div>
      <div style="position:absolute; right:8%; top:8%; width:30px; height:30px; border-radius:50%; background:#3a302a;"></div>
      <div style="position:absolute; left:8%; bottom:8%; width:30px; height:30px; border-radius:50%; background:#3a302a;"></div>
      <div style="position:absolute; right:8%; bottom:8%; width:30px; height:30px; border-radius:50%; background:#3a302a;"></div>
    </div>'''


def hero_img_html(image_path: str) -> str:
    return f'<img class="hero" id="hero" src="{image_path}" />'


def fmt_title(title: str = "", subtitle: str = "") -> str:
    out = ""
    if title:
        out += f'<div class="title" id="title">{title}</div>\n'
    if subtitle:
        out += f'<div class="subtitle" id="subtitle">{subtitle}</div>\n'
    return out


# ===========================================================
# Generic recipe — used by 80% of formats. Tweakable via opts.
# ===========================================================

def recipe_hero_overlay(entry, version, image_path, *, opts=None, **_extra):
    """Hero image + overlays (stars, comet, fireflies, glows, title).

    opts:
      proc_bg: callable returning HTML for HF-only background (default: night_sky+ground)
      use_stars: bool
      use_comet: bool
      glow_positions: list of dicts
      particle_kind: 'firefly'|'dust-mote'|None
      particle_count: int
      particle_area: (lx, ty, rx, by) in %
      particle_seed: int
      title: str
      subtitle: str
      kenburns: bool
      extra_html: str
      extra_tl_js: str
    """
    opts = opts or {}
    dur = entry["dur"]
    parts = []

    if version == "recraft" and image_path:
        parts.append(hero_img_html(image_path))
        # Subtle vignette for title legibility — much lighter than before so the image is not cropped-feeling
        parts.append('<div style="position:absolute; inset:0; background: linear-gradient(180deg, rgba(5,9,19,0.18), transparent 25%, transparent 75%, rgba(5,9,19,0.22) 100%); pointer-events:none;"></div>')
    else:
        proc_bg_fn = opts.get("proc_bg")
        if proc_bg_fn:
            parts.append(proc_bg_fn())
        else:
            parts.append(night_sky())
            parts.append(night_ground())

    if opts.get("use_stars", False):
        parts.append(STARFIELD_SVG)
    if opts.get("use_comet", False):
        parts.append(COMET_SVG)
    for g in opts.get("glow_positions", []) or []:
        parts.append(
            f'<div class="glow" style="left:{g["left"]}; top:{g["top"]}; width:{g["w"]}; height:{g["h"]}; '
            f'background: radial-gradient(ellipse, {g.get("color", "rgba(255,205,100,0.85)")}, transparent 70%);"></div>'
        )
    pkind = opts.get("particle_kind")
    if pkind:
        parts.append(
            particles(pkind, opts.get("particle_count", 8),
                      area=opts.get("particle_area", (15, 60, 90, 92)),
                      seed=opts.get("particle_seed", entry["n"]))
        )

    if opts.get("extra_html"):
        parts.append(opts["extra_html"])

    parts.append(fmt_title(opts.get("title", ""), opts.get("subtitle", "")))

    # Timeline
    tl = []
    if version == "recraft" and opts.get("kenburns", True):
        tl.append("  MM.kenBurns(tl, { selector: '#hero', duration: D });")
    if opts.get("use_stars", False):
        tl.append("  MM.starfield(tl, { duration: D });")
    if opts.get("use_comet", False):
        tl.append("  MM.cometPass(tl, { start: 1.6, duration: 2.0 });")
    if opts.get("glow_positions"):
        tl.append("  MM.glowBreathe(tl, { selector: '.glow', duration: D });")
    if pkind:
        tl.append(f"  MM.particleDrift(tl, {{ selector: '.{pkind}', duration: D }});")
    if opts.get("title"):
        tl.append(f"  MM.titleBurn(tl, {{ start: {opts.get('title_start', 1.6)} }});")
    if opts.get("extra_tl_js"):
        tl.append(opts["extra_tl_js"])

    return {"scene_html": "\n  ".join(parts), "tl_js": "\n".join(tl), "scene_css": ""}


# ===========================================================
# Specialized recipes per family pattern
# ===========================================================

def recipe_parallax(entry, version, image_path, *, layers_data: list, opts=None, **_extra):
    """Multi-layer parallax.

    For Recraft mode, we use the AI image as the deep parallax layer and kenburns it,
    plus optionally add a foreground frame/vignette overlay. We do NOT stack procedural
    silhouettes on top of the AI image.

    For HF-only, all layers are procedural and parallax pushes them at different depths.
    """
    opts = opts or {}
    parts = []
    dur = entry["dur"]
    if version == "recraft" and image_path:
        # Recraft mode: image is the deep parallax layer, kenburns moves it
        parts.append(hero_img_html(image_path))
        # Foreground frame overlay (if any) — typically the last layer with depth >= 0.9
        for ld in layers_data:
            if ld.get("depth", 0) >= 0.9:
                parts.append(
                    f'<div class="parallax-fg" style="{ld.get("style","position:absolute; inset:0;")} pointer-events:none;">'
                    f'{ld.get("html","")}'
                    f'</div>'
                )
        parts.append('<div style="position:absolute; inset:0; background: linear-gradient(180deg, rgba(5,9,19,0.35), transparent 50%, rgba(5,9,19,0.4) 100%); pointer-events:none;"></div>')
    else:
        # HF-only: procedural multi-layer parallax
        parts.append(night_sky())
        for i, ld in enumerate(layers_data):
            cls = f"layer-d-{i}"
            parts.append(
                f'<div class="layer-d {cls}" data-depth="{ld["depth"]}" style="{ld.get("style","position:absolute; inset:0;")}">'
                f'{ld.get("html","")}'
                f'</div>'
            )
    parts.append(fmt_title(opts.get("title", ""), opts.get("subtitle", "")))

    if version == "recraft" and image_path:
        # Single hero ken-burns gives the parallax feel
        tl = [f"  MM.kenBurns(tl, {{ selector: '#hero', duration: D, dx:{opts.get('dx', -60)}, dy:{opts.get('dy', 0)}, scaleEnd:{1 + opts.get('zoom', 0.1):.3f} }});"]
    else:
        tl = [
            f"  MM.parallaxPush(tl, {{ selector: '.layer-d', duration: D, dx: {opts.get('dx', -80)}, zoom: {opts.get('zoom', 0.1)} }});",
        ]
    if opts.get("title"):
        tl.append("  MM.titleBurn(tl, { start: 1.2 });")
    if opts.get("extra_tl_js"):
        tl.append(opts["extra_tl_js"])
    return {"scene_html": "\n  ".join(parts), "tl_js": "\n".join(tl), "scene_css": ""}


def recipe_pan(entry, version, image_path, *, direction="x", opts=None, **_extra):
    """Pan a wide/tall hero across the canvas.

    For Recraft mode, the AI image is shown with its natural aspect ratio and panned
    by an amount that won't reveal blank canvas. Pan capped at ~60% of image overflow.

    For HF-only, a procedural wide scene is shown and we pan a generic backdrop.
    """
    opts = opts or {}
    dur = entry["dur"]
    parts = []
    if version == "recraft" and image_path:
        if direction == "x":
            # Image is 1820x1024. Scaled to height 1080 → width = 1920. Wider than canvas to allow horizontal pan.
            # Use scale:1.6 so width = 1.6 × canvas_w = 3072 → overflow = 1152px
            parts.append(f'<img id="pan-img" src="{image_path}" style="position:absolute; left:0; top:0; height:100%; width:auto; transform-origin:left top; transform:scale(1.6);" />')
        else:
            # Vertical pan — scale image up to allow vertical room
            parts.append(f'<img id="pan-img" src="{image_path}" style="position:absolute; left:0; top:0; width:100%; height:auto; transform-origin:left top; transform:scale(1.8);" />')
    else:
        # Procedural — show a generic wide noir scene
        parts.append(night_sky())
        parts.append(night_ground())
        parts.append(mansion_silhouette(scale=0.85))
        parts.append(f'<div id="pan-img" style="position:absolute; inset:0;"></div>')

    parts.append(fmt_title(opts.get("title", ""), opts.get("subtitle", "")))

    # Pan distances tuned to avoid revealing blank canvas
    if direction == "x":
        x_end = opts.get("x1", -900)  # 900px is conservative for typical scale 1.6
        tl = [f"  MM.panX(tl, {{ selector: '#pan-img', x0: {opts.get('x0', 0)}, x1: {x_end}, duration: D - 0.6, start: 0.4 }});"]
    else:
        y_end = opts.get("y1", -700)  # 700px is conservative for typical scale 1.8
        tl = [f"  MM.panY(tl, {{ selector: '#pan-img', y0: {opts.get('y0', 0)}, y1: {y_end}, duration: D - 0.6, start: 0.4 }});"]
    if opts.get("title"):
        tl.append("  MM.titleBurn(tl, { start: 1.0 });")
    if opts.get("extra_tl_js"):
        tl.append(opts["extra_tl_js"])
    return {"scene_html": "\n  ".join(parts), "tl_js": "\n".join(tl), "scene_css": ""}


def recipe_card_stage(entry, version, image_path, *, card_html, frame_color="#c9a84c", opts=None, **_extra):
    """A single card/poster/photo entrance on dark backdrop.

    When `image_is_backdrop=True` (in opts), the Recraft image fills the canvas
    and card_html overlays ON TOP — for formats where AI generates a scene but
    SVG annotations/markers/text should stack on top (map, equation, tree).

    Default (False): the Recraft image REPLACES card_html — for formats where
    the AI image IS the entire card (portrait, poster, document).
    """
    opts = opts or {}
    parts = []
    image_is_backdrop = opts.get("image_is_backdrop", False)

    if version == "recraft" and image_path and image_is_backdrop:
        # AI image as full backdrop, with card_html overlays on top
        parts.append(f'<img id="hero" class="hero" src="{image_path}" />')
        parts.append('<div style="position:absolute; inset:0; background: linear-gradient(180deg, rgba(5,9,19,0.14), transparent 30%, transparent 70%, rgba(5,9,19,0.20) 100%); pointer-events:none;"></div>')
        parts.append(card_html)
    elif version == "recraft" and image_path:
        # Image REPLACES the card content
        parts.append(velvet_table())
        parts.append(f'<img id="card" class="clip" src="{image_path}" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%) scale(0.85); max-width:62%; max-height:80%; box-shadow:0 24px 60px rgba(0,0,0,0.7); border:6px solid {frame_color};" />')
    else:
        parts.append(velvet_table())
        parts.append(card_html)
    parts.append(fmt_title(opts.get("title", ""), opts.get("subtitle", "")))

    tl = []
    if version == "recraft" and image_is_backdrop:
        # Image is backdrop — kenburns + the custom_card_in for the overlay content
        tl.append("  MM.kenBurns(tl, { selector: '#hero', duration: D });")
        tl.append(opts.get("custom_card_in", ""))
    elif version == "recraft":
        tl.append("  MM.slamIn(tl, { selector: '#card', start: 0.5, fromScale: 1.4, fromY: -40 });")
    else:
        tl.append(opts.get("custom_card_in", "  MM.slamIn(tl, { selector: '#card', start: 0.5 });"))
    if opts.get("title"):
        tl.append("  MM.titleBurn(tl, { start: 1.4 });")
    if opts.get("extra_tl_js"):
        tl.append(opts["extra_tl_js"])
    return {"scene_html": "\n  ".join(parts), "tl_js": "\n".join(tl), "scene_css": ""}


def recipe_document(entry, version, image_path, *, opts=None, show_stamp=False, **_extra):
    """A document scene — paper rises into frame, typewriter banner, stamps, etc."""
    opts = opts or {}
    parts = [desk_top()]
    if version == "recraft" and image_path:
        parts.append(f'<img id="doc" class="clip" src="{image_path}" style="position:absolute; left:14%; right:14%; top:12%; bottom:12%; width:72%; height:76%; object-fit:contain; transform: rotateX(5deg); box-shadow:0 24px 60px rgba(0,0,0,0.7); border-radius:4px;" />')
    else:
        parts.append(parchment_paper())

    parts += [opts.get("extra_html", "")]
    parts.append(fmt_title(opts.get("title", ""), opts.get("subtitle", "")))

    tl = [
        "  tl.fromTo('#doc', { y:80, opacity:0, scale:0.96 }, { y:0, opacity:1, scale:1, duration:1.2, ease:'sine.out' }, 0.4);",
    ]
    if opts.get("show_stamp"):
        tl.append("  MM.stampSlam(tl, { selector: '#stamp', start: 2.4 });")
    if opts.get("title"):
        tl.append("  MM.titleBurn(tl, { start: 1.8 });")
    if opts.get("extra_tl_js"):
        tl.append(opts["extra_tl_js"])
    return {"scene_html": "\n  ".join(parts), "tl_js": "\n".join(tl), "scene_css": ""}


def recipe_typo(entry, version, image_path, *, lines: list, opts=None, **_extra):
    """Kinetic typography on a backdrop. Lines reveal stagger or word-by-word."""
    opts = opts or {}
    parts = []
    if version == "recraft" and image_path:
        parts.append(hero_img_html(image_path))
        parts.append('<div style="position:absolute; inset:0; background: rgba(8,12,22,0.35); pointer-events:none;"></div>')
    else:
        parts.append(night_sky())
        parts.append(mansion_silhouette(scale=0.65))

    css_for_lines = """
  .typo-line { position:absolute; left:50%; transform:translateX(-50%); white-space:nowrap;
              font-family:'Playfair Display',Georgia,serif; color:#f5f0e4;
              text-shadow:0 0 18px rgba(8,12,22,0.85); opacity:0; }
"""
    # Render text lines positioned at staggered vertical positions
    line_html = []
    n = max(len(lines), 1)
    for i, line in enumerate(lines):
        top = 25 + (i * (50 / n))
        size = line.get("size", 56)
        weight = line.get("weight", 700)
        spacing = line.get("spacing", 3)
        text = line.get("text", "")
        line_html.append(
            f'<div class="typo-line" id="typo-{i}" style="top:{top:.1f}%; font-size:{size}px; font-weight:{weight}; letter-spacing:{spacing}px;">{text}</div>'
        )
    parts += line_html

    tl = []
    for i in range(len(lines)):
        tl.append(f"  tl.fromTo('#typo-{i}', {{ opacity:0, y:-12, filter:'blur(8px)' }}, {{ opacity:0.95, y:0, filter:'blur(0px)', duration:1.0, ease:'sine.out' }}, {0.6 + i*0.5});")
    if opts.get("extra_tl_js"):
        tl.append(opts["extra_tl_js"])
    return {"scene_html": "\n  ".join(parts), "tl_js": "\n".join(tl), "scene_css": css_for_lines}


def recipe_portrait_card(entry, version, image_path, *, name="", role="", dates="", opts=None, **_extra):
    """A portrait + name banner + role/dates — used by F (talking-head), Q (chyron), S (archival)."""
    opts = opts or {}
    parts = [velvet_table()]
    if version == "recraft" and image_path:
        parts.append(f'<img id="portrait" src="{image_path}" style="position:absolute; left:50%; top:46%; transform:translate(-50%,-50%); width:46%; height:68%; object-fit:cover; border-radius:200px; border:6px solid #c9a84c; box-shadow:0 24px 60px rgba(0,0,0,0.7);" />')
    else:
        # Procedural oval portrait — visible bust silhouette
        parts.append(
            '<div id="portrait" class="clip" style="position:absolute; left:50%; top:46%; transform:translate(-50%,-50%); width:420px; height:540px; '
            'background: radial-gradient(ellipse at 50% 30%, #6e5836 0%, #3a2d1a 50%, #1a120a 100%); '
            'border-radius:50%; box-shadow: inset 0 -40px 80px rgba(0,0,0,0.6), 0 24px 50px rgba(0,0,0,0.65); '
            'border:6px solid #c9a84c; overflow:hidden;">'
            '<svg viewBox="0 0 420 540" style="width:100%; height:100%; display:block;">'
            # Bust silhouette
            '<ellipse cx="210" cy="200" rx="90" ry="105" fill="#0a0706"/>'  # head
            # Top hat
            '<path d="M 130 150 L 290 150 L 290 100 L 270 100 L 270 60 L 150 60 L 150 100 L 130 100 Z" fill="#050302"/>'
            '<ellipse cx="210" cy="150" rx="100" ry="8" fill="#050302"/>'
            # Coat (large shoulders)
            '<path d="M 40 540 L 40 380 Q 100 320 210 320 Q 320 320 380 380 L 380 540 Z" fill="#0a0706"/>'
            # Lapel V
            '<path d="M 170 360 L 210 480 L 250 360" fill="none" stroke="#1a120a" stroke-width="3"/>'
            # Bow-tie / cravat hint
            '<rect x="195" y="350" width="30" height="14" fill="#c9a84c" opacity="0.6"/>'
            '</svg>'
            '</div>'
        )

    # Name banner under
    banner_top = "75%"
    parts.append(
        f'<div id="name-banner" class="clip" style="position:absolute; left:50%; top:{banner_top}; transform:translate(-50%,0); width:48%; padding:14px 24px; '
        f'background: linear-gradient(180deg, rgba(201,168,76,0.95), rgba(122,94,29,0.85)); text-align:center; opacity:0; box-shadow:0 4px 18px rgba(0,0,0,0.55);">'
        f'<div style="font-family:\'Playfair Display\',serif; font-weight:700; font-size:34px; color:#080c16; letter-spacing:3px;">{name}</div>'
        + (f'<div style="font-family:Georgia,serif; font-style:italic; font-size:20px; color:#1a1208; margin-top:4px;">{role}</div>' if role else '')
        + (f'<div style="font-family:\'Courier New\',monospace; font-size:16px; color:#1a1208; margin-top:4px;">{dates}</div>' if dates else '')
        + '</div>'
    )

    tl = [
        "  MM.slamIn(tl, { selector: '#portrait', start: 0.5, fromScale: 1.25, fromY: -20 });",
        "  tl.fromTo('#name-banner', { opacity:0, y:24 }, { opacity:0.95, y:0, duration:0.9, ease:'sine.out' }, 1.4);",
    ]
    if opts.get("extra_tl_js"):
        tl.append(opts["extra_tl_js"])
    return {"scene_html": "\n  ".join(parts), "tl_js": "\n".join(tl), "scene_css": ""}


def recipe_step_seq(entry, version, image_path, *, steps: list, opts=None, **_extra):
    """Sequential numbered step reveal — used by G (process), maybe parts of M."""
    opts = opts or {}
    parts = [desk_top()]
    if version == "recraft" and image_path:
        parts.append(f'<img id="hero" class="hero" src="{image_path}" />')
        parts.append('<div style="position:absolute; inset:0; background: rgba(8,12,22,0.4); pointer-events:none;"></div>')

    n = len(steps)
    cell_w = 28
    cell_h = 28
    margin = 6
    total_w = n * cell_w + (n - 1) * margin
    start_x = (100 - total_w) / 2
    for i, step in enumerate(steps):
        x = start_x + i * (cell_w + margin)
        parts.append(
            f'<div class="step-cell" id="step-{i}" style="position:absolute; left:{x}%; top:32%; width:{cell_w}%; height:{cell_h}%; '
            f'background: rgba(20,16,12,0.85); border:2px solid #c9a84c; border-radius:8px; box-shadow:0 12px 32px rgba(0,0,0,0.6); '
            f'opacity:0; padding:16px;">'
            f'<div style="font-family:Playfair Display,serif; font-size:60px; color:#c9a84c; font-weight:900;">{i+1}.</div>'
            f'<div style="font-family:Georgia,serif; font-size:22px; color:#f5f0e4; margin-top:10px; line-height:1.3;">{step}</div>'
            f'</div>'
        )

    tl = []
    for i in range(n):
        tl.append(f"  MM.slamIn(tl, {{ selector: '#step-{i}', start: {0.6 + i*0.7}, fromScale: 1.2, fromY: -30 }});")
    if opts.get("extra_tl_js"):
        tl.append(opts["extra_tl_js"])
    return {"scene_html": "\n  ".join(parts), "tl_js": "\n".join(tl), "scene_css": ""}


def recipe_ui_mockup(entry, version, image_path, *, ui_html: str, opts=None, **_extra):
    """A UI mockup (phone/computer) — used by J (phone/chat UI)."""
    opts = opts or {}
    parts = []
    if version == "recraft" and image_path:
        parts.append(hero_img_html(image_path))
        parts.append('<div style="position:absolute; inset:0; background: rgba(8,12,22,0.55); pointer-events:none;"></div>')
    else:
        parts.append(velvet_table())
    parts.append(ui_html)
    parts.append(fmt_title(opts.get("title", ""), opts.get("subtitle", "")))

    tl = [opts.get("ui_tl_js", "")]
    if opts.get("extra_tl_js"):
        tl.append(opts["extra_tl_js"])
    return {"scene_html": "\n  ".join(parts), "tl_js": "\n".join(tl), "scene_css": opts.get("ui_css", "")}


def recipe_vintage_media(entry, version, image_path, *, kind="crt", opts=None, **_extra):
    """Vintage media treatment — CRT/VHS/Newspaper/Radio/Projector."""
    opts = opts or {}
    parts = []
    if version == "recraft" and image_path:
        parts.append(f'<img class="hero" id="hero" src="{image_path}" />')
    else:
        parts.append(night_sky())
        parts.append(mansion_silhouette(scale=0.8))

    css = ""
    if kind == "crt":
        parts.append('<div class="crt-scanlines" style="position:absolute; inset:0; pointer-events:none; mix-blend-mode:overlay; opacity:0.45; background: repeating-linear-gradient(0deg, rgba(0,0,0,0.4) 0px, rgba(0,0,0,0.4) 1px, transparent 1px, transparent 3px);"></div>')
        parts.append('<div class="crt-curve" id="crt-curve" style="position:absolute; inset:0; pointer-events:none; box-shadow: inset 0 0 200px rgba(0,0,0,0.7);"></div>')
        parts.append('<div class="crt-flicker" id="crt-flicker" style="position:absolute; inset:0; pointer-events:none; background:rgba(255,255,255,0.04); opacity:0;"></div>')
    elif kind == "vhs":
        parts.append('<div class="vhs-streak" id="vhs-streak" style="position:absolute; left:0; right:0; top:30%; height:60%; pointer-events:none; background: repeating-linear-gradient(90deg, rgba(255,255,255,0.08) 0px, rgba(255,255,255,0.08) 12px, transparent 12px, transparent 60px); opacity:0;"></div>')
        parts.append('<div class="vhs-track" id="vhs-track" style="position:absolute; left:0; right:0; top:0; height:8px; background:rgba(255,255,255,0.4); pointer-events:none; opacity:0;"></div>')
        parts.append('<div style="position:absolute; right:36px; bottom:36px; font-family:\'Courier New\',monospace; font-size:24px; color:rgba(255,255,255,0.7); letter-spacing:2px; text-shadow:0 0 8px rgba(0,0,0,0.9);">00:14:32</div>')
    elif kind == "projector":
        parts.append('<div style="position:absolute; left:0; right:0; top:0; bottom:0; pointer-events:none; background: linear-gradient(180deg, rgba(0,0,0,0) 96%, #000 100%), linear-gradient(0deg, rgba(0,0,0,0) 96%, #000 100%);"></div>')
        # Sprocket holes
        sprocket_left = '<div style="position:absolute; left:0; top:0; bottom:0; width:40px; background: linear-gradient(180deg, transparent 0, transparent 12px, #000 12px, #000 36px, transparent 36px, transparent 84px, #000 84px, #000 108px, transparent 108px); opacity:0.6; pointer-events:none;"></div>'
        sprocket_right = sprocket_left.replace("left:0", "right:0")
        parts.append(sprocket_left)
        parts.append(sprocket_right)
        parts.append('<div id="film-scratch" style="position:absolute; left:30%; top:0; width:2px; height:100%; background:rgba(255,255,255,0.5); pointer-events:none; opacity:0;"></div>')

    parts.append(fmt_title(opts.get("title", ""), opts.get("subtitle", "")))

    tl = []
    if version == "recraft":
        tl.append("  MM.kenBurns(tl, { selector: '#hero', duration: D, dx:-10, dy:-4, scaleEnd:1.02 });")
    if kind == "crt":
        tl.append("  // CRT channel-flicker on entry")
        tl.append("  tl.fromTo('#crt-flicker', { opacity:0.0 }, { opacity:0.4, duration:0.1, yoyo:true, repeat:5, ease:'power2.out' }, 0.0);")
        tl.append("  // Tracking-glitch flickers every 2s")
        tl.append("  for (let t=1.0; t<D-0.5; t+=2.0) {")
        tl.append("    tl.fromTo('#crt-flicker', { opacity:0 }, { opacity:0.5, duration:0.08, yoyo:true, repeat:1, ease:'power2.out' }, t);")
        tl.append("  }")
    elif kind == "vhs":
        tl.append("  tl.fromTo('#vhs-streak', { opacity:0 }, { opacity:0.7, duration:0.2 }, 0.2);")
        tl.append("  tl.to('#vhs-streak', { y:-300, duration:1.6, ease:'sine.inOut', repeat:2, yoyo:true }, 0.4);")
        tl.append("  tl.fromTo('#vhs-track', { opacity:0, y:0 }, { opacity:0.9, y:1080, duration:2.0, ease:'sine.inOut' }, 0.6);")
    elif kind == "projector":
        tl.append("  for (let t=0.5; t<D-0.5; t+=0.8) {")
        tl.append("    tl.fromTo('#film-scratch', { opacity:0, x:0 }, { opacity:0.4, x: -1920+gsap.utils.random(0,1920), duration:0.4, ease:'none' }, t);")
        tl.append("  }")
    if opts.get("title"):
        tl.append("  MM.titleBurn(tl, { start: 1.6 });")
    if opts.get("extra_tl_js"):
        tl.append(opts["extra_tl_js"])
    return {"scene_html": "\n  ".join(parts), "tl_js": "\n".join(tl), "scene_css": css}


def recipe_surreal(entry, version, image_path, *, kind="zoom", opts=None, **_extra):
    """Surreal effects — infinite zoom, glitch, shadow, mirror, morph."""
    opts = opts or {}
    parts = []
    if version == "recraft" and image_path:
        parts.append(hero_img_html(image_path))
    else:
        parts.append(night_sky())
        parts.append(mansion_silhouette(scale=0.85))

    tl = []
    if kind == "zoom":
        tl.append("  tl.fromTo('#hero', { scale:1.0, x:0, y:0 }, { scale:3.6, x:0, y:0, duration:D-0.6, ease:'power1.inOut' }, 0.3);")
    elif kind == "glitch":
        # Repeat RGB-split at start, then settle
        tl.append("  tl.fromTo('#hero', { x:0, filter:'none' }, { x: -16, filter:'hue-rotate(60deg) saturate(2)', duration:0.06, yoyo:true, repeat:3, ease:'power2.in' }, 0.0);")
        tl.append("  tl.fromTo('#hero', { x:0 }, { x:14, duration:0.05, yoyo:true, repeat:3, ease:'power2.in' }, 0.2);")
        tl.append("  tl.to('#hero', { x:0, filter:'none', duration:0.3, ease:'sine.out' }, 0.4);")
        tl.append("  // late mid-scene scramble")
        tl.append("  tl.to('#hero', { filter:'hue-rotate(30deg) saturate(1.6)', duration:0.06, yoyo:true, repeat:2, ease:'power2.out' }, 2.4);")
    elif kind == "mirror":
        # Adds a flipped overlay
        if version == "recraft" and image_path:
            parts.append(f'<img id="hero-mirror" src="{image_path}" style="position:absolute; left:50%; top:0; width:50%; height:100%; object-fit:cover; transform: scaleX(-1); opacity:0; filter:brightness(0.7) hue-rotate(-15deg);" />')
            parts.append('<div style="position:absolute; left:50%; top:0; bottom:0; width:3px; background: linear-gradient(180deg, rgba(201,168,76,0.0), rgba(201,168,76,0.9), rgba(201,168,76,0.0)); transform:translateX(-50%); z-index:60;"></div>')
        tl.append("  tl.fromTo('#hero', { clipPath:'inset(0 50% 0 0)' }, { clipPath:'inset(0 0 0 0)', duration:1.4, ease:'sine.inOut' }, 0.4);")
        tl.append("  if (document.querySelector('#hero-mirror')) tl.fromTo('#hero-mirror', { opacity:0 }, { opacity:1, duration:1.4, ease:'sine.out' }, 0.8);")
    elif kind == "shadow":
        # Wallpaper + magnate shadow shifting
        if version == "hyperframes":
            # Override with a wallpaper background
            parts = ['<div style="position:absolute; inset:0; background: linear-gradient(180deg, #2a201a 0%, #1a1410 100%);"></div>']
            parts.append('<div style="position:absolute; inset:0; opacity:0.25; background-image: url(&quot;data:image/svg+xml;utf8,&lt;svg xmlns=\'http://www.w3.org/2000/svg\' width=\'100\' height=\'100\'&gt;&lt;path d=\'M0 0 L50 50 L100 0 M0 100 L50 50 L100 100\' fill=\'none\' stroke=\'%23c9a84c\' stroke-width=\'1\'/&gt;&lt;/svg&gt;&quot;);"></div>')
        parts.append('<div id="shadow" style="position:absolute; left:30%; top:20%; width:280px; height:600px; background:rgba(0,0,0,0.65); transform: skewX(-12deg); filter: blur(4px);"></div>')
        parts.append('<div style="position:absolute; left:15%; top:30%; width:100px; height:100px; border-radius:50%; background: radial-gradient(circle, rgba(255,220,120,0.8), transparent 70%); z-index:50;"></div>')
        tl.append("  tl.fromTo('#shadow', { x:0, scaleX:1, skewX:-12 }, { x:160, scaleX:1.4, skewX:-30, duration:D-0.6, ease:'sine.inOut' }, 0.3);")

    parts.append(fmt_title(opts.get("title", ""), opts.get("subtitle", "")))
    if opts.get("title"):
        tl.append("  MM.titleBurn(tl, { start: 1.6 });")
    if opts.get("extra_tl_js"):
        tl.append(opts["extra_tl_js"])
    return {"scene_html": "\n  ".join(parts), "tl_js": "\n".join(tl), "scene_css": ""}
