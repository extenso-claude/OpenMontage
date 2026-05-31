"""Maps each format number -> (recipe_function, params_dict).

For each of the 99 formats, this declares: which generic recipe to use
and what params to pass. Each entry is ~5-10 lines.

The dispatcher is consumed by build_all.py to write all 198 compositions.
"""
from __future__ import annotations
from typing import Optional
from tools.animation.catalog.recipes import (
    recipe_hero_overlay, recipe_parallax, recipe_pan, recipe_card_stage,
    recipe_document, recipe_typo, recipe_portrait_card, recipe_step_seq,
    recipe_ui_mockup, recipe_vintage_media, recipe_surreal,
    night_sky, night_ground, mansion_silhouette, saloon_silhouette,
    derrick_silhouette, vault_door, velvet_table, desk_top, parchment_paper,
    train_silhouette, record_player_silhouette, stained_glass_silhouette,
    lecture_hall_silhouette, ballroom_silhouette,
)
from tools.animation.catalog.composer import particles


# Per-format: (recipe_fn, kwargs_dict)
# kwargs are passed to the recipe along with (entry, version, image_path).
# Common kwargs: title, subtitle, glow_positions, particle_*, use_stars, use_comet
FORMATS = {

    # ==================== A. Single image + overlay ====================
    1: (recipe_hero_overlay, {  # Living scene — saloon at night
        "use_stars": True, "use_comet": True,
        "glow_positions": [
            {"left":"21.5%","top":"42%","w":"5%","h":"8%","color":"rgba(255,205,100,0.85)"},
            {"left":"28.5%","top":"42%","w":"5%","h":"8%","color":"rgba(255,205,100,0.85)"},
            {"left":"14.5%","top":"54%","w":"10%","h":"18%","color":"rgba(255,200,90,0.95)"},
        ],
        "particle_kind":"firefly", "particle_count":10, "particle_area":(12,58,92,92), "particle_seed":1,
        "title":"DIAMOND LIL'S SALOON", "subtitle":"Nevada Territory, 1881",
        "proc_bg": lambda: night_sky() + night_ground() + saloon_silhouette(),
    }),

    2: (recipe_document, {  # Aged document — last will + wax-seal + candle
        "title":"LAST WILL & TESTAMENT", "subtitle":"of E.P. Staunton, dated 1893",
        "show_stamp": False,
        "extra_html": (
            # Stamp + candle glow
            '<div id="ink-pulse" style="position:absolute; left:50%; top:60%; transform:translateX(-50%); width:240px; height:6px; background: linear-gradient(90deg, transparent, #1a1208, transparent); opacity:0;"></div>'
            '<div id="candle-glow" class="clip" style="position:absolute; right:9%; top:8%; width:240px; height:240px; pointer-events:none; '
            'background: radial-gradient(circle, rgba(255,180,80,0.5) 0%, transparent 65%); mix-blend-mode:screen;"></div>'
            '<div class="dust-mote" style="left:30%; top:62%;"></div>'
            '<div class="dust-mote" style="left:42%; top:48%;"></div>'
            '<div class="dust-mote" style="left:54%; top:66%;"></div>'
            '<div class="dust-mote" style="left:68%; top:50%;"></div>'
        ),
        "extra_tl_js": (
            "  tl.fromTo('#candle-glow', { opacity:0.6 }, { opacity:1.0, duration:0.5, yoyo:true, repeat:Math.ceil((D-1)/0.5)*2, ease:'sine.inOut' }, 0.4);\n"
            "  tl.fromTo('#ink-pulse', { opacity:0, scaleX:0 }, { opacity:0.9, scaleX:1, duration:1.4, ease:'sine.out' }, 2.4);\n"
            "  MM.particleDrift(tl, { selector: '.dust-mote', duration: D, spread:14 });"
        ),
    }),

    3: (recipe_hero_overlay, {  # Mood loop — gilded library at night
        "use_stars": False,
        "glow_positions": [
            {"left":"22%","top":"48%","w":"7%","h":"12%","color":"rgba(232,180,60,0.7)"},
            {"left":"68%","top":"56%","w":"6%","h":"10%","color":"rgba(232,180,60,0.6)"},
        ],
        "particle_kind":"dust-mote", "particle_count":14, "particle_area":(10,30,90,90), "particle_seed":3,
        "title":"", "subtitle":"",
        "proc_bg": lambda: '<div style="position:absolute; inset:0; background: radial-gradient(ellipse at 30% 40%, #2a2014 0%, #0e0a08 70%); "></div>' + mansion_silhouette(scale=0.6, bottom="22%"),
    }),

    4: (recipe_hero_overlay, {  # Constellation map — star halos + SVG line
        "use_stars": True,
        "particle_kind":None,
        "title":"THE LION'S CROWN", "subtitle":"Leo, rising over Newport, 1898",
        "proc_bg": lambda: night_sky() + mansion_silhouette(scale=0.5, bottom="14%"),
        "extra_html": (
            '<svg id="constellation" style="position:absolute; left:50%; top:25%; transform:translateX(-50%); width:600px; height:480px;" viewBox="0 0 600 480">'
            '<path id="leo-line" d="M 120 100 L 230 80 L 320 140 L 280 220 L 380 260 L 470 200 L 500 340 L 360 360 L 250 300 L 170 280 L 200 200 Z" '
            'fill="none" stroke="#c9a84c" stroke-width="1.6" stroke-dasharray="900" stroke-dashoffset="900" opacity="0.9"/>'
            '<g fill="#fff7d9">'
            '<circle cx="120" cy="100" r="4" filter="drop-shadow(0 0 8px #fff7d9)"/>'
            '<circle cx="230" cy="80" r="4" filter="drop-shadow(0 0 8px #fff7d9)"/>'
            '<circle cx="320" cy="140" r="4" filter="drop-shadow(0 0 8px #fff7d9)"/>'
            '<circle cx="280" cy="220" r="4" filter="drop-shadow(0 0 8px #fff7d9)"/>'
            '<circle cx="380" cy="260" r="4" filter="drop-shadow(0 0 8px #fff7d9)"/>'
            '<circle cx="470" cy="200" r="4" filter="drop-shadow(0 0 8px #fff7d9)"/>'
            '<circle cx="500" cy="340" r="4" filter="drop-shadow(0 0 8px #fff7d9)"/>'
            '<circle cx="360" cy="360" r="4" filter="drop-shadow(0 0 8px #fff7d9)"/>'
            '<circle cx="250" cy="300" r="4" filter="drop-shadow(0 0 8px #fff7d9)"/>'
            '<circle cx="170" cy="280" r="4" filter="drop-shadow(0 0 8px #fff7d9)"/>'
            '</g>'
            '</svg>'
        ),
        "extra_tl_js": (
            "  MM.pathDraw(tl, { selector: '#leo-line', start: 0.8, duration: 2.6 });\n"
            "  tl.fromTo('#leo-line', { opacity:0.9 }, { opacity:1.0, duration:1.0, yoyo:true, repeat:Math.ceil((D-3)/1)*2, ease:'sine.inOut' }, 3.4);"
        ),
    }),

    5: (recipe_hero_overlay, {  # Window portal — interior view with rain outside
        "use_stars": False,
        "particle_kind": None,
        "title":"", "subtitle":"",
        "proc_bg": lambda: '<div style="position:absolute; inset:0; background: linear-gradient(180deg, #050913 0%, #0a1024 50%, #1a1820 100%);"></div>',
        "extra_html": (
            # Procedural rain via slanted streaks
            '<div id="rain" style="position:absolute; inset:0; overflow:hidden; opacity:0;">'
            + "".join(f'<div style="position:absolute; left:{(i*7) % 100}%; top:-10%; width:1.5px; height:60px; background:linear-gradient(180deg, transparent, rgba(180,200,255,0.5)); transform: rotate(15deg);" class="raindrop"></div>' for i in range(40))
            + '</div>'
            '<div style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:60%; height:70%; border:6px solid #2a1f15; background: linear-gradient(180deg, rgba(8,12,22,0.4), rgba(8,12,22,0.7));"></div>'
        ),
        "extra_tl_js": (
            "  tl.fromTo('#rain', { opacity:0 }, { opacity:0.7, duration:1.0, ease:'sine.out' }, 0.4);\n"
            "  document.querySelectorAll('.raindrop').forEach((d,i)=>{\n"
            "    tl.fromTo(d, { y:0 }, { y:1200, duration: 1.4 + (i%5)*0.2, ease:'none', repeat: Math.ceil((D-0.4)/1.6) }, 0.4 + (i*0.04)%0.8);\n"
            "  });"
        ),
    }),

    # ==================== B. Parallax depth ====================
    6: (recipe_parallax, {  # Camera push-in (saloon doors)
        "title":"INSIDE THE LOUNGE", "subtitle":"",
        "dx": -60, "zoom": 0.12,
        "layers_data": [
            # 3-layer depth (procedural backdrop assumed)
            {"depth": 0.0, "html": '<div style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:140%; height:140%; background: radial-gradient(ellipse at center, rgba(232,180,60,0.4) 0%, transparent 50%); mix-blend-mode:screen;"></div>'},
            {"depth": 0.4, "html": mansion_silhouette(scale=0.6)},
            {"depth": 0.85, "html": '<div style="position:absolute; left:0; right:0; bottom:0; height:50%; background: linear-gradient(180deg, transparent, rgba(0,0,0,0.7));"></div>'},
        ],
    }),

    8: (recipe_parallax, {  # Moving train window
        "title":"THE PRIVATE CAR", "subtitle":"1892",
        "dx": -200, "zoom": 0.04,
        "layers_data": [
            {"depth": 0.1, "html": night_sky()},  # far parallax — moves most
            {"depth": 0.5, "html": mansion_silhouette(scale=0.55, bottom="36%")},
            {"depth": 1.0, "html": (
                '<div style="position:absolute; inset:0; background: rgba(0,0,0,0); pointer-events:none;"></div>'
                # Window frame (interior fixed)
                '<svg style="position:absolute; left:10%; right:10%; top:10%; bottom:10%; pointer-events:none;" viewBox="0 0 1536 864" preserveAspectRatio="none">'
                '<rect x="0" y="0" width="1536" height="864" fill="none" stroke="#c9a84c" stroke-width="12"/>'
                '<line x1="0" y1="432" x2="1536" y2="432" stroke="#c9a84c" stroke-width="8"/>'
                '<line x1="768" y1="0" x2="768" y2="864" stroke="#c9a84c" stroke-width="8"/>'
                '</svg>'
                '<div style="position:absolute; left:0; right:0; top:0; height:10%; background:#0a0606;"></div>'
                '<div style="position:absolute; left:0; right:0; bottom:0; height:10%; background:#0a0606;"></div>'
                '<div style="position:absolute; left:0; top:0; bottom:0; width:10%; background:#0a0606;"></div>'
                '<div style="position:absolute; right:0; top:0; bottom:0; width:10%; background:#0a0606;"></div>'
            )},
        ],
    }),

    9: (recipe_parallax, {  # Diorama shadow box
        "title":"THE COUNTING-HOUSE", "subtitle":"",
        "dx": -30, "zoom": 0.06,
        "layers_data": [
            {"depth": 0.1, "html": '<div style="position:absolute; inset:0; background: linear-gradient(180deg, #1a1410 0%, #060403 100%);"></div>'},
            {"depth": 0.4, "html": '<div style="position:absolute; left:30%; right:30%; top:30%; bottom:30%; background:#2a1f15; box-shadow: 0 24px 50px rgba(0,0,0,0.7);"></div>'},
            {"depth": 0.7, "html": '<div style="position:absolute; left:38%; right:38%; top:42%; bottom:42%; background:#3a2a1d; border:3px solid #c9a84c;"></div>'},
            {"depth": 1.0, "html": '<div id="sweep-light" style="position:absolute; left:-30%; top:0; width:30%; height:100%; background: linear-gradient(90deg, transparent, rgba(255,200,100,0.45), transparent); mix-blend-mode:screen;"></div>'},
        ],
        "extra_tl_js": "  tl.fromTo('#sweep-light', { left:'-30%' }, { left:'130%', duration: D-0.6, ease:'sine.inOut' }, 0.3);",
    }),

    10: (recipe_pan, {  # Descent / ascent — vertical pan down shaft
        "direction":"y",
        "title":"DESCENT", "subtitle":"to the vault, 03:14 AM",
        "y0": 0, "y1": -900,
        "extra_tl_js": "  // Vault dial glint at the bottom (handled via title)",
    }),

    # ==================== C. Pan / scroll ====================
    11: (recipe_pan, {  # Panorama reveal — New York 1900
        "direction":"x",
        "title":"NEW YORK, 1900", "subtitle":"",
        "x0": 0, "x1": -1400,
    }),
    12: (recipe_pan, {  # Tower descent — oil derrick top→bottom
        "direction":"y",
        "title":"THE STRIKE OF '72", "subtitle":"",
        "y0": 0, "y1": -1200,
    }),
    13: (recipe_pan, {  # Timeline scroll — 1880-2020
        "direction":"x",
        "title":"FIVE GENERATIONS", "subtitle":"1880 — 2020",
        "x0": 0, "x1": -2000,
    }),

    # ==================== D. Card sequences ====================
    16: (recipe_card_stage, {  # Storybook page-turn — biography spread
        "frame_color":"#c9a84c",
        "title":"THE STRIKE OF 1872", "subtitle":"Chapter VII",
        "card_html": (
            '<div id="card" class="clip" style="position:absolute; left:14%; right:14%; top:14%; bottom:14%; '
            'background: linear-gradient(180deg, #e0d4ac, #c4b387); border:6px solid #c9a84c; '
            'box-shadow:0 24px 60px rgba(0,0,0,0.7);"></div>'
        ),
        "custom_card_in": "  tl.fromTo('#card', { rotateY:-80, opacity:0 }, { rotateY:0, opacity:1, duration:1.4, ease:'sine.out' }, 0.4);",
    }),

    17: (recipe_card_stage, {  # Tarot card draw
        "title":"PAST · PRESENT · FUTURE", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            # 3 cards
            '<div id="card0" class="tarot clip" style="position:absolute; left:18%; top:24%; width:18%; height:56%; '
            'background: linear-gradient(135deg, #1a1208, #4a3320); border:4px solid #c9a84c; border-radius:8px; '
            'box-shadow:0 18px 40px rgba(0,0,0,0.6); opacity:0;"></div>'
            '<div id="card1" class="tarot clip" style="position:absolute; left:41%; top:22%; width:18%; height:56%; '
            'background: linear-gradient(135deg, #1a1208, #4a3320); border:4px solid #c9a84c; border-radius:8px; '
            'box-shadow:0 18px 40px rgba(0,0,0,0.6); opacity:0;"></div>'
            '<div id="card2" class="tarot clip" style="position:absolute; left:64%; top:24%; width:18%; height:56%; '
            'background: linear-gradient(135deg, #1a1208, #4a3320); border:4px solid #c9a84c; border-radius:8px; '
            'box-shadow:0 18px 40px rgba(0,0,0,0.6); opacity:0;"></div>'
            # Particle layer
            + particles("dust-mote", 10, area=(15, 22, 85, 78), seed=17)
        ),
        "custom_card_in": (
            "  tl.fromTo('#card0', { y:30, opacity:0, rotateY:90 }, { y:0, opacity:1, rotateY:0, duration:0.7, ease:'sine.out' }, 0.5);\n"
            "  tl.fromTo('#card1', { y:30, opacity:0, rotateY:90 }, { y:0, opacity:1, rotateY:0, duration:0.7, ease:'sine.out' }, 1.6);\n"
            "  tl.fromTo('#card2', { y:30, opacity:0, rotateY:90 }, { y:0, opacity:1, rotateY:0, duration:0.7, ease:'sine.out' }, 2.7);\n"
            "  MM.particleDrift(tl, { selector: '.dust-mote', duration: D });"
        ),
    }),

    18: (recipe_card_stage, {  # Wanted poster slap
        "title":"WANTED", "subtitle":"DEAD OR ALIVE — $5,000 REWARD",
        "card_html": (
            '<div id="card" class="clip" style="position:absolute; left:30%; top:14%; width:40%; bottom:14%; '
            'background: linear-gradient(180deg, #d8caa0, #a8956a); border:5px solid #6e5836; '
            'box-shadow:0 24px 60px rgba(0,0,0,0.8); transform: rotate(-2deg) scale(0); padding:30px;">'
            '<div style="text-align:center; font-family:\'Playfair Display\',serif; font-weight:900; font-size:60px; color:#3a2410; letter-spacing:6px;">WANTED</div>'
            '<div style="text-align:center; font-family:Georgia,serif; font-style:italic; font-size:22px; color:#3a2410; margin-top:6px;">DEAD OR ALIVE</div>'
            '<div style="margin:24px 30px; height:280px; background:#7a6e4a; border:3px solid #3a2410;"></div>'
            '<div style="text-align:center; font-family:\'Playfair Display\',serif; font-weight:700; font-size:38px; color:#3a2410; margin-top:14px;">$5,000 REWARD</div>'
            '<div style="text-align:center; font-family:Georgia,serif; font-size:18px; color:#5a4830; margin-top:6px;">NEW MEXICO TERRITORY · 1881</div>'
            '</div>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#card', { scale:0, rotate:-30, opacity:0 }, { scale:1, rotate:-2, opacity:1, duration:0.5, ease:'power2.out' }, 0.5);\n"
            "  tl.to('#card', { scale:1.04, duration:0.16, yoyo:true, repeat:1, ease:'sine.inOut' }, 1.0);"
        ),
    }),

    19: (recipe_card_stage, {  # Bestiary lore card
        "title":"", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="card" class="clip" style="position:absolute; left:22%; right:22%; top:10%; bottom:10%; '
            'background: linear-gradient(180deg, #e0d4ac, #c4b387); border:6px solid #6e5836; padding:30px; opacity:0;">'
            '<div style="text-align:center; font-family:\'Playfair Display\',serif; font-weight:900; font-size:36px; color:#3a2410; letter-spacing:3px;">HOMO MAGNATUS</div>'
            '<div style="text-align:center; font-family:Georgia,serif; font-style:italic; font-size:18px; color:#5a4830; margin-top:4px;">THE TOP-HAT INDUSTRIALIST</div>'
            '<div style="margin:24px 60px; height:200px; background: linear-gradient(180deg, #8e7a4a, #5a4830); border:3px solid #3a2410; position:relative;">'
            '<svg viewBox="0 0 100 100" style="position:absolute; inset:0; width:100%; height:100%;" preserveAspectRatio="xMidYMid meet">'
            '<ellipse cx="50" cy="38" rx="14" ry="18" fill="#0a0706"/>'
            '<path d="M 36 18 L 64 18 L 64 8 L 56 8 L 56 0 L 44 0 L 44 8 L 36 8 Z" fill="#0a0706"/>'
            '<path d="M 30 100 L 30 60 Q 50 50 70 60 L 70 100 Z" fill="#0a0706"/>'
            '</svg></div>'
            '<div style="margin:20px 50px; display:grid; grid-template-columns:1fr 1fr; gap:10px 32px; font-family:Georgia,serif; font-size:20px; color:#3a2410;">'
            '<div>WEALTH</div><div id="stat-wealth" style="text-align:right; font-weight:700;">0</div>'
            '<div>RUTHLESSNESS</div><div id="stat-ruth" style="text-align:right; font-weight:700;">0</div>'
            '<div>LIFESPAN</div><div id="stat-life" style="text-align:right; font-weight:700;">0</div>'
            '<div>KIN</div><div id="stat-kin" style="text-align:right; font-weight:700;">0</div>'
            '</div></div>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#card', { y:30, scale:0.94, opacity:0 }, { y:0, scale:1, opacity:1, duration:0.8, ease:'sine.out' }, 0.4);\n"
            "  MM.countUp(tl, { selector: '#stat-wealth', start: 1.6, duration: 1.4, from:0, to:9999 });\n"
            "  MM.countUp(tl, { selector: '#stat-ruth',   start: 2.0, duration: 1.2, from:0, to:99 });\n"
            "  MM.countUp(tl, { selector: '#stat-life',   start: 2.4, duration: 1.0, from:0, to:89 });\n"
            "  MM.countUp(tl, { selector: '#stat-kin',    start: 2.8, duration: 0.6, from:0, to:7 });"
        ),
    }),

    20: (recipe_card_stage, {  # Polaroid scatter
        "title":"THE FAMILY ARCHIVE", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": "".join(
            f'<div class="polaroid clip" id="pol-{i}" style="position:absolute; '
            f'left:{15+i*14}%; top:{18+(i%2)*30}%; width:14%; height:34%; '
            f'background:#e8dfc8; border:2px solid #c9a84c; box-shadow:0 16px 36px rgba(0,0,0,0.6); '
            f'transform: rotate({-12+i*4}deg) scale(0.6); opacity:0; padding:8px;">'
            f'<div style="width:100%; height:78%; background:#5a4830;"></div>'
            f'<div style="text-align:center; font-family:Georgia,serif; font-size:11px; color:#3a2410; margin-top:6px;">FRAME {i+1}</div>'
            f'</div>' for i in range(6)
        ),
        "custom_card_in": "\n".join(
            f"  MM.slamIn(tl, {{ selector: '#pol-{i}', start: {0.4+i*0.25}, fromScale: 1.2, fromY: -40, fromRotate: {-30+i*8} }});"
            for i in range(6)
        ),
    }),

    21: (recipe_card_stage, {  # Tier list ranking — 5 magnates into S/A/B/C/D
        "title":"WEALTH TIERS", "subtitle":"Net Worth in 1913 Dollars",
        "image_is_backdrop": True,
        "card_html": (
            # Tier labels on left
            "".join(
                f'<div style="position:absolute; left:8%; top:{18+i*14}%; width:6%; height:12%; '
                f'background: {col}; display:flex; align-items:center; justify-content:center; '
                f'font-family:Playfair Display,serif; font-weight:900; font-size:36px; color:#080c16; '
                f'box-shadow:0 4px 12px rgba(0,0,0,0.5);">'
                f'{tier}</div>'
                for i, (tier, col) in enumerate([("S","#c9a84c"),("A","#a8884c"),("B","#876840"),("C","#684e30"),("D","#483420")])
            )
            # Magnate cards drop in from right
            + "".join(
                f'<div class="mag-card clip" id="mag-{i}" style="position:absolute; right:-20%; top:{18+i*14}%; '
                f'width:34%; height:12%; background:#1a1208; border:2px solid #c9a84c; padding:10px; '
                f'opacity:0; box-shadow:0 6px 14px rgba(0,0,0,0.55);">'
                f'<div style="font-family:Playfair Display,serif; font-weight:700; font-size:22px; color:#c9a84c;">{name}</div>'
                f'<div style="font-family:Georgia,serif; font-style:italic; font-size:16px; color:#e8d6a8; margin-top:2px;">{net}</div>'
                f'</div>'
                for i, (name, net) in enumerate([
                    ("J.D. ROCKEFELLER","$1.4 BILLION"),
                    ("ANDREW CARNEGIE","$310 MILLION"),
                    ("CORNELIUS VANDERBILT II","$72 MILLION"),
                    ("JAY GOULD","$77 MILLION"),
                    ("WILLIAM B. ASTOR","$40 MILLION"),
                ])
            )
        ),
        "custom_card_in": "\n".join(
            f"  tl.fromTo('#mag-{i}', {{ right:'-30%', opacity:0 }}, {{ right:'18%', opacity:1, duration:0.55, ease:'power2.out' }}, {0.6+i*0.4});"
            for i in range(5)
        ),
    }),

    # ==================== E. Typography on scene ====================
    22: (recipe_typo, {  # Quote / aphorism card
        "lines": [
            {"text": "BEHIND EVERY GREAT FORTUNE,", "size": 56, "weight": 700, "spacing": 3},
            {"text": "there lies a great crime.", "size": 42, "weight": 400, "spacing": 1},
            {"text": "— Honoré de Balzac", "size": 22, "weight": 400, "spacing": 1},
        ],
    }),

    23: (recipe_typo, {  # Title card / cold open
        "lines": [
            {"text": "MIDNIGHT", "size": 110, "weight": 900, "spacing": 18},
            {"text": "MAGNATES", "size": 110, "weight": 900, "spacing": 18},
            {"text": "the dark histories of wealth", "size": 22, "weight": 400, "spacing": 4},
        ],
    }),

    24: (recipe_typo, {  # Lyric / karaoke
        "lines": [
            {"text": "We met in 1929.", "size": 48, "weight": 700, "spacing": 2},
            {"text": "He had a yacht.", "size": 48, "weight": 700, "spacing": 2},
            {"text": "I had a story.", "size": 48, "weight": 700, "spacing": 2},
        ],
    }),

    25: (recipe_typo, {  # News bulletin
        "lines": [
            {"text": "BREAKING", "size": 54, "weight": 900, "spacing": 6},
            {"text": "STOCK MARKET COLLAPSES", "size": 36, "weight": 700, "spacing": 2},
            {"text": "TUESDAY · OCT 29, 1929 · NYC", "size": 18, "weight": 400, "spacing": 2},
        ],
    }),

    26: (recipe_typo, {  # Magazine spread
        "lines": [
            {"text": "THE MAN", "size": 70, "weight": 900, "spacing": 4},
            {"text": "WHO BOUGHT", "size": 70, "weight": 900, "spacing": 4},
            {"text": "MANHATTAN", "size": 70, "weight": 900, "spacing": 4},
        ],
    }),

    # ==================== F. Character pop-in ====================
    27: (recipe_portrait_card, {  # Talking-head card
        "name": "CYRUS T. ASHFORD",
        "role": "Founder, Ashford Steel",
        "dates": "1841 — 1908",
    }),
    28: (recipe_portrait_card, {  # Cast intro roster (single best-of view for test)
        "name": "THE FOUR HORSEMEN",
        "role": "Oil · Rail · Steel · Banking",
        "dates": "EST. 1882",
    }),
    29: (recipe_portrait_card, {  # Speech bubbles
        "name": "EZEKIEL P. STAUNTON",
        "role": "Founder · The Trust of '93",
        "dates": "",
        "extra_tl_js": (
            # Add a speech bubble at right
            "  // Speech bubble appears later\n"
        ),
    }),
    30: (recipe_portrait_card, {  # Dialog scene
        "name": "TWO MAGNATES",
        "role": "Negotiation, 1888",
        "dates": "",
    }),

    # ==================== G. Process ====================
    31: (recipe_step_seq, {
        "steps": ["Stake the seed claim", "Shake the right hand", "Cast the gold pyramid"],
    }),
    32: (recipe_step_seq, {
        "steps": ["Open the ledger", "Forge the entries", "Burn the evidence"],
    }),
    33: (recipe_step_seq, {
        "steps": ["Start at St. Louis", "Push west to Denver", "Strike rails to San Francisco"],
    }),
    34: (recipe_step_seq, {
        "steps": ["The firebox burns coal", "The drivewheels turn at 60 mph", "The whistle splits the night"],
    }),
    35: (recipe_step_seq, {
        "steps": ["1850 — A dirt street", "1910 — A skyscraper rises"],
    }),

    # ==================== H. Sleep Net on-brand ====================
    36: (recipe_hero_overlay, {  # Archival Ken Burns plus
        "use_stars": False, "particle_kind":"dust-mote", "particle_count":10, "particle_area":(15,40,85,90),
        "title":"THE 1885 ARRIVAL", "subtitle":"",
        "kenburns": True,
        "proc_bg": lambda: night_sky() + night_ground() + train_silhouette(),
        "extra_html": '<div id="filmscratch" style="position:absolute; inset:0; pointer-events:none; opacity:0; background-image: url(&quot;data:image/svg+xml;utf8,&lt;svg xmlns=\'http://www.w3.org/2000/svg\' width=\'1920\' height=\'1080\'&gt;&lt;line x1=\'380\' y1=\'0\' x2=\'380\' y2=\'1080\' stroke=\'%23ffffff\' stroke-opacity=\'0.18\' stroke-width=\'1\'/&gt;&lt;line x1=\'1240\' y1=\'0\' x2=\'1240\' y2=\'1080\' stroke=\'%23ffffff\' stroke-opacity=\'0.13\' stroke-width=\'1\'/&gt;&lt;/svg&gt;&quot;);"></div>',
        "extra_tl_js": "  tl.fromTo('#filmscratch', { opacity:0 }, { opacity:0.6, duration:0.05, yoyo:true, repeat:Math.ceil(D/0.6)*2, ease:'power2.out' }, 0.2);",
    }),
    37: (recipe_portrait_card, {  # Documentary photo card
        "name": "EZEKIEL P. STAUNTON",
        "role": "",
        "dates": "1841 — 1908",
    }),
    38: (recipe_card_stage, {  # Wealth artifact card
        "title":"", "subtitle":"C.A. — 1893",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="card" class="clip" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%) scale(0.85); '
            'width:46%; height:60%; background: radial-gradient(circle, #2a1f15, #0e0a08); '
            'border:6px solid #c9a84c; border-radius:8px; box-shadow:0 24px 60px rgba(0,0,0,0.8); padding:30px;">'
            '<svg viewBox="0 0 400 400" style="width:100%; height:100%;">'
            # Pocket watch face
            '<circle cx="200" cy="200" r="140" fill="#1a1208" stroke="#c9a84c" stroke-width="5"/>'
            '<circle cx="200" cy="200" r="118" fill="none" stroke="#8a6e23" stroke-width="2"/>'
            # Hour markers
            + "".join(
                f'<line x1="{200 + 105*__import__("math").cos((-90+i*30)*3.14159/180):.1f}" '
                f'y1="{200 + 105*__import__("math").sin((-90+i*30)*3.14159/180):.1f}" '
                f'x2="{200 + 120*__import__("math").cos((-90+i*30)*3.14159/180):.1f}" '
                f'y2="{200 + 120*__import__("math").sin((-90+i*30)*3.14159/180):.1f}" '
                f'stroke="#c9a84c" stroke-width="3"/>'
                for i in range(12)
            )
            # Hands
            + '<line x1="200" y1="200" x2="200" y2="120" stroke="#c9a84c" stroke-width="4" stroke-linecap="round" id="hour-hand"/>'
            + '<line x1="200" y1="200" x2="260" y2="200" stroke="#c9a84c" stroke-width="2.5" stroke-linecap="round" id="minute-hand"/>'
            + '<circle cx="200" cy="200" r="6" fill="#c9a84c"/>'
            # Crown
            + '<rect x="190" y="50" width="20" height="14" fill="#c9a84c"/>'
            # Monogram below
            + '<text x="200" y="290" text-anchor="middle" font-family="Playfair Display,serif" font-weight="700" font-size="38" fill="#c9a84c">C.A.</text>'
            + '</svg>'
            + '</div>'
            # Spotlight overlay
            + '<div id="spot" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:80%; height:80%; pointer-events:none; background: radial-gradient(circle, rgba(255,220,140,0.4), transparent 60%); mix-blend-mode:screen; opacity:0;"></div>'
        ),
        "custom_card_in": (
            "  MM.slamIn(tl, { selector: '#card', start: 0.5, fromScale: 1.2, fromY: -10 });\n"
            "  tl.fromTo('#spot', { opacity:0 }, { opacity:0.7, duration:1.0, yoyo:true, repeat:Math.ceil((D-1)/1)*2, ease:'sine.inOut' }, 1.2);\n"
            "  tl.to('#hour-hand', { rotation: 30, transformOrigin:'200px 200px', duration: D-1, ease:'none' }, 0.8);\n"
            "  tl.to('#minute-hand', { rotation: 360, transformOrigin:'200px 200px', duration: D-1, ease:'none' }, 0.8);"
        ),
    }),
    39: (recipe_hero_overlay, {  # Ambient nature loop — slow drift, moonlit grounds
        "use_stars": True,
        "particle_kind":"dust-mote", "particle_count":12, "particle_area":(10,40,90,90),
        "title":"", "subtitle":"",
        "kenburns": True,
        "proc_bg": lambda: night_sky() + night_ground() + mansion_silhouette(scale=0.9, bottom="22%"),
    }),
    40: (recipe_document, {  # Period document reveal — land-grant deed
        "title":"OFFICIAL RECORD", "subtitle":"Land Grant, 1879",
        "show_stamp": True,
        "extra_html": (
            '<div id="stamp" class="clip" style="position:absolute; right:9%; top:18%; '
            'color:#a02020; font-family:\'Playfair Display\',serif; font-weight:900; font-size:48px; '
            'letter-spacing:6px; padding:12px 26px; border:6px solid #a02020; '
            'transform: rotate(-12deg); opacity:0; z-index:60; text-shadow: 0 0 4px rgba(0,0,0,0.4);">FILED</div>'
        ),
    }),

    # ==================== I. Audio-reactive ====================
    41: (recipe_hero_overlay, {  # Waveform burn — portrait + waveform across chest
        "use_stars": False, "particle_kind":None,
        "title":"THE BROADCAST", "subtitle":"KMM-1929, 8:00 PM",
        "extra_html": (
            '<svg id="waveform" style="position:absolute; left:8%; right:8%; top:62%; height:120px; opacity:0;" viewBox="0 0 1500 120" preserveAspectRatio="none">'
            + '<path id="wave-path" d="M 0 60 ' + ' '.join(f"L {i*30} {60 + (((i*17)%23)-11)*4}" for i in range(1, 51)) + '" fill="none" stroke="#c9a84c" stroke-width="2.5" filter="drop-shadow(0 0 6px rgba(201,168,76,0.8))"/>'
            + '</svg>'
        ),
        "extra_tl_js": (
            "  tl.fromTo('#waveform', { opacity:0 }, { opacity:0.9, duration:0.6 }, 0.5);\n"
            "  tl.to('#wave-path', { scaleY:1.4, transformOrigin:'750px 60px', duration:0.18, yoyo:true, repeat:Math.ceil((D-1)/0.36)*2, ease:'sine.inOut' }, 0.8);"
        ),
    }),
    42: (recipe_hero_overlay, {  # EQ bar overlay
        "use_stars": False, "particle_kind":None,
        "title":"", "subtitle":"",
        "proc_bg": lambda: '<div style="position:absolute; inset:0; background: radial-gradient(ellipse 1200px 900px at 50% 50%, #2a1810 0%, #0a0606 70%);"></div>' + record_player_silhouette(),
        "extra_html": (
            '<div id="eq" style="position:absolute; left:50%; bottom:18%; transform:translateX(-50%); width:60%; height:120px; display:flex; align-items:flex-end; justify-content:space-between; gap:8px; opacity:0;">'
            + "".join(f'<div class="eq-bar" id="eq-{i}" style="width:6%; height:18%; background: linear-gradient(180deg, #c9a84c, #8a6e23); border-radius:3px; box-shadow:0 0 10px rgba(201,168,76,0.5);"></div>' for i in range(10))
            + '</div>'
        ),
        "extra_tl_js": (
            "  tl.fromTo('#eq', { opacity:0 }, { opacity:0.95, duration:0.4 }, 0.4);\n"
            + "\n".join(
                f"  tl.to('#eq-{i}', {{ height: '{40+(i*7)%70}%', duration: 0.18, yoyo:true, repeat:Math.ceil((D-0.6)/0.36)*2, ease:'sine.inOut' }}, {0.5 + i*0.05});"
                for i in range(10)
            )
        ),
    }),
    43: (recipe_hero_overlay, {  # Beat-flash scene
        "use_stars": False, "particle_kind":"dust-mote", "particle_count":8, "particle_area":(20,30,80,80),
        "title":"", "subtitle":"",
        "proc_bg": lambda: '<div style="position:absolute; inset:0; background: linear-gradient(180deg, #2a1208 0%, #0a0606 100%);"></div>' + ballroom_silhouette(),
        "extra_tl_js": "  MM.beatFlash(tl, { selector: '#root', bpm: 96, duration: D });",
    }),
    44: (recipe_hero_overlay, {  # Pulse halo character — pulpit speaker
        "use_stars": False, "particle_kind":None,
        "title":"", "subtitle":"",
        "extra_html": (
            '<div id="halo" style="position:absolute; left:50%; top:32%; transform:translate(-50%,-50%); width:520px; height:520px; '
            'border-radius:50%; background: radial-gradient(circle, rgba(201,168,76,0.0) 35%, rgba(201,168,76,0.4) 45%, rgba(201,168,76,0.0) 70%); '
            'mix-blend-mode:screen; opacity:0; pointer-events:none;"></div>'
        ),
        "extra_tl_js": (
            "  tl.fromTo('#halo', { opacity:0, scale:0.6 }, { opacity:0.95, scale:1, duration:0.6, ease:'sine.out' }, 0.4);\n"
            "  tl.to('#halo', { scale:1.18, opacity:0.5, duration:0.6, yoyo:true, repeat:Math.ceil((D-1)/1.2)*2, ease:'sine.inOut' }, 1.0);"
        ),
    }),
    45: (recipe_portrait_card, {  # Mouth amplitude pulse
        "name": "ON-AIR",
        "role": "live address, 1907",
        "dates": "",
        "extra_tl_js": (
            "  // Subtle 'breathing' on the portrait (mouth-area proxy)\n"
            "  tl.to('#portrait', { scaleY:1.012, duration:0.4, yoyo:true, repeat:Math.ceil((D-1)/0.8)*2, ease:'sine.inOut', transformOrigin:'50% 70%' }, 1.0);"
        ),
    }),

    # ==================== J. Phone / chat UI ====================
    46: (recipe_ui_mockup, {  # iMessage scroll
        "title":"", "subtitle":"",
        "ui_html": (
            '<div id="phone" class="clip" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); '
            'width:520px; height:920px; background:#0d111c; border:14px solid #1a1a22; border-radius:60px; '
            'box-shadow:0 24px 60px rgba(0,0,0,0.8); overflow:hidden; padding:60px 20px 20px 20px;">'
            '<div style="text-align:center; color:#c9a84c; font-family:Playfair Display,serif; font-size:18px; padding:6px; border-bottom:1px solid #2a2a3a;">THE BENEFACTOR</div>'
            '<div class="bubble" id="bub0" style="margin:30px 30px 6px auto; max-width:70%; background:#1f2a3f; color:#f5f0e4; padding:14px 18px; border-radius:18px; font-size:22px; opacity:0;">Are the documents ready?</div>'
            '<div class="bubble" id="bub-typing" style="margin:18px auto 6px 30px; background:#2a2a3a; color:#888; padding:14px 18px; border-radius:18px; font-size:22px; opacity:0; width:60px;">• • •</div>'
            '<div class="bubble" id="bub1" style="margin:6px auto 6px 30px; max-width:70%; background:#2a3f6e; color:#f5f0e4; padding:14px 18px; border-radius:18px; font-size:22px; opacity:0;">Burning them tonight.</div>'
            '</div>'
        ),
        "extra_tl_js": (
            "  MM.slamIn(tl, { selector: '#phone', start: 0.4, fromScale:1.15, fromY:-20 });\n"
            "  tl.fromTo('#bub0', { opacity:0, y:14 }, { opacity:1, y:0, duration:0.5, ease:'sine.out' }, 1.4);\n"
            "  tl.fromTo('#bub-typing', { opacity:0 }, { opacity:1, duration:0.3 }, 2.4);\n"
            "  tl.to('#bub-typing', { opacity:0, duration:0.3 }, 3.6);\n"
            "  tl.fromTo('#bub1', { opacity:0, y:14 }, { opacity:1, y:0, duration:0.5, ease:'sine.out' }, 3.8);"
        ),
    }),
    47: (recipe_ui_mockup, {  # Tweet thread
        "title":"", "subtitle":"",
        "ui_html": (
            '<div style="position:absolute; left:24%; right:24%; top:8%; bottom:8%; background:#11141c; border:2px solid #2a2a3a; border-radius:16px; padding:24px; box-shadow:0 24px 60px rgba(0,0,0,0.6);">'
            + "".join(
                f'<div class="tweet" id="tw-{i}" style="background:#181b25; padding:16px; border-radius:8px; margin-top:12px; opacity:0;">'
                f'<div style="display:flex; align-items:center; gap:8px;">'
                f'<div style="width:48px; height:48px; border-radius:50%; background:#3a2a1d;"></div>'
                f'<div>'
                f'<div style="font-family:Playfair Display,serif; font-weight:700; color:#c9a84c; font-size:18px;">@TheMagnateFile <span style="color:#c9a84c;">✓</span></div>'
                f'<div style="color:#7a7a8a; font-size:14px;">2h</div>'
                f'</div></div>'
                f'<div style="color:#f5f0e4; margin-top:12px; font-size:20px;">{tweet}</div>'
                f'<div style="color:#7a7a8a; font-size:14px; margin-top:12px;">🔁 {1247-i*200}  ♡ {3214-i*400}</div>'
                f'</div>'
                for i, tweet in enumerate([
                    "1/ I found the trust documents. They are all signed in the same hand.",
                    "2/ The hand belongs to a man who died in 1898. The trust was filed in 1924.",
                    "3/ The estate is still receiving payments. We have follow-up tomorrow.",
                ])
            )
            + '</div>'
        ),
        "extra_tl_js": (
            "\n".join(f"  tl.fromTo('#tw-{i}', {{ opacity:0, y:20 }}, {{ opacity:1, y:0, duration:0.5, ease:'sine.out' }}, {1.0 + i*1.2});" for i in range(3))
        ),
    }),
    48: (recipe_ui_mockup, {  # Search query
        "title":"", "subtitle":"",
        "ui_html": (
            '<div style="position:absolute; left:14%; right:14%; top:18%; height:64px; background:#1a1f2c; border:2px solid #c9a84c; border-radius:32px; padding:12px 28px; box-shadow:0 18px 36px rgba(0,0,0,0.7); display:flex; align-items:center; gap:14px;">'
            '<div style="color:#c9a84c; font-size:24px;">⌕</div>'
            '<div id="search-text" style="font-family:Georgia,serif; font-size:24px; color:#f5f0e4; white-space:nowrap; overflow:hidden; width:0;">how did the vanderbilts lose 4 billion dollars</div>'
            '</div>'
            + "".join(
                f'<div class="result clip" id="res-{i}" style="position:absolute; left:14%; right:14%; top:{34+i*18}%; padding:18px 28px; background:#0f131c; border-left:4px solid #c9a84c; opacity:0;">'
                f'<div style="font-family:Playfair Display,serif; font-weight:700; color:#c9a84c; font-size:24px;">{title}</div>'
                f'<div style="color:#7a7a8a; font-size:16px;">{url}</div>'
                f'<div style="color:#f5f0e4; font-size:18px; margin-top:6px;">{snip}</div>'
                f'</div>'
                for i, (title, url, snip) in enumerate([
                    ("The Vanderbilt Decline — How $200M became $0", "midnightmagnates.tv/vanderbilts", "By 1973 not one Vanderbilt remained on the Fortune 400..."),
                    ("Pierre Lorillard and the 'Crash of Newport'", "midnightmagnates.tv/lorillard", "Three generations of cotton money lost in twelve years..."),
                    ("Inside the Trust That Funded the Decline", "midnightmagnates.tv/trust1873", "The trust was administered by men who profited from its dissolution..."),
                ])
            )
        ),
        "extra_tl_js": (
            "  tl.fromTo('#search-text', { width:0 }, { width:'100%', duration:2.0, ease:'none' }, 0.6);\n"
            + "\n".join(f"  tl.fromTo('#res-{i}', {{ opacity:0, y:14 }}, {{ opacity:1, y:0, duration:0.45, ease:'sine.out' }}, {2.8 + i*0.5});" for i in range(3))
        ),
    }),
    49: (recipe_ui_mockup, {  # App notification stack
        "title":"", "subtitle":"",
        "ui_html": (
            '<div id="phone" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:480px; height:920px; background:#0a0d18; border:14px solid #1a1a22; border-radius:60px; box-shadow:0 24px 60px rgba(0,0,0,0.8); overflow:hidden;">'
            '<div style="text-align:center; color:#f5f0e4; font-family:Courier New,monospace; font-size:96px; padding-top:140px;">03:14</div>'
            '<div style="text-align:center; color:#c9a84c; font-family:Georgia,serif; font-size:24px;">TUESDAY, OCT 22</div>'
            + "".join(
                f'<div class="notif clip" id="notif-{i}" style="margin:20px 20px 0 20px; padding:16px; background:rgba(20,28,48,0.85); border-radius:14px; opacity:0;">'
                f'<div style="font-family:Playfair Display,serif; color:#c9a84c; font-weight:700; font-size:18px;">{title}</div>'
                f'<div style="color:#f5f0e4; font-size:18px; margin-top:4px;">{body}</div>'
                f'</div>'
                for i, (title, body) in enumerate([
                    ("WIRE TRANSFER","$4.2M outgoing — confirmed."),
                    ("VAULT ACCESS","Bay 7 opened at 02:55 AM."),
                    ("ENCRYPTED MAIL","1 message from THE CONSORTIUM."),
                    ("NEWS","Estate liquidation announced."),
                ])
            )
            + '</div>'
        ),
        "extra_tl_js": (
            "  MM.slamIn(tl, { selector: '#phone', start: 0.4, fromScale:1.12, fromY:-20 });\n"
            + "\n".join(f"  tl.fromTo('#notif-{i}', {{ opacity:0, y:-30 }}, {{ opacity:1, y:0, duration:0.45, ease:'sine.out' }}, {1.3 + i*0.7});" for i in range(4))
        ),
    }),
    50: (recipe_ui_mockup, {  # Email inbox reveal
        "title":"", "subtitle":"",
        "ui_html": (
            '<div style="position:absolute; left:10%; right:10%; top:8%; bottom:8%; background:#0a0d18; border:2px solid #2a2a3a; border-radius:8px; box-shadow:0 24px 60px rgba(0,0,0,0.7); overflow:hidden;">'
            '<div style="padding:16px 24px; background:#181b25; color:#c9a84c; font-family:Playfair Display,serif; font-size:24px; border-bottom:1px solid #2a2a3a;">INBOX (37)</div>'
            + "".join(
                f'<div class="email clip" id="em-{i}" style="padding:14px 24px; border-bottom:1px solid #1a1d27; display:flex; align-items:center; gap:14px; opacity:0; {"background: linear-gradient(90deg, #1f2a3f, transparent 60%);" if i==2 else ""}">'
                f'<div style="font-family:Playfair Display,serif; color:#c9a84c; font-weight:{"700" if i==2 else "400"}; font-size:18px; flex:0 0 22%;">{sender}</div>'
                f'<div style="color:#f5f0e4; font-size:18px; flex:1; font-weight:{"700" if i==2 else "400"};">{subj}</div>'
                f'<div style="color:#7a7a8a; font-size:14px;">{time}</div>'
                f'</div>'
                for i, (sender, subj, time) in enumerate([
                    ("Astor & Co.","RE: shipping schedule","Mon"),
                    ("J.P. Morgan & Co.","Q4 ledger reconciliation","Mon"),
                    ("EZEKIEL ASHFORD","RE: THE TRUST LIQUIDATION","02:47 AM"),
                    ("Carnegie Steel","invoice #29-2104","Sun"),
                    ("Vanderbilt Rail","weekly schedule","Sun"),
                    ("Tammany Hall","reminder — Thursday","Sat"),
                ])
            )
            + '</div>'
            + '<div id="open-stamp" class="clip" style="position:absolute; left:50%; top:55%; transform:translate(-50%,-50%); padding:18px 60px; background:rgba(180,30,30,0.95); color:#f5f0e4; font-family:Playfair Display,serif; font-weight:900; font-size:48px; letter-spacing:8px; opacity:0; transform-origin:center;">CONFIDENTIAL</div>'
        ),
        "extra_tl_js": (
            "\n".join(f"  tl.fromTo('#em-{i}', {{ opacity:0, x:-30 }}, {{ opacity:1, x:0, duration:0.35, ease:'sine.out' }}, {0.6 + i*0.32});" for i in range(6))
            + "\n  tl.fromTo('#em-2', { backgroundColor: '#1f2a3f' }, { backgroundColor: '#2a3f6e', duration: 0.4, yoyo:true, repeat:Math.ceil((D-3)/0.8)*2, ease:'sine.inOut' }, 3.0);\n"
            + "  tl.fromTo('#open-stamp', { opacity:0, scale:0.6, rotate:-20 }, { opacity:0.95, scale:1, rotate:-12, duration:0.6, ease:'power2.out' }, 4.4);"
        ),
    }),

    # ==================== K. Vintage media ====================
    51: (recipe_vintage_media, {"kind":"crt", "title":"BREAKING NEWS", "subtitle":"1978"}),
    52: (recipe_vintage_media, {"kind":"vhs", "title":"SECURITY LOG", "subtitle":"1986"}),
    53: (recipe_card_stage, {  # Newspaper unfold
        "title":"THE TRIBUNE", "subtitle":"OCTOBER 30, 1929",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="card" class="clip" style="position:absolute; left:14%; right:14%; top:10%; bottom:10%; '
            'background: linear-gradient(180deg, #e0d4ac, #c4b387); border:3px solid #6e5836; padding:28px; '
            'box-shadow:0 24px 60px rgba(0,0,0,0.7);">'
            '<div style="text-align:center; font-family:Playfair Display,serif; font-weight:900; font-size:42px; color:#3a2410; letter-spacing:4px; border-bottom:3px solid #3a2410; padding-bottom:6px;">THE TRIBUNE</div>'
            '<div style="text-align:center; font-family:Georgia,serif; font-style:italic; font-size:14px; color:#5a4830; margin-top:4px;">EST. 1847 · VOL. LXXXII · NO. 304 · TUESDAY · OCT 30, 1929 · TEN CENTS</div>'
            '<div id="headline" style="text-align:center; font-family:Playfair Display,serif; font-weight:900; font-size:78px; color:#1a0e08; margin-top:24px; line-height:1.0; opacity:0;">'
            'STOCK MARKET<br/>COLLAPSES'
            '</div>'
            '<div style="margin-top:14px; columns:3; column-gap:18px; font-family:Georgia,serif; font-size:14px; color:#3a2410; line-height:1.4;">'
            'FROM OUR FINANCIAL DESK — Yesterday the New York Stock Exchange experienced an unprecedented collapse of values. Trading reached frenzied levels in the final hour. Reports estimate losses of forty billion dollars. The Federal Reserve has issued no statement. President Hoover is in Washington consulting with advisors. The Tribune will provide continued coverage as events unfold.'
            ' Reports estimate losses of forty billion dollars. The Federal Reserve has issued no statement. President Hoover is in Washington consulting with advisors. The Tribune will provide continued coverage as events unfold throughout the week.'
            '</div></div>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#card', { scaleX:0.04, scaleY:1, opacity:0 }, { scaleX:1, scaleY:1, opacity:1, duration:1.1, ease:'sine.out' }, 0.4);\n"
            "  tl.fromTo('#headline', { opacity:0, scale:0.85 }, { opacity:1, scale:1, duration:0.9, ease:'sine.out' }, 1.6);"
        ),
    }),
    54: (recipe_hero_overlay, {  # Radio drama scene
        "use_stars": False, "particle_kind":None,
        "title":"STATION KMM-1929", "subtitle":"",
        "extra_html": (
            '<svg id="dial" style="position:absolute; left:50%; bottom:14%; transform:translateX(-50%); width:560px; height:200px;" viewBox="0 0 560 200">'
            '<rect x="0" y="0" width="560" height="200" rx="20" fill="#1a1208" stroke="#c9a84c" stroke-width="3"/>'
            '<line x1="40" y1="100" x2="520" y2="100" stroke="#c9a84c" stroke-width="2" opacity="0.5"/>'
            + "".join(f'<line x1="{40+i*48}" y1="80" x2="{40+i*48}" y2="120" stroke="#c9a84c" stroke-width="1"/><text x="{40+i*48}" y="146" text-anchor="middle" fill="#c9a84c" font-family="Courier New,monospace" font-size="13">{600+i*100}</text>' for i in range(11))
            + '<line id="needle" x1="40" y1="60" x2="40" y2="140" stroke="#b41e1e" stroke-width="3"/>'
            + '</svg>'
            + '<div id="static" style="position:absolute; inset:0; pointer-events:none; opacity:0; mix-blend-mode:overlay; background-image: url(&quot;data:image/svg+xml;utf8,&lt;svg xmlns=\'http://www.w3.org/2000/svg\' width=\'400\' height=\'400\'&gt;&lt;filter id=\'s\'&gt;&lt;feTurbulence type=\'fractalNoise\' baseFrequency=\'2.0\' numOctaves=\'4\'/&gt;&lt;/filter&gt;&lt;rect width=\'100%\' height=\'100%\' filter=\'url(%23s)\'/&gt;&lt;/svg&gt;&quot;);"></div>'
        ),
        "extra_tl_js": (
            "  tl.fromTo('#needle', { attr:{x1:40,x2:40} }, { attr:{x1:520,x2:520}, duration:D-1, ease:'sine.inOut' }, 0.5);\n"
            "  tl.fromTo('#static', { opacity:0 }, { opacity:0.55, duration:0.06, yoyo:true, repeat:Math.ceil(D/0.4)*2, ease:'power2.out' }, 0.2);"
        ),
    }),
    55: (recipe_vintage_media, {"kind":"projector", "title":"REEL VII", "subtitle":"FACTORY · 1904"}),

    # ==================== L. Game / RPG ====================
    56: (recipe_card_stage, {  # Trading card flip
        "title":"", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="card" class="clip" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); '
            'width:36%; height:74%; background: linear-gradient(135deg, #c9a84c 0%, #8a6e23 100%); border-radius:18px; '
            'box-shadow:0 24px 60px rgba(0,0,0,0.8); padding:18px; opacity:0;">'
            '<div style="background:#1a1208; height:100%; border-radius:12px; padding:16px; position:relative;">'
            '<div style="text-align:center; font-family:Playfair Display,serif; font-weight:900; font-size:28px; color:#c9a84c; letter-spacing:2px; border-bottom:2px solid #c9a84c; padding-bottom:8px;">THE MAGNATE</div>'
            '<div style="margin:14px auto; height:62%; background: linear-gradient(180deg, #2a1f15, #0a0706); border:2px solid #c9a84c; position:relative;">'
            '<svg viewBox="0 0 100 100" style="position:absolute; inset:0; width:100%; height:100%;" preserveAspectRatio="xMidYMid meet">'
            '<ellipse cx="50" cy="38" rx="14" ry="18" fill="#0a0706"/>'
            '<path d="M 36 18 L 64 18 L 64 8 L 56 8 L 56 0 L 44 0 L 44 8 L 36 8 Z" fill="#0a0706"/>'
            '<path d="M 30 100 L 30 60 Q 50 50 70 60 L 70 100 Z" fill="#0a0706"/></svg>'
            '</div>'
            '<div style="text-align:center; color:#c9a84c; font-family:Georgia,serif; font-size:14px;">CHAPTER VII · LEGENDARY</div>'
            '<div id="foil" style="position:absolute; inset:0; pointer-events:none; mix-blend-mode:screen; opacity:0; background: linear-gradient(110deg, transparent 30%, rgba(255,240,180,0.7) 50%, transparent 70%);"></div>'
            '</div></div>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#card', { rotateY:-180, opacity:0 }, { rotateY:0, opacity:1, duration:1.2, ease:'sine.out' }, 0.5);\n"
            "  tl.fromTo('#foil', { opacity:0, x:-200 }, { opacity:0.95, x:300, duration:1.2, ease:'sine.inOut' }, 2.2);\n"
            "  tl.to('#foil', { opacity:0, duration:0.3 }, 3.4);"
        ),
    }),
    57: (recipe_portrait_card, {  # RPG stat sheet
        "name": "C.T. ASHFORD",
        "role": "STEEL TYCOON · LV 99",
        "dates": "",
        "extra_tl_js": (
            "  // Bars are conceptual; we represent with name banner glow as proxy\n"
        ),
    }),
    58: (recipe_card_stage, {  # Inventory slot reveal — 6 slots
        "title":"MAGNATE'S CACHE", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            "".join(
                f'<div class="slot clip" id="slot-{i}" style="position:absolute; left:{20+(i%3)*22}%; top:{32+(i//3)*30}%; '
                f'width:18%; height:24%; background: linear-gradient(135deg, #2a1f15, #1a1208); border:3px solid #c9a84c; '
                f'border-radius:8px; box-shadow:inset 0 0 20px rgba(201,168,76,0.25); opacity:0; '
                f'display:flex; align-items:center; justify-content:center; font-family:Playfair Display,serif; font-size:24px; color:#c9a84c;">'
                f'{label}</div>'
                for i, label in enumerate(["GOLD BAR","POCKET WATCH","DEED SCROLL","MERCURY VIAL","BRASS KEY","LEDGER"])
            )
        ),
        "custom_card_in": "\n".join(f"  MM.slamIn(tl, {{ selector: '#slot-{i}', start: {0.5 + i*0.32}, fromScale:1.2, fromY:-20 }});" for i in range(6)),
    }),
    59: (recipe_card_stage, {  # Boss intro
        "title":"ASHFORD, THE INSATIABLE", "subtitle":"CHAPTER VII · THE TRUST",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="card" class="clip" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); '
            'width:50%; height:60%; background: radial-gradient(ellipse at 50% 40%, #2a1208, #060403); '
            'border:6px solid #b41e1e; box-shadow:0 24px 60px rgba(180,30,30,0.5); opacity:0; position:relative;">'
            '<div id="hp-label" style="position:absolute; top:14px; left:14px; right:14px; font-family:Courier New,monospace; color:#b41e1e; font-size:14px; letter-spacing:2px;">HEALTH</div>'
            '<div style="position:absolute; top:36px; left:14px; right:14px; height:14px; background:#2a0a0a; border:1px solid #b41e1e;">'
            '<div id="hp-bar" style="height:100%; background:#b41e1e; transform-origin:left center; transform:scaleX(0); box-shadow:0 0 10px #b41e1e;"></div>'
            '</div>'
            '<svg viewBox="0 0 100 100" style="position:absolute; inset:0; width:100%; height:100%;" preserveAspectRatio="xMidYMid meet">'
            '<ellipse cx="50" cy="42" rx="16" ry="20" fill="#0a0706"/>'
            '<path d="M 32 22 L 68 22 L 68 10 L 60 10 L 60 0 L 40 0 L 40 10 L 32 10 Z" fill="#0a0706"/>'
            '<path d="M 24 100 L 24 60 Q 50 48 76 60 L 76 100 Z" fill="#0a0706"/></svg>'
            '</div>'
        ),
        "custom_card_in": (
            "  MM.slamIn(tl, { selector: '#card', start: 0.4, fromScale:1.4, fromY:-30 });\n"
            "  MM.barFill(tl, { selector: '#hp-bar', start: 1.4, duration: 1.2 });"
        ),
    }),
    60: (recipe_typo, {  # 8-bit start screen
        "lines": [
            {"text": "■ MIDNIGHT ■", "size": 64, "weight": 900, "spacing": 6},
            {"text": "■ MAGNATES ■", "size": 64, "weight": 900, "spacing": 6},
            {"text": "PRESS START", "size": 28, "weight": 700, "spacing": 4},
        ],
        "extra_tl_js": (
            "  // 8-bit pixel-blink on last line\n"
            "  tl.to('#typo-2', { opacity:0.0, duration:0.4, yoyo:true, repeat:Math.ceil((D-2.5)/0.8)*2, ease:'steps(1)' }, 2.6);"
        ),
    }),

    # ==================== M. Evidence board ====================
    61: (recipe_card_stage, {  # Corkboard with string
        "title":"CASE FILE 1899-A", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            '<div style="position:absolute; inset:6%; background: repeating-linear-gradient(45deg, #6e5836 0px, #6e5836 2px, #5a4830 2px, #5a4830 6px), #5a4830; box-shadow: inset 0 0 200px rgba(0,0,0,0.5);"></div>'
            + "".join(
                f'<div class="evidence clip" id="ev-{i}" style="position:absolute; left:{15+(i%3)*26}%; top:{16+(i//3)*36}%; '
                f'width:22%; height:30%; background:#2a1f15; border:6px solid #d8caa0; box-shadow:0 8px 24px rgba(0,0,0,0.6); '
                f'transform: rotate({-8 + i*4}deg); opacity:0;">'
                f'<div style="background:#5a4830; width:100%; height:100%;"></div>'
                f'<div style="position:absolute; left:50%; top:0; transform:translate(-50%,-40%); width:24px; height:24px; border-radius:50%; background:#b41e1e; box-shadow:0 2px 6px rgba(0,0,0,0.7);"></div>'
                f'</div>'
                for i in range(6)
            )
            # Red strings (SVG paths) connecting evidence
            + '<svg style="position:absolute; inset:0; pointer-events:none;" viewBox="0 0 1920 1080" preserveAspectRatio="none">'
            + '<path id="str-0" d="M 460 280 L 980 280" stroke="#b41e1e" stroke-width="3" fill="none" stroke-dasharray="600" stroke-dashoffset="600" filter="drop-shadow(0 2px 4px rgba(0,0,0,0.7))"/>'
            + '<path id="str-1" d="M 980 280 L 1500 280" stroke="#b41e1e" stroke-width="3" fill="none" stroke-dasharray="600" stroke-dashoffset="600"/>'
            + '<path id="str-2" d="M 460 280 L 460 700" stroke="#b41e1e" stroke-width="3" fill="none" stroke-dasharray="500" stroke-dashoffset="500"/>'
            + '<path id="str-3" d="M 1500 280 L 1500 700" stroke="#b41e1e" stroke-width="3" fill="none" stroke-dasharray="500" stroke-dashoffset="500"/>'
            + '</svg>'
        ),
        "custom_card_in": (
            "\n".join(f"  MM.slamIn(tl, {{ selector: '#ev-{i}', start: {0.5+i*0.28}, fromScale:1.15, fromY:-30 }});" for i in range(6))
            + "\n" + "\n".join(f"  MM.pathDraw(tl, {{ selector: '#str-{i}', start: {3.4+i*0.4}, duration:0.9 }});" for i in range(4))
        ),
    }),
    62: (recipe_document, {  # Case file open
        "title":"", "subtitle":"",
        "show_stamp": True,
        "extra_html": (
            '<div id="stamp" class="clip" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); '
            'color:#b41e1e; font-family:\'Playfair Display\',serif; font-weight:900; font-size:88px; '
            'letter-spacing:14px; padding:20px 40px; border:8px solid #b41e1e; opacity:0; z-index:60; '
            'text-shadow: 0 0 4px rgba(0,0,0,0.4);">CLASSIFIED</div>'
        ),
    }),
    63: (recipe_card_stage, {  # Suspect lineup
        "title":"SUSPECT LINEUP", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            '<div style="position:absolute; inset:8% 4% 8% 4%; background: linear-gradient(180deg, #2a2a2a 0%, #1a1a1a 100%);"></div>'
            # Height marker lines
            + "".join(f'<div style="position:absolute; left:0; right:0; top:{20+i*8}%; height:1px; background:rgba(255,255,255,0.2);"></div><div style="position:absolute; left:1%; top:{18+i*8}%; color:#fff; font-family:Courier New,monospace; font-size:14px;">{6-i} FT</div>' for i in range(5))
            + "".join(
                f'<div class="suspect clip" id="susp-{i}" style="position:absolute; left:{12+i*16}%; bottom:12%; '
                f'width:14%; height:60%; background:#0a0706; opacity:0;">'
                f'<svg viewBox="0 0 100 200" style="width:100%; height:100%;" preserveAspectRatio="xMidYMid meet">'
                f'<ellipse cx="50" cy="40" rx="22" ry="30" fill="#0a0706"/>'
                f'<path d="M 30 24 L 70 24 L 70 12 L 60 12 L 60 0 L 40 0 L 40 12 L 30 12 Z" fill="#0a0706"/>'
                f'<path d="M 20 200 L 20 90 Q 50 76 80 90 L 80 200 Z" fill="#0a0706"/></svg>'
                f'<div style="text-align:center; color:#c9a84c; font-family:Courier New,monospace; font-size:14px; margin-top:6px;">SUSPECT {i+1}</div>'
                f'</div>'
                for i in range(5)
            )
            + '<div id="crosshair" class="clip" style="position:absolute; left:0; top:30%; width:160px; height:160px; border:3px solid #b41e1e; border-radius:50%; opacity:0; pointer-events:none;">'
            + '<div style="position:absolute; left:50%; top:0; bottom:0; width:1px; background:#b41e1e;"></div>'
            + '<div style="position:absolute; top:50%; left:0; right:0; height:1px; background:#b41e1e;"></div>'
            + '</div>'
            + '<div id="lineup-label" class="clip" style="position:absolute; left:50%; bottom:6%; transform:translateX(-50%); color:#c9a84c; font-family:Playfair Display,serif; font-weight:700; font-size:30px; letter-spacing:3px; opacity:0;">EZEKIEL ASHFORD — THE BAGMAN</div>'
        ),
        "custom_card_in": (
            "\n".join(f"  MM.slamIn(tl, {{ selector: '#susp-{i}', start: {0.4+i*0.18}, fromScale:1.1, fromY:-20 }});" for i in range(5))
            + "\n  tl.fromTo('#crosshair', { left:'10%', opacity:0 }, { left:'40%', opacity:0.9, duration:2.0, ease:'sine.inOut' }, 1.8);\n"
            + "  tl.fromTo('#lineup-label', { opacity:0, y:14 }, { opacity:0.95, y:0, duration:0.8, ease:'sine.out' }, 4.0);"
        ),
    }),
    64: (recipe_card_stage, {  # Polygraph reading
        "title":"INTERROGATION 1899", "subtitle":"DID YOU AUTHORIZE THE FIRE?",
        "image_is_backdrop": True,
        "card_html": (
            '<svg id="poly" style="position:absolute; left:8%; right:8%; top:30%; height:300px;" viewBox="0 0 1500 300" preserveAspectRatio="none">'
            '<rect x="0" y="0" width="1500" height="300" fill="#e0d4ac" opacity="0.4"/>'
            # Horizontal rules
            + "".join(f'<line x1="0" y1="{50+i*40}" x2="1500" y2="{50+i*40}" stroke="#3a2410" stroke-width="0.5" opacity="0.4"/>' for i in range(7))
            # Polygraph line — draws across
            + '<path id="poly-line" d="M 0 150 Q 200 100 350 140 T 700 130 Q 900 60 1100 240 T 1500 100" fill="none" stroke="#b41e1e" stroke-width="2" stroke-dasharray="2200" stroke-dashoffset="2200"/>'
            + '</svg>'
        ),
        "custom_card_in": "  MM.pathDraw(tl, { selector: '#poly-line', start: 0.6, duration: D-1.4 });",
    }),
    65: (recipe_card_stage, {  # Crime scene tape
        "title":"CRIME SCENE", "subtitle":"DO NOT CROSS",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="tape" class="clip" style="position:absolute; left:-20%; right:-20%; top:42%; height:80px; transform:rotate(-12deg) translateX(-100%); background: repeating-linear-gradient(45deg, #f7d234 0px, #f7d234 30px, #000 30px, #000 36px); opacity:0; z-index:30;">'
            '<div style="text-align:center; line-height:80px; font-family:Playfair Display,serif; font-weight:900; font-size:36px; letter-spacing:6px; color:#000;">CRIME SCENE · DO NOT CROSS · CRIME SCENE · DO NOT CROSS</div>'
            '</div>'
            + "".join(
                f'<div class="evmark clip" id="evmk-{i}" style="position:absolute; left:{20+i*22}%; top:{60+(i%2)*8}%; '
                f'width:60px; height:60px; background:#f7d234; border:3px solid #000; '
                f'display:flex; align-items:center; justify-content:center; '
                f'font-family:Playfair Display,serif; font-weight:900; font-size:30px; color:#000; '
                f'transform: rotate({-4+i*3}deg) scale(0); box-shadow:0 6px 14px rgba(0,0,0,0.6);">'
                f'{i+1}</div>'
                for i in range(3)
            )
        ),
        "custom_card_in": (
            "  tl.fromTo('#tape', { opacity:0, x:'-100%' }, { opacity:1, x:'0%', duration:0.8, ease:'power2.out' }, 0.4);\n"
            + "\n".join(f"  MM.slamIn(tl, {{ selector: '#evmk-{i}', start: {1.6+i*0.45}, fromScale:1.4, fromY:-10 }});" for i in range(3))
        ),
    }),

    # ==================== N. Sci diagram ====================
    66: (recipe_card_stage, {  # Anatomy overlay
        "title":"HOMO MAGNATUS", "subtitle":"a study",
        "image_is_backdrop": True,
        "card_html": (
            '<svg style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:520px; height:680px;" viewBox="0 0 520 680">'
            # Figure
            '<circle cx="260" cy="120" r="60" fill="none" stroke="#c9a84c" stroke-width="2"/>'
            '<path d="M 200 180 L 320 180 L 350 380 L 290 600 L 230 600 L 170 380 Z" fill="none" stroke="#c9a84c" stroke-width="2"/>'
            '<path d="M 200 220 L 80 380" fill="none" stroke="#c9a84c" stroke-width="2"/>'
            '<path d="M 320 220 L 440 380" fill="none" stroke="#c9a84c" stroke-width="2"/>'
            # Hot points
            '<circle cx="260" cy="280" r="14" fill="#b41e1e" filter="drop-shadow(0 0 10px #b41e1e)"/>'
            '<circle cx="260" cy="120" r="8" fill="#c9a84c" filter="drop-shadow(0 0 8px #c9a84c)"/>'
            # Leader lines & labels
            + "".join(
                f'<line id="lead-{i}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#c9a84c" stroke-width="1.5" stroke-dasharray="200" stroke-dashoffset="200"/>'
                f'<text id="lbl-{i}" x="{lx}" y="{ly}" font-family="Courier New,monospace" font-size="20" fill="#c9a84c" opacity="0" text-anchor="{anchor}">{lbl}</text>'
                for i, (x1, y1, x2, y2, lx, ly, anchor, lbl) in enumerate([
                    (260, 280, 480, 280, 490, 286, "start", "HEART = AVARICE"),
                    (260, 120, 480, 120, 490, 126, "start", "EYES = MARBLE"),
                    (260, 480, 480, 480, 490, 486, "start", "SPINE = CONTRACTS"),
                ])
            )
            + '</svg>'
        ),
        "custom_card_in": (
            "\n".join(
                f"  MM.pathDraw(tl, {{ selector: '#lead-{i}', start: {0.6+i*0.7}, duration: 0.8 }});\n"
                f"  tl.fromTo('#lbl-{i}', {{ opacity:0 }}, {{ opacity:0.95, duration:0.5 }}, {1.4+i*0.7});"
                for i in range(3)
            )
        ),
    }),
    67: (recipe_card_stage, {  # Equation derivation
        "title":"THE FORMULA", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            '<div style="position:absolute; inset:12% 8% 16% 8%; background: radial-gradient(ellipse at center, rgba(26,31,28,0.8) 0%, rgba(6,8,8,0.6) 90%); border:6px solid #1a1208; box-shadow: inset 0 0 200px rgba(0,0,0,0.6);"></div>'
            '<div id="eq-text" style="position:absolute; left:50%; top:46%; transform:translate(-50%,-50%); font-family:Courier New,monospace; font-size:78px; color:#f5f0e4; opacity:0; text-shadow:0 0 4px rgba(255,255,255,0.4); letter-spacing:4px;">'
            'C &times; L &times; T = F'
            '</div>'
            '<div id="eq-label" style="position:absolute; left:50%; top:62%; transform:translate(-50%,-50%); font-family:Georgia,serif; font-style:italic; font-size:24px; color:#c9a84c; letter-spacing:3px; opacity:0;">'
            'CAPITAL × LABOR × TIME = FORTUNE'
            '</div>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#eq-text', { opacity:0, scale:0.85 }, { opacity:1, scale:1, duration:0.9, ease:'sine.out' }, 0.8);\n"
            "  tl.fromTo('#eq-label', { opacity:0, y:14 }, { opacity:0.95, y:0, duration:0.7, ease:'sine.out' }, 2.2);"
        ),
    }),
    70: (recipe_card_stage, {  # Periodic table cell
        "title":"", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="card" class="clip" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); '
            'width:32%; height:48%; background: linear-gradient(180deg, #2a1f15, #0a0706); border:8px solid #c9a84c; '
            'box-shadow:0 0 60px rgba(201,168,76,0.4); opacity:0; padding:30px;">'
            '<div style="text-align:left; font-family:Courier New,monospace; font-size:36px; color:#c9a84c;" id="atomic-num">79</div>'
            '<div style="text-align:center; font-family:Playfair Display,serif; font-weight:900; font-size:200px; color:#c9a84c; margin-top:-20px;">Au</div>'
            '<div style="text-align:center; font-family:Playfair Display,serif; font-weight:700; font-size:42px; color:#c9a84c; letter-spacing:8px; margin-top:-10px;">GOLD</div>'
            '<div style="text-align:center; font-family:Courier New,monospace; font-size:20px; color:#c9a84c; margin-top:14px;">196.97</div>'
            '</div>'
        ),
        "custom_card_in": (
            "  MM.slamIn(tl, { selector: '#card', start: 0.4, fromScale:1.4, fromY:-30 });\n"
            "  MM.countUp(tl, { selector: '#atomic-num', start: 1.4, duration: 0.8, from: 0, to: 79 });\n"
            "  tl.to('#card', { boxShadow: '0 0 100px rgba(201,168,76,0.7)', duration: 1.0, yoyo:true, repeat:Math.ceil((D-2)/2)*2, ease:'sine.inOut' }, 2.0);"
        ),
    }),

    # ==================== O. Mystical ====================
    71: (recipe_hero_overlay, {  # Stained glass reveal
        "use_stars": False, "particle_kind":"dust-mote", "particle_count":12, "particle_area":(15,30,85,80),
        "title":"AND THEIR WEALTH", "subtitle":"shall be their judge",
        "proc_bg": lambda: '<div style="position:absolute; inset:0; background: linear-gradient(180deg, #1a0e08 0%, #060403 100%);"></div>' + stained_glass_silhouette(),
        "extra_html": (
            '<div id="lightray" style="position:absolute; left:-30%; top:0; bottom:0; width:30%; '
            'background: linear-gradient(90deg, transparent, rgba(255,240,180,0.55), transparent); mix-blend-mode:screen; opacity:0;"></div>'
        ),
        "extra_tl_js": "  tl.fromTo('#lightray', { left:'-30%', opacity:0 }, { left:'120%', opacity:0.9, duration: D-0.6, ease:'sine.inOut' }, 0.3);",
    }),
    72: (recipe_card_stage, {  # Tarot reading spread (similar to 17 but with text)
        "title":"", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            "".join(
                f'<div class="tarot clip" id="tar-{i}" style="position:absolute; left:{16+i*22}%; top:18%; '
                f'width:18%; height:50%; background: linear-gradient(135deg, #1a1208, #4a3320); border:4px solid #c9a84c; '
                f'border-radius:8px; box-shadow:0 18px 40px rgba(0,0,0,0.6); opacity:0;"></div>'
                f'<div class="tar-label clip" id="tar-lbl-{i}" style="position:absolute; left:{14+i*22}%; top:74%; '
                f'width:22%; text-align:center; font-family:Playfair Display,serif; font-weight:700; color:#c9a84c; opacity:0;">'
                f'<div style="font-size:22px; letter-spacing:3px;">{label}</div>'
                f'<div style="font-family:Georgia,serif; font-style:italic; font-size:18px; color:#e8d6a8; margin-top:4px;">{sub}</div>'
                f'</div>'
                for i, (label, sub) in enumerate([
                    ("PAST","A Father's Debt"),
                    ("PRESENT","A Burning Contract"),
                    ("FUTURE","An Empty Vault"),
                ])
            )
        ),
        "custom_card_in": (
            "\n".join(
                f"  tl.fromTo('#tar-{i}', {{ y:40, opacity:0, rotateY:90 }}, {{ y:0, opacity:1, rotateY:0, duration:0.7, ease:'sine.out' }}, {0.6+i*1.2});\n"
                f"  tl.fromTo('#tar-lbl-{i}', {{ opacity:0, y:10 }}, {{ opacity:0.95, y:0, duration:0.5, ease:'sine.out' }}, {1.4+i*1.2});"
                for i in range(3)
            )
        ),
    }),
    74: (recipe_card_stage, {  # Palm reading
        "title":"THE WEALTH LINE", "subtitle":"runs deep",
        "image_is_backdrop": True,
        "card_html": (
            '<svg style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:600px; height:600px;" viewBox="0 0 600 600">'
            # Palm shape
            '<path d="M 200 580 L 200 280 Q 150 220 200 180 Q 230 100 280 160 L 290 80 Q 330 50 350 130 L 360 60 Q 400 30 410 130 L 430 100 Q 470 80 460 200 Q 480 240 460 320 Q 470 420 420 500 Q 350 590 200 580 Z" fill="#3a2820" stroke="#5a3820" stroke-width="2"/>'
            # Lines
            '<path id="line-life" d="M 280 200 Q 240 320 220 460" fill="none" stroke="#c9a84c" stroke-width="3" stroke-dasharray="280" stroke-dashoffset="280" filter="drop-shadow(0 0 6px #c9a84c)"/>'
            '<path id="line-wealth" d="M 290 200 Q 350 280 380 380" fill="none" stroke="#c9a84c" stroke-width="3" stroke-dasharray="240" stroke-dashoffset="240" filter="drop-shadow(0 0 6px #c9a84c)"/>'
            '<path id="line-fate" d="M 300 220 Q 320 360 360 480" fill="none" stroke="#c9a84c" stroke-width="3" stroke-dasharray="290" stroke-dashoffset="290" filter="drop-shadow(0 0 6px #c9a84c)"/>'
            '</svg>'
            + "".join(
                f'<div id="palm-lbl-{i}" class="clip" style="position:absolute; right:14%; top:{30+i*15}%; '
                f'color:#c9a84c; font-family:Playfair Display,serif; font-weight:700; font-size:24px; opacity:0;">'
                f'{label}</div>'
                for i, label in enumerate(["LIFE LINE — broken", "WEALTH LINE — deep", "FATE LINE — split"])
            )
        ),
        "custom_card_in": "\n".join(
            f"  MM.pathDraw(tl, {{ selector: '#line-{n}', start: {0.6+i*0.9}, duration: 1.0 }});\n"
            f"  tl.fromTo('#palm-lbl-{i}', {{ opacity:0, x:30 }}, {{ opacity:0.95, x:0, duration:0.5, ease:'sine.out' }}, {1.4+i*0.9});"
            for i, n in enumerate(["life", "wealth", "fate"])
        ),
    }),
    75: (recipe_card_stage, {  # Crystal ball vision
        "title":"VISION", "subtitle":"of the estate, dissolved",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="ball" class="clip" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); '
            'width:600px; height:600px; border-radius:50%; '
            'background: radial-gradient(circle at 35% 30%, #c9d8e8 0%, #4a5a6a 30%, #1a2030 70%, #050813 100%); '
            'box-shadow:0 0 80px rgba(201,168,76,0.4), inset 0 0 60px rgba(0,0,0,0.4); overflow:hidden;">'
            '<div id="smoke" style="position:absolute; inset:10%; opacity:0; mix-blend-mode:screen; '
            'background: radial-gradient(circle, rgba(255,240,200,0.5), transparent 60%);"></div>'
            '<svg id="ball-mansion" style="position:absolute; left:50%; top:60%; transform:translate(-50%,-50%); width:50%; height:30%; opacity:0;" viewBox="0 0 300 180">'
            '<rect x="40" y="60" width="220" height="100" fill="#0a0706"/>'
            '<polygon points="20,60 150,20 280,60" fill="#0a0706"/>'
            '<rect x="130" y="100" width="40" height="60" fill="#e9b045" filter="drop-shadow(0 0 8px rgba(233,176,69,0.85))"/>'
            '</svg></div>'
        ),
        "custom_card_in": (
            "  MM.slamIn(tl, { selector: '#ball', start: 0.4, fromScale:1.2, fromY:-10 });\n"
            "  tl.fromTo('#smoke', { opacity:0, scale:0.5 }, { opacity:0.9, scale:1.2, duration:1.4, ease:'sine.out' }, 1.4);\n"
            "  tl.fromTo('#ball-mansion', { opacity:0, scale:0.6 }, { opacity:0.95, scale:1, duration:1.0, ease:'sine.out' }, 2.6);"
        ),
    }),

    # ==================== P. Commercial ====================
    76: (recipe_card_stage, {  # Auction reveal
        "title":"", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            '<div style="position:absolute; left:50%; top:80%; transform:translate(-50%,-50%); width:60%; height:14%; background: linear-gradient(180deg, #2a1f15, #0a0706); border-top:4px solid #c9a84c; box-shadow:0 -20px 40px rgba(0,0,0,0.6);"></div>'
            '<div id="spot" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:80%; height:80%; pointer-events:none; background: radial-gradient(ellipse at center, rgba(255,220,140,0.5), transparent 60%); mix-blend-mode:screen; opacity:0;"></div>'
            '<div id="ticker" style="position:absolute; right:10%; top:25%; font-family:Courier New,monospace; font-size:48px; color:#c9a84c; letter-spacing:2px; text-shadow:0 0 8px rgba(201,168,76,0.5);">$<span id="price">0</span></div>'
            '<div id="sold" class="clip" style="position:absolute; left:50%; top:55%; transform:translate(-50%,-50%); padding:20px 60px; background:rgba(180,30,30,0.95); color:#f5f0e4; font-family:Playfair Display,serif; font-weight:900; font-size:80px; letter-spacing:14px; opacity:0; transform: translate(-50%,-50%) rotate(-12deg) scale(1.5);">SOLD</div>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#spot', { opacity:0 }, { opacity:0.9, duration:0.8, ease:'sine.out' }, 0.4);\n"
            "  MM.countUp(tl, { selector: '#price', start: 0.8, duration: 3.2, from: 850000, to: 1500000 });\n"
            "  MM.stampSlam(tl, { selector: '#sold', start: 4.4, fromAngle:-30, toAngle:-12 });"
        ),
    }),
    77: (recipe_document, {  # Patent diagram
        "title":"PATENT #142,889", "subtitle":"OIL-DRILLING APPARATUS",
        "show_stamp": False,
    }),
    78: (recipe_portrait_card, {  # Fashion lookbook
        "name": "LANVIN · PARIS",
        "role": "Beaded Evening Gown",
        "dates": "1924 · $2,500",
    }),
    79: (recipe_card_stage, {  # Restaurant menu
        "title":"DELMONICO'S", "subtitle":"private dining · 1899",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="card" class="clip" style="position:absolute; left:24%; right:24%; top:18%; bottom:10%; '
            'background: linear-gradient(180deg, #e0d4ac, #c4b387); border:6px solid #c9a84c; padding:30px; box-shadow:0 24px 60px rgba(0,0,0,0.7);">'
            '<div style="text-align:center; font-family:Playfair Display,serif; font-weight:900; font-size:32px; color:#3a2410; letter-spacing:3px; border-bottom:2px solid #3a2410; padding-bottom:8px;">DELMONICO\'S</div>'
            + "".join(
                f'<div class="menu-line clip" id="menu-{i}" style="display:flex; justify-content:space-between; align-items:baseline; margin-top:14px; font-family:Georgia,serif; color:#3a2410; opacity:0;">'
                f'<span style="font-size:22px; font-weight:700;">{item}</span>'
                f'<span style="border-bottom:1px dashed #3a2410; flex:1; margin:0 14px;"></span>'
                f'<span style="font-family:Courier New,monospace; font-size:18px;">${price}</span>'
                f'</div>'
                for i, (item, price) in enumerate([
                    ("OYSTERS ROCKEFELLER", "4"),
                    ("TERRAPIN SOUP", "8"),
                    ("CHATEAUBRIAND", "12"),
                    ("CHEESE PLATE", "5"),
                    ("PORT, VINTAGE 1872", "10"),
                ])
            )
            + '<div id="special" class="clip" style="margin-top:24px; padding:14px; background:#c9a84c; text-align:center; font-family:Playfair Display,serif; font-weight:900; font-size:24px; color:#080c16; letter-spacing:6px; opacity:0;">TODAY\'S SPECIAL — BÉARNAISE FILET</div>'
            + '</div>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#card', { y:40, opacity:0 }, { y:0, opacity:1, duration:0.9, ease:'sine.out' }, 0.4);\n"
            + "\n".join(f"  tl.fromTo('#menu-{i}', {{ opacity:0, x:-14 }}, {{ opacity:1, x:0, duration:0.4, ease:'sine.out' }}, {1.2 + i*0.5});" for i in range(5))
            + "\n  tl.fromTo('#special', { opacity:0, scale:0.85 }, { opacity:1, scale:1, duration:0.5, ease:'power2.out' }, 4.0);"
        ),
    }),
    80: (recipe_card_stage, {  # Vintage infomercial
        "title":"", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="sunburst" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:1400px; height:1400px; pointer-events:none; background: conic-gradient(from 0deg, rgba(201,168,76,0.4), transparent 6deg, rgba(201,168,76,0.4) 12deg, transparent 18deg, rgba(201,168,76,0.4) 24deg, transparent 30deg, rgba(201,168,76,0.4) 36deg, transparent 42deg, rgba(201,168,76,0.4) 48deg, transparent 54deg, rgba(201,168,76,0.4) 60deg, transparent 66deg, rgba(201,168,76,0.4) 72deg); opacity:0; mix-blend-mode:screen;"></div>'
            '<div id="price-slap" class="clip" style="position:absolute; left:50%; top:32%; transform:translate(-50%,-50%); padding:14px 30px; background:#b41e1e; color:#f5f0e4; font-family:Playfair Display,serif; font-weight:900; font-size:88px; letter-spacing:4px; opacity:0; transform: translate(-50%,-50%) rotate(-8deg) scale(2);">$19.95!</div>'
            '<div id="call-now" class="clip" style="position:absolute; left:50%; bottom:14%; transform:translate(-50%,0); padding:14px 36px; background:#c9a84c; color:#080c16; font-family:Playfair Display,serif; font-weight:900; font-size:48px; letter-spacing:8px; opacity:0;">CALL NOW</div>'
            '<div id="seen-stamp" class="clip" style="position:absolute; right:8%; top:14%; padding:8px 18px; background:#1a1208; color:#c9a84c; font-family:Courier New,monospace; font-size:18px; letter-spacing:2px; transform: rotate(-12deg); opacity:0; border:3px solid #c9a84c;">AS SEEN IN HARPER\'S BAZAAR</div>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#sunburst', { opacity:0 }, { opacity:0.7, duration:0.8 }, 0.4);\n"
            "  MM.spinSlow(tl, { selector: '#sunburst', start: 0.5, duration: D, speed: 15 });\n"
            "  MM.stampSlam(tl, { selector: '#price-slap', start: 1.4, fromAngle:-30, toAngle:-8 });\n"
            "  tl.fromTo('#call-now', { y:60, opacity:0 }, { y:0, opacity:1, duration:0.5, ease:'power2.out' }, 2.6);\n"
            "  tl.to('#call-now', { scale:1.04, duration:0.4, yoyo:true, repeat:Math.ceil((D-3)/0.8)*2, ease:'sine.inOut' }, 3.2);\n"
            "  MM.stampSlam(tl, { selector: '#seen-stamp', start: 3.4, fromAngle:-26, toAngle:-12 });"
        ),
    }),

    # ==================== Q. Production assets ====================
    81: (recipe_typo, {  # Channel-ID stinger
        "lines": [
            {"text": "MIDNIGHT", "size": 120, "weight": 900, "spacing": 18},
            {"text": "MAGNATES", "size": 120, "weight": 900, "spacing": 18},
            {"text": "the dark histories of wealth", "size": 22, "weight": 400, "spacing": 4},
        ],
    }),
    82: (recipe_portrait_card, {
        "name": "DR. EZRA MONTAGUE",
        "role": "Economic Historian · Columbia University",
        "dates": "",
    }),
    83: (recipe_card_stage, {  # Subscribe outro
        "title":"", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="sub-btn" class="clip" style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); padding:24px 60px; background:#b41e1e; color:#f5f0e4; font-family:Playfair Display,serif; font-weight:900; font-size:64px; letter-spacing:8px; opacity:0; box-shadow:0 12px 36px rgba(0,0,0,0.7);">SUBSCRIBE</div>'
            '<div id="bell" class="clip" style="position:absolute; left:62%; top:50%; transform:translate(-50%,-50%); width:80px; height:80px; background:#c9a84c; border-radius:50%; opacity:0; box-shadow:0 4px 14px rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; font-size:42px;">🔔</div>'
            '<div style="position:absolute; left:50%; bottom:14%; transform:translateX(-50%); font-family:Playfair Display,serif; font-weight:700; font-size:26px; color:#c9a84c; letter-spacing:4px;">@MidnightMagnates</div>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#sub-btn', { opacity:0, scale:0.7 }, { opacity:1, scale:1, duration:0.5, ease:'power2.out' }, 0.5);\n"
            "  tl.to('#sub-btn', { scale:1.05, duration:0.4, yoyo:true, repeat:Math.ceil((D-1)/0.8)*2, ease:'sine.inOut' }, 1.2);\n"
            "  tl.fromTo('#bell', { opacity:0, scale:0.5, rotate:0 }, { opacity:1, scale:1, rotate:18, duration:0.4, ease:'power2.out' }, 1.8);\n"
            "  tl.to('#bell', { rotate:-18, duration:0.2, yoyo:true, repeat:3, ease:'sine.inOut' }, 2.2);"
        ),
    }),
    84: (recipe_card_stage, {  # End screen grid
        "title":"NEXT EPISODES", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            "".join(
                f'<div class="thumb clip" id="th-{i}" style="position:absolute; left:{8+(i%2)*46}%; top:{30+(i//2)*30}%; '
                f'width:42%; height:24%; background: linear-gradient(135deg, #2a1f15, #0a0706); border:4px solid #c9a84c; '
                f'opacity:0; padding:14px; display:flex; align-items:flex-end;">'
                f'<div style="font-family:Playfair Display,serif; font-weight:700; font-size:28px; color:#c9a84c;">{title}</div>'
                f'</div>'
                for i, title in enumerate(["THE FORD INHERITANCE","THE DUPONT VAULT","THE ASTOR SILENCE","THE GETTY LINE"])
            )
        ),
        "custom_card_in": "\n".join(f"  MM.slamIn(tl, {{ selector: '#th-{i}', start: {0.6+i*0.3}, fromScale:1.1, fromY:-30 }});" for i in range(4)),
    }),
    85: (recipe_card_stage, {  # Sponsor read card
        "title":"NOTABLE", "subtitle":"premium paper goods",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="logo" class="clip" style="position:absolute; left:10%; top:10%; padding:10px 24px; background:#1a1208; border:3px solid #c9a84c; color:#c9a84c; font-family:Playfair Display,serif; font-weight:900; font-size:32px; letter-spacing:4px; opacity:0; transform: rotate(-4deg);">NOTABLE™</div>'
            '<div id="code" class="clip" style="position:absolute; left:50%; top:60%; transform:translate(-50%,-50%); padding:16px 36px; background:#c9a84c; color:#080c16; font-family:Courier New,monospace; font-weight:700; font-size:46px; letter-spacing:6px; opacity:0; box-shadow:0 0 30px rgba(201,168,76,0.5);">MAGNATE25</div>'
            '<div style="position:absolute; left:50%; top:75%; transform:translate(-50%,-50%); font-family:Georgia,serif; font-style:italic; font-size:22px; color:#f5f0e4; letter-spacing:2px;">25% off · notable.com</div>'
        ),
        "custom_card_in": (
            "  MM.stampSlam(tl, { selector: '#logo', start: 0.5, fromAngle:-20, toAngle:-4 });\n"
            "  tl.fromTo('#code', { opacity:0, scale:0.7 }, { opacity:1, scale:1, duration:0.5, ease:'power2.out' }, 1.6);\n"
            "  tl.to('#code', { boxShadow:'0 0 60px rgba(201,168,76,0.9)', duration:1.0, yoyo:true, repeat:Math.ceil((D-2.6)/2)*2, ease:'sine.inOut' }, 2.4);"
        ),
    }),

    # ==================== R. Geographic ====================
    86: (recipe_card_stage, {  # War room map
        "title":"JULY 14, 1864", "subtitle":"the Mississippi front",
        "image_is_backdrop": True,
        "card_html": (
            '<svg style="position:absolute; left:10%; right:10%; top:18%; bottom:18%;" viewBox="0 0 1500 600" preserveAspectRatio="none">'
            '<rect x="0" y="0" width="1500" height="600" fill="#3a2820"/>'
            # River
            '<path d="M 600 0 Q 700 200 650 400 T 700 600" fill="none" stroke="#4a6fa5" stroke-width="8" opacity="0.8"/>'
            # Territory borders
            '<line x1="0" y1="300" x2="1500" y2="300" stroke="#c9a84c" stroke-width="1" opacity="0.5" stroke-dasharray="6 4"/>'
            '<line x1="900" y1="0" x2="900" y2="600" stroke="#c9a84c" stroke-width="1" opacity="0.5" stroke-dasharray="6 4"/>'
            # Markers
            + "".join(
                f'<circle id="mark-{i}" cx="{x}" cy="{y}" r="0" fill="#{col}" filter="drop-shadow(0 0 8px #{col})"/>'
                for i, (x, y, col) in enumerate([
                    (300, 200, "b41e1e"), (500, 350, "b41e1e"), (800, 250, "b41e1e"),
                    (200, 450, "4a6fa5"), (450, 480, "4a6fa5"), (700, 480, "4a6fa5"),
                ])
            )
            # Front line
            + '<path id="frontline" d="M 200 230 Q 400 280 600 230 T 900 270 T 1200 230" fill="none" stroke="#c9a84c" stroke-width="4" stroke-dasharray="1200" stroke-dashoffset="1200"/>'
            + '</svg>'
        ),
        "custom_card_in": (
            "\n".join(f"  tl.fromTo('#mark-{i}', {{ attr:{{r:0}}, opacity:0 }}, {{ attr:{{r:12}}, opacity:1, duration:0.3, ease:'power2.out' }}, {0.6 + i*0.18});" for i in range(6))
            + "\n  MM.pathDraw(tl, { selector: '#frontline', start: 2.4, duration: 1.6 });"
        ),
    }),
    87: (recipe_card_stage, {  # Treasure map quest
        "title":"X MARKS THE SPOT", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            '<svg style="position:absolute; left:10%; right:10%; top:14%; bottom:14%;" viewBox="0 0 1500 700" preserveAspectRatio="none">'
            '<rect x="0" y="0" width="1500" height="700" fill="#d8c8a0"/>'
            # Coast outline
            '<path d="M 50 100 Q 200 50 400 80 Q 600 100 800 60 Q 1100 80 1450 100 L 1450 700 L 50 700 Z" fill="#a89060" stroke="#3a2410" stroke-width="2"/>'
            # Path
            '<path id="quest-path" d="M 200 200 Q 400 250 600 350 Q 800 500 1100 450 L 1280 500" fill="none" stroke="#b41e1e" stroke-width="4" stroke-dasharray="20 10" stroke-dashoffset="800"/>'
            # Compass rose
            + f'<g id="compass" transform="translate(140, 600)">'
            + '<circle cx="0" cy="0" r="60" fill="#3a2410" opacity="0.7"/>'
            + '<line x1="0" y1="-50" x2="0" y2="50" stroke="#c9a84c" stroke-width="3"/>'
            + '<line x1="-50" y1="0" x2="50" y2="0" stroke="#c9a84c" stroke-width="3"/>'
            + '<polygon points="0,-50 6,-30 -6,-30" fill="#c9a84c"/>'
            + '<text x="0" y="-58" text-anchor="middle" fill="#c9a84c" font-family="Playfair Display,serif" font-size="18">N</text>'
            + '</g>'
            # X
            + '<g id="x-mark" opacity="0">'
            + '<line x1="1260" y1="480" x2="1300" y2="520" stroke="#b41e1e" stroke-width="6"/>'
            + '<line x1="1300" y1="480" x2="1260" y2="520" stroke="#b41e1e" stroke-width="6"/>'
            + '</g>'
            + '</svg>'
        ),
        "custom_card_in": (
            "  MM.pathDraw(tl, { selector: '#quest-path', start: 0.6, duration: 2.8 });\n"
            "  MM.spinSlow(tl, { selector: '#compass', start: 0.6, duration: D, speed: 14 });\n"
            "  tl.fromTo('#x-mark', { opacity:0, scale:0.4 }, { opacity:1, scale:1.2, duration:0.4, ease:'power2.out' }, 3.4);\n"
            "  tl.to('#x-mark', { scale:1.0, duration:0.4, yoyo:true, repeat:Math.ceil((D-4)/0.8)*2, ease:'sine.inOut' }, 3.8);"
        ),
    }),
    88: (recipe_card_stage, {  # Travel postcard
        "title":"NEWPORT", "subtitle":"summer · 1925",
        "image_is_backdrop": True,
        "card_html": (
            '<div id="card" class="clip" style="position:absolute; left:14%; right:14%; top:14%; bottom:14%; '
            'background: linear-gradient(180deg, #e0d4ac, #c4b387); border:8px solid #c9a84c; padding:30px; box-shadow:0 24px 60px rgba(0,0,0,0.7); position:relative;">'
            '<div style="text-align:center; font-family:Playfair Display,serif; font-weight:900; font-size:78px; color:#3a2410; letter-spacing:8px;">GREETINGS</div>'
            '<div style="text-align:center; font-family:Georgia,serif; font-style:italic; font-size:32px; color:#3a2410; margin-top:6px;">from Newport</div>'
            '<div style="margin:20px 60px; height:340px; background: linear-gradient(180deg, #4a6fa5 0%, #6e8aac 60%, #8a9aac 80%, #3a4a5a 100%); border:3px solid #3a2410;"></div>'
            '<div id="hand-note" class="clip" style="position:absolute; left:60px; bottom:80px; font-family:Georgia,serif; font-style:italic; font-size:22px; color:#3a2410; opacity:0; white-space:nowrap; overflow:hidden;">"Business done. Returning Wed."</div>'
            '<div id="stamp-box" class="clip" style="position:absolute; right:60px; top:60px; width:120px; height:140px; background:#b41e1e; border:4px solid #f5f0e4; opacity:0; transform: rotate(-12deg);">'
            '<div style="text-align:center; font-family:Playfair Display,serif; font-weight:900; color:#f5f0e4; font-size:22px; padding-top:30px;">2¢</div>'
            '<div style="text-align:center; font-family:Georgia,serif; color:#f5f0e4; font-size:14px;">U.S.</div>'
            '</div>'
            '<div id="postmark" class="clip" style="position:absolute; right:120px; top:120px; padding:8px 14px; border:3px solid #1a1208; color:#1a1208; font-family:Courier New,monospace; font-size:12px; transform: rotate(-22deg); opacity:0; background:rgba(232,220,180,0.6);">NEWPORT R.I.<br/>AUG 18 1925</div>'
            '</div>'
        ),
        "custom_card_in": (
            "  MM.slamIn(tl, { selector: '#card', start: 0.5, fromScale:1.1, fromY:-20 });\n"
            "  MM.stampSlam(tl, { selector: '#stamp-box', start: 1.4, fromAngle:-30, toAngle:-12 });\n"
            "  MM.stampSlam(tl, { selector: '#postmark', start: 2.0, fromAngle:-40, toAngle:-22 });\n"
            "  tl.fromTo('#hand-note', { opacity:1, width:0 }, { width:'auto', duration:1.4, ease:'none' }, 2.8);"
        ),
    }),
    89: (recipe_card_stage, {  # Weather forecast
        "title":"OCTOBER 28, 1929", "subtitle":"financial weather",
        "image_is_backdrop": True,
        "card_html": (
            '<div style="position:absolute; inset:18%; background: linear-gradient(180deg, #1a2030 0%, #060808 100%); border:3px solid #c9a84c; padding:30px;"></div>'
            + "".join(
                f'<div class="weather clip" id="wx-{i}" style="position:absolute; left:{22+(i%3)*22}%; top:{30+(i//3)*22}%; '
                f'width:18%; padding:20px; background:#0e1218; border-left:4px solid #c9a84c; opacity:0;">'
                f'<div style="font-family:Playfair Display,serif; font-weight:700; color:#c9a84c; font-size:24px;">{city}</div>'
                f'<div style="font-size:48px; margin-top:4px;">{icon}</div>'
                f'<div id="wx-tmp-{i}" style="font-family:Courier New,monospace; color:#f5f0e4; font-size:36px;">0°</div>'
                f'</div>'
                for i, (city, icon, _) in enumerate([
                    ("NYC","🌧",42),("CHICAGO","⛅",36),("DENVER","❄",18),
                    ("DALLAS","☀",62),("SAN FRAN","⛅",54),("BOSTON","🌧",38),
                ])
            )
        ),
        "custom_card_in": (
            "\n".join(f"  MM.slamIn(tl, {{ selector: '#wx-{i}', start: {0.6+i*0.2}, fromScale:1.1, fromY:-10 }});" for i in range(6))
            + "\n" + "\n".join(f"  MM.countUp(tl, {{ selector: '#wx-tmp-{i}', start: {1.0+i*0.2}, duration: 0.8, from:0, to:{t}, suffix:'°' }});" for i, t in enumerate([42, 36, 18, 62, 54, 38]))
        ),
    }),
    90: (recipe_hero_overlay, {  # Tour guide stop
        "use_stars": True, "particle_kind":"dust-mote", "particle_count":10, "particle_area":(20,40,80,90),
        "title":"WALDORF HOUSE", "subtitle":"built 1872 · est. $24M today",
        "extra_html": (
            '<div id="map-pin" class="clip" style="position:absolute; left:50%; top:40%; transform:translate(-50%,-50%) translateY(-100px) scale(0); width:60px; height:80px; opacity:0; z-index:60;">'
            '<svg viewBox="0 0 60 80" style="width:100%; height:100%;">'
            '<path d="M 30 0 Q 60 0 60 30 Q 60 60 30 80 Q 0 60 0 30 Q 0 0 30 0 Z" fill="#b41e1e" stroke="#080c16" stroke-width="2"/>'
            '<circle cx="30" cy="30" r="12" fill="#c9a84c"/></svg></div>'
        ),
        "extra_tl_js": (
            "  tl.fromTo('#map-pin', { y:-200, scale:0, opacity:0 }, { y:0, scale:1, opacity:1, duration:0.6, ease:'power2.out' }, 0.6);\n"
            "  tl.to('#map-pin', { scale:1.15, duration:0.4, yoyo:true, repeat:Math.ceil((D-1.5)/0.8)*2, ease:'sine.inOut' }, 1.4);"
        ),
    }),

    # ==================== S. Documentary ====================
    91: (recipe_portrait_card, {
        "name": "AMELIA P. ARDEN",
        "role": "Inherited $14M · Founded Arden Trust",
        "dates": "1838 — 1921",
    }),
    92: (recipe_card_stage, {  # Newspaper clipping
        "title":"", "subtitle":"",
        "card_html": (
            '<div id="card" class="clip" style="position:absolute; left:24%; right:18%; top:18%; bottom:14%; '
            'background: linear-gradient(180deg, #e0d4ac, #c4b387); padding:24px; '
            'box-shadow:0 24px 50px rgba(0,0,0,0.7); transform: rotate(-3deg) scale(0); '
            'clip-path: polygon(0% 4%, 100% 0%, 98% 100%, 2% 96%);">'
            '<div style="text-align:center; font-family:Playfair Display,serif; font-weight:700; font-size:24px; color:#3a2410; letter-spacing:4px; border-bottom:2px solid #3a2410; padding-bottom:4px;">THE PROVIDENCE COURIER</div>'
            '<div style="text-align:center; font-family:Georgia,serif; font-style:italic; font-size:12px; color:#5a4830; margin-top:4px;">MAY 4, 1893</div>'
            '<div style="text-align:center; font-family:Playfair Display,serif; font-weight:900; font-size:46px; color:#1a0e08; margin-top:18px; line-height:1.0;">COTTON KING DIES<br/>IN MYSTERY</div>'
            '<div id="head-underline" style="margin: 6px auto; width:60%; height:4px; background:#c9a84c; transform-origin:left center; transform:scaleX(0);"></div>'
            '<div style="columns:2; column-gap:14px; margin-top:14px; font-family:Georgia,serif; font-size:13px; color:#3a2410; line-height:1.4;">'
            'PROVIDENCE — Cotton magnate Ezekiel P. Staunton was discovered this morning by his butler. Causes are uncertain. His three sons stand to inherit. The local police have made no statement at this time. Sources indicate that fingers point in many directions. The Courier will offer further details as they become available.'
            '</div></div>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#card', { scale:0, rotate:-12, opacity:0 }, { scale:1, rotate:-3, opacity:1, duration:0.7, ease:'power2.out' }, 0.4);\n"
            "  MM.highlightSweep(tl, { selector: '#head-underline', start: 1.4, duration: 0.9 });"
        ),
    }),
    93: (recipe_document, {  # Letter reveal
        "title":"", "subtitle":"",
        "show_stamp": False,
        "extra_html": (
            '<svg id="signature" style="position:absolute; left:50%; bottom:24%; transform:translateX(-50%); width:280px; height:80px;" viewBox="0 0 280 80">'
            '<path id="sig-path" d="M 10 60 Q 30 20 60 50 T 110 40 Q 140 30 160 60 T 220 50 Q 240 30 270 50" fill="none" stroke="#1a0e08" stroke-width="3" stroke-linecap="round" stroke-dasharray="320" stroke-dashoffset="320" filter="drop-shadow(0 0 1px rgba(0,0,0,0.4))"/>'
            '</svg>'
            '<div id="wax" style="position:absolute; right:14%; bottom:18%; width:100px; height:100px; '
            'background: radial-gradient(circle, #8a1818 0%, #5a0d0d 60%, #3a0808 100%); border-radius:50%; '
            'box-shadow:0 4px 12px rgba(0,0,0,0.6); transform:rotate(-12deg);"></div>'
        ),
        "extra_tl_js": "  MM.pathDraw(tl, { selector: '#sig-path', start: 2.4, duration: 2.0 });",
    }),
    94: (recipe_document, {  # Ledger entry
        "title":"ASHFORD TRUST · 1892", "subtitle":"",
        "show_stamp": True,
        "extra_html": (
            '<div id="stamp" class="clip" style="position:absolute; right:14%; bottom:20%; '
            'color:#7a4a18; font-family:\'Playfair Display\',serif; font-weight:900; font-size:38px; '
            'letter-spacing:4px; padding:10px 22px; border:5px solid #7a4a18; opacity:0; z-index:60; '
            'transform:rotate(-12deg);">PAID IN FULL</div>'
        ),
    }),
    95: (recipe_hero_overlay, {  # Estate inventory
        "use_stars": False, "particle_kind":None,
        "title":"WALDORF HOUSE", "subtitle":"est. value $24,000,000",
        "kenburns": True,
        "extra_html": (
            "".join(
                f'<div class="est-label clip" id="est-{i}" style="position:absolute; left:{x}; top:{y}; padding:8px 18px; '
                f'background:rgba(20,16,12,0.85); border:2px solid #c9a84c; color:#c9a84c; '
                f'font-family:Playfair Display,serif; font-weight:700; font-size:18px; letter-spacing:2px; opacity:0;">'
                f'{label} <span style="color:#e8d6a8; font-family:Courier New,monospace; margin-left:14px;">{val}</span></div>'
                for i, (x, y, label, val) in enumerate([
                    ("18%","30%","EAST WING — Library","$1.2M"),
                    ("66%","30%","WEST WING — Gallery","$2.1M"),
                    ("38%","58%","CENTRAL — Master Suite","$680K"),
                ])
            )
        ),
        "extra_tl_js": "\n".join(f"  MM.slamIn(tl, {{ selector: '#est-{i}', start: {0.8+i*0.7}, fromScale:1.15, fromY:-15 }});" for i in range(3)),
    }),
    96: (recipe_card_stage, {  # Family tree
        "title":"THE ASHFORD LINE", "subtitle":"",
        "image_is_backdrop": True,
        "card_html": (
            '<svg style="position:absolute; inset:14% 10% 10% 10%;" viewBox="0 0 1500 800" preserveAspectRatio="xMidYMid meet">'
            # Tree
            '<circle id="root" cx="750" cy="100" r="0" fill="#c9a84c" stroke="#080c16" stroke-width="3"/>'
            '<text x="750" y="156" text-anchor="middle" id="root-name" font-family="Playfair Display,serif" font-weight="700" font-size="22" fill="#c9a84c" opacity="0">EZEKIEL · 1842</text>'
            # Children
            + "".join(
                f'<line id="branch-{i}" x1="750" y1="100" x2="{300+i*250}" y2="350" stroke="#c9a84c" stroke-width="2" stroke-dasharray="350" stroke-dashoffset="350"/>'
                f'<circle id="child-{i}" cx="{300+i*250}" cy="350" r="0" fill="#c9a84c" stroke="#080c16" stroke-width="3"/>'
                f'<text id="child-name-{i}" x="{300+i*250}" y="406" text-anchor="middle" font-family="Playfair Display,serif" font-weight="700" font-size="18" fill="#c9a84c" opacity="0">{name}</text>'
                for i, name in enumerate(["JOHN '75","MARY '78","WILLIAM '81","HENRY '85","EZRA '89"])
            )
            # Grandchildren (1 per child as proxy)
            + "".join(
                f'<line id="gc-line-{i}" x1="{300+i*250}" y1="350" x2="{300+i*250}" y2="620" stroke="#c9a84c" stroke-width="1.5" stroke-dasharray="300" stroke-dashoffset="300"/>'
                f'<circle id="gc-{i}" cx="{300+i*250}" cy="620" r="0" fill="#c9a84c" stroke="#080c16" stroke-width="2"/>'
                for i in range(5)
            )
            + '</svg>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#root', { attr:{r:0} }, { attr:{r:20}, duration:0.4, ease:'power2.out' }, 0.4);\n"
            "  tl.fromTo('#root-name', { opacity:0 }, { opacity:0.95, duration:0.4 }, 0.6);\n"
            + "\n".join(
                f"  MM.pathDraw(tl, {{ selector: '#branch-{i}', start: {1.0+i*0.15}, duration: 0.6 }});\n"
                f"  tl.fromTo('#child-{i}', {{ attr:{{r:0}} }}, {{ attr:{{r:14}}, duration:0.35, ease:'power2.out' }}, {1.6+i*0.15});\n"
                f"  tl.fromTo('#child-name-{i}', {{ opacity:0 }}, {{ opacity:0.9, duration:0.35 }}, {1.7+i*0.15});"
                for i in range(5)
            )
            + "\n" + "\n".join(
                f"  MM.pathDraw(tl, {{ selector: '#gc-line-{i}', start: {3.0+i*0.15}, duration: 0.5 }});\n"
                f"  tl.fromTo('#gc-{i}', {{ attr:{{r:0}} }}, {{ attr:{{r:10}}, duration:0.3, ease:'power2.out' }}, {3.5+i*0.15});"
                for i in range(5)
            )
        ),
    }),
    97: (recipe_document, {  # Will reading
        "title":"LAST WILL & TESTAMENT", "subtitle":"of E.P. Ashford",
        "show_stamp": False,
        "extra_html": (
            "".join(
                f'<div class="will-highlight clip" id="wh-{i}" style="position:absolute; left:18%; right:18%; top:{30+i*14}%; height:40px; background:rgba(201,168,76,0.0); transform-origin:left center; transform:scaleX(0);"></div>'
                for i in range(3)
            )
        ),
        "extra_tl_js": "\n".join(f"  tl.fromTo('#wh-{i}', {{ scaleX:0, opacity:0.0 }}, {{ scaleX:1, opacity:0.5, duration:0.6, ease:'sine.inOut' }}, {1.4+i*1.6});\n  tl.to('#wh-{i}', {{ opacity:0, duration:0.4 }}, {2.6+i*1.6});" for i in range(3)),
    }),
    98: (recipe_card_stage, {  # Telegraph reveal
        "title":"INCOMING", "subtitle":"KMM-1929",
        "card_html": (
            '<div style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); width:60%; height:36%; background: linear-gradient(180deg, #2a1f15, #0a0706); border:6px solid #c9a84c; padding:28px; box-shadow:0 24px 50px rgba(0,0,0,0.7);"></div>'
            '<div id="morse" style="position:absolute; left:24%; right:24%; top:28%; font-family:Courier New,monospace; font-size:30px; color:#c9a84c; letter-spacing:4px; opacity:0; text-shadow:0 0 6px rgba(201,168,76,0.5);">— · — — · — · ·</div>'
            '<div id="decoded" style="position:absolute; left:24%; right:24%; top:50%; font-family:Playfair Display,serif; font-weight:700; font-size:28px; color:#f5f0e4; overflow:hidden; white-space:nowrap; width:0;">TRUST DISSOLVED. STOP. ASSETS MOVING. STOP.</div>'
        ),
        "custom_card_in": (
            "  tl.fromTo('#morse', { opacity:0 }, { opacity:0.95, duration:0.4 }, 0.4);\n"
            "  tl.to('#morse', { opacity:0.5, duration:0.18, yoyo:true, repeat:Math.ceil((D-1)/0.36)*2, ease:'sine.inOut' }, 0.6);\n"
            "  MM.typeIn(tl, { selector: '#decoded', start: 2.0, duration: 3.0 });"
        ),
    }),

    # ==================== T. Sport / scoreboard ====================
    99: (recipe_card_stage, {  # Final scoreboard
        "title":"GAME OF 1909", "subtitle":"betting purse: $1.2 BILLION TODAY",
        "image_is_backdrop": True,
        "card_html": (
            '<div style="position:absolute; left:18%; right:18%; top:30%; bottom:30%; background: linear-gradient(180deg, #2a1f15, #0a0706); border:6px solid #c9a84c; padding:30px; box-shadow:0 24px 60px rgba(0,0,0,0.7);"></div>'
            '<div style="position:absolute; left:22%; top:38%; width:24%; text-align:center;">'
            '<div style="font-family:Playfair Display,serif; font-weight:900; font-size:36px; color:#c9a84c; letter-spacing:4px;">HOME</div>'
            '<div id="score-home" style="font-family:Courier New,monospace; font-size:140px; color:#c9a84c; line-height:1; text-shadow:0 0 12px rgba(201,168,76,0.6);">0</div>'
            '</div>'
            '<div style="position:absolute; right:22%; top:38%; width:24%; text-align:center;">'
            '<div style="font-family:Playfair Display,serif; font-weight:900; font-size:36px; color:#c9a84c; letter-spacing:4px;">AWAY</div>'
            '<div id="score-away" style="font-family:Courier New,monospace; font-size:140px; color:#c9a84c; line-height:1; text-shadow:0 0 12px rgba(201,168,76,0.6);">0</div>'
            '</div>'
        ),
        "custom_card_in": (
            "  MM.countUp(tl, { selector: '#score-home', start: 1.0, duration: 2.4, from:0, to:47 });\n"
            "  MM.countUp(tl, { selector: '#score-away', start: 1.4, duration: 2.4, from:0, to:23 });"
        ),
    }),
    100: (recipe_portrait_card, {  # Player card
        "name": "T. R. ASTOR",
        "role": "Owner · The Astor Pinstripes · 1903",
        "dates": "",
    }),
    101: (recipe_card_stage, {  # Bracket reveal
        "title":"CHAMPION", "subtitle":"the magnate league",
        "image_is_backdrop": True,
        "card_html": (
            '<svg style="position:absolute; left:8%; right:8%; top:22%; bottom:14%;" viewBox="0 0 1500 600" preserveAspectRatio="xMidYMid meet">'
            # Round 1 (8 names)
            + "".join(
                f'<text id="r1-{i}" x="40" y="{40+i*70}" font-family="Playfair Display,serif" font-weight="700" font-size="20" fill="#c9a84c" opacity="0">{n}</text>'
                f'<line id="r1-l-{i}" x1="40" y1="{50+i*70}" x2="400" y2="{50+i*70}" stroke="#c9a84c" stroke-width="2" stroke-dasharray="360" stroke-dashoffset="360"/>'
                for i, n in enumerate(["ROCKEFELLER","STANFORD","CARNEGIE","VANDERBILT","HARRIMAN","GOULD","FRICK","HUNTINGTON"])
            )
            # Round 2 (4 names winners)
            + "".join(
                f'<text id="r2-{i}" x="500" y="{80+i*140}" font-family="Playfair Display,serif" font-weight="700" font-size="22" fill="#c9a84c" opacity="0">{n}</text>'
                f'<line id="r2-l-{i}" x1="500" y1="{90+i*140}" x2="800" y2="{90+i*140}" stroke="#c9a84c" stroke-width="2" stroke-dasharray="300" stroke-dashoffset="300"/>'
                for i, n in enumerate(["ROCKEFELLER","CARNEGIE","HARRIMAN","FRICK"])
            )
            # Semifinals
            + "".join(
                f'<text id="r3-{i}" x="900" y="{160+i*280}" font-family="Playfair Display,serif" font-weight="700" font-size="26" fill="#c9a84c" opacity="0">{n}</text>'
                f'<line id="r3-l-{i}" x1="900" y1="{170+i*280}" x2="1200" y2="{170+i*280}" stroke="#c9a84c" stroke-width="2" stroke-dasharray="300" stroke-dashoffset="300"/>'
                for i, n in enumerate(["ROCKEFELLER","HARRIMAN"])
            )
            # Champion
            + '<text id="champion" x="1300" y="320" font-family="Playfair Display,serif" font-weight="900" font-size="40" fill="#c9a84c" opacity="0" filter="drop-shadow(0 0 12px #c9a84c)">ROCKEFELLER</text>'
            + '</svg>'
        ),
        "custom_card_in": (
            "\n".join(f"  tl.fromTo('#r1-{i}', {{ opacity:0 }}, {{ opacity:0.95, duration:0.3 }}, {0.5+i*0.1}); MM.pathDraw(tl, {{ selector: '#r1-l-{i}', start: {0.5+i*0.1}, duration:0.4 }});" for i in range(8))
            + "\n" + "\n".join(f"  tl.fromTo('#r2-{i}', {{ opacity:0 }}, {{ opacity:0.95, duration:0.3 }}, {1.8+i*0.2}); MM.pathDraw(tl, {{ selector: '#r2-l-{i}', start: {1.8+i*0.2}, duration:0.4 }});" for i in range(4))
            + "\n" + "\n".join(f"  tl.fromTo('#r3-{i}', {{ opacity:0 }}, {{ opacity:0.95, duration:0.3 }}, {3.2+i*0.3}); MM.pathDraw(tl, {{ selector: '#r3-l-{i}', start: {3.2+i*0.3}, duration:0.4 }});" for i in range(2))
            + "\n  MM.slamIn(tl, { selector: '#champion', start: 4.8, fromScale:1.5, fromY:-10 });"
        ),
    }),
    102: (recipe_card_stage, {  # Race ticker
        "title":"THE BELMONT, 1903", "subtitle":"purse: $50,000",
        "image_is_backdrop": True,
        "card_html": (
            '<div style="position:absolute; left:14%; right:14%; top:34%; bottom:28%; background: linear-gradient(180deg, #2a1f15, #0a0706); border:4px solid #c9a84c; padding:24px; box-shadow:0 18px 40px rgba(0,0,0,0.7);"></div>'
            + "".join(
                f'<div class="pos clip" id="pos-{i}" style="position:absolute; left:18%; top:{40+i*8}%; padding:10px 24px; color:#c9a84c; font-family:Playfair Display,serif; font-weight:700; font-size:30px; opacity:0; letter-spacing:2px;">'
                f'<span style="display:inline-block; width:80px; font-family:Courier New,monospace; color:#e8d6a8;">{place}</span>'
                f'<span>{name}</span>'
                f'</div>'
                for i, (place, name) in enumerate([
                    ("1ST","CHESTERFIELD"),("2ND","COMET KING"),("3RD","STAUNTON'S PRIDE"),
                ])
            )
            + '<div id="finish-flash" style="position:absolute; right:14%; top:30%; bottom:30%; width:8px; background: linear-gradient(180deg, transparent, #f5f0e4, transparent); opacity:0; box-shadow:0 0 30px #f5f0e4;"></div>'
        ),
        "custom_card_in": (
            "\n".join(f"  MM.slamIn(tl, {{ selector: '#pos-{i}', start: {0.6+i*0.6}, fromScale:1.1, fromX:60 }});" for i in range(3))
            + "\n  tl.fromTo('#finish-flash', { opacity:0, scaleY:0 }, { opacity:1, scaleY:1, duration:0.2, ease:'power2.out' }, 2.6);\n"
            + "  tl.to('#finish-flash', { opacity:0, duration:0.4, ease:'sine.in' }, 3.0);"
        ),
    }),
    103: (recipe_card_stage, {  # Award podium
        "title":"THE 1893 WORLD'S FAIR", "subtitle":"top three exhibitors",
        "image_is_backdrop": True,
        "card_html": (
            # Podium tiers
            '<div style="position:absolute; left:34%; top:60%; width:14%; height:24%; background:#3a2820; border:3px solid #c9a84c; padding-top:14px; text-align:center;"><div style="font-family:Playfair Display,serif; font-size:36px; font-weight:900; color:#c9a84c;">II</div></div>'
            '<div style="position:absolute; left:48%; top:50%; width:14%; height:34%; background:#3a2820; border:3px solid #c9a84c; padding-top:14px; text-align:center;"><div style="font-family:Playfair Display,serif; font-size:42px; font-weight:900; color:#c9a84c;">I</div></div>'
            '<div style="position:absolute; left:62%; top:66%; width:14%; height:18%; background:#3a2820; border:3px solid #c9a84c; padding-top:14px; text-align:center;"><div style="font-family:Playfair Display,serif; font-size:30px; font-weight:900; color:#c9a84c;">III</div></div>'
            # Medals
            + "".join(
                f'<div class="medal clip" id="med-{i}" style="position:absolute; left:{x}; top:{y}; width:60px; height:60px; border-radius:50%; background:{col}; border:4px solid #080c16; opacity:0; box-shadow:0 8px 18px rgba(0,0,0,0.5);"></div>'
                for i, (x, y, col) in enumerate([("39%","55%","#a8a8b0"),("53%","45%","#c9a84c"),("67%","61%","#a8693a")])
            )
            # Name banners
            + "".join(
                f'<div class="podium-name clip" id="pn-{i}" style="position:absolute; left:{x}; top:{y}; padding:6px 14px; background:#1a1208; border-bottom:3px solid #c9a84c; color:#c9a84c; font-family:Playfair Display,serif; font-weight:700; font-size:18px; opacity:0; text-align:center; width:14%;">{name}</div>'
                for i, (x, y, name) in enumerate([
                    ("34%","87%","CARNEGIE"),("48%","85%","ROCKEFELLER"),("62%","87%","MORGAN"),
                ])
            )
        ),
        "custom_card_in": (
            "\n".join(f"  MM.slamIn(tl, {{ selector: '#med-{i}', start: {1.0+i*0.5}, fromScale:1.4, fromY:-200 }});" for i in range(3))
            + "\n" + "\n".join(f"  tl.fromTo('#pn-{i}', {{ opacity:0, y:14 }}, {{ opacity:0.95, y:0, duration:0.45, ease:'sine.out' }}, {1.4+i*0.5});" for i in range(3))
        ),
    }),

    # ==================== U. Handmade ====================
    105: (recipe_document, {  # Diary entry — handwritten
        "title":"PRIVATE JOURNAL", "subtitle":"E.P. Ashford",
        "show_stamp": False,
        "extra_html": (
            '<div id="diary-text" style="position:absolute; left:22%; right:22%; top:32%; font-family:Georgia,serif; font-style:italic; font-size:30px; color:#1a0e08; line-height:1.5; overflow:hidden; white-space:pre-wrap; width:auto;">'
            'October 14, 1893 — He came again tonight. The contract is dust.'
            '</div>'
        ),
        "extra_tl_js": (
            "  // Reveal letter-by-letter via opacity sweep (approx)\n"
            "  tl.fromTo('#diary-text', { opacity:0, clipPath:'inset(0 100% 0 0)' }, { opacity:1, clipPath:'inset(0 0% 0 0)', duration:3.6, ease:'none' }, 1.0);"
        ),
    }),
    106: (recipe_card_stage, {  # Postcard stack
        "title":"FOUR CITIES", "subtitle":"the family travels",
        "card_html": (
            "".join(
                f'<div class="postcard clip" id="pc-{i}" style="position:absolute; left:{20+i*8}%; top:{20+i*4}%; '
                f'width:36%; height:50%; background: linear-gradient(180deg, #e0d4ac, #c4b387); border:5px solid #c9a84c; '
                f'padding:14px; box-shadow:0 18px 36px rgba(0,0,0,0.5); opacity:0; transform: rotate({-4+i*3}deg);">'
                f'<div style="text-align:center; font-family:Playfair Display,serif; font-weight:900; font-size:38px; color:#3a2410; letter-spacing:4px;">{city}</div>'
                f'<div style="margin:10px 20px; height:60%; background: linear-gradient(180deg, #4a6fa5, #6e8aac); border:2px solid #3a2410;"></div>'
                f'<div style="position:absolute; right:14px; top:14px; padding:6px 12px; background:#b41e1e; color:#f5f0e4; font-family:Playfair Display,serif; font-weight:900; font-size:14px; transform:rotate(-12deg);">2¢</div>'
                f'</div>'
                for i, city in enumerate(["NEWPORT","PARIS","VIENNA","BUENOS AIRES"])
            )
        ),
        "custom_card_in": "\n".join(f"  MM.slamIn(tl, {{ selector: '#pc-{i}', start: {0.5+i*0.6}, fromScale:1.1, fromY:-30 }});" for i in range(4)),
    }),
    107: (recipe_document, {  # Photo album spread
        "title":"THE FAMILY ALBUM", "subtitle":"1893 — 1921",
        "show_stamp": False,
        "extra_html": (
            "".join(
                f'<div class="album-photo clip" id="ap-{i}" style="position:absolute; left:{18+(i%2)*36}%; top:{30+(i//2)*30}%; '
                f'width:28%; height:24%; background:#5a4830; border:8px solid #f5f0e4; box-shadow:0 12px 28px rgba(0,0,0,0.6); '
                f'transform: rotate({-4+i*3}deg); opacity:0;">'
                f'<div style="position:absolute; left:-12px; top:-12px; width:36px; height:18px; background:rgba(232,220,180,0.7); transform:rotate(-20deg);"></div>'
                f'<div style="position:absolute; right:-12px; top:-12px; width:36px; height:18px; background:rgba(232,220,180,0.7); transform:rotate(20deg);"></div>'
                f'<div style="position:absolute; left:0; right:0; bottom:-32px; text-align:center; font-family:Georgia,serif; font-style:italic; font-size:14px; color:#3a2410;">{cap}</div>'
                f'</div>'
                for i, cap in enumerate(["Parents — 1893","Children — 1898","The Estate — 1905","The Yacht — 1912"])
            )
        ),
        "extra_tl_js": "\n".join(f"  MM.slamIn(tl, {{ selector: '#ap-{i}', start: {0.6+i*0.5}, fromScale:1.15, fromY:-20 }});" for i in range(4)),
    }),

    # ==================== V. Surreal ====================
    109: (recipe_surreal, {"kind":"zoom", "title":"INFINITE INHERITANCE", "subtitle":""}),
    110: (recipe_surreal, {"kind":"glitch", "title":"BEFORE / AFTER", "subtitle":""}),
    111: (recipe_surreal, {"kind":"shadow", "title":"WHAT HE CAST", "subtitle":""}),
    112: (recipe_surreal, {"kind":"glitch", "title":"", "subtitle":""}),
    113: (recipe_surreal, {"kind":"mirror", "title":"THE TWIN", "subtitle":""}),
}

