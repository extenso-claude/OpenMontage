"""qa_asset_sourcing — every imagery beat proves the copyright space was searched.

The maps-channel hard rule (asset-and-clip-director.md): for EVERY visual beat
you always search copyright + potential-copyright sources too, not just PD/free,
so you reach for the BEST asset and then decide how to clear it. This gate makes
that auditable: every IMAGERY asset's record must either

  (a) show the copyright space was searched  -> sourcing.searched_copyright == true
      (PD/free-only sourcing with no copyright search is the bug this catches), OR
  (b) carry a documented reason it was generated instead
      -> copyright_status == "generated" AND sourcing.generation_reason non-empty
      (Google Nano Banana fallback — paid, per-run approval, no baked text).

An imagery asset that satisfies NEITHER is an undocumented sourcing decision and
FAILS. Non-imagery assets (audio / music / sfx / procedural sprites / floorplans)
are not "imagery beats" and are skipped. The gate FAILS hard if the manifest is
missing — a gate that can't run must never silently pass.

Consistency guards (cheap, catch copy-paste mistakes):
  * copyright_status == "generated" but searched_copyright claimed true and no
    generation_reason -> still a FAIL (it's generated, document why).
  * a `sourcing` block that is present but not an object -> FAIL.

Reads: <project>/artifacts/asset_manifest.json
Shape (maps channel): assets[] each with `category`, `copyright_status`, and a
  `sourcing` block {searched_free?, searched_copyright?, queries?[], generation_reason?}.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List

from ._contract import Finding, GateInputError, load_json, run_cli

# Imagery categories that represent a visual beat the sourcing rule governs.
_IMAGERY_CATEGORIES = {
    "portrait", "character", "character_card", "character_cutout", "cutout",
    "illustration", "image", "archival_photo", "photo", "still",
    "archival_video", "video", "clip", "stock", "scene", "broll", "b-roll",
}
# Categories explicitly NOT imagery beats (no copyright-search obligation).
_NON_IMAGERY_CATEGORIES = {
    "audio", "music", "sfx", "sound", "voice", "narration",
    "sprite", "svg", "floorplan", "map", "basemap", "data",
}
# Imagery file extensions (fallback when category is absent/ambiguous).
_IMAGERY_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff",
                 ".mp4", ".mov", ".webm", ".mkv"}


def _is_imagery(asset: dict) -> bool:
    cat = str(asset.get("category", "")).strip().lower()
    if cat in _NON_IMAGERY_CATEGORIES:
        return False
    if cat in _IMAGERY_CATEGORIES:
        return True
    # Unknown/blank category: fall back to the file extension.
    path = str(asset.get("path", "")).strip().lower()
    return any(path.endswith(ext) for ext in _IMAGERY_EXTS)


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    manifest = load_json(project_dir / "artifacts" / "asset_manifest.json")
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise GateInputError("asset_manifest.json has no 'assets' array")

    findings: List[Finding] = []

    for i, asset in enumerate(assets):
        if not isinstance(asset, dict):
            findings.append(Finding(
                "fail", "malformed_asset", "asset entry is not an object",
                where=f"asset_manifest.json#assets[{i}]"))
            continue

        if not _is_imagery(asset):
            continue  # not an imagery beat -> no copyright-search obligation

        aid = asset.get("asset_id") or asset.get("id") or f"assets[{i}]"
        status = str(asset.get("copyright_status", "")).strip().lower()

        sourcing = asset.get("sourcing")
        if sourcing is not None and not isinstance(sourcing, dict):
            findings.append(Finding(
                "fail", "malformed_sourcing",
                f"imagery asset '{aid}' has a `sourcing` field that is not an object.",
                where=aid))
            continue
        sourcing = sourcing or {}

        gen_reason = sourcing.get("generation_reason")
        has_gen_reason = isinstance(gen_reason, str) and gen_reason.strip() != ""
        searched_copyright = sourcing.get("searched_copyright") is True

        # Path (a): generated assets must document WHY (what was searched, why nothing cleared).
        if status == "generated":
            if not has_gen_reason:
                findings.append(Finding(
                    "fail", "generated_without_reason",
                    f"imagery asset '{aid}' is copyright_status='generated' but carries no "
                    "`sourcing.generation_reason` — a generated (paid Nano Banana) asset must "
                    "document what copyright/free sources were searched and why nothing cleared.",
                    where=aid))
            continue  # documented generation is an acceptable sourcing decision

        # Path (b): everything else must prove the copyright space was searched.
        if not searched_copyright:
            findings.append(Finding(
                "fail", "copyright_space_not_searched",
                f"imagery asset '{aid}' does not record `sourcing.searched_copyright: true` "
                "and is not a documented generation — the copyright/potential-copyright space "
                "must ALWAYS be searched (not just PD/free), or the asset must be generated "
                "with a documented reason.",
                where=aid))

    return findings


if __name__ == "__main__":
    run_cli("qa_asset_sourcing", check)
