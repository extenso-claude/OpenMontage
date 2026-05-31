"""qa_no_reimplementation — forbid hand-rolled parallel engines (anti-bypass lint).

The prior failure was NOT "no good engine existed" — the agent WROTE ITS OWN
(a 2,076-line monolith) instead of using the sanctioned tools. Offering a better
engine does not stop that; the gate must FORBID re-implementation. This is the
check the audit named as the only thing that would have caught the monolith.

Two structural checks:
  1. Every HyperFrames composition under hyperframes/**.html MUST carry the
     compiler's `<meta name="compiler-version" ...>` stamp — i.e. it was emitted
     by lib/animated_history_map/compiler.py, not hand-authored. Un-stamped HF
     HTML is a parallel compositor bypassing the schema / enum / gates.
  2. No project file may contain a hand-rolled Web-Mercator projection (the
     20037508 max-extent constant or atanh/log-tan mercator math) — geographic
     pixels must come from lib.mapkit_subjects, never re-derived inline.

This gate legitimately PASSES when it finds no violations (it is a lint over
whatever exists, not a presence check), so it does not raise on an empty project.

Reads: <project>/hyperframes/**/*.html + a text scan of <project>
(skipping binary asset / render / cache dirs).
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List

from ._contract import Finding, run_cli

# Signatures of a hand-rolled spherical-Mercator projection (the sanctioned path
# is lib.mapkit_subjects.latlon_to_pixel / latlon_to_local_pixel).
_MERCATOR_SIGNATURES = ("20037508", "math.atanh(", "log(math.tan(", "log(tan(")
_SKIP_DIRS = {"assets", "renders", "_tile_cache", ".git", "node_modules", "music_library", "__pycache__"}
_TEXT_EXTS = {".html", ".htm", ".css", ".js", ".json", ".yaml", ".yml", ".txt", ".md", ".sh", ".svg"}


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    findings: List[Finding] = []

    # 1. Every HF composition must be compiler-stamped.
    hf_dir = project_dir / "hyperframes"
    if hf_dir.is_dir():
        for h in sorted(hf_dir.rglob("*.html")):
            try:
                txt = h.read_text(errors="replace")
            except OSError:
                continue
            if 'name="compiler-version"' not in txt:
                findings.append(Finding(
                    "fail", "unstamped_hf_html",
                    "HyperFrames HTML has no <meta name=\"compiler-version\"> stamp — it was "
                    "hand-authored, bypassing the compiler/schema/enum. All HF compositions "
                    "must be emitted by lib.animated_history_map.compiler.",
                    where=str(h.relative_to(project_dir)),
                ))

    # 2. No hand-rolled Web-Mercator anywhere in the project's text files.
    for p in project_dir.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in _TEXT_EXTS:
            continue
        rel_parts = p.relative_to(project_dir).parts
        if any(part in _SKIP_DIRS for part in rel_parts):
            continue
        try:
            txt = p.read_text(errors="replace")
        except OSError:
            continue
        for sig in _MERCATOR_SIGNATURES:
            if sig in txt:
                findings.append(Finding(
                    "fail", "hand_rolled_projection",
                    "contains a hand-rolled Web-Mercator signature ({0!r}) — geographic "
                    "pixels must be computed by lib.mapkit_subjects, never re-derived inline.".format(sig),
                    where=str(p.relative_to(project_dir)),
                ))
                break

    return findings


if __name__ == "__main__":
    run_cli("qa_no_reimplementation", check)
