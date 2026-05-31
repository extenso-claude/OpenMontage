"""Animated History Map hard gates.

Each gate is a standalone CLI: ``python -m lib.animated_history_map.gates.<gate> --project <dir>``.
Contract (enforced by _contract.run_cli):
  * exit 0  = pass
  * exit 1  = at least one BLOCKING (severity="fail") finding
  * exit 2  = usage / bad invocation
A gate that cannot run because a required input is missing FAILS (exit 1) — a
gate that can't run must never silently pass. Every gate ships with good/ and
bad/ fixtures under fixtures/<gate>/ and is covered by test_gates.py.
"""
