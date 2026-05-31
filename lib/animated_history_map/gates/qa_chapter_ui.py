"""qa_chapter_ui — no "Chapter N" badge bleeding into a normal narrative shot.

The open shot b01_b02_open shipped with a "Chapter I" sub-label (a ``.badge-sub``
inside the subject badge) sitting on screen for the whole narrative beat. A chapter
marker belongs on a dedicated chapter-intro card, not baked over the map while the
story is playing — on a maps channel it reads as leftover UI furniture.

This gate reads each per-shot HTML and finds CHAPTER-LABEL elements:
  * a leaf text element whose visible text matches ``Chapter <ordinal>``
    (roman numeral, digit, or a spelled ordinal like "One"), OR
  * an element explicitly tagged ``data-qa-role="chapter-label"``.
Text inside ``<script>`` / ``<style>`` / ``<head>`` is ignored (CSS comments and
GSAP code mention "chapter" constantly — only RENDERED text counts), and only the
most specific holder (a node with no child carrying the same text) is reported, so
one "Chapter I" badge is one finding, not five nested ones.

A chapter label is allowed ONLY on a chapter-intro card. A shot opts in by setting
``data-qa-shot-kind="chapter_card"`` on its root (or the element sets
``data-qa-chapter-ok="true"``). Otherwise the shot is narrative and a VISIBLE
chapter label is a ``fail``.

VISIBLE means the element is not hidden: not ``display:none`` /
``visibility:hidden``, not statically ``opacity:0`` (with no override), and not
declared ``data-qa-visible="false"``. (A badge that was correctly removed is absent
or hard-hidden; a bleed like this one is fully painted.)

Reads:  <project>/hyperframes/**/shots/*.html
A project with no shots passes with an informational note.
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, run_cli
from ._shot_html import Element, ParsedShot, iter_shot_html_files, parse_shot

# "Chapter" followed by a roman numeral, an integer, or a spelled ordinal/number.
_ORDINAL_WORDS = (
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth"
)
_CHAPTER_LABEL_RE = re.compile(
    r"\bchapter\b\s*[:\-–—]?\s*"
    r"(?:[ivxlcdm]+\b|\d+|(?:" + _ORDINAL_WORDS + r")\b)",
    re.IGNORECASE,
)

# Tags whose text is NOT rendered to the viewer.
_NON_RENDERED_TAGS = frozenset({"script", "style", "head", "meta", "title", "noscript"})

_HIDE_DISPLAY = ("none",)


def _is_chapter_card_shot(shot: ParsedShot) -> bool:
    """True if this shot is a dedicated chapter-intro card (chapter labels allowed)."""
    for e in shot.elements:
        if e.data.get("data-qa-shot-kind", "").strip().lower() == "chapter_card":
            return True
    return False


def _has_nonrendered_ancestor(shot: ParsedShot, el: Element) -> bool:
    idx = el.parent
    while idx >= 0:
        anc = shot.elements[idx]
        if anc.tag in _NON_RENDERED_TAGS:
            return True
        idx = anc.parent
    return False


def _is_chapter_label(el: Element) -> bool:
    if el.data.get("data-qa-role", "").strip().lower() == "chapter-label":
        return True
    if el.tag in _NON_RENDERED_TAGS:
        return False
    txt = el.text or ""
    return bool(_CHAPTER_LABEL_RE.search(txt))


def _is_most_specific(shot: ParsedShot, el: Element) -> bool:
    """True if no CHILD element of el also carries the chapter-label text (so we
    report the innermost badge, not every ancestor that concatenates it)."""
    for child in shot.children_of(el):
        if child.tag in _NON_RENDERED_TAGS:
            continue
        if _is_chapter_label(child):
            return False
    return True


def _hidden_reason(shot: ParsedShot, el: Element) -> Optional[str]:
    """Return a reason string if the element is effectively hidden, else None.
    Walks self + ancestors for display:none / visibility:hidden; checks the element
    (and the chain) for a static opacity:0 with no later override; honors
    data-qa-visible="false"."""
    cur: Optional[Element] = el
    while cur is not None:
        if cur.data.get("data-qa-visible", "").strip().lower() == "false":
            return "declared data-qa-visible=false"
        disp = (cur.decl("display") or "").strip().lower()
        if disp in _HIDE_DISPLAY:
            return "display:none"
        vis = (cur.decl("visibility") or "").strip().lower()
        if vis == "hidden":
            return "visibility:hidden"
        cur = shot.elements[cur.parent] if cur.parent >= 0 else None

    # NOTE on opacity: a static ``opacity:0`` is intentionally NOT treated as hidden.
    # The badge family starts at opacity:0 and is faded UP by GSAP to sit on screen
    # for the whole beat (exactly the bleed we caught). Only an explicit
    # ``display:none`` / ``visibility:hidden`` / ``data-qa-visible="false"`` removes
    # a chapter label from the frame for this gate's purposes.
    return None


def _check_shot(shot: ParsedShot) -> List[Finding]:
    if _is_chapter_card_shot(shot):
        return []  # chapter labels are legitimate on a chapter-intro card

    findings: List[Finding] = []
    where_base = shot.path.name
    for el in shot.elements:
        if not _is_chapter_label(el):
            continue
        if _has_nonrendered_ancestor(shot, el):
            continue  # text lives in <script>/<style>, never painted
        if not _is_most_specific(shot, el):
            continue  # report only the innermost holder
        if el.data.get("data-qa-chapter-ok", "").strip().lower() == "true":
            continue  # explicitly sanctioned chapter overlay
        reason = _hidden_reason(shot, el)
        if reason is not None:
            continue  # correctly hidden -> not on screen
        label = (el.text or "").strip()
        label = re.sub(r"\s+", " ", label)[:60]
        ident = el.id or ("." + "/".join(el.classes) if el.classes else el.tag)
        findings.append(Finding(
            "fail", "chapter_label_in_narrative",
            "chapter-label element '{0}' (text {1!r}) is visible during a narrative "
            "shot — a 'Chapter N' marker belongs on a chapter-intro card, not baked "
            "over the map. Remove it, hide it, or declare the shot "
            "data-qa-shot-kind=\"chapter_card\".".format(ident, label),
            where="{0} :: {1}".format(where_base, ident)))
    return findings


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    shots = iter_shot_html_files(project_dir)
    if not shots:
        return [Finding("warn", "no_shots",
                        "no per-shot HTML under hyperframes/**/shots/; no chapter-UI to check")]
    findings: List[Finding] = []
    for path in shots:
        findings.extend(_check_shot(parse_shot(path)))
    return findings


if __name__ == "__main__":
    run_cli("qa_chapter_ui", check)
