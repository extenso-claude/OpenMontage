#!/usr/bin/env python3
"""CLI shim -> runner run-gates. Runs a stage's (or all) hard_gates and writes
a machine-authored artifacts/qa_report.json.

  python scripts/run_gates.py --pipeline animated-history-map --project <dir> [--stage <stage>]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.animated_history_map.runner import _main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(_main(["run-gates", *sys.argv[1:]]))
