"""Channel themes for the animation catalog.

Each theme is a Python module exposing a `THEME` dict with:

    {
        "name": str,                          # canonical channel slug
        "display_name": str,                  # human-readable
        "palette_rgb": list[list[int]],       # for Recraft controls.colors
        "palette_css": dict[str, str],        # CSS var name → hex (overrides tokens.css)
        "style_addendum": str,                # prepended to every Recraft prompt
        "negative_prompt": str,               # passed to Recraft as negative_prompt
        "noir_filter_css": str,               # filter: ... applied via .hero / .noir-grade
        "default_copy": dict,                 # per format_id: {title: ..., subtitle: ...}
        "default_scenes": dict[int, str],     # per format_id: Recraft scene prompt
    }

Lookup:
    from tools.animation.catalog.themes import load_theme
    theme = load_theme("midnight-magnates")
    # → returns the THEME dict (raises if not found)

Add a new channel by dropping `themes/<slug>.py` exposing THEME and listing it
in `KNOWN_THEMES` below.
"""
from __future__ import annotations
from importlib import import_module
from typing import Any

KNOWN_THEMES = ["midnight-magnates", "grandpa-huxley"]


def load_theme(slug: str) -> dict[str, Any]:
    """Load a theme module by its slug. Raises if unknown."""
    if slug not in KNOWN_THEMES:
        raise ValueError(
            f"Unknown theme {slug!r}. Known: {KNOWN_THEMES}. "
            f"To add a theme: drop tools/animation/catalog/themes/<slug>.py with a THEME dict + register in KNOWN_THEMES."
        )
    module = import_module(f"tools.animation.catalog.themes.{slug.replace('-', '_')}")
    return module.THEME
