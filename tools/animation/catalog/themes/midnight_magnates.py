"""Midnight Magnates theme — noir documentary on dark histories of wealth.

Palette: deep navy / brass gold / muted red / cool noir blue / cream.
Mood: nighttime noir, single warm light source, deep cool shadows.
"""

THEME = {
    "name": "midnight-magnates",
    "display_name": "Midnight Magnates",

    # Recraft `controls.colors` payload — keeps generations on-brand.
    "palette_rgb": [
        [8, 12, 22],       # deep navy-black plate
        [17, 24, 42],      # night blue
        [201, 168, 76],    # brass gold
        [140, 110, 35],    # dimmed gold
        [74, 111, 165],    # cool noir blue
        [245, 240, 228],   # cream
        [180, 30, 30],     # classified red (sparingly)
    ],

    # CSS variable overrides — override tokens.css per-channel
    "palette_css": {
        "--mm-deep":      "#080c16",
        "--mm-night":     "#11182a",
        "--mm-gold":      "#c9a84c",
        "--mm-gold-dim":  "#8c6e23",
        "--mm-red":       "#b41e1e",
        "--mm-blue":      "#4a6fa5",
        "--mm-cream":     "#f5f0e4",
        "--mm-cream-dim": "#e8e0d0",
    },

    # Prepended to every Recraft prompt.
    # NOTE: "moonlit" is included as a default but should be overridden in the
    # scene prompt for indoor / non-moonlit scenes (interior offices, daytime
    # archival photos, basement scenes). Add "interior scene, no moonlight"
    # or similar to the scene prompt to override.
    "style_addendum": (
        "night colors, noir atmosphere, moonlit, flat segmented color illustration"
    ),

    # Recraft negative prompt — kept out of generations
    "negative_prompt": (
        "photorealistic, 3d render, photograph, gradients, soft shadows, glossy, "
        "busy, cluttered, motivational, daylight, pink, magenta, cyan, neon, "
        "bright pop art, cartoon mascot, candlelight philosopher imagery, "
        "exclamation point energy, hustle culture, "
        "text labels, lorem ipsum, captions, banners with text, writing on objects, "
        "dates, numbers, signs with text, headlines, watermark, signature, logo"
    ),

    # Filter applied to .hero / .noir-grade — uniform across all clips
    "noir_filter_css": "brightness(0.78) saturate(0.85) contrast(1.10) hue-rotate(-6deg)",

    # Default scene prompts per format — used when the caller doesn't override
    "default_scenes": {
        1:   "A wild-west saloon at night, exterior view — gold rush boom town, weathered wood facade, wide swinging doors slightly ajar, gas lanterns glowing in upstairs windows, hitching post with two saddled horses, dusty main street, distant frontier-town silhouette under starlight",
        2:   "An aged parchment last-will-and-testament on a desk lit by a single candle, deep navy table beneath, wax-seal half-broken, quill pen and ink-pot beside, brass-gold border on the page, ledger spine visible to the side",
        3:   "An empty Gilded-Age library at night — leather-bound books on tall shelves, brass reading-lamp glowing on an oak table, a single high-back armchair, deep cool moonlight through tall window, ornate Persian rug suggested in muted brass tones",
        8:   "Interior of a Gilded-Age private railcar — velvet bench seat, brass fixtures, ornate window frame. Through window: prairie at night parallaxing past — distant telegraph poles, scattered farmhouse lights, moonlit foothills",
        9:   "Cutout-paper diorama of a 19th-century counting-house: layered silhouettes — clerks at desks (front), safe (middle), magnate behind desk (back). Single warm light sweeps across all layers like a peep-show",
        17:  "Three tarot cards on a dark velvet table — backs facing up showing ornate gold-on-navy art-deco pattern. Reveal flips to: THE TOWER (lightning-struck), THE MAGICIAN (top-hat tycoon), THE WHEEL OF FORTUNE (golden gears)",
        18:  "WANTED dead or alive WESTERN poster — ink-stained cream paper, bold WANTED at top, REWARD $5,000 mid, sketch portrait of mustachioed cattle-baron at center, NEW MEXICO TERRITORY 1881 at bottom, all in brown ink",
        20:  "Six polaroids on a noir desktop — sepia photos of: oil derrick, family portrait, signed contract, mahogany mansion exterior, train yard, vault door. Strips of tape on corners, scattered diagonally",
        21:  "Vertical tier-list with rows S/A/B/C/D in brass-gold left tabs against dark backdrop. Six items in cards on dark navy: J.P.Morgan, Rockefeller, Carnegie, Vanderbilt, Gould, Astor — small portrait + name each",
        31:  "Three illustrated stages of a robber-baron's recipe for fortune: 1) bag of seed money on burlap, 2) hand-shake at lamplit table, 3) gold-bar pyramid on velvet — all single panels stacked",
        44:  "Profile of a 19th-century financier at his pulpit-podium, mid-speech, dim audience in foreground",
        46:  "Dark navy iMessage thread interface — gold-and-cream bubbles. Avatar of a top-hat figure labeled 'THE BENEFACTOR'",
        48:  "Dark-noir Google-style search screen — background is faint sepia mansion silhouette",
        53:  "Front-page of THE TRIBUNE 1929 — STOCK MARKET COLLAPSES huge headline, photo of crowd outside NYSE, sub-headlines about fortunes lost",
        55:  "B&W still of an early-1900s factory floor, workers at long benches, foremen looking on",
        58:  "6-slot grid inventory panel on dark navy backdrop — empty slots with gold borders, frame above 'MAGNATE'S CACHE'",
        67:  "Wide chalkboard at the front of an antique lecture-hall — gas lamps glowing dim, wooden desks in foreground out-of-focus",
        107: "Open vintage photo-album spread, leather binding, cream paper, 4 sepia photos taped at corners (parents, children, mansion, yacht)",
        111: "Wall with sharp silhouette of a top-hat-magnate-on-staircase casting elongated shadow, single warm light source from side",
    },

    # Default title / subtitle copy per format
    "default_copy": {
        1:   {"title": "DIAMOND LIL'S SALOON",      "subtitle": "Nevada Territory, 1881"},
        2:   {"title": "LAST WILL & TESTAMENT",     "subtitle": "of E.P. Staunton, dated 1893"},
        3:   {"title": "",                          "subtitle": ""},
        8:   {"title": "THE PRIVATE CAR",           "subtitle": "1892"},
        9:   {"title": "THE COUNTING-HOUSE",        "subtitle": ""},
        17:  {"title": "PAST · PRESENT · FUTURE",   "subtitle": ""},
        18:  {"title": "WANTED",                    "subtitle": "DEAD OR ALIVE — $5,000 REWARD"},
        20:  {"title": "THE FAMILY ARCHIVE",        "subtitle": ""},
        21:  {"title": "WEALTH TIERS",              "subtitle": "Net Worth in 1913 Dollars"},
        31:  {"title": "",                          "subtitle": ""},
        44:  {"title": "",                          "subtitle": ""},
        46:  {"title": "",                          "subtitle": ""},
        48:  {"title": "",                          "subtitle": ""},
        53:  {"title": "THE TRIBUNE",               "subtitle": "OCTOBER 30, 1929"},
        55:  {"title": "REEL VII",                  "subtitle": "FACTORY · 1904"},
        58:  {"title": "MAGNATE'S CACHE",           "subtitle": ""},
        67:  {"title": "THE FORMULA",               "subtitle": ""},
        107: {"title": "THE FAMILY ALBUM",          "subtitle": "1893 — 1921"},
        111: {"title": "WHAT HE CAST",              "subtitle": ""},
    },
}
