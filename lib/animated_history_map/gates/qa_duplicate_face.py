"""qa_duplicate_face — the same portrait must not appear at two places at once.

In the DC open shot, Lincoln's portrait was painted twice on screen at the same
time: as the ``<img>`` inside the lower-left character card AND as the
``background-image`` of the subject-badge avatar (top-right). Both were up together
from 17.4s on. Two copies of one man's face in one frame is an obvious tell that the
overlay layout double-sourced the same asset.

This gate reads each per-shot HTML, collects every PORTRAIT reference (an ``<img
src>`` or a CSS ``background-image: url(...)`` whose path looks like a portrait —
contains ``portrait`` / ``face`` / ``character`` / ``cutout`` / ``avatar``, or any
element marked ``data-qa-portrait="<id>"``), resolves each reference's on-screen
WINDOW (the nearest ancestor clip's ``data-start``/``data-duration``, else the shot
window) and its LOCATION (that owning clip). It then FAILs when the SAME portrait is
shown at TWO DISTINCT locations whose windows overlap in time.

Same asset reused in a different shot, or in a non-overlapping window within a shot
(badge swapped out before the card comes up), is fine — only a simultaneous
double-exposure of one face fails.

Reads:  <project>/hyperframes/**/shots/*.html
A project with no shots passes with an informational note.
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, run_cli
from ._shot_html import Element, ParsedShot, iter_shot_html_files, parse_shot

EPSILON = 1e-6

# A path is a portrait/face asset (not a basemap / texture) if it carries one of
# these hints. Channel portraits live under assets/portraits/.
_PORTRAIT_HINTS = ("portrait", "face", "character", "cutout", "avatar", "headshot")

_NON_RENDERED_TAGS = frozenset({"script", "style", "head", "meta", "title", "noscript"})


def _portrait_ref(el: Element) -> Optional[str]:
    """Return the normalized portrait asset path this element paints, or None.
    Honors an explicit data-qa-portrait id (wins), then <img src>, then a CSS
    background-image url — but only when the path looks like a portrait/face."""
    declared = el.data.get("data-qa-portrait")
    if declared and declared.strip():
        return declared.strip().lower()

    candidate: Optional[str] = None
    if el.tag == "img" and el.src.strip():
        candidate = el.src.strip()
    else:
        bg = el.background_url
        if bg:
            candidate = bg.strip()

    if not candidate:
        return None
    low = candidate.lower()
    if any(h in low for h in _PORTRAIT_HINTS):
        return _normalize(low)
    return None


def _normalize(path: str) -> str:
    """Normalize an asset path for identity comparison: drop query/hash, collapse
    ./ and ../ and repeated slashes, take the tail after the last 'assets/' so a
    symlinked 'assets/...' and '../../assets/...' resolve equal."""
    path = path.split("?")[0].split("#")[0]
    path = re.sub(r"/+", "/", path)
    parts = path.split("/")
    out: List[str] = []
    for p in parts:
        if p in ("", "."):
            continue
        if p == "..":
            if out:
                out.pop()
            continue
        out.append(p)
    norm = "/".join(out)
    if "assets/" in norm:
        norm = "assets/" + norm.split("assets/", 1)[1]
    return norm


def _window(shot: ParsedShot, el: Element) -> Tuple[float, float, str]:
    """(start_s, end_s, owner_id) for the nearest ancestor-or-self carrying
    data-start + data-duration. Falls back to (0, +inf, '<shot>') when nothing on
    the chain declares a window (whole-shot visibility)."""
    cur: Optional[Element] = el
    while cur is not None:
        ds = cur.data.get("data-start")
        dd = cur.data.get("data-duration")
        if ds is not None and dd is not None:
            try:
                s = float(ds)
                d = float(dd)
                owner = cur.id or (cur.tag + "#" + str(cur.index))
                return (s, s + d, owner)
            except ValueError:
                pass
        cur = shot.elements[cur.parent] if cur.parent >= 0 else None
    return (0.0, float("inf"), "<shot>")


def _overlap(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
    """Half-open interval overlap (touching end-to-end is not simultaneous)."""
    return (a[0] < b[1] - EPSILON) and (b[0] < a[1] - EPSILON)


def _check_shot(shot: ParsedShot) -> List[Finding]:
    # Collect (portrait, start, end, owner, ident) for every portrait reference.
    refs: List[Tuple[str, float, float, str, str]] = []
    for el in shot.elements:
        if el.tag in _NON_RENDERED_TAGS:
            continue
        portrait = _portrait_ref(el)
        if portrait is None:
            continue
        start, end, owner = _window(shot, el)
        ident = el.id or ("." + "/".join(el.classes) if el.classes else el.tag)
        refs.append((portrait, start, end, owner, ident))

    findings: List[Finding] = []
    reported = set()
    n = len(refs)
    for i in range(n):
        p_i, s_i, e_i, owner_i, id_i = refs[i]
        for j in range(i + 1, n):
            p_j, s_j, e_j, owner_j, id_j = refs[j]
            if p_i != p_j:
                continue                 # different faces — fine
            if owner_i == owner_j:
                continue                 # same on-screen location/clip — one place
            if not _overlap((s_i, e_i), (s_j, e_j)):
                continue                 # not on screen at the same time — fine
            key = (p_i, frozenset((owner_i, owner_j)))
            if key in reported:
                continue
            reported.add(key)
            lo = max(s_i, s_j)
            hi = min(e_i, e_j)
            findings.append(Finding(
                "fail", "duplicate_face",
                "portrait {0!r} is shown at TWO locations at once — '{1}' ({2}) and "
                "'{3}' ({4}) — overlapping {5:.1f}s..{6:.1f}s. One face must not "
                "appear twice in the same frame; source it in a single overlay or "
                "stagger the windows.".format(
                    p_i, id_i, owner_i, id_j, owner_j, lo, hi),
                where="{0} :: {1}".format(shot.path.name, p_i)))
    return findings


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    shots = iter_shot_html_files(project_dir)
    if not shots:
        return [Finding("warn", "no_shots",
                        "no per-shot HTML under hyperframes/**/shots/; no faces to de-dup")]
    findings: List[Finding] = []
    for path in shots:
        findings.extend(_check_shot(parse_shot(path)))
    return findings


if __name__ == "__main__":
    run_cli("qa_duplicate_face", check)
