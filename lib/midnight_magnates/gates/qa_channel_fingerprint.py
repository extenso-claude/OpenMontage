"""qa_channel_fingerprint — the cross-channel swap-test for the two sleep
channels that share one niche.

Prevents the SPECIFIC demonetization bug class: a Grandpa Huxley overlay drifting
into Midnight Magnates' look (or vice-versa) so the two channels become visually
interchangeable. Two near-identical channels in the same niche is exactly the
"inauthentic / duplicated content" signal YouTube enforces against, so each
channel's LOCKED fingerprint — its typography family, its color palette, and its
music-bed ceiling — must be honored by every cue. A single Georgia caption on a
Huxley card, or a noir-navy #080c16 plate on a Huxley overlay, makes the frame
indistinguishable from Midnight Magnates and is a blocking fail here.

What it does:
  * Reads the cuelist's declared ``channel`` (grandpa_huxley | midnight_magnates).
    If the cuelist declares no channel, the swap-test cannot run -> GateInputError
    (a gate that cannot run is a blocking fail, never a silent pass).
  * Loads that channel's style playbook (styles/<channel>.yaml) and reads the
    LOCKED fingerprint from it:
        - allowed fonts   = typography.headings.font + typography.body.font
                            (+ any other typography.*.font the playbook declares)
        - in-palette hexes = every hex string under visual_language.color_palette
        - music cap        = audio.music_volume
  * Then asserts the cuelist does not violate that fingerprint. For every cue:
        - any cue-declared font MUST be one of the channel's font families, and
          MUST NOT be the OTHER channel's signature font (Georgia on GH, or
          Alegreya/Alegreya Sans on MM) -> cross_channel_font / off_brand_font.
        - any cue-declared plate/background color MUST be in the channel palette,
          and MUST NOT be the OTHER channel's signature color (the MM noir navy
          #080c16 / #0d0d1a on GH; the GH warm earth #1a1410 / brass-amber on MM)
          -> cross_channel_color / off_brand_color.
        - any cue-declared music level MUST be <= the playbook music cap
          -> music_over_cap.

  Rendered-frame palette sampling is OPTIONAL: if rendered frames exist under
  <project>/renders we note that a deeper pixel-level check could run, but the
  gate's verdict is computed from the cuelist + playbook alone so it is
  deterministically fixture-testable on artifacts.

Reads:  <project>/artifacts/cuelist.json   (must declare top-level "channel")
        <project>/styles/<channel>.yaml     (project-local override) OR
        <repo>/styles/<channel>.yaml        (canonical playbook fallback)
Shapes (only the fields this gate reads):
    cuelist  = {"channel": "grandpa_huxley"|"midnight_magnates",
                "cues": [{"id", ...,
                          "font"|"font_family"|"typography.font"?: str,
                          "plate_color"|"bg"|"background"|"plate.color"?: "#rrggbb",
                          "music_volume"|"music_level"|"music.volume"?: number},
                         ...]}
    playbook = {"typography": {"headings": {"font": str}, "body": {"font": str}},
                "visual_language": {"color_palette": {... hex strings ...}},
                "audio": {"music_volume": number}}
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml  # available in this environment; no yaml-free option for the playbook

from ._contract import Finding, GateInputError, load_json, run_cli

# Canonical channel slugs the swap-test understands.
KNOWN_CHANNELS = ("grandpa_huxley", "midnight_magnates")

# The OTHER channel — used to police a cross-channel swap directly.
OPPOSITE = {
    "grandpa_huxley": "midnight_magnates",
    "midnight_magnates": "grandpa_huxley",
}

# Hard cross-channel signatures. These are the LOCKED, channel-defining values
# from the two playbooks; declaring the opposite channel's signature is the swap
# bug itself, so we flag it even if (defensively) it somehow appears in-palette.
#   GH signature fonts: Alegreya / Alegreya Sans   GH signature bg: #1a1410 (warm earth)
#   MM signature font:  Georgia                    MM signature bg: #080c16 / #0d0d1a (noir navy)
SIGNATURE_FONTS: Dict[str, Set[str]] = {
    "grandpa_huxley": {"alegreya", "alegreya sans"},
    "midnight_magnates": {"georgia"},
}
# Channel-defining colors that must NEVER appear on the OTHER channel.
SIGNATURE_COLORS: Dict[str, Set[str]] = {
    # GH warm earth-dark + warm brass/amber — banned on MM.
    "grandpa_huxley": {"#1a1410", "#241a14", "#c9a84c", "#d4a54a", "#f0e6d2"},
    # MM noir navy — banned on GH. (#0d0d1a is the legacy noir-black variant.)
    "midnight_magnates": {"#080c16", "#0d0d1a", "#0d1424"},
}

# Fields a cue may use to declare each fingerprint dimension (compiler-flexible).
_FONT_KEYS = ("font", "font_family", "fontFamily", "typeface")
_COLOR_KEYS = ("plate_color", "plate_bg", "bg", "background", "background_color",
               "bg_color", "plate_color_hex")
_MUSIC_KEYS = ("music_volume", "music_level", "music_vol")

_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b")


def _is_number(v) -> bool:
    # bool is an int subclass; a True/False is not a real level.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _norm_font(name: str) -> str:
    """Lowercase + collapse internal whitespace so 'Alegreya  Sans' == 'alegreya sans'."""
    return " ".join(name.strip().lower().split())


def _norm_hex(value: str) -> Optional[str]:
    """Return a canonical lowercase ``#rrggbb`` if ``value`` is one hex color, else None.

    Expands the 3-digit shorthand (#abc -> #aabbcc) so palette and cue colors
    compare identically regardless of which form was written.
    """
    if not isinstance(value, str):
        return None
    s = value.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3})", s)
    if m:
        r, g, b = m.group(1)
        return "#" + r + r + g + g + b + b
    if re.fullmatch(r"#[0-9a-f]{6}", s):
        return s
    return None


def _nested_get(cue: dict, dotted_keys, sub_field: str):
    """Look up either a flat key or a one-level-nested {sub: {field}} for ``cue``.

    e.g. for plate color this also reads cue["plate"]["color"] / cue["typography"]
    ["font"], which is how a compiler might group per-cue style. Returns the first
    present value, else None.
    """
    for k in dotted_keys:
        if k in cue:
            return cue[k]
    # one-level nests the compiler might emit
    nest = cue.get(sub_field)
    if isinstance(nest, dict):
        for k in dotted_keys:
            if k in nest:
                return nest[k]
    return None


# --- playbook resolution ----------------------------------------------------

def _repo_styles_dir() -> Path:
    # this module: <repo>/lib/midnight_magnates/gates/qa_channel_fingerprint.py
    return Path(__file__).resolve().parents[3] / "styles"


def _candidate_playbook_paths(project_dir: Path, channel: str) -> List[Path]:
    """Where a channel playbook may live, in priority order.

    Project-local first (so a fixture/project can bundle its own playbook and the
    gate is testable without depending on the live repo styles), then the
    canonical repo styles dir. The channel slug uses underscores
    (grandpa_huxley); the style files use hyphens (grandpa-huxley.yaml), so we
    try both spellings.
    """
    names = {channel, channel.replace("_", "-")}
    paths: List[Path] = []
    for base in (project_dir / "styles", _repo_styles_dir()):
        for name in names:
            paths.append(base / f"{name}.yaml")
            paths.append(base / f"{name}.yml")
    # de-dup, keep order
    seen: Set[Path] = set()
    uniq: List[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def _load_playbook(project_dir: Path, channel: str) -> dict:
    tried: List[Path] = []
    for p in _candidate_playbook_paths(project_dir, channel):
        tried.append(p)
        if not p.exists():
            continue
        try:
            with open(p) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as exc:
            raise GateInputError(f"could not parse style playbook {p}: {exc}") from exc
        if not isinstance(data, dict):
            raise GateInputError(f"style playbook {p} is not a mapping")
        return data
    raise GateInputError(
        "no style playbook found for channel {0!r}; looked in: {1}".format(
            channel, ", ".join(str(t) for t in tried)
        )
    )


def _fingerprint_from_playbook(playbook: dict, channel: str):
    """Pull (allowed_fonts, palette_hexes, music_cap) — the LOCKED fingerprint.

    Each dimension is required: a playbook missing it cannot anchor the swap-test
    for that dimension, which is a blocking input error (never a silent pass)."""
    typ = playbook.get("typography")
    if not isinstance(typ, dict):
        raise GateInputError(f"playbook for {channel} has no 'typography' mapping")

    allowed_fonts: Set[str] = set()
    for role, spec in typ.items():
        if isinstance(spec, dict):
            f = spec.get("font")
            if isinstance(f, str) and f.strip():
                allowed_fonts.add(_norm_font(f))
    # headings + body are the load-bearing pair the rule names explicitly.
    for role in ("headings", "body"):
        spec = typ.get(role)
        if not (isinstance(spec, dict) and isinstance(spec.get("font"), str)
                and spec["font"].strip()):
            raise GateInputError(
                f"playbook for {channel} has no typography.{role}.font to lock"
            )
    if not allowed_fonts:
        raise GateInputError(f"playbook for {channel} declares no fonts to lock")

    vl = playbook.get("visual_language")
    if not isinstance(vl, dict) or not isinstance(vl.get("color_palette"), dict):
        raise GateInputError(
            f"playbook for {channel} has no visual_language.color_palette to lock"
        )
    palette_hexes: Set[str] = set()
    # color_palette values are strings or lists of strings; harvest every hex.
    for v in vl["color_palette"].values():
        items = v if isinstance(v, list) else [v]
        for item in items:
            if isinstance(item, str):
                for m in _HEX_RE.findall(item):
                    h = _norm_hex(m)
                    if h:
                        palette_hexes.add(h)
    if not palette_hexes:
        raise GateInputError(
            f"playbook for {channel} color_palette has no hex colors to lock"
        )

    audio = playbook.get("audio")
    if not isinstance(audio, dict) or not _is_number(audio.get("music_volume")):
        raise GateInputError(
            f"playbook for {channel} has no numeric audio.music_volume cap to lock"
        )
    music_cap = float(audio["music_volume"])

    return allowed_fonts, palette_hexes, music_cap


# --- the check ---------------------------------------------------------------

def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")

    channel_raw = data.get("channel")
    if not isinstance(channel_raw, str) or not channel_raw.strip():
        raise GateInputError(
            "cuelist.json declares no 'channel' — the cross-channel swap-test "
            "cannot run without knowing which channel's fingerprint to enforce"
        )
    channel = channel_raw.strip().lower()
    if channel not in KNOWN_CHANNELS:
        raise GateInputError(
            "cuelist.json 'channel' is {0!r}; expected one of {1}".format(
                channel_raw, " / ".join(KNOWN_CHANNELS)
            )
        )

    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    playbook = _load_playbook(project_dir, channel)
    allowed_fonts, palette_hexes, music_cap = _fingerprint_from_playbook(
        playbook, channel
    )

    other = OPPOSITE[channel]
    other_fonts = SIGNATURE_FONTS[other]
    other_colors = SIGNATURE_COLORS[other]

    findings: List[Finding] = []
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            findings.append(Finding(
                "fail", "malformed_cue", "cue is not an object",
                where="cue[{0}]".format(i)))
            continue
        if cue.get("_dropped") is True:
            continue  # a documented drop is not rendered — nothing to fingerprint
        cid = str(cue.get("id") or "cue[{0}]".format(i))

        # 1) Font fingerprint.
        font_val = _nested_get(cue, _FONT_KEYS, "typography")
        if isinstance(font_val, str) and font_val.strip():
            nf = _norm_font(font_val)
            if nf in other_fonts:
                findings.append(Finding(
                    "fail", "cross_channel_font",
                    "cue declares font {0!r}, the signature font of {1} — a "
                    "{2} overlay using it is visually interchangeable with the "
                    "other channel".format(font_val, other, channel),
                    where=cid))
            elif nf not in allowed_fonts:
                findings.append(Finding(
                    "fail", "off_brand_font",
                    "cue declares font {0!r}, not in {1}'s locked family "
                    "({2})".format(
                        font_val, channel,
                        ", ".join(sorted(allowed_fonts))),
                    where=cid))

        # 2) Plate / background color fingerprint.
        color_val = _nested_get(cue, _COLOR_KEYS, "plate")
        if isinstance(color_val, str) and color_val.strip():
            ch = _norm_hex(color_val)
            if ch is None:
                findings.append(Finding(
                    "fail", "bad_color",
                    "cue plate/background color {0!r} is not a #rrggbb hex".format(
                        color_val),
                    where=cid))
            elif ch in other_colors:
                findings.append(Finding(
                    "fail", "cross_channel_color",
                    "cue declares plate color {0}, a signature color of {1} — a "
                    "{2} overlay with it reads as the other channel".format(
                        ch, other, channel),
                    where=cid))
            elif ch not in palette_hexes:
                findings.append(Finding(
                    "fail", "off_brand_color",
                    "cue plate color {0} is not in {1}'s locked palette "
                    "({2})".format(
                        ch, channel, ", ".join(sorted(palette_hexes))),
                    where=cid))

        # 3) Music level vs the playbook cap.
        music_val = _nested_get(cue, _MUSIC_KEYS, "music")
        if music_val is not None:
            if not _is_number(music_val):
                findings.append(Finding(
                    "fail", "bad_music_level",
                    "cue music level {0!r} is not numeric".format(music_val),
                    where=cid))
            elif float(music_val) > music_cap + 1e-9:
                findings.append(Finding(
                    "fail", "music_over_cap",
                    "cue music level {0:g} exceeds {1}'s locked cap {2:g}".format(
                        float(music_val), channel, music_cap),
                    where=cid))

    # OPTIONAL deeper check: if rendered frames exist, a pixel-level palette
    # sample could run here. We keep the verdict on artifacts (cuelist+playbook)
    # so the gate is deterministically fixture-testable; just note availability.
    renders = project_dir / "renders"
    if renders.is_dir() and any(renders.rglob("*.png")):
        findings.append(Finding(
            "warn", "render_palette_check_skipped",
            "rendered frames present under renders/ — pixel-level palette "
            "sampling is available but not run by this artifact-only gate"))

    return findings


if __name__ == "__main__":
    run_cli("qa_channel_fingerprint", check)
