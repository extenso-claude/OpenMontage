"""Animated History Map — the invariant enforcement spine.

This package is the load-bearing replacement for the prior "paper" framework.
The design rule (see docs/animated-history-map-rebuild-plan.md): quality gates
live INSIDE the only sanctioned path to output, and the "done" signal is
produced by a deterministic runner the agent does not control.

Layout:
  runner.py       — runs a stage's hard_gates, writes a machine-authored
                    qa_report.json, and provides the render-lock.
  gates/          — individual exit-code gates (one concern each), each with
                    known-good / known-bad fixtures and a test.
  compiler.py     — (TODO) storyboard JSON -> HyperFrames HTML, the only emitter.
"""

__version__ = "0.1.0"
