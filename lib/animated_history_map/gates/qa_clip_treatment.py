"""qa_clip_treatment — third-party copyrighted media must be transformed + framed.

Ports the Midnight-Magnates transformative-use rule to the maps channel: any
copyright / potential-copyright IMAGE or VIDEO asset that a project uses must be
run through the shared clip_treatment engine — a real color-grade recipe applied
AND composited inside a frame — before it can ship. Raw, ungraded, unframed
third-party media in the manifest is a copyright-exposure bug and FAILS.

Two exemptions, both deliberate:
  * Character images (a person we're introducing/telling a story about) route to
    the main flow's character cards/cutouts, NOT the copyright frame wrap. They
    are skipped (category in the character set, or is_character: true).
  * PD / free-licensed media needs no transformation — the rule is only about
    third-party copyright exposure.

What counts as "applied + framed":
  * `treatment` (alias `filter`) must name a REAL recipe in the engine
    (tools/clip_treatment/filters.py — parsed from source so the gate can't drift
    from the engine). A made-up grade name does not clear the rule.
  * `frame` must be one of the 8 approved frames OR an ERA frame whose
    frame-<name>.html actually exists in tools/clip_treatment/frames/ (e.g. the
    Lincoln-1865 `civil-war-portrait`). A frame name with no composition behind
    it is not a real wrap.
  * If the asset is a VIDEO clip whose audio is kept (`audio_role` == vo_pause /
    mixed / kept), the kept audio must also carry a real audio recipe
    (`audio_treatment`/`audio`) — a fingerprint-defeating shift, per the locked
    default. vo_over / muted clips don't need it.

The gate PASSES on a project with no copyright assets (it's a lint over what
exists, not a presence check), but FAILS hard if asset_manifest.json is missing —
a gate that can't run must never silently pass.

Reads: <project>/artifacts/asset_manifest.json
Shape (maps channel, see asset-and-clip-director.md):
  {"assets":[{"asset_id","category","path",
              "copyright_status": pd|free_license|copyright|potential_copyright|generated,
              "treatment"?, "frame"?, "audio_role"?, "audio_treatment"?,
              "is_character"?}]}
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import List, Set

from ._contract import Finding, GateInputError, load_json, run_cli

# Statuses that carry third-party copyright exposure -> must be transformed.
_COPYRIGHT_STATUSES = {"copyright", "potential_copyright"}

# Imagery categories whose media is third-party B-roll/scene/document content.
# Character categories are EXEMPT (handled by character cards, not the frame wrap).
_CHARACTER_CATEGORIES = {"portrait", "character", "character_card", "character_cutout", "cutout"}

# Audio-role tags meaning the clip's own audio is kept (so it needs an audio recipe).
_KEPT_AUDIO_ROLES = {"vo_pause", "vo-pause", "mixed", "kept", "keep"}

# The 8 production-approved frames (mirrors ClipTreatment.APPROVED_FRAMES).
_APPROVED_FRAMES = {
    "tv-vintage", "dossier", "newspaper", "fireside",
    "surveillance", "boardroom", "magnifier", "library",
}

_REPO = Path(__file__).resolve().parents[3]
_CLIP_TK = _REPO / "tools" / "clip_treatment"
_FRAMES_DIR = _CLIP_TK / "frames"


def _real_filter_recipes() -> Set[str]:
    """Parse the real filter-recipe names from the engine source (no heavy import)."""
    src = _CLIP_TK / "filters.py"
    if not src.exists():
        raise GateInputError(f"clip_treatment engine missing: {src}")
    return set(re.findall(r'\bRecipe\(\s*"([a-z0-9_]+)"', src.read_text(errors="replace")))


def _real_audio_recipes() -> Set[str]:
    src = _CLIP_TK / "audio_recipes.py"
    if not src.exists():
        raise GateInputError(f"clip_treatment engine missing: {src}")
    return set(re.findall(r'\bAudioRecipe\(\s*"([a-z0-9_]+)"', src.read_text(errors="replace")))


def _valid_frames() -> Set[str]:
    """Approved frames PLUS any era frame whose composition HTML actually exists."""
    frames = set(_APPROVED_FRAMES)
    if _FRAMES_DIR.is_dir():
        for h in _FRAMES_DIR.glob("frame-*.html"):
            frames.add(h.name[len("frame-"):-len(".html")])
    return frames


def _is_character(asset: dict) -> bool:
    if asset.get("is_character") is True:
        return True
    cat = str(asset.get("category", "")).strip().lower()
    return cat in _CHARACTER_CATEGORIES


def _kind_of(asset: dict) -> str:
    """image | video | other, from category/path."""
    cat = str(asset.get("category", "")).lower()
    path = str(asset.get("path", "")).lower()
    if "video" in cat or "clip" in cat or path.endswith((".mp4", ".mov", ".webm", ".mkv")):
        return "video"
    if (cat in {"image", "illustration", "archival_photo", "photo", "still", "stock"}
            or path.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff"))):
        return "image"
    return "other"


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    manifest = load_json(project_dir / "artifacts" / "asset_manifest.json")
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise GateInputError("asset_manifest.json has no 'assets' array")

    filters_ok = _real_filter_recipes()
    audio_ok = _real_audio_recipes()
    frames_ok = _valid_frames()

    findings: List[Finding] = []

    for i, asset in enumerate(assets):
        if not isinstance(asset, dict):
            findings.append(Finding(
                "fail", "malformed_asset", "asset entry is not an object",
                where=f"asset_manifest.json#assets[{i}]"))
            continue

        aid = asset.get("asset_id") or asset.get("id") or f"assets[{i}]"
        status = str(asset.get("copyright_status", "")).strip().lower()

        # Only third-party copyright/potential-copyright media is in scope.
        if status not in _COPYRIGHT_STATUSES:
            continue

        # Character imagery is exempt — routed to character cards, not the wrap.
        if _is_character(asset):
            continue

        kind = _kind_of(asset)
        if kind == "other":
            # A copyright asset we can't classify as image/video still must be
            # treated+framed; treat as in-scope rather than waving it through.
            kind = "media"

        # --- Treatment (color grade) must be a REAL engine recipe. ---
        treatment = asset.get("treatment") or asset.get("filter")
        if not isinstance(treatment, str) or not treatment.strip():
            findings.append(Finding(
                "fail", "raw_untreated_media",
                f"copyright {kind} '{aid}' has no `treatment` — raw third-party media "
                "may not ship. Apply an era-appropriate grade via clip_treatment "
                "(e.g. sepia_archive for 1865, NOT MM noir).",
                where=aid))
        elif treatment.strip() not in filters_ok:
            findings.append(Finding(
                "fail", "unknown_treatment_recipe",
                f"copyright {kind} '{aid}' names treatment '{treatment}' which is not a "
                "real recipe in tools/clip_treatment/filters.py — it was never actually "
                "applied. Use a real recipe name.",
                where=aid))

        # --- Frame wrap must be approved or a real era-frame composition. ---
        frame = asset.get("frame")
        if not isinstance(frame, str) or not frame.strip():
            findings.append(Finding(
                "fail", "unframed_media",
                f"copyright {kind} '{aid}' is not composited inside a frame — third-party "
                "media must be wrapped (one of the 8 approved frames or an era frame).",
                where=aid))
        elif frame.strip() not in frames_ok:
            findings.append(Finding(
                "fail", "unknown_frame",
                f"copyright {kind} '{aid}' names frame '{frame}' which is neither an "
                "approved frame nor an era frame with a frame-<name>.html in "
                "tools/clip_treatment/frames/ — there is no composition behind it.",
                where=aid))

        # --- Kept clip audio must also carry a real audio recipe. ---
        if kind == "video":
            role = str(asset.get("audio_role", "")).strip().lower()
            if role in _KEPT_AUDIO_ROLES:
                a_recipe = asset.get("audio_treatment") or asset.get("audio")
                if not isinstance(a_recipe, str) or not a_recipe.strip():
                    findings.append(Finding(
                        "fail", "kept_audio_untreated",
                        f"copyright clip '{aid}' keeps its audio (audio_role='{role}') but "
                        "applies no audio recipe — the kept track must carry a "
                        "fingerprint-defeating shift (locked default: pitch_up_1st).",
                        where=aid))
                elif a_recipe.strip() not in audio_ok:
                    findings.append(Finding(
                        "fail", "unknown_audio_recipe",
                        f"copyright clip '{aid}' names audio recipe '{a_recipe}' which is not "
                        "in tools/clip_treatment/audio_recipes.py.",
                        where=aid))

    return findings


if __name__ == "__main__":
    run_cli("qa_clip_treatment", check)
