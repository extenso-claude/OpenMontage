"""qa_schema_validate — make the registered JSON schemas load-bearing + check assets exist.

The animated-history-map artifact schemas were registered (2026-05-29) but nothing
actually validated project artifacts against them — they were decorative. This gate
closes that gap: for every schema-backed artifact that EXISTS in the project it runs
``schemas.artifacts.validate_file(name, path)`` and turns any ValidationError into a
blocking "fail" (reporting the JSON path + the schema message). It then existence-checks
every asset path the project declares, catching dangling references (a manifest entry or
a cue pointing at a panel image that was never written to disk).

Two distinct failure classes:
  1. SCHEMA INVALID — an artifact that exists violates its registered schema
     (e.g. theme.json missing a required field, a bad enum, a malformed hex accent).
  2. MISSING FILE   — an asset 'path' (from asset_manifest.json, or a file path
     referenced by a cue in cuelist.json) does not exist on disk relative to the
     project. That render would show a hole / fail; it must never reach compose.

Deliberately NOT a presence gate: an artifact being ABSENT is fine here (other gates
own presence). We only validate what exists. The one presence-like rule is on asset
paths — a manifest/cue path that points at a nonexistent file IS a fail, because the
manifest is asserting that file exists.

Reads (each optional except where a referenced path is asserted):
    <project>/artifacts/theme.json            -> midnight_magnates_theme
    <project>/artifacts/geography.json        -> midnight_magnates_geography
    <project>/artifacts/canonical_names.json  -> midnight_magnates_canonical_names
    <project>/artifacts/storyboard/*.json     -> midnight_magnates_storyboard
    <project>/artifacts/asset_manifest.json   (asset 'path' values existence-checked)
    <project>/artifacts/cuelist.json          (referenced file paths existence-checked)

Allowed: import schemas.artifacts (jsonschema is installed). stdlib otherwise.
"""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# (relative artifact path under the project, registered schema name).
# A single-file artifact validated against its schema iff the file exists.
SINGLE_FILE_SCHEMAS: List[Tuple[str, str]] = [
    ("artifacts/theme.json", "midnight_magnates_theme"),
    ("artifacts/geography.json", "midnight_magnates_geography"),
    ("artifacts/canonical_names.json", "midnight_magnates_canonical_names"),
]

# storyboard is one JSON per chapter under artifacts/storyboard/*.json
STORYBOARD_GLOB_DIR = "artifacts/storyboard"
STORYBOARD_SCHEMA = "midnight_magnates_storyboard"

# File extensions we treat as "this string is meant to be a file on disk" when
# scanning cue fields for referenced paths (so we don't flag e.g. anchor ids).
_PATHLIKE_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif",
    ".mp4", ".mov", ".webm", ".m4v",
    ".wav", ".mp3", ".aac", ".m4a", ".ogg", ".flac",
    ".json", ".html", ".lottie",
)


def _import_validate():
    """Import the schema validator lazily so an import failure is reported as a
    blocking input error (a gate that cannot run must never silently pass)."""
    try:
        from schemas.artifacts import validate_file  # type: ignore
        from jsonschema import ValidationError  # type: ignore
    except Exception as exc:  # ImportError, or jsonschema missing
        raise GateInputError(
            "could not import schema validator (schemas.artifacts / jsonschema): "
            f"{exc}"
        )
    return validate_file, ValidationError


def _validation_where(exc) -> str:
    """Best-effort JSON path of a ValidationError, e.g. '$.palette_master.primary_accent'."""
    jp = getattr(exc, "json_path", None)
    if isinstance(jp, str) and jp:
        return jp
    # Fallback for older jsonschema: build from absolute_path.
    parts = [str(p) for p in getattr(exc, "absolute_path", [])]
    return "$" + "".join(f".{p}" if not p.isdigit() else f"[{p}]" for p in parts) if parts else "$"


def _validate_one(
    validate_file, ValidationError, project_dir: Path, rel_path: str, schema_name: str
) -> List[Finding]:
    """Validate a single existing artifact file against its schema."""
    path = project_dir / rel_path
    if not path.exists():
        return []  # absence is not a fail here — other gates own presence.

    # If it exists but isn't valid JSON, the gate cannot do its job -> blocking input error.
    try:
        with open(path) as f:
            json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise GateInputError(f"could not read {rel_path}: {exc}")

    findings: List[Finding] = []
    try:
        validate_file(schema_name, str(path))
    except ValidationError as exc:
        findings.append(Finding(
            "fail", "schema_invalid",
            f"fails schema '{schema_name}': {exc.message}",
            where=f"{rel_path} @ {_validation_where(exc)}",
        ))
    return findings


def _validate_storyboards(
    validate_file, ValidationError, project_dir: Path
) -> List[Finding]:
    sb_dir = project_dir / STORYBOARD_GLOB_DIR
    if not sb_dir.is_dir():
        return []  # no storyboard dir -> nothing to validate (presence is another gate's job).
    findings: List[Finding] = []
    for path in sorted(sb_dir.glob("*.json")):
        rel = str(path.relative_to(project_dir))
        findings.extend(
            _validate_one(validate_file, ValidationError, project_dir, rel, STORYBOARD_SCHEMA)
        )
    return findings


def _referenced_cue_paths(cuelist: dict) -> List[Tuple[str, str]]:
    """Pull file-path-looking strings out of cues. Returns (path_string, cue_id) pairs.

    We scan known path-bearing fields plus any string field whose value ends in a
    recognised media/asset suffix, so a panel image wired straight into a cue (not
    via asset_manifest) is still existence-checked.
    """
    out: List[Tuple[str, str]] = []
    cues = cuelist.get("cues")
    if not isinstance(cues, list):
        return out
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            continue
        cid = cue.get("id", f"#{i}")
        for key, val in cue.items():
            if key in ("text", "id", "kind", "anchor_id", "asset_id"):
                continue  # ids/text are not file paths
            if isinstance(val, str) and val.lower().endswith(_PATHLIKE_SUFFIXES):
                out.append((val, str(cid)))
    return out


def _check_path_exists(project_dir: Path, raw_path: str) -> bool:
    """Resolve a declared asset path relative to the project and report existence.

    Accepts both project-relative paths (the norm) and absolute paths.
    """
    p = Path(raw_path)
    candidate = p if p.is_absolute() else (project_dir / p)
    return candidate.exists()


def _existence_check_assets(project_dir: Path) -> List[Finding]:
    findings: List[Finding] = []

    # 1) asset_manifest.json paths.
    manifest_path = project_dir / "artifacts" / "asset_manifest.json"
    if manifest_path.exists():
        manifest = load_json(manifest_path)  # JSON error here -> blocking input error
        assets = manifest.get("assets")
        if not isinstance(assets, list):
            raise GateInputError("asset_manifest.json has no 'assets' array")
        for i, asset in enumerate(assets):
            if not isinstance(asset, dict):
                continue
            raw = asset.get("path")
            if not isinstance(raw, str) or not raw.strip():
                continue  # path bookkeeping is owned by other gates; we only check existence
            if not _check_path_exists(project_dir, raw):
                aid = asset.get("id", f"#{i}")
                findings.append(Finding(
                    "fail", "asset_file_missing",
                    f"asset_manifest declares path '{raw}' but no file exists there "
                    "(dangling reference — render would show a hole).",
                    where=str(aid),
                ))

    # 2) file paths referenced directly by cues.
    cuelist_path = project_dir / "artifacts" / "cuelist.json"
    if cuelist_path.exists():
        cuelist = load_json(cuelist_path)
        for raw, cid in _referenced_cue_paths(cuelist):
            if not _check_path_exists(project_dir, raw):
                findings.append(Finding(
                    "fail", "asset_file_missing",
                    f"cue references file path '{raw}' but no file exists there "
                    "(dangling reference — render would show a hole).",
                    where=cid,
                ))

    return findings


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    validate_file, ValidationError = _import_validate()

    findings: List[Finding] = []

    # Schema validation of every present, schema-backed artifact.
    for rel_path, schema_name in SINGLE_FILE_SCHEMAS:
        findings.extend(
            _validate_one(validate_file, ValidationError, project_dir, rel_path, schema_name)
        )
    findings.extend(_validate_storyboards(validate_file, ValidationError, project_dir))

    # Existence-check declared asset paths.
    findings.extend(_existence_check_assets(project_dir))

    return findings


if __name__ == "__main__":
    run_cli("qa_schema_validate", check)
