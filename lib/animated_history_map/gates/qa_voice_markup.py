"""qa_voice_markup — enforce InWorld TTS-2 markup limits on the approved script.

The voice stage hands InWorld TTS-2 a `text_markup` string per segment. InWorld
rejects (or silently mangles) requests that exceed its documented limits, so we
gate the markup BEFORE it ever reaches the synthesizer. Verified InWorld facts:

  * At most 20 `<break>` tags per request, and each segment is one request.
  * A break's duration must be <= 10000ms (and obviously > 0).
  * DELIVERY steering tags (a [bracketed] instruction like "[say sadly]") only
    take effect when they are the FIRST token of the request; mid-text they are
    spoken verbatim or ignored — a bug either way. The inline NON-VERBALS
    (laugh, breathe, sigh, cough, yawn, "clear throat") are the exception: those
    may legitimately appear anywhere inline.
  * The voice must be driven in CREATIVE delivery mode on model inworld-tts-2
    with a real voice_id.

Line breaks are the *intended* natural-pause mechanism for this voice, so they
are never penalized here.

Rules (all "fail" unless noted):
  voice block:  delivery_mode == "CREATIVE"; model_id == "inworld-tts-2";
                voice_id non-empty.
  per segment text_markup:
    (a) <= 20 <break> tags (case-insensitive).
    (b) every break time <= 10000ms; a parsed time <= 0 also fails.
    (c) any delivery steering tag (a [bracketed] phrase NOT in the inline
        non-verbal set) must be the first non-whitespace token; mid-text => fail.
  WARN (advisory): a break time outside the 500-2000ms recommended band.

Reads:  <project>/artifacts/script.json
Shape:  {"voice": {"voice_id","delivery_mode","model_id"},
         "segments": [{"id","text_markup"}, ...]}
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

MAX_BREAKS = 20
MAX_BREAK_MS = 10000
REC_MIN_MS = 500
REC_MAX_MS = 2000

# Inline non-verbals InWorld accepts anywhere in the line. Normalized to compare
# case-insensitively with internal whitespace collapsed (so "clear throat" and
# "Clear  Throat" both match).
INLINE_NONVERBALS = {"laugh", "breathe", "sigh", "cough", "yawn", "clear throat"}

# Any <break ...> tag, case-insensitive. Self-closing or not, attrs in any order.
_BREAK_TAG_RE = re.compile(r"<\s*break\b[^>]*>", re.IGNORECASE)
# The time attribute inside a break tag, e.g. time="650ms" / time='1s'.
_BREAK_TIME_RE = re.compile(
    r"""\btime\s*=\s*["']?\s*([0-9]*\.?[0-9]+)\s*(ms|s)\b""",
    re.IGNORECASE,
)
# Square-bracket tags, e.g. [say sadly] or [breathe]. Non-greedy, no nesting.
_BRACKET_TAG_RE = re.compile(r"\[([^\[\]]*)\]")


def _normalize_tag(inner: str) -> str:
    """Lowercase + collapse internal whitespace so '[ Clear  Throat ]' -> 'clear throat'."""
    return " ".join(inner.split()).lower()


def _parse_break_ms(tag: str) -> Optional[float]:
    """Return the break duration in milliseconds, or None if no parseable time."""
    m = _BREAK_TIME_RE.search(tag)
    if not m:
        return None
    value = float(m.group(1))
    unit = m.group(2).lower()
    return value * 1000.0 if unit == "s" else value


def _first_nonspace_index(markup: str) -> int:
    """Index of the first non-whitespace character, or -1 if markup is blank.

    A steering tag is "leading" when it begins here — i.e. nothing but
    whitespace precedes it. We anchor on the first non-space character rather
    than the first whitespace-delimited word because a steering instruction may
    itself contain spaces (e.g. ``[say sadly]``, ``[grave, measured]``)."""
    m = re.search(r"\S", markup)
    return m.start() if m else -1


def _check_voice_block(voice: dict) -> List[Finding]:
    findings: List[Finding] = []
    where = "voice"

    delivery = voice.get("delivery_mode")
    if delivery != "CREATIVE":
        findings.append(Finding(
            "fail", "delivery_mode_not_creative",
            f"delivery_mode must be 'CREATIVE', got {delivery!r}",
            where=where,
        ))

    model = voice.get("model_id")
    if model != "inworld-tts-2":
        findings.append(Finding(
            "fail", "model_id_wrong",
            f"model_id must be 'inworld-tts-2', got {model!r}",
            where=where,
        ))

    voice_id = voice.get("voice_id")
    if not (isinstance(voice_id, str) and voice_id.strip()):
        findings.append(Finding(
            "fail", "voice_id_empty",
            f"voice_id must be a non-empty string, got {voice_id!r}",
            where=where,
        ))

    return findings


def _check_segment(seg_id: str, markup: str) -> List[Finding]:
    findings: List[Finding] = []

    # --- (a) break count -----------------------------------------------------
    break_tags = list(_BREAK_TAG_RE.finditer(markup))
    if len(break_tags) > MAX_BREAKS:
        findings.append(Finding(
            "fail", "too_many_breaks",
            f"{len(break_tags)} <break> tags exceeds InWorld's limit of {MAX_BREAKS} per request",
            where=seg_id,
        ))

    # --- (b) break durations -------------------------------------------------
    for m in break_tags:
        tag = m.group(0)
        ms = _parse_break_ms(tag)
        if ms is None:
            # No parseable time => default pause; nothing to bound.
            continue
        if ms <= 0:
            findings.append(Finding(
                "fail", "break_time_nonpositive",
                f"break time must be > 0, parsed {ms:.0f}ms from {tag!r}",
                where=seg_id,
            ))
        elif ms > MAX_BREAK_MS:
            findings.append(Finding(
                "fail", "break_time_too_long",
                f"break time {ms:.0f}ms exceeds InWorld max of {MAX_BREAK_MS}ms ({tag!r})",
                where=seg_id,
            ))
        elif ms < REC_MIN_MS or ms > REC_MAX_MS:
            findings.append(Finding(
                "warn", "break_time_out_of_band",
                f"break time {ms:.0f}ms is outside the recommended "
                f"{REC_MIN_MS}-{REC_MAX_MS}ms band ({tag!r})",
                where=seg_id,
            ))

    # --- (c) steering tags only as the first token ---------------------------
    first_nonspace = _first_nonspace_index(markup)
    for m in _BRACKET_TAG_RE.finditer(markup):
        norm = _normalize_tag(m.group(1))
        if norm in INLINE_NONVERBALS:
            continue  # inline non-verbal: allowed anywhere
        # A delivery steering tag is legal only when it leads the segment:
        # it must open at the first non-whitespace character (nothing but
        # whitespace before it). Anywhere else is a fail.
        is_leading = first_nonspace != -1 and m.start() == first_nonspace
        if not is_leading:
            findings.append(Finding(
                "fail", "steering_tag_mid_text",
                f"delivery steering tag [{m.group(1).strip()}] must be the "
                f"first token of the segment, found at char {m.start()}",
                where=seg_id,
            ))

    return findings


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "script.json")

    voice = data.get("voice")
    if not isinstance(voice, dict):
        raise GateInputError("script.json has no 'voice' object")

    segments = data.get("segments")
    if not isinstance(segments, list):
        raise GateInputError("script.json has no 'segments' array")

    findings: List[Finding] = []
    findings.extend(_check_voice_block(voice))

    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            findings.append(Finding(
                "fail", "segment_malformed",
                "segment is not an object",
                where=f"#{i}",
            ))
            continue
        seg_id = seg.get("id", f"#{i}")
        markup = seg.get("text_markup")
        if not isinstance(markup, str):
            findings.append(Finding(
                "fail", "missing_text_markup",
                f"segment has no string 'text_markup' (got {type(markup).__name__})",
                where=seg_id,
            ))
            continue
        findings.extend(_check_segment(seg_id, markup))

    return findings


if __name__ == "__main__":
    run_cli("qa_voice_markup", check)
