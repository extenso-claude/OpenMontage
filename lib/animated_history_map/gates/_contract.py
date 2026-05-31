"""Shared gate contract: Finding type + the run_cli harness.

Keeping the I/O contract in one place means every gate behaves identically
(same args, same exit-code semantics, same --json shape), which is what lets
the runner shell them uniformly and lets one test fixture-check them all.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, List, Optional


class GateInputError(Exception):
    """A required input is missing/unreadable. Treated as a BLOCKING failure —
    a gate that cannot run must never silently pass."""


@dataclass
class Finding:
    severity: str  # "fail" (blocks) | "warn" (advisory)
    code: str
    message: str
    where: str = ""


def load_json(path: Path) -> dict:
    if not path.exists():
        raise GateInputError(f"required input not found: {path}")
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise GateInputError(f"could not read {path}: {exc}") from exc


def run_cli(
    gate_name: str,
    check: Callable[[Path, argparse.Namespace], List[Finding]],
    argv: Optional[List[str]] = None,
) -> int:
    """Standard entrypoint. ``check(project_dir, args) -> list[Finding]``.

    Exits 1 if any finding has severity == "fail" (or a GateInputError is
    raised), else 0. Returns the exit code (also passed to sys.exit).
    """
    ap = argparse.ArgumentParser(prog=gate_name)
    ap.add_argument("--project", required=True, help="Path to the project workspace.")
    ap.add_argument("--pipeline", default="animated-history-map")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    project_dir = Path(args.project).resolve()
    try:
        findings = check(project_dir, args)
    except GateInputError as exc:
        findings = [Finding("fail", "missing_input", str(exc))]

    fails = [f for f in findings if f.severity == "fail"]
    passed = not fails

    if args.as_json:
        print(json.dumps(
            {"gate": gate_name, "passed": passed,
             "findings": [asdict(f) for f in findings]},
            indent=2,
        ))
    else:
        for f in findings:
            loc = f" @ {f.where}" if f.where else ""
            print(f"{gate_name}: [{f.severity.upper()}] {f.code}{loc} — {f.message}")
        verdict = "PASS" if passed else "FAIL"
        print(f"{gate_name}: {verdict} ({len(fails)} blocking, {len(findings)} total)")

    code = 1 if fails else 0
    sys.exit(code)
