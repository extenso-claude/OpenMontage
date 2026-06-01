"""qa_sfx_event_sync — every IMPULSIVE SFX must be bound to the visual event it scores.

A transient one-shot — a gunshot, a card slam, a pin "tock", a stamp thud, a door
slam, a wood crack, a finger snap — only reads as real if its onset lands on the
same frame as the visual event it is reacting to. qa_audio_drift already proves an
sfx is anchored to a WORD in the VO (so it doesn't slide off the narration), but a
gunshot doesn't score a word — it scores the muzzle FLASH on the map. Anchoring a
gunshot to "raised a pistol" can still leave the bang 300ms off the flash cue,
which is the exact desync this gate forbids: the audience hears the report a beat
after they see the flash, and the whole moment falls apart (the documented
SFX-event-desync hole the swarm found in the maps sound stage).

So this gate CROSSES the two cuelists the way qa_ui_sfx_coverage does, but in the
other direction and with a frame-tight tolerance: it takes each impulsive sfx,
demands it name the VISUAL cue it is bound to (``event_cue_id``), resolves that id
in cuelist.json, and checks that the sfx's transient ONSET (``t_in`` plus any
``transient_offset_ms`` — the lead-in before the attack) sits within
``TOL_S`` of that visual cue's ``start_s``. Sustained beds (a music swell, an
ambient rumble) and non-impulsive sfx (a long whoosh) are out of scope — only
percussive one-shots demand frame-locking.

An impulsive sfx is one whose asset OR id matches the IMPULSIVE keyword set
(gunshot/impact/tock/pin/card/stamp/door/slam/crack/snap/...). Membership is by
keyword so the gate fires on real assets like "gunshot_report.wav" or
"card_slam_27s" without the cue having to self-declare "I am impulsive".

Rule (fail), for each category=="sfx" cue that is impulsive:
  * ``unpaired_event_sfx`` — it carries no ``event_cue_id`` (a transient one-shot
    with nothing to bind to WILL drift off its visual event; bind it).
  * ``event_cue_not_found`` — its ``event_cue_id`` names no cue in cuelist.json
    (a dangling binding is as bad as none — the compiler can't sync to a ghost).
  * ``sfx_event_desync`` — |(t_in + (transient_offset_ms or 0)/1000) -
    visual_cue.start_s| > TOL_S (0.08s). Reports the onset, the visual start, the
    delta, and the budget.

Non-impulsive sfx, music, and ambient are NOT policed here (their looseness is
qa_audio_drift's per-category budget; this gate is only the frame-lock on
percussive one-shots).

A gate that cannot run must never silently pass:
  * sound_cuelist.json / cuelist.json missing or unreadable  -> GateInputError
  * either file has no 'cues' array                          -> GateInputError
  * a cue is not an object                                   -> GateInputError
  * an impulsive sfx whose t_in is non-numeric               -> "fail"
    (missing_onset — cannot place its transient against the event)

Reads:  <project>/artifacts/sound_cuelist.json
        <project>/artifacts/cuelist.json
Shapes (only the fields this gate reads):
    sound_cuelist = {"cues": [
        {"id", "category" ("music"|"sfx"|"ambient"), "asset",
         "t_in", "t_out", "event_cue_id"?, "transient_offset_ms"?,
         "anchor_phrase"?}, ...]}
    cuelist       = {"cues": [{"id", "kind", "start_s", "end_s", ...}, ...]}
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import Dict, List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

# Frame-tight tolerance between an impulsive sfx's transient onset and the
# visual event's start. ~2 frames at 24fps; tight enough that a 0.3s-off gunshot
# always trips, loose enough to absorb sub-frame seek/quantization slop.
TOL_S = 0.08

# Impulsive (percussive one-shot) keyword set. An sfx whose asset OR id contains
# any of these reads as a transient that must hit its visual event on the frame.
# Word-boundary-ish matching via regex so "card" matches "card_slam" / "slam_card"
# but not "cardiac"; kept broad enough to cover the task's named families plus the
# obvious siblings (thud/bang/click/knock/whip) that behave identically.
IMPULSIVE_RE = re.compile(
    r"(gun ?shot|gunfire|gunshot|impact|tock|tick|\bpin\b|\bcard\b|stamp|"
    r"door|slam|crack|snap|thud|bang|click|knock|whip|clap|smack|pop|"
    r"hammer|gavel|punch|hit)",
    re.IGNORECASE,
)


def _is_number(v) -> bool:
    # bool is an int subclass; True/False is not a real timestamp/offset.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _sfx_text(cue: dict) -> str:
    """Lowercased asset+id — the haystack we match impulsive keywords against."""
    asset = cue.get("asset") if isinstance(cue.get("asset"), str) else ""
    cid = cue.get("id") if isinstance(cue.get("id"), str) else ""
    return (asset + " " + cid).lower()


def _is_impulsive(cue: dict) -> bool:
    return IMPULSIVE_RE.search(_sfx_text(cue)) is not None


def _load_visual_starts(project_dir: Path) -> Dict[str, Optional[float]]:
    """Map every visual cue id -> its start_s (None if non-numeric/missing).

    Presence in the map answers "does this event_cue_id name a real cue"; the
    value answers "where is its visual event in time". Duplicate ids keep the
    FIRST occurrence (cuelist ids are meant to be unique; first-wins is stable).
    """
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")
    starts: Dict[str, Optional[float]] = {}
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError(
                "cuelist.json cue #{0} is not an object".format(i))
        cid = cue.get("id")
        if not isinstance(cid, str) or not cid:
            continue  # an id-less visual cue can't be the target of a binding
        if cid in starts:
            continue
        # Overlay cuelists use t_in/t_out; the maps cuelist uses start_s/end_s.
        # Read either so this gate frame-locks against BOTH pipelines (mirrors the
        # same t_in/t_out alias already accepted by qa_min_hold and qa_cue_lifecycle).
        s = cue.get("start_s")
        if not _is_number(s):
            s = cue.get("t_in")
        starts[cid] = float(s) if _is_number(s) else None
    return starts


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    visual_starts = _load_visual_starts(project_dir)

    data = load_json(project_dir / "artifacts" / "sound_cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("sound_cuelist.json has no 'cues' array")

    findings: List[Finding] = []
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError(
                "sound_cuelist.json cue #{0} is not an object".format(i))

        category = (cue.get("category") or "").strip().lower()
        if category != "sfx":
            continue  # music/ambient beds are not frame-locked one-shots
        if not _is_impulsive(cue):
            continue  # a sustained/long sfx (whoosh, drone) isn't policed here

        cid = str(cue.get("id") or "cue[{0}]".format(i))
        event_id = cue.get("event_cue_id")

        # 1) Must be bound to a visual event.
        if not isinstance(event_id, str) or not event_id.strip():
            findings.append(Finding(
                "fail", "unpaired_event_sfx",
                "impulsive sfx (asset/id {0!r}) has no event_cue_id — a transient "
                "one-shot with nothing to bind to will drift off its visual event; "
                "name the cuelist cue it scores".format(_sfx_text(cue).strip()),
                where=cid,
            ))
            continue
        event_id = event_id.strip()

        # 2) The binding must resolve to a real visual cue.
        if event_id not in visual_starts:
            findings.append(Finding(
                "fail", "event_cue_not_found",
                "event_cue_id {0!r} names no cue in cuelist.json — a dangling "
                "binding cannot be synced (the compiler has no visual event to "
                "lock the transient to)".format(event_id),
                where=cid,
            ))
            continue

        visual_start = visual_starts[event_id]
        if visual_start is None:
            findings.append(Finding(
                "fail", "event_cue_not_found",
                "event_cue_id {0!r} resolves to a cuelist cue with no numeric "
                "start_s — there is no visual onset to bind the transient "
                "to".format(event_id),
                where=cid,
            ))
            continue

        # 3) The transient onset must land within frame-tight tolerance of it.
        t_in = cue.get("t_in")
        if not _is_number(t_in):
            findings.append(Finding(
                "fail", "missing_onset",
                "impulsive sfx needs a numeric t_in to place its transient "
                "against event {0!r} at {1:.3f}s".format(event_id, visual_start),
                where=cid,
            ))
            continue

        offset_ms = cue.get("transient_offset_ms")
        offset_s = (float(offset_ms) / 1000.0) if _is_number(offset_ms) else 0.0
        onset = float(t_in) + offset_s
        delta = abs(onset - visual_start)
        if delta > TOL_S:
            findings.append(Finding(
                "fail", "sfx_event_desync",
                "transient onset {0:.3f}s (t_in {1:.3f}s + offset {2:.3f}s) is "
                "{3:.3f}s off its visual event {4!r} at {5:.3f}s (> {6:.3f}s "
                "frame-lock budget) — the sound lands off the flash/impact".format(
                    onset, float(t_in), offset_s, delta, event_id,
                    visual_start, TOL_S),
                where=cid,
            ))

    return findings


if __name__ == "__main__":
    run_cli("qa_sfx_event_sync", check)
