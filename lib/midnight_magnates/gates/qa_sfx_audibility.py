"""qa_sfx_audibility — event SFX that should be heard must actually be audible.

Catches the "SFX too quiet to hear" bug AND the sneakier "marked subliminal to
dodge the check" bug. A sound-design pass drops a sfx EVENT ACCENT (a gunshot,
an impact, a landing rumble, a map pin) that the audience is MEANT to register,
but the cue is either (a) parked below the audible floor, (b) buried under the
simultaneous bed, or (c) flagged ``subliminal: true`` so the old gate waved it
through — leaving the headline sound effect inaudible. The user's standard is
explicit: EVENT SFX ARE AUDIBLE. The lead wrongly marked the gunshot subliminal;
that is now itself a failure.

The sound stage records, per sfx cue:
  * loudness_lufs  — the cue's own short-term integrated loudness.
  * bed_lufs_at    — the simultaneous VO+music bed loudness under the cue.

Who may be subliminal: ONLY a true ambient BED — category == "ambient", mixed
very quietly, with no narrative anchor (it is texture, not an event). An
``sfx``-category cue is an event accent by definition and may NOT use
``subliminal: true`` to pass. The sanctioned way to keep an accent above the bed
is to DUCK THE MUSIC under it (NEVER duck the VO) so the accent clears the
headroom margin — not to bury or hide the accent.

Rule (fail): for each cue with category == "sfx":
  * subliminal == true                    -> FAIL (an event accent may not be
    subliminal; make it audible by ducking music under it).
  * MISSING loudness_lufs or bed_lufs_at  -> FAIL (unmeasured — a gate that
    cannot confirm audibility must never silently pass it).
  * loudness_lufs < -40.0                 -> FAIL (below the absolute audible
    floor — inaudible regardless of the bed).
  * (loudness_lufs - bed_lufs_at) < 3.0   -> FAIL (masked by the bed — a sfx
    needs >= 3 LU of headroom over the simultaneous bed to register; the fix is
    to duck the music bed, not the VO).
The offending cue and its margin over the bed are reported. Music cues are out
of scope. Ambient beds are out of scope EXCEPT they are the only cues allowed to
carry ``subliminal: true``.

Reads:  <project>/artifacts/sound_cuelist.json
Shape:  {"cues": [{"id","category"("music"|"sfx"|"ambient"),"asset":str,
                    "t_in":float,"t_out":float,"alarming"?:bool,
                    "subliminal"?:bool,"loudness_lufs"?:float,
                    "bed_lufs_at"?:float}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List

from ._contract import Finding, GateInputError, load_json, run_cli

# Absolute audible floor. A short-term loudness below this is effectively
# inaudible in a sleep-documentary mix regardless of what the bed is doing.
ABSOLUTE_FLOOR_LUFS = -40.0

# Minimum headroom a sfx needs over the simultaneous VO+music bed to register
# rather than be masked by it. Below this the cue is "there on paper" only.
MIN_HEADROOM_LU = 3.0

# This gate only polices one-shot SFX. Music/ambient beds are intentionally
# allowed to sit quietly under the foreground and are handled elsewhere.
POLICED_CATEGORY = "sfx"


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "sound_cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("sound_cuelist.json has no 'cues' array")

    findings: List[Finding] = []
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError("sound_cuelist.json cue #{0} is not an object".format(i))

        cid = cue.get("id", "#{0}".format(i))
        category = (cue.get("category") or "").strip().lower()
        if category != POLICED_CATEGORY:
            continue  # music / ambient — out of scope for audibility

        # An sfx is an EVENT ACCENT; it may NOT hide behind subliminal:true.
        # (Only an ambient bed may be subliminal — and ambient is filtered out
        # above.) An accent flagged subliminal is the inaudible-gunshot bug.
        if cue.get("subliminal") is True:
            findings.append(Finding(
                "fail", "event_accent_subliminal",
                "sfx event accent is flagged subliminal=true — event SFX must be "
                "AUDIBLE; make it clear the bed by ducking the MUSIC under it "
                "(never the VO), not by marking it subliminal",
                where=cid,
            ))
            continue  # already a fail; the loudness checks below would pile on

        loudness = cue.get("loudness_lufs")
        bed = cue.get("bed_lufs_at")

        # Unmeasured cue: we cannot confirm it is audible, so it must not pass.
        if not isinstance(loudness, (int, float)) or not isinstance(bed, (int, float)):
            missing = []
            if not isinstance(loudness, (int, float)):
                missing.append("loudness_lufs")
            if not isinstance(bed, (int, float)):
                missing.append("bed_lufs_at")
            findings.append(Finding(
                "fail", "unmeasured_sfx",
                "sfx cue is missing {0}; audibility cannot be confirmed".format(
                    " and ".join(missing)
                ),
                where=cid,
            ))
            continue

        loudness_f = float(loudness)
        bed_f = float(bed)
        margin = loudness_f - bed_f

        if loudness_f < ABSOLUTE_FLOOR_LUFS:
            findings.append(Finding(
                "fail", "sfx_inaudible",
                "sfx loudness {0:.1f} LUFS is below the audible floor "
                "{1:.1f} LUFS — inaudible".format(loudness_f, ABSOLUTE_FLOOR_LUFS),
                where=cid,
            ))
            continue  # below the floor; the masking check is moot

        if margin < MIN_HEADROOM_LU:
            findings.append(Finding(
                "fail", "sfx_masked_by_bed",
                "sfx is only {0:.1f} LU over the bed "
                "({1:.1f} vs {2:.1f} LUFS); needs >= {3:.1f} LU to register".format(
                    margin, loudness_f, bed_f, MIN_HEADROOM_LU
                ),
                where=cid,
            ))

    return findings


if __name__ == "__main__":
    run_cli("qa_sfx_audibility", check)
