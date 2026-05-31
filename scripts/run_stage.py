#!/usr/bin/env python3
"""CLI shim -> runner run-stage. Refuses to advance past a stage that
requires_human_approval without an approval artifact, then runs its gates.

  python scripts/run_stage.py --pipeline animated-history-map --project <dir> --stage <stage>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.animated_history_map.runner import _main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(_main(["run-stage", *sys.argv[1:]]))
