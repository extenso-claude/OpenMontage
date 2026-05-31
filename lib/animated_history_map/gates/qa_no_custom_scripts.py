"""qa_no_custom_scripts — the anti-monolith guarantee.

The prior failure shipped a 2,076-line projects/<id>/scripts/build_composition.py.
The one real guardrail (lib/pipeline_loader.check_extension_permitted) raises
ExtensionNotPermitted for un-whitelisted custom scripts — but was CALLED NOWHERE.
This gate wires it into the run path: if any project-level .py exists while the
manifest sets extensions.custom_scripts: false, the build fails.

Per-video logic must live as DATA (theme.json, storyboard JSON), not code.
All real logic lives in the version-controlled spine (lib/), never in projects/.
"""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path
from typing import List

# Ensure the repo root is importable when run as a module from anywhere.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lib.pipeline_loader import (  # noqa: E402
    ExtensionNotPermitted,
    check_extension_permitted,
    load_pipeline,
)

from ._contract import Finding, GateInputError, run_cli  # noqa: E402


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    try:
        manifest = load_pipeline(args.pipeline)
    except Exception as exc:  # manifest must load & validate first
        raise GateInputError(f"pipeline manifest {args.pipeline!r} failed to load/validate: {exc}")

    scripts = sorted(p for p in project_dir.rglob("*.py") if p.is_file())
    if not scripts:
        return []  # nothing hand-rolled -> clean

    # Scripts exist. Are they permitted? Mirror the intended guardrail API.
    try:
        check_extension_permitted(manifest, "custom_scripts")
    except ExtensionNotPermitted:
        rel = [str(p.relative_to(project_dir)) for p in scripts]
        return [
            Finding(
                "fail",
                "custom_script_forbidden",
                "hand-rolled project-level Python is forbidden (extensions.custom_scripts: false). "
                "Per-video logic must be DATA; real logic lives in lib/. Offending file: " + r,
                where=r,
            )
            for r in rel
        ]
    return []  # scripts present but explicitly permitted by the manifest


if __name__ == "__main__":
    run_cli("qa_no_custom_scripts", check)
