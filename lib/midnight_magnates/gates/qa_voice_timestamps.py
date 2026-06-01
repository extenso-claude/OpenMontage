"""qa_voice_timestamps — the timing spine must exist before anything resolves to it.

Every downstream drift gate (qa_drift, qa_audio_drift, qa_cue_drift,
qa_sfx_event_sync, qa_scene_sync, …) converts "this fires when the narrator says
X" into a concrete second by looking the phrase up in the Whisper transcript at
``artifacts/whisper/full.json``. That transcript — the word stream with numeric
``start`` times — IS the timing spine the whole montage hangs off of. If it is
missing, unreadable, or carries an empty ``words[]`` array, those gates have
nothing to resolve against: a transcript-less build would let every anchor slide
(or let the drift gates degenerate to "no words, nothing to check, pass") and
the visuals/sound would float free of the narration.

So this gate is the load-bearing presence check ON the spine itself. A gate that
cannot run must never silently pass — and neither may the build proceed on a
spine that was never produced. The absence of the transcript BLOCKS here, before
any drift gate gets the chance to vacuously green-light an unanchored timeline.

Rule (fail):
  * ``artifacts/whisper/full.json`` is absent or unreadable (not valid JSON / not
    an object) -> ``whisper_missing`` (BLOCKING). The spine does not exist.
  * It exists and parses, but has no ``words`` key, ``words`` is not a list, or
    the list is empty -> ``whisper_no_words`` (BLOCKING). An empty transcript is
    indistinguishable from "no narration to anchor to" for every drift gate.
  * ``words`` is a non-empty list but NOT ONE entry is a well-formed word with a
    numeric ``start`` (every entry malformed / missing a numeric start) ->
    ``whisper_no_words`` (BLOCKING): there is not a single resolvable timestamp,
    so the stream cannot serve as a spine even though the array is non-empty.

Pass: a ``full.json`` whose ``words[]`` holds at least one entry with a string
``word`` and a numeric ``start`` — i.e. a real, resolvable timing spine.

This gate deliberately does NOT police per-word coverage, ordering, or anchor
resolution — those belong to the drift gates downstream. It guards exactly one
invariant: the spine they all resolve against is actually there.

Reads:  <project>/artifacts/whisper/full.json
Shape (only the fields this gate reads):
    whisper = {"words": [{"word": str, "start": float, "end": float}, ...]}
Allowed: Python stdlib only.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List

from ._contract import Finding, GateInputError, load_json, run_cli

# Where the transcript lives, relative to the project workspace. Kept as a
# constant so the message and the read can never drift apart.
_WHISPER_REL = Path("artifacts") / "whisper" / "full.json"


def _is_number(v) -> bool:
    # bool is an int subclass; a True/False is not a real timestamp.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _has_resolvable_word(words: list) -> bool:
    """True iff at least one entry is a well-formed word with a numeric start.

    A single such word is enough for the stream to function as a spine — the
    drift gates each resolve their own phrases against it; here we only need to
    prove the spine carries real timestamps at all, not that it is complete.
    """
    for w in words:
        if not isinstance(w, dict):
            continue
        if not isinstance(w.get("word"), str):
            continue
        if _is_number(w.get("start")):
            return True
    return False


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    path = project_dir / _WHISPER_REL

    # 1) The spine must exist and be readable JSON. We translate the read failure
    #    into an explicit, well-coded BLOCKING finding (rather than letting it
    #    bubble as the harness's generic missing_input) so the cause is named
    #    precisely — but it still blocks, because a missing spine must never let
    #    the build (or a downstream drift gate) proceed.
    try:
        data = load_json(path)
    except GateInputError as exc:
        return [Finding(
            "fail", "whisper_missing",
            "the timing spine {0} is absent or unreadable ({1}); every drift "
            "gate resolves anchors against this transcript, so the build cannot "
            "proceed without it".format(_WHISPER_REL.as_posix(), exc),
            where=_WHISPER_REL.as_posix(),
        )]

    if not isinstance(data, dict):
        return [Finding(
            "fail", "whisper_missing",
            "the timing spine {0} parsed but its root is not a JSON object "
            "(expected {{\"words\": [...]}})".format(_WHISPER_REL.as_posix()),
            where=_WHISPER_REL.as_posix(),
        )]

    # 2) A non-empty words[] array is the spine. Empty / wrong-typed / absent ->
    #    block: an empty transcript is indistinguishable from "no narration", and
    #    every downstream drift gate would either fail to resolve or vacuously
    #    pass on it.
    words = data.get("words")
    if not isinstance(words, list) or not words:
        return [Finding(
            "fail", "whisper_no_words",
            "the timing spine {0} has no non-empty 'words' array (got {1!r}); "
            "there are no narration word-timings for any drift gate to resolve "
            "anchors against".format(
                _WHISPER_REL.as_posix(),
                type(words).__name__ if words is not None else None,
            ),
            where=_WHISPER_REL.as_posix(),
        )]

    # 3) The array is non-empty but must carry at least one resolvable timestamp;
    #    a list of malformed entries (no string word / no numeric start) is a
    #    spine in name only and cannot anchor anything.
    if not _has_resolvable_word(words):
        return [Finding(
            "fail", "whisper_no_words",
            "the timing spine {0} has a non-empty 'words' array but not a single "
            "entry carries a numeric 'start' with a string 'word' — there is no "
            "resolvable timestamp to anchor any cue to".format(
                _WHISPER_REL.as_posix()),
            where=_WHISPER_REL.as_posix(),
        )]

    return []


if __name__ == "__main__":
    run_cli("qa_voice_timestamps", check)
