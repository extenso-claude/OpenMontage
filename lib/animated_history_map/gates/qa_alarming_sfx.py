"""qa_alarming_sfx — no alarming SFX after the 10-minute mark (locked sound rule).

The sleep-documentary channels run long: the first ~10 minutes can carry dense,
attention-grabbing sound design, but past 10:00 the audience is settling toward
sleep. A siren, klaxon, explosion, gunshot, or any startle cue placed after that
point yanks the viewer awake — the exact failure the locked sound-design rule
forbids (memory: sound_design_rules_locked; canonical skill
skills/core/sound-design-rules.md). This gate enforces the hard half of that
rule: NOTHING alarming may begin after 600.0s.

Rule (fail): for any cue whose category is "sfx" or "ambient" and whose t_in is
strictly greater than 600.0s, FAIL if either
  * the cue is explicitly flagged alarming == true, OR
  * the cue id OR asset name matches the deny-list regex (case-insensitive):
      (siren|klaxon|air[_ -]?raid|boom|explosion|crash|gunshot|alarm|blast|detonat)
The offending cue and the matched term are reported. Cues that begin at or
before 600.0s are out of scope here (the early dense section is allowed to be
loud). Music cues are out of scope for this particular gate.

Reads:  <project>/artifacts/sound_cuelist.json
Shape:  {"cues": [{"id","category"("music"|"sfx"|"ambient"),"asset":str,
                    "t_in":float,"t_out":float,"alarming"?:bool}, ...]}
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

# The locked 10:00 boundary. A cue is only in scope if it STARTS after this.
QUIET_AFTER_S = 600.0

# Categories this gate polices. Music is intentionally excluded (handled by the
# sparse-music rule elsewhere); startle risk lives in sfx/ambient one-shots.
POLICED_CATEGORIES = {"sfx", "ambient"}

# Deny-list of startle/alarm sounds. "air[_ -]?raid" tolerates air_raid /
# air-raid / "air raid"; "detonat" catches detonate/detonation. Matched
# case-insensitively against both the cue id and the asset name.
ALARMING_RE = re.compile(
    r"(siren|klaxon|air[_ -]?raid|boom|explosion|crash|gunshot|alarm|blast|detonat)",
    re.IGNORECASE,
)


def _matched_term(*fields: Optional[str]) -> Optional[str]:
    """Return the first deny-list term found across the given text fields."""
    for field in fields:
        if not field:
            continue
        m = ALARMING_RE.search(field)
        if m:
            return m.group(1).lower()
    return None


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
        if category not in POLICED_CATEGORIES:
            continue  # music (or unknown non-policed category) — out of scope here

        t_in = cue.get("t_in")
        if not isinstance(t_in, (int, float)):
            # A policed cue with no usable start time can't be cleared as "early";
            # refuse to silently pass it.
            raise GateInputError(
                "sound cue {0!r} (category {1}) needs a numeric t_in".format(cid, category)
            )

        if float(t_in) <= QUIET_AFTER_S:
            continue  # before/at 10:00 — alarming sound is permitted here

        asset = cue.get("asset")
        if cue.get("alarming") is True:
            findings.append(Finding(
                "fail", "alarming_after_10min",
                "cue is flagged alarming==true at t_in={0:.1f}s (> {1:.0f}s); "
                "alarming SFX are banned after 10:00".format(float(t_in), QUIET_AFTER_S),
                where=cid,
            ))
            continue  # already a fail; no need to also report a regex match

        term = _matched_term(cid if isinstance(cid, str) else None, asset)
        if term is not None:
            findings.append(Finding(
                "fail", "alarming_after_10min",
                "matches deny-listed startle term {0!r} at t_in={1:.1f}s (> {2:.0f}s); "
                "alarming SFX are banned after 10:00".format(term, float(t_in), QUIET_AFTER_S),
                where=cid,
            ))

    return findings


if __name__ == "__main__":
    run_cli("qa_alarming_sfx", check)
