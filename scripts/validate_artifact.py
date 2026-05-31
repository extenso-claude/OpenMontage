#!/usr/bin/env python3
"""CLI shim: validate a JSON artifact against its registered schema.
Exit 0 = valid, 1 = invalid, 2 = usage/error.

  python scripts/validate_artifact.py <schema_name> <file.json>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jsonschema  # noqa: E402
from schemas.artifacts import ARTIFACT_NAMES, validate_file  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python scripts/validate_artifact.py <schema_name> <file.json>", file=sys.stderr)
        print("known schemas: " + ", ".join(sorted(ARTIFACT_NAMES)), file=sys.stderr)
        raise SystemExit(2)
    name, path = sys.argv[1], sys.argv[2]
    try:
        validate_file(name, path)
    except jsonschema.ValidationError as exc:
        loc = "/".join(str(p) for p in exc.absolute_path) or "<root>"
        print(f"INVALID: {path} fails '{name}' at {loc}: {exc.message}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:  # FileNotFound / JSON error / unknown schema
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
    print(f"OK: {path} validates against '{name}'")
