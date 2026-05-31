"""Grandpa Huxley theme — sleep-documentary style for the Huxley channel.

STUB — the palette and scene defaults are placeholders.
Tune them in a future Huxley R&D sprint similar to the May 2026 MM sprint.

The recipe library is shared with Midnight Magnates; only the palette,
style addendum, and default scene content differ here.
"""

THEME = {
    "name": "grandpa-huxley",
    "display_name": "Grandpa Huxley",

    # Placeholder palette — softer / warmer than MM. Adjust during channel R&D.
    "palette_rgb": [
        [22, 18, 12],     # deep warm bistre
        [42, 32, 22],     # muted umber
        [201, 168, 76],   # warm gold (kept from MM — works for both)
        [120, 90, 50],    # darkened brown
        [165, 130, 100],  # tan/sand
        [232, 220, 200],  # warm cream
        [140, 60, 40],    # rusted ember
    ],
    "palette_css": {
        "--mm-deep":      "#16120c",
        "--mm-night":     "#2a2016",
        "--mm-gold":      "#c9a84c",
        "--mm-gold-dim":  "#785a32",
        "--mm-red":       "#8c3c28",
        "--mm-blue":      "#5a4a3a",
        "--mm-cream":     "#e8dcc8",
        "--mm-cream-dim": "#d8c8b0",
    },

    "style_addendum": (
        "simple gentle minimalist flat segmented colors illustration, "
        "soft sleep-documentary mood, muted warm earth tones, clean flat shapes"
    ),

    "negative_prompt": (
        "photorealistic, 3d render, photograph, harsh shadows, glossy, busy, "
        "cluttered, motivational, bright neon, pink, magenta, cyan, "
        "exclamation point energy, hustle culture, "
        "text labels, lorem ipsum, captions, banners with text, writing on objects, "
        "dates, numbers, signs with text, headlines, watermark, signature, logo"
    ),

    # Slightly softer noir filter than MM
    "noir_filter_css": "brightness(0.85) saturate(0.75) contrast(1.05) sepia(0.10) hue-rotate(-2deg)",

    # Default scene prompts — Grandpa Huxley narrative beats. Placeholders for the channel.
    "default_scenes": {
        1: "An autumn cottage at dusk, exterior view — old stone walls, ivy, gas lamps in upstairs windows, garden path lined with chrysanthemums, distant elm trees under a warm dusk sky",
        2: "An aged journal page on a wooden writing-desk, single oil lamp beside, dried flower pressed in the binding, fountain pen, ink-pot, warm cream paper with cursive writing",
        3: "An empty woodland reading nook at dusk — a cozy armchair, knitted blanket, lantern on side-table, tall window onto autumn forest, soft warm glow",
        # ...remaining formats: same use cases, Huxley-flavored scenes. Tune during channel R&D.
        8:   "Interior of an Edwardian railcar at dusk — wooden interior, glowing wall lamps, gentle prairie at dusk parallaxing past the window",
        9:   "Cutout-paper diorama of a Victorian library — librarian at desk, towering shelves, warm reading light",
        17:  "Three storybook cards on a wooden table — warm parchment with brown ink illustrations of a clock, a moon, a lantern",
        18:  "A vintage carnival poster — cream paper, brown ink, sketch portrait of an old performer, warm earth-tone palette",
        20:  "Six sepia photographs scattered on a wooden desktop — countryside scenes, family meals, garden flowers, autumn leaves, with tape corners",
        21:  "Vertical list of sleep-story qualities S/A/B/C/D in warm gold tabs against dusk backdrop, six exemplar storybook cards",
        31:  "Three illustrated stages of brewing a calming tea: 1) gathered herbs in a basket, 2) kettle on hearth, 3) steaming cup on saucer — single panels stacked",
        44:  "Profile of a narrator at his old reading desk, single oil lamp, audience implied in the warm shadows",
        46:  "Warm-cream notebook with handwritten dialogue between two old friends, soft brown ink",
        48:  "Soft-warm Google-style search screen — background is faint sepia woodland silhouette",
        53:  "Front-page of THE COUNTY GAZETTE 1899 — gentle headline about a town fair, photo of the village green",
        55:  "B&W still of an early-1900s village square at dawn, market stalls being set up, gentle activity",
        58:  "6-slot grid inventory panel on warm-cream backdrop — empty slots with brown borders, frame above 'HUXLEY'S POCKETS'",
        67:  "Wide blackboard at the front of a country schoolhouse, oil lamps glowing, wooden benches in foreground out-of-focus",
        107: "Open vintage photo-album spread, warm leather binding, cream paper, 4 sepia photos taped at corners (family, harvest, hearth, garden)",
        111: "Wall with sharp silhouette of an old man with cane, casting elongated shadow, single warm lantern from side",
    },

    # Placeholder copy — tune during channel R&D
    "default_copy": {
        1:   {"title": "THE COTTAGE",         "subtitle": "Cotswolds, 1899"},
        2:   {"title": "THE OLD JOURNAL",     "subtitle": "Vol. III"},
        3:   {"title": "",                    "subtitle": ""},
        8:   {"title": "THE OLD CARRIAGE",    "subtitle": ""},
        9:   {"title": "THE LIBRARY",         "subtitle": ""},
        17:  {"title": "STORYBOOK CARDS",     "subtitle": ""},
        18:  {"title": "CARNIVAL TONIGHT",    "subtitle": "ONE NIGHT ONLY"},
        20:  {"title": "FAMILY ALBUM",        "subtitle": ""},
        21:  {"title": "BEDTIME TIERS",       "subtitle": "what helps you sleep"},
        31:  {"title": "",                    "subtitle": ""},
        44:  {"title": "",                    "subtitle": ""},
        46:  {"title": "",                    "subtitle": ""},
        48:  {"title": "",                    "subtitle": ""},
        53:  {"title": "THE COUNTY GAZETTE",  "subtitle": "1899"},
        55:  {"title": "REEL IV",             "subtitle": "VILLAGE · 1903"},
        58:  {"title": "HUXLEY'S POCKETS",    "subtitle": ""},
        67:  {"title": "THE LESSON",          "subtitle": ""},
        107: {"title": "THE ALBUM",           "subtitle": "1888 — 1920"},
        111: {"title": "THE OLD MAN'S SHADOW", "subtitle": ""},
    },
}
