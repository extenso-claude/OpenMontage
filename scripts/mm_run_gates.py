#!/usr/bin/env python3
"""CLI shim -> Midnight Magnates runner run-gates. Runs a stage's (or all)
hard_gates and writes a machine-authored artifacts/qa_report.json.

  python scripts/mm_run_gates.py --project <dir> [--stage <stage>]

(Fork of scripts/run_gates.py pointed at lib.midnight_magnates; --pipeline
defaults to midnight-magnates-doc.)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.midnight_magnates.runner import _main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(_main(["run-gates", *sys.argv[1:]]))
