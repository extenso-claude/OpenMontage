"""qa_no_reimplementation — forbid hand-rolled parallel engines (anti-bypass lint).

The prior failure was NOT "no good engine existed" — the agent WROTE ITS OWN
(a 2,076-line monolith) instead of using the sanctioned tools. Offering a better
engine does not stop that; the gate must FORBID re-implementation. This is the
check the audit named as the only thing that would have caught the monolith.

Three structural checks:
  1. Every HyperFrames composition under hyperframes/**.html MUST carry the
     compiler's `<meta name="compiler-version" ...>` stamp — i.e. it was emitted
     by lib/midnight_magnates/compiler.py, not hand-authored. Un-stamped HF
     HTML is a parallel compositor bypassing the schema / enum / gates.
  2. The PER-SHOT / PER-CHAPTER render output (the compiler emits
     hyperframes/chapter_<id>/index.html, hyperframes/chapter_<id>/shots/*.html,
     and the master hyperframes/index.html) is scanned — DISTINCTLY from the
     meta-stamp — for HAND-ROLLED Web-Mercator math and a HAND-ROLLED COMPOSITOR
     (inline canvas compositing, a hand-authored timeline scheduler, or inline
     projection math). The sanctioned compiler emits a GSAP timeline registered
     to window.__timelines and resolves every geographic pixel up-front from
     positions.json — it never paints to a 2D canvas, never schedules with
     setInterval/setTimeout, and never re-derives Mercator in the HTML. A
     per-shot HTML that does any of those is a parallel compositor wearing the
     compiler's stamp. This scan does NOT exclude the render dir.
  3. No project file anywhere may contain a hand-rolled Web-Mercator projection
     (the 20037508 max-extent constant or atanh/log-tan mercator math) —
     geographic pixels must come from lib.mapkit_subjects, never re-derived
     inline (this is the broad text scan; it still skips binary/cache dirs).

This gate legitimately PASSES when it finds no violations (it is a lint over
whatever exists, not a presence check), so it does not raise on an empty project.

Reads: <project>/hyperframes/**/*.html + a text scan of <project>
(skipping binary asset / render / cache dirs for check #3 only).
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import List

from ._contract import Finding, run_cli

# Signatures of a hand-rolled spherical-Mercator projection (the sanctioned path
# is lib.mapkit_subjects.latlon_to_pixel / latlon_to_local_pixel). Used by the
# broad project-wide text scan (check #3).
_MERCATOR_SIGNATURES = ("20037508", "math.atanh(", "log(math.tan(", "log(tan(")
_SKIP_DIRS = {"assets", "renders", "_tile_cache", ".git", "node_modules", "music_library", "__pycache__"}
_TEXT_EXTS = {".html", ".htm", ".css", ".js", ".json", ".yaml", ".yml", ".txt", ".md", ".sh", ".svg"}

# --- Per-shot render scan (check #2) -----------------------------------------
# The compiler is the SOLE, stamped emitter. Its emitted HTML registers a GSAP
# timeline to window.__timelines and consumes geographic pixels pre-resolved in
# positions.json. The patterns below appear ONLY in a hand-rolled parallel
# compositor, never in compiler output, so matching one inside a per-shot /
# per-chapter render is proof the agent re-implemented the engine in the HTML.
#
# Each entry: (compiled_regex, human_reason). Regexes are case-insensitive and
# matched against whitespace-collapsed text so "Math . log ( Math . tan ("
# can't sneak past a literal-substring check.

# Hand-rolled Web-Mercator math expressed in JS (the JS twin of
# _MERCATOR_SIGNATURES, which is Python-flavored). The Python-only forms are
# also re-checked here so an inline <script> can't hide log(math.tan(...).
_MERCATOR_PATTERNS = [
    (re.compile(r"20037508"), "the 20037508 Web-Mercator max-extent constant"),
    (re.compile(r"\bmercator\b", re.IGNORECASE), "the token 'mercator' (inline projection math)"),
    (re.compile(r"math\.log\s*\(\s*math\.tan\s*\(", re.IGNORECASE), "Math.log(Math.tan(...)) forward-Mercator math"),
    (re.compile(r"math\.atan\s*\(\s*math\.(exp|sinh)\s*\(", re.IGNORECASE), "Math.atan(Math.exp/sinh(...)) inverse-Mercator math"),
    (re.compile(r"math\.atanh\s*\(", re.IGNORECASE), "Math.atanh(...) Mercator math"),
    (re.compile(r"\blog\s*\(\s*(math\.)?tan\s*\(", re.IGNORECASE), "log(tan(...)) Mercator math"),
]

# Hand-rolled compositor: inline 2D-canvas compositing or a hand-authored
# scheduler driving the timeline. The compiler does NONE of these.
_COMPOSITOR_PATTERNS = [
    (re.compile(r"getcontext\s*\(\s*['\"]2d['\"]", re.IGNORECASE), "a hand-rolled 2D canvas context (manual compositing)"),
    (re.compile(r"\.drawimage\s*\(", re.IGNORECASE), "canvas drawImage() compositing"),
    (re.compile(r"globalcompositeoperation", re.IGNORECASE), "canvas globalCompositeOperation compositing"),
    (re.compile(r"\.putimagedata\s*\(", re.IGNORECASE), "canvas putImageData() compositing"),
    (re.compile(r"\b(set(interval|timeout))\s*\(", re.IGNORECASE), "a hand-authored setInterval/setTimeout scheduler (the compiler drives motion via the paused GSAP timeline)"),
    (re.compile(r"requestanimationframe\s*\(", re.IGNORECASE), "a hand-authored requestAnimationFrame render loop"),
]

_WS = re.compile(r"\s+")


def _per_shot_html(project_dir: Path) -> List[Path]:
    """Every compiler render-output HTML under hyperframes/: the master
    (hyperframes/index.html), each per-chapter index, and each per-shot file.
    The render dir is INCLUDED here on purpose (check #2 must not skip it)."""
    hf_dir = project_dir / "hyperframes"
    if not hf_dir.is_dir():
        return []
    return sorted(hf_dir.rglob("*.html"))


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    findings: List[Finding] = []

    per_shot = _per_shot_html(project_dir)

    # 1. Every HF composition must be compiler-stamped (provenance).
    for h in per_shot:
        try:
            txt = h.read_text(errors="replace")
        except OSError:
            continue
        if 'name="compiler-version"' not in txt:
            findings.append(Finding(
                "fail", "unstamped_hf_html",
                "HyperFrames HTML has no <meta name=\"compiler-version\"> stamp — it was "
                "hand-authored, bypassing the compiler/schema/enum. All HF compositions "
                "must be emitted by lib.midnight_magnates.compiler.",
                where=str(h.relative_to(project_dir)),
            ))

    # 2. DISTINCT from the stamp: the per-shot / per-chapter render output must be
    #    FREE of hand-rolled projection + compositor code. A stamped file that
    #    nonetheless re-implements Mercator or hand-composites is a parallel
    #    engine wearing the compiler's badge. This scan does NOT skip the render
    #    dir (that was exactly the hole — a monolith could hide under hyperframes/).
    for h in per_shot:
        try:
            raw = h.read_text(errors="replace")
        except OSError:
            continue
        collapsed = _WS.sub(" ", raw)
        for rx, reason in _MERCATOR_PATTERNS:
            if rx.search(collapsed):
                findings.append(Finding(
                    "fail", "hand_rolled_projection_in_render",
                    "per-shot render HTML contains {0} — geographic pixels must be "
                    "pre-resolved from positions.json by lib.mapkit_subjects, never "
                    "re-derived in the rendered HTML. This is a hand-rolled "
                    "projection inside the compiler's own output dir.".format(reason),
                    where=str(h.relative_to(project_dir)),
                ))
                break
        for rx, reason in _COMPOSITOR_PATTERNS:
            if rx.search(collapsed):
                findings.append(Finding(
                    "fail", "hand_rolled_compositor_in_render",
                    "per-shot render HTML contains {0} — the compiler is the sole "
                    "compositor (a paused GSAP timeline registered to "
                    "window.__timelines). Hand-rolled compositing/scheduling in the "
                    "render output is a parallel engine bypassing the compiler.".format(reason),
                    where=str(h.relative_to(project_dir)),
                ))
                break

    # 3. Broad sweep: no hand-rolled Web-Mercator ANYWHERE in the project's text
    #    files (storyboards, scripts, scratch notes…). This is the original check
    #    and keeps skipping binary/cache/render dirs — check #2 already owns the
    #    render dir, so excluding it here is fine and avoids double-reporting.
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
