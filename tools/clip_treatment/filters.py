"""Clip Transformation Filter Library
====================================

A registry of FFmpeg filter-chain recipes for transformative editing of
third-party video clips. Each recipe returns the filter string for the
ffmpeg `-vf` (video filter) or `-filter_complex` parameter.

After the test sprint locks in winners, this library moves to
``tools/clip_treatment/filters.py`` as a BaseTool-wrapped capability.

Usage
-----
    from filter_library import apply_filter, list_filters

    apply_filter(
        input_path="raw.mp4",
        output_path="treated.mp4",
        recipe_name="crt_subtle",
        target_resolution=(1920, 1080),
    )

Design notes
------------
- All filters end with scale+pad+setsar to 1920x1080 SAR=1 by default so the
  final cuts assemble cleanly. Override via `target_resolution`.
- Recipes use only ffmpeg built-in filters (no external libs) so the toolkit
  is portable across machines.
- Each recipe has a `mood_score` (1=jarring, 5=sleep-safe) to support QA.
"""
from __future__ import annotations

import dataclasses
import shlex
import subprocess
from pathlib import Path
from typing import Callable, Dict, Tuple

# ---------------------------------------------------------------------------
# Recipe dataclass
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class Recipe:
    name: str
    category: str
    description: str
    mood_score: int  # 1=jarring, 5=sleep-safe (Midnight Magnates needs 3+)
    vf_builder: Callable[[Tuple[int, int]], str]
    best_for: list[str]  # content types this fits

    def filter_chain(self, target_resolution: Tuple[int, int] = (1920, 1080)) -> str:
        return self.vf_builder(target_resolution)


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------

def _scale_pad(target: Tuple[int, int]) -> str:
    """Always end with this. Letterboxes/pillarboxes to 1920x1080, square pixels."""
    w, h = target
    return (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1"
    )


def _chromatic_aberration(offset_px: int = 2) -> str:
    """RGB channel offset for that off-broadcast TV vibe."""
    return f"rgbashift=rh={offset_px}:rv=0:bh=-{offset_px}:bv=0"


def _vignette(angle: float = 1.2) -> str:
    """Darken corners. angle in radians; 1.2 = subtle, 0.9 = heavy."""
    return f"vignette=PI/{angle:.2f}"


def _scanlines(intensity: float = 0.3, frequency: float = 2.0) -> str:
    """Horizontal scan lines via geq."""
    return (
        f"geq=lum='lum(X,Y)*(1-{intensity}+{intensity}*"
        f"sin(2*PI*Y/{frequency}))':cb='cb(X,Y)':cr='cr(X,Y)'"
    )


def _aperture_grille(dot_size: int = 3) -> str:
    """Fine TV-pixel dot grille (the look in the reference image).

    Uses lt() function instead of < operator to avoid ffmpeg eval parser
    confusion with nested parens. Multiplies two AND-like masks for X and Y.
    """
    k = dot_size // 2 or 1
    return (
        f"geq=lum='lum(X\\,Y)*(0.65+0.35*"
        f"lt(mod(X\\,{dot_size})\\,{k})*"
        f"lt(mod(Y\\,{dot_size})\\,{k}))':"
        f"cb='cb(X\\,Y)':cr='cr(X\\,Y)'"
    )


# ---------------------------------------------------------------------------
# CRT variants
# ---------------------------------------------------------------------------

def _crt_subtle(t):
    # The reference-image look. Fine aperture grille, mild aberration, gentle vignette.
    # Brightness +0.02 floor so dark sources don't black out completely (QA finding).
    return ",".join([
        "eq=brightness=0.04",  # pre-lift dark sources before filter compounding
        _aperture_grille(dot_size=3),
        _chromatic_aberration(2),
        "eq=brightness=-0.02:contrast=1.08:saturation=0.85",
        _vignette(1.4),  # softer vignette to avoid black corners on dark sources
        "gblur=sigma=0.4",
        _scale_pad(t),
    ])


def _crt_heavy(t):
    # 60s broadcast: coarse grille, heavy bloom, strong vignette, desaturated.
    # Lifted minimum brightness so it stays watchable on dark sources.
    return ",".join([
        "eq=brightness=0.06",  # lift before compounding
        _aperture_grille(dot_size=5),
        _scanlines(0.45, 3.0),
        _chromatic_aberration(4),
        "eq=brightness=-0.04:contrast=1.18:saturation=0.55",
        _vignette(1.05),
        "gblur=sigma=0.8",
        _scale_pad(t),
    ])


def _crt_dream(t):
    # Sleep-tuned: soft grille, warm color, heavy blur, gentle vignette.
    # Sleep niche prefers dim but not unwatchable. Floor mean luma ~ 25-35.
    return ",".join([
        "eq=brightness=0.08",  # raise floor first
        _aperture_grille(dot_size=4),
        _chromatic_aberration(1),
        "eq=brightness=-0.04:contrast=0.92:saturation=0.65:gamma_r=1.12:gamma_b=0.88",
        _vignette(1.2),
        "gblur=sigma=1.5",
        _scale_pad(t),
    ])


# ---------------------------------------------------------------------------
# VHS variants
# ---------------------------------------------------------------------------

def _vhs_subtle(t):
    return ",".join([
        "noise=alls=8:allf=t",
        _chromatic_aberration(3),
        "eq=saturation=0.9:contrast=1.05",
        # Occasional horizontal tracking line via geq is expensive; use hue jitter for now.
        "hue=h=2*sin(2*PI*t/3)",
        _scale_pad(t),
    ])


def _vhs_heavy(t):
    return ",".join([
        "noise=alls=20:allf=t",
        _chromatic_aberration(6),
        "eq=saturation=0.7:contrast=1.15:brightness=-0.06",
        "hue=h=8*sin(2*PI*t/2)",
        "gblur=sigma=0.6",
        _scale_pad(t),
    ])


def _vhs_ep_mode(t):
    # Faded EP-mode: soft, smeary, color-bleed
    return ",".join([
        "noise=alls=12:allf=t",
        _chromatic_aberration(5),
        "eq=saturation=0.55:contrast=0.85:brightness=-0.04:gamma=1.15",
        "gblur=sigma=1.8",
        _scale_pad(t),
    ])


# ---------------------------------------------------------------------------
# Halftone / newsprint
# ---------------------------------------------------------------------------

def _halftone_fine(t):
    # Fine dot pattern. Outputs grays (180/40) instead of pure binary (255/0)
    # so bright sources don't blow out to mean luma > 200 (QA finding on Dulles ID).
    # cb=128, cr=128 enforces true grayscale (without this, geq inherits lum
    # expression for chroma and produces magenta/green artifacts).
    return ",".join([
        "hue=s=0",
        "eq=contrast=0.85",
        f"geq=lum='if(gt(lum(X\\,Y),128+64*sin(X*PI/3)*sin(Y*PI/3)),180,40)':cb='128':cr='128'",
        _scale_pad(t),
    ])


def _halftone_coarse(t):
    return ",".join([
        "hue=s=0",
        "eq=contrast=0.85",
        f"geq=lum='if(gt(lum(X\\,Y),128+96*sin(X*PI/6)*sin(Y*PI/6)),190,30)':cb='128':cr='128'",
        _scale_pad(t),
    ])


def _bw_posterize(t):
    return ",".join([
        "hue=s=0",
        "eq=contrast=1.6:brightness=-0.05",
        "noise=alls=5:allf=t",
        _scale_pad(t),
    ])


# ---------------------------------------------------------------------------
# Film grain / archive
# ---------------------------------------------------------------------------

def _film_16mm(t):
    return ",".join([
        "noise=alls=10:allf=t+p",
        "eq=contrast=1.08:saturation=0.85:gamma_r=1.05",
        _vignette(1.3),
        _scale_pad(t),
    ])


def _film_8mm(t):
    return ",".join([
        "noise=alls=22:allf=t+p",
        "eq=contrast=1.15:saturation=0.7:gamma_r=1.1:brightness=0.02",
        "hue=h=3*sin(2*PI*t/0.7)",
        _vignette(1.0),
        "gblur=sigma=0.5",
        _scale_pad(t),
    ])


def _sepia_archive(t):
    return ",".join([
        "hue=s=0",
        "colorbalance=rs=0.3:gs=0.05:bs=-0.2",
        "eq=brightness=-0.04:contrast=1.05",
        "noise=alls=14:allf=t",
        _vignette(1.1),
        _scale_pad(t),
    ])


# ---------------------------------------------------------------------------
# Glitch / datamosh
# ---------------------------------------------------------------------------

def _glitch_subtle(t):
    # Subtle pixel smear via deflate + temporal noise
    return ",".join([
        "deflate=threshold0=20",
        "noise=alls=15:allf=t",
        _chromatic_aberration(3),
        _scale_pad(t),
    ])


def _glitch_heavy(t):
    return ",".join([
        "deflate=threshold0=40",
        "noise=alls=30:allf=t",
        _chromatic_aberration(8),
        "eq=contrast=1.2:saturation=1.1",
        _scale_pad(t),
    ])


def _signal_interference(t):
    return ",".join([
        "noise=alls=18:allf=t",
        _chromatic_aberration(5),
        "eq=brightness=0.05:contrast=1.3",
        # Horizontal interference: shift rows via geq is heavy; use chroma noise instead.
        _scale_pad(t),
    ])


# ---------------------------------------------------------------------------
# Color grade only
# ---------------------------------------------------------------------------

def _grade_crushed_warm(t):
    return ",".join([
        "eq=brightness=-0.06:contrast=1.18:saturation=0.85:gamma_r=1.1:gamma_b=0.92",
        "curves=preset=darker",
        _scale_pad(t),
    ])


def _grade_cyan_orange(t):
    return ",".join([
        "colorbalance=rs=0.15:gs=-0.05:bs=-0.15:rm=0.1:gm=0:bm=-0.1:rh=-0.1:gh=0:bh=0.15",
        "eq=contrast=1.1:saturation=1.05",
        _scale_pad(t),
    ])


def _grade_sepia_heavy(t):
    return ",".join([
        "hue=s=0",
        "colorbalance=rs=0.45:gs=0.1:bs=-0.3",
        "eq=brightness=-0.04:contrast=1.1",
        _vignette(0.95),
        _scale_pad(t),
    ])


# ---------------------------------------------------------------------------
# Inversion / posterize
# ---------------------------------------------------------------------------

def _negative_full(t):
    return ",".join([
        "negate",
        "eq=saturation=0.6:contrast=1.05",
        _scale_pad(t),
    ])


def _negative_selective_red(t):
    return ",".join([
        "lutrgb=r=negval:g=val:b=val",
        _scale_pad(t),
    ])


def _posterize_8(t):
    # Bit-depth reduction to 8 levels per channel via integer quantization.
    # `val/32*32` quantizes 0-255 into 8 bands. Avoids the nested-if quoting issue.
    return ",".join([
        "eq=saturation=1.1",
        "lutrgb=r=val/32*32:g=val/32*32:b=val/32*32",
        _scale_pad(t),
    ])


def _posterize_4(t):
    # 4 levels per channel: val/64*64.
    return ",".join([
        "eq=saturation=1.2:contrast=1.15",
        "lutrgb=r=val/64*64:g=val/64*64:b=val/64*64",
        _scale_pad(t),
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RECIPES: Dict[str, Recipe] = {
    "crt_subtle":            Recipe("crt_subtle",            "crt",       "Reference-image look: fine aperture grille, mild aberration, soft vignette.", 4, _crt_subtle,            ["interview", "talking-head", "archival"]),
    "crt_heavy":             Recipe("crt_heavy",             "crt",       "60s broadcast: coarse grille, heavy bloom, strong vignette.",                 3, _crt_heavy,             ["archival", "event", "newscast"]),
    "crt_dream":             Recipe("crt_dream",             "crt",       "Sleep-tuned: warm, blurred, gentle. Best for Midnight Magnates.",             5, _crt_dream,             ["interview", "photo", "ambient"]),

    "vhs_subtle":            Recipe("vhs_subtle",            "vhs",       "Subtle VHS: mild grain, light chroma bleed.",                                 3, _vhs_subtle,            ["archival", "amateur"]),
    "vhs_heavy":             Recipe("vhs_heavy",             "vhs",       "Heavy VHS: strong noise, chroma bleed, hue wobble.",                          2, _vhs_heavy,             ["surveillance", "leaked"]),
    "vhs_ep_mode":           Recipe("vhs_ep_mode",           "vhs",       "Faded EP-mode VHS: smudgy, low contrast.",                                    3, _vhs_ep_mode,           ["home-recording", "ambient"]),

    "halftone_fine":         Recipe("halftone_fine",         "halftone",  "Fine newsprint dot halftone (B&W).",                                          3, _halftone_fine,         ["document", "still", "photo"]),
    "halftone_coarse":       Recipe("halftone_coarse",       "halftone",  "Coarse newsprint dot halftone (B&W).",                                        2, _halftone_coarse,       ["document", "still"]),
    "bw_posterize":          Recipe("bw_posterize",          "halftone",  "High-contrast B&W posterize with grain.",                                     3, _bw_posterize,          ["document", "still"]),

    "film_16mm":             Recipe("film_16mm",             "film",      "Subtle 16mm: modest grain, slight warm cast.",                                4, _film_16mm,             ["archival", "interview", "event"]),
    "film_8mm":              Recipe("film_8mm",              "film",      "Heavy 8mm: strong grain, scratches feel, hue weave.",                         3, _film_8mm,              ["home-movie", "old-archive"]),
    "sepia_archive":         Recipe("sepia_archive",         "film",      "Sepia archive: desaturated, warm-shifted, grainy.",                           4, _sepia_archive,         ["photo", "old-document"]),

    "glitch_subtle":         Recipe("glitch_subtle",         "glitch",    "Subtle glitch: pixel smear + noise + aberration.",                            2, _glitch_subtle,         ["digital", "modern"]),
    "glitch_heavy":          Recipe("glitch_heavy",          "glitch",    "Heavy glitch: strong artifact, color shift.",                                 1, _glitch_heavy,          ["transition", "burst"]),
    "signal_interference":   Recipe("signal_interference",   "glitch",    "Signal noise: high contrast + aberration.",                                   2, _signal_interference,   ["transition", "burst"]),

    "grade_crushed_warm":    Recipe("grade_crushed_warm",    "grade",     "Color grade only: crushed blacks + warm cast.",                               4, _grade_crushed_warm,    ["interview", "archival"]),
    "grade_cyan_orange":     Recipe("grade_cyan_orange",     "grade",     "Color grade only: cyan-orange teal grade.",                                   3, _grade_cyan_orange,     ["event", "modern"]),
    "grade_sepia_heavy":     Recipe("grade_sepia_heavy",     "grade",     "Color grade only: heavy sepia + vignette.",                                   4, _grade_sepia_heavy,     ["archival", "photo"]),

    "negative_full":         Recipe("negative_full",         "invert",    "Full negative: thematic / dream moments.",                                    2, _negative_full,         ["transition", "abstract"]),
    "negative_selective":    Recipe("negative_selective",    "invert",    "Invert red channel only.",                                                    1, _negative_selective_red, ["transition", "abstract"]),

    "posterize_8":           Recipe("posterize_8",           "posterize", "Posterize to 8 color levels.",                                                3, _posterize_8,           ["still", "illustration"]),
    "posterize_4":           Recipe("posterize_4",           "posterize", "Posterize to 4 color levels (graphic novel).",                                3, _posterize_4,           ["still", "illustration"]),
}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def list_filters(category: str | None = None, min_mood: int = 0) -> list[str]:
    """List filter names, optionally filtered by category and mood floor."""
    return [
        name for name, r in RECIPES.items()
        if (category is None or r.category == category) and r.mood_score >= min_mood
    ]


def apply_filter(
    input_path: str | Path,
    output_path: str | Path,
    recipe_name: str,
    target_resolution: Tuple[int, int] = (1920, 1080),
    preserve_audio: bool = True,
    overwrite: bool = True,
) -> dict:
    """Apply a named filter recipe to a video. Returns a result dict.

    The audio is preserved untouched unless preserve_audio=False. Use the
    separate audio_treatment module to pitch-shift / EQ / mute the source audio.
    """
    if recipe_name not in RECIPES:
        raise ValueError(f"Unknown recipe: {recipe_name}. Try one of: {list(RECIPES)}")

    recipe = RECIPES[recipe_name]
    vf = recipe.filter_chain(target_resolution)

    cmd = [
        "ffmpeg",
        "-y" if overwrite else "-n",
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
    ]
    if preserve_audio:
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    else:
        cmd.append("-an")
    cmd.append(str(output_path))

    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "recipe": recipe_name,
        "category": recipe.category,
        "mood_score": recipe.mood_score,
        "input": str(input_path),
        "output": str(output_path),
        "filter_chain": vf,
        "success": proc.returncode == 0,
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-10:]) if proc.stderr else "",
        "cmd": " ".join(shlex.quote(c) for c in cmd),
    }


if __name__ == "__main__":
    print(f"Recipe count: {len(RECIPES)}")
    by_cat: Dict[str, list[str]] = {}
    for name, r in RECIPES.items():
        by_cat.setdefault(r.category, []).append(f"{name} (mood={r.mood_score})")
    for cat, items in by_cat.items():
        print(f"\n{cat}:")
        for it in items:
            print(f"  - {it}")
