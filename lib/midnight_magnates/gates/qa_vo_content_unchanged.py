"""qa_vo_content_unchanged — adding TTS markup must NOT change the VO content.

Enforces the locked HARD RULE: the human approves the plain spoken script
(script_approved.json); the voice step then formats that exact text for the TTS
engine (script.json -> segments[].text_markup) by adding ONLY presentation
markup — [steering tags], <break .../> pauses, line breaks, and CAPS emphasis.
None of that may add, drop, or alter a single spoken word.

For every segment id present in BOTH files we:
  1. strip ALL bracketed tags `[...]` and all `<break .../>` tags from the markup,
  2. normalize both the stripped markup and the approved text the same way
     (lowercase, collapse all whitespace incl. newlines, drop punctuation so
     spacing artifacts from removed tags don't create phantom diffs),
  3. assert the resulting WORD sequences are identical.
Any added/removed/changed word is a "fail" with a short diff. A segment id
present on one side but missing from the other is also a "fail" — you can't
prove the content survived a segment you can't see.

CAPS is allowed emphasis (compared case-insensitively); line breaks are not
content (collapsed to spaces).

Reads:  <project>/artifacts/script_approved.json   (plain, human-approved)
        <project>/artifacts/script.json            (TTS markup)
Shapes: script_approved.json = {"segments":[{"id","text"}]}
        script.json          = {"segments":[{"id","text_markup"}]}
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import List, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# Markup we must strip before comparing content.
#   [steering tags]  -> bracketed; may span / nest words, so strip non-greedily.
#   <break time="650ms"/> and any other <.../> tag -> SSML-ish, never spoken.
_BRACKET_RE = re.compile(r"\[[^\[\]]*\]")
_TAG_RE = re.compile(r"<[^<>]*>")
# After stripping, anything that isn't a word/number char is treated as a
# separator so that "word," / "word ," / "word" all tokenize identically.
_WORD_RE = re.compile(r"[0-9a-z]+(?:'[0-9a-z]+)*")


def _strip_markup(text: str) -> str:
    """Remove bracketed steering tags and angle-bracket (break) tags."""
    text = _BRACKET_RE.sub(" ", text)
    text = _TAG_RE.sub(" ", text)
    return text


def _words(text: str) -> List[str]:
    """Normalize to a comparable word sequence.

    Lowercase (CAPS emphasis is allowed), then extract word tokens. This
    collapses all whitespace incl. newlines and drops punctuation-spacing
    artifacts, while keeping intra-word apostrophes (don't, U.S. -> u, s)."""
    return _WORD_RE.findall(text.lower())


def _first_diff(approved: List[str], markup: List[str]) -> str:
    """Short human-readable description of the first divergence."""
    n = min(len(approved), len(markup))
    for i in range(n):
        if approved[i] != markup[i]:
            ctx = " ".join(approved[max(0, i - 2):i]) or "<start>"
            return (
                f"word #{i + 1} differs after \"{ctx}\": "
                f"approved={approved[i]!r} vs markup={markup[i]!r}"
            )
    # No positional mismatch in the shared prefix -> length differs.
    if len(markup) > len(approved):
        extra = " ".join(markup[len(approved):][:5])
        return f"markup adds {len(markup) - len(approved)} word(s): \"{extra}\"..."
    dropped = " ".join(approved[len(markup):][:5])
    return f"markup drops {len(approved) - len(markup)} word(s): \"{dropped}\"..."


def _index(segments, file_label: str) -> Tuple[dict, List[Finding]]:
    """Map segment id -> segment dict; flag malformed entries."""
    by_id: dict = {}
    findings: List[Finding] = []
    if not isinstance(segments, list):
        raise GateInputError(f"{file_label} has no 'segments' array")
    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            findings.append(Finding(
                "fail", "malformed_segment",
                f"{file_label} segment #{i} is not an object", where=file_label,
            ))
            continue
        sid = seg.get("id")
        if not sid:
            findings.append(Finding(
                "fail", "missing_segment_id",
                f"{file_label} segment #{i} has no id", where=file_label,
            ))
            continue
        by_id[sid] = seg
    return by_id, findings


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    approved_doc = load_json(project_dir / "artifacts" / "script_approved.json")
    markup_doc = load_json(project_dir / "artifacts" / "script.json")

    approved_by_id, findings = _index(approved_doc.get("segments"), "script_approved.json")
    markup_by_id, markup_findings = _index(markup_doc.get("segments"), "script.json")
    findings.extend(markup_findings)

    approved_ids = set(approved_by_id)
    markup_ids = set(markup_by_id)

    # A segment present on one side but missing on the other -> can't verify.
    for sid in sorted(approved_ids - markup_ids):
        findings.append(Finding(
            "fail", "segment_missing_in_markup",
            "approved segment has no counterpart in script.json (text_markup) — "
            "cannot verify its VO content survived",
            where=sid,
        ))
    for sid in sorted(markup_ids - approved_ids):
        findings.append(Finding(
            "fail", "segment_missing_in_approved",
            "script.json segment has no counterpart in script_approved.json — "
            "markup for unapproved content",
            where=sid,
        ))

    # Compare content for segments present in BOTH.
    for sid in sorted(approved_ids & markup_ids):
        approved_text = approved_by_id[sid].get("text")
        markup_text = markup_by_id[sid].get("text_markup")
        if not isinstance(approved_text, str):
            findings.append(Finding(
                "fail", "missing_approved_text",
                "approved segment has no string 'text'", where=sid,
            ))
            continue
        if not isinstance(markup_text, str):
            findings.append(Finding(
                "fail", "missing_text_markup",
                "markup segment has no string 'text_markup'", where=sid,
            ))
            continue

        approved_words = _words(approved_text)
        markup_words = _words(_strip_markup(markup_text))

        if approved_words != markup_words:
            findings.append(Finding(
                "fail", "vo_content_changed",
                "markup altered approved VO content — " + _first_diff(approved_words, markup_words),
                where=sid,
            ))

    return findings


if __name__ == "__main__":
    run_cli("qa_vo_content_unchanged", check)
