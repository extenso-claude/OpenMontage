"""Artifact schema loading and validation utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

SCHEMA_DIR = Path(__file__).parent

ARTIFACT_NAMES = [
    "research_brief",
    "proposal_packet",
    "brief",
    "script",
    "character_design",
    "rig_plan",
    "pose_library",
    "scene_plan",
    "action_timeline",
    "asset_manifest",
    "edit_decisions",
    "render_report",
    "publish_log",
    "review",
    "cost_log",
    "decision_log",
    "source_media_review",
    "final_review",
    "character_qa_report",
    "video_analysis_brief",
    # animated-history-map pipeline (registered 2026-05-29 — previously unregistered,
    # so nothing validated against them; that was the root of the "paper" failure).
    "animated_history_map_theme",
    "animated_history_map_geography",
    "animated_history_map_canonical_names",
    "animated_history_map_storyboard",
    "animated_history_map_qa_report",
]


def load_schema(name: str) -> dict:
    """Load a JSON schema by artifact name."""
    path = SCHEMA_DIR / f"{name}.schema.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    with open(path) as f:
        return json.load(f)


def validate_artifact(name: str, data: dict[str, Any]) -> None:
    """Validate artifact data against its schema. Raises on failure."""
    schema = load_schema(name)
    jsonschema.validate(instance=data, schema=schema)


def list_schemas() -> list[str]:
    """List all available artifact schema names."""
    return [p.stem.replace(".schema", "") for p in SCHEMA_DIR.glob("*.schema.json")]


def validate_file(name: str, path: str) -> None:
    """Validate a JSON file on disk against the named schema. Raises on failure."""
    with open(path) as f:
        data = json.load(f)
    validate_artifact(name, data)


if __name__ == "__main__":
    # Exit-code validation CLI:  python -m schemas.artifacts <schema_name> <file.json>
    import sys

    if len(sys.argv) != 3:
        print("usage: python -m schemas.artifacts <schema_name> <file.json>", file=sys.stderr)
        print(f"known schemas: {', '.join(sorted(ARTIFACT_NAMES))}", file=sys.stderr)
        sys.exit(2)

    _name, _path = sys.argv[1], sys.argv[2]
    try:
        validate_file(_name, _path)
    except jsonschema.ValidationError as exc:
        loc = "/".join(str(p) for p in exc.absolute_path) or "<root>"
        print(f"INVALID: {_path} fails schema '{_name}' at {loc}: {exc.message}", file=sys.stderr)
        sys.exit(1)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
    print(f"OK: {_path} validates against '{_name}'")
    sys.exit(0)
