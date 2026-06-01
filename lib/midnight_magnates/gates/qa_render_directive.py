"""qa_render_directive — every HERO shot must carry a full Render Directive.

LOCKED RULE (user, 2026-05-29): the rich per-shot brief (the "Render Directive")
is MANDATORY at storyboard time for hero shots and is the thing handed to the
animator agents later. A medium-scale scene (2D OR 3D) — or any beat flagged
hero — that lacks a complete directive cannot proceed. This is how we guarantee
lively, physics-verified motion (authored per-shot from the directive) instead of
flat fades, while still preserving the explicit "Improvise" latitude the directive
declares. Motion is NOT a pre-built library; it is determined per shot by the
directive, and `qa_physics` verifies the result.

A beat REQUIRES a directive when:  shot_scale == "medium" (any animation_tier)
OR  hero == true.
For such a beat:
  * `animation_tier` must be resolved to "2d" or "3d" — the per-shot render-mode
    choice (MM RULE 2: 2D and 3D are co-equal, picked for best fit per shot),
  * `render_directive` must be present (a path, relative to the project root),
  * that file must exist, and
  * it must contain the load-bearing sections — BINDING, PHYSICS, and the
    LOCKED / IMPROVISE creative-latitude split — plus the richness sections
    (camera/style, environment, subject animation, pacing).

Reads:  <project>/artifacts/storyboard/*.json  (+ each referenced directive file)
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import List

from ._contract import Finding, GateInputError, load_json, run_cli

# The scene tier — 2D or 3D; the render-mode-agnostic analog of the old
# "medium_diorama". Any medium-scale scene is a hero shot that needs a directive.
HERO_SCALES = {"medium"}

# Required section -> a case-insensitive pattern that must appear in the directive.
REQUIRED_SECTIONS = {
    "BINDING": r"binding",
    "PHYSICS": r"physics",
    "LOCKED": r"locked",
    "IMPROVISE/ENHANCE": r"improvise|enhance",
    "CAMERA/STYLE": r"camera|style",
    "ENVIRONMENT": r"environment|canvas",
    "SUBJECT ANIMATION": r"subject|animation",
    "PACING": r"pacing|timeline",
}


def _is_hero(beat: dict) -> bool:
    return beat.get("hero") is True or beat.get("shot_scale") in HERO_SCALES


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        raise GateInputError("required input not found: " + str(sb_dir) + " (no storyboard directory)")
    paths = sorted(sb_dir.glob("*.json"))
    if not paths:
        raise GateInputError("no storyboard files in " + str(sb_dir) + " (expected one *.json per chapter)")

    findings: List[Finding] = []
    for p in paths:
        sb = load_json(p)
        cid = sb.get("chapter_id", p.name)
        phases = sb.get("phases")
        if not isinstance(phases, list):
            continue
        for ph in phases:
            beats = ph.get("beats") if isinstance(ph, dict) else None
            if not isinstance(beats, list):
                continue
            for beat in beats:
                if not isinstance(beat, dict) or not _is_hero(beat):
                    continue
                bid = beat.get("beat_id", "?")
                where = "{0} :: {1}".format(cid, bid)

                # RULE 2 (2D/3D co-equal): a hero/medium beat MUST have chosen a
                # render mode. An unresolved animation_tier means the per-shot
                # 2D-vs-3D decision was skipped — a decision the storyboard/animator
                # makes for best fit, never the renderer by default.
                atier = beat.get("animation_tier")
                if atier not in ("2d", "3d"):
                    findings.append(Finding(
                        "fail", "animation_tier_unresolved",
                        "hero/medium beat (shot_scale={0!r} / hero={1}) has animation_tier={2!r} — "
                        "every hero shot must choose 2d or 3d (best fit per shot)".format(
                            beat.get("shot_scale"), beat.get("hero"), atier),
                        where=where))

                rd = beat.get("render_directive")
                if not (isinstance(rd, str) and rd.strip()):
                    findings.append(Finding(
                        "fail", "missing_render_directive",
                        "hero shot (shot_scale={0!r} / hero={1}) has NO render_directive — a "
                        "full Render Directive is mandatory for hero shots".format(
                            beat.get("shot_scale"), beat.get("hero")),
                        where=where))
                    continue
                rd_path = Path(rd) if Path(rd).is_absolute() else (project_dir / rd)
                if not rd_path.is_file():
                    findings.append(Finding(
                        "fail", "render_directive_not_found",
                        "render_directive points to {0!r} but no such file exists".format(rd),
                        where=where))
                    continue
                text = rd_path.read_text(errors="ignore").lower()
                missing = [name for name, rx in REQUIRED_SECTIONS.items() if not re.search(rx, text)]
                if missing:
                    findings.append(Finding(
                        "fail", "render_directive_incomplete",
                        "directive {0!r} is missing required section(s): {1}".format(rd, ", ".join(missing)),
                        where=where))
    return findings


if __name__ == "__main__":
    run_cli("qa_render_directive", check)
