#!/usr/bin/env python3
"""CLI shim -> Midnight Magnates runner run-stage. Refuses to advance past a
stage that requires_human_approval without an approval artifact, then runs its
gates.

  python scripts/mm_run_stage.py --project <dir> --stage <stage>

(Fork of scripts/run_stage.py pointed at lib.midnight_magnates; --pipeline
defaults to midnight-magnates-doc.)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.midnight_magnates.runner import _main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(_main(["run-stage", *sys.argv[1:]]))
