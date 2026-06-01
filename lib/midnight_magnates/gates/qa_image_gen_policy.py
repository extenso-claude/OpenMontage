"""qa_image_gen_policy — the AI-image-generation policy is physically enforced.

Midnight Magnates FORBIDS every AI image generator except Google Nano Banana.
The rule has lived in prose (asset-director.md, the channel quality_rules
recraft_forbidden / nano_banana_cap) but nothing in the only sanctioned output
path actually refused a Recraft/Flux/DALL·E/etc. asset — so a single
`provenance.generator: "recraft"` could ship undetected. This gate closes that
hole: it reads the asset manifest's provenance and makes both halves of the
policy un-shippable.

Two independent halves of the policy (both hard fails):

  1. forbidden_generator — ANY asset whose ``provenance.generator`` is one of
     the banned AI image generators {recraft, flux, dalle, imagen, midjourney,
     sdxl} is a FAIL. MM permits exactly ONE AI image generator — nano_banana —
     and forbids the rest outright; a Recraft-sourced still is the canonical bug.
     Real (non-AI) provenance — wikimedia, pexels, loc, internet_archive,
     hand-authored sprites — is fine and not policed here.

  2. nano_banana_over_cap — Nano Banana is paid + per-run-approved, so its use is
     capped. If the COUNT of assets with ``provenance.generator == "nano_banana"``
     exceeds NANO_BANANA_CAP, that is a FAIL (one finding for the whole manifest,
     reporting the count vs the cap). At/under the cap is fine.

Generator matching is case-insensitive and tolerant of ANY separator: both
sides are canonicalized by stripping every non-alphanumeric character (not by
collapsing separator runs to "_", which left "DALL-E"->"dall_e" never matching
"dalle" — a real RULE-4 hole). So "Nano Banana"/"nano-banana"/"NANO_BANANA" all
read as "nanobanana"; "DALL-E"/"dall_e"/"dalle"/"DALL·E" (unicode middle dot)
all read as "dalle"; "Mid Journey" reads as "midjourney" and "Imagen 3" as
"imagen3" — a cosmetic spelling can't smuggle a banned generator past the gate.

A gate that cannot run must never silently pass:
  * no asset_manifest.json / unreadable JSON      -> GateInputError (blocking)
  * manifest root is not an object                -> GateInputError
  * `assets` missing or not a list                -> GateInputError
  * an asset entry is not an object               -> "fail" (malformed_asset)
  * an asset's `provenance` present but not object -> "fail" (malformed_provenance)
Assets that simply omit provenance/generator are not AI-generated and are not
policed (they were sourced, not generated) — only a DECLARED banned generator,
or an over-cap nano_banana count, trips this gate.

Reads:  <project>/artifacts/asset_manifest.json
Shape (only the fields this gate reads):
    asset_manifest = {"assets": [
        {"id", "kind", "provenance": {"generator", ...}}, ...]}
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

# AI image generators MM forbids outright. Nano Banana is the ONLY permitted AI
# image generator and is deliberately absent from this set (it is cap-checked
# separately below). Stored in canonical (separator-free, lowercase) form — see
# _canon_generator. Each entry is exactly what its real-world spellings collapse
# to once EVERY non-alphanumeric character is stripped: "DALL-E"/"DALL·E"/"dall_e"
# /"dall e" -> "dalle"; "Mid Journey"/"mid-journey" -> "midjourney"; "Imagen 3"
# -> "imagen3"; "Stable Diffusion XL" -> "stablediffusionxl" (alias of "sdxl").
FORBIDDEN_GENERATORS = frozenset(
    {
        "recraft",
        "flux",
        "dalle",
        "imagen",      # bare "imagen" / "Imagen"
        "imagen3",     # "Imagen 3" -> "imagen3" (separators stripped, not collapsed)
        "imagen4",     # "Imagen 4"
        "midjourney",  # "Mid Journey" / "mid-journey" -> "midjourney"
        "sdxl",
        "stablediffusion",    # "Stable Diffusion" -> "stablediffusion"
        "stablediffusionxl",  # "Stable Diffusion XL" -> "stablediffusionxl"
    }
)

# The single permitted AI image generator, in canonical (separator-free) form.
# "nano_banana" / "Nano Banana" / "nano-banana" all canonicalize to "nanobanana".
NANO_BANANA = "nanobanana"

# Nano Banana is paid + per-run-approved, so its use is capped per video.
# A count strictly GREATER than this is a fail (the cap itself is allowed).
NANO_BANANA_CAP = 100

# Everything that is NOT an ASCII letter or digit is a separator. Stripping ALL
# such characters (rather than collapsing runs to a single "_") is what makes the
# two sides compare identically: "DALL-E", "dall_e", "dalle", "dall e" and the
# unicode middle-dot "DALL·E" (·) every collapse to the same bare token the
# forbidden/permitted name is stored under. A collapse-to-"_" scheme left a
# RULE-4 hole — "DALL-E"->"dall_e" never matched the stored "dalle".
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _canon_generator(raw) -> Optional[str]:
    """Canonicalize a generator value to a comparable token, or None.

    Lowercases, then strips EVERY non-alphanumeric character (whitespace,
    ._-, the unicode middle dot ·, etc.) so cosmetic spellings collapse to one
    bare token: "DALL-E"/"DALL·E"/"dall_e"/"dall e" -> "dalle",
    "Mid Journey" -> "midjourney", "Nano Banana" -> "nanobanana". Returns None
    for non-strings or values that are empty after normalization (an asset with
    no usable generator is treated as "no declared generator").
    """
    if not isinstance(raw, str):
        return None
    token = _NON_ALNUM.sub("", raw.lower())
    return token or None


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    manifest = load_json(project_dir / "artifacts" / "asset_manifest.json")
    if not isinstance(manifest, dict):
        raise GateInputError("asset_manifest.json root is not an object")
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise GateInputError("asset_manifest.json has no 'assets' array")

    findings: List[Finding] = []
    nano_banana_count = 0

    for i, asset in enumerate(assets):
        if not isinstance(asset, dict):
            findings.append(Finding(
                "fail", "malformed_asset", "asset entry is not an object",
                where="asset_manifest.json#assets[{0}]".format(i)))
            continue

        aid = str(asset.get("id") or asset.get("asset_id") or "assets[{0}]".format(i))

        provenance = asset.get("provenance")
        if provenance is None:
            # No provenance block at all -> not a declared AI generation; skip.
            continue
        if not isinstance(provenance, dict):
            findings.append(Finding(
                "fail", "malformed_provenance",
                "asset '{0}' has a `provenance` field that is not an object — "
                "cannot verify the image-gen policy against it".format(aid),
                where=aid))
            continue

        generator = _canon_generator(provenance.get("generator"))
        if generator is None:
            # No (usable) generator named -> sourced, not generated; not policed.
            continue

        # Half 1: an outright-forbidden AI image generator is an immediate fail.
        if generator in FORBIDDEN_GENERATORS:
            findings.append(Finding(
                "fail", "forbidden_generator",
                "asset '{0}' was produced by AI image generator '{1}', which "
                "Midnight Magnates forbids — the ONLY permitted AI image "
                "generator is nano_banana (source from wikimedia/pexels/etc. or "
                "regenerate with nano_banana).".format(
                    aid, provenance.get("generator")),
                where=aid))
            continue

        # Half 2 (tally): count permitted nano_banana assets for the cap check.
        if generator == NANO_BANANA:
            nano_banana_count += 1

    # Half 2 (verdict): one finding for the whole manifest if over the cap.
    if nano_banana_count > NANO_BANANA_CAP:
        findings.append(Finding(
            "fail", "nano_banana_over_cap",
            "{0} nano_banana-generated assets exceed the per-video cap of {1} "
            "(nano_banana is paid + per-run-approved; trim generated stills or "
            "source them from a free/PD provider).".format(
                nano_banana_count, NANO_BANANA_CAP),
            where="asset_manifest.json#assets"))

    return findings


if __name__ == "__main__":
    run_cli("qa_image_gen_policy", check)
