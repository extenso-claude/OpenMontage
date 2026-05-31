"""qa_asset_reference_closure — every sourced asset is used, every reference resolves.

Catches the twin "asset bookkeeping" bugs that bloat a run and break renders:
  1. SOURCED-BUT-UNUSED: an asset was sourced (paid for / downloaded / cleared)
     and sits in the manifest but no cue references it. Either wire it in or
     formally scrap it — silent orphans are wasted work and license risk.
  2. DANGLING REFERENCE: a cue points at an asset_id that the manifest does not
     contain. That render will fail or show a hole; it must never reach compose.

Rule (locked):
    referenced = { cue.asset_id for cue in cuelist.json if cue.asset_id }
    For each asset in asset_manifest.json:
        - id in referenced                         -> ok
        - has structured scrap {reason, evidence_url} both NON-EMPTY -> scrapped
        - otherwise                                -> FAIL (sourced-but-unused)
    For each referenced id with no matching manifest asset -> FAIL (dangling).
    Finally, if scrapped / total > 0.30 -> FAIL (too much waved through).
A scrap missing either reason or evidence_url is NOT valid: it does not count as
scrapped and the asset is treated as unused (FAIL). This stops "scrap: {}" from
laundering an orphan past the gate.

Reads:  <project>/artifacts/asset_manifest.json
        <project>/artifacts/cuelist.json
Shapes:
  asset_manifest.json = {"assets":[{"id","path","category","required"(bool),
                                    "scrap"?:{"reason","evidence_url"}}]}
  cuelist.json        = {"cues":[{"id", ..., "asset_id"?}]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Set

from ._contract import Finding, GateInputError, load_json, run_cli

SCRAP_BUDGET = 0.30  # max fraction of the manifest that may be scrapped


def _is_valid_scrap(scrap: object) -> bool:
    """A scrap is valid only if it carries a non-empty reason AND evidence_url."""
    if not isinstance(scrap, dict):
        return False
    reason = scrap.get("reason")
    evidence = scrap.get("evidence_url")
    return (
        isinstance(reason, str)
        and reason.strip() != ""
        and isinstance(evidence, str)
        and evidence.strip() != ""
    )


def _referenced_asset_ids(cuelist: dict) -> Set[str]:
    cues = cuelist.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")
    referenced: Set[str] = set()
    for cue in cues:
        if not isinstance(cue, dict):
            continue
        asset_id = cue.get("asset_id")
        if isinstance(asset_id, str) and asset_id.strip():
            referenced.add(asset_id)
    return referenced


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    manifest = load_json(project_dir / "artifacts" / "asset_manifest.json")
    cuelist = load_json(project_dir / "artifacts" / "cuelist.json")

    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise GateInputError("asset_manifest.json has no 'assets' array")

    referenced = _referenced_asset_ids(cuelist)

    findings: List[Finding] = []

    # Pass 1: classify every manifest asset.
    manifest_ids: Set[str] = set()
    total = 0
    scrapped = 0
    for i, asset in enumerate(assets):
        if not isinstance(asset, dict):
            findings.append(Finding(
                "fail", "malformed_asset",
                "asset entry is not an object",
                where=f"asset_manifest.json#assets[{i}]",
            ))
            continue
        # This pipeline's manifest + cuelist use `asset_id` as the canonical key
        # (cue references are `cue.asset_id`); accept it as an alias for the
        # generic `id` so the closure check matches the real field convention.
        aid = asset.get("id") or asset.get("asset_id")
        if not isinstance(aid, str) or not aid.strip():
            findings.append(Finding(
                "fail", "missing_asset_id",
                "manifest asset has no usable 'id' (nor 'asset_id')",
                where=f"asset_manifest.json#assets[{i}]",
            ))
            continue

        total += 1
        manifest_ids.add(aid)

        if aid in referenced:
            continue  # used by a cue -> ok

        # Not referenced: it must be formally scrapped to be acceptable.
        scrap = asset.get("scrap")
        if _is_valid_scrap(scrap):
            scrapped += 1
            continue

        # Unreferenced and not validly scrapped -> sourced-but-unused.
        if isinstance(scrap, dict):
            why = ("scrap present but invalid: 'reason' and 'evidence_url' must "
                   "both be non-empty")
        else:
            why = "no cue references it and it carries no structured scrap"
        findings.append(Finding(
            "fail", "sourced_but_unused",
            "asset was sourced but is never used (" + why + "). "
            "Wire it into a cue or add a valid scrap {reason, evidence_url}.",
            where=aid,
        ))

    # Pass 2: dangling references — a cue points at an id the manifest lacks.
    for ref in sorted(referenced - manifest_ids):
        findings.append(Finding(
            "fail", "dangling_reference",
            "cue references asset_id with no matching entry in asset_manifest.json "
            "(render would show a hole / fail).",
            where=ref,
        ))

    # Pass 3: scrap budget — too many waved-through assets signals sloppy sourcing.
    if total > 0:
        ratio = scrapped / total
        if ratio > SCRAP_BUDGET:
            findings.append(Finding(
                "fail", "scrap_budget_exceeded",
                "{}/{} assets ({:.0%}) were scrapped, over the {:.0%} ceiling — "
                "too much sourced work waved through.".format(
                    scrapped, total, ratio, SCRAP_BUDGET),
                where="asset_manifest.json",
            ))

    return findings


if __name__ == "__main__":
    run_cli("qa_asset_reference_closure", check)
