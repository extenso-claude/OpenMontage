"""qa_ui_sfx_coverage — high-priority UI moments must be SCORED, not silent.

Catches the "UI element fired with no sound" bug: a character card slams in or a
location pin drops onto the map, but no sound-effect cue is paired with it, so
the most tactile beats of the piece happen in silence. The animation reads as
unfinished — the editor expects a card-whoosh and a pin "tock". lint/validate
check the visual cuelist and the sound cuelist separately and never cross them,
so a pin dropping into dead air sails through.

This gate cross-references the two cuelists against a small UI-SFX TAXONOMY:
each high-priority UI kind declares the family of sound that must accompany it.

UI-SFX taxonomy (the high-priority pairings this gate enforces):
    character_card / character_card_pop  -> a card-reveal accent
        (asset/id contains: card | whoosh | swish | chime | shimmer | reveal | swoosh)
    pin_drop                             -> a pin/impact accent
        (asset/id contains: pin | tock | tick | drop | impact | thud | stamp)

A high-priority UI visual cue is COVERED iff there exists an sfx cue (category
"sfx") whose asset or id matches that UI kind's sound family AND whose time
window overlaps the UI cue's [start_s, end_s]. An uncovered high-priority UI cue
is a "fail" (a silent card/pin). A UI cue whose only overlapping sound is the
WRONG family (e.g. a chapter-transition swell under a pin drop) is still
uncovered — the pin itself has no sound.

Reads:  <project>/artifacts/cuelist.json         (visual UI cues; required)
        <project>/artifacts/sound_cuelist.json    (sfx cues; required)
Shapes (only the fields this gate reads):
    cuelist       = {"cues": [{"id","kind","start_s","end_s", ...}, ...]}
    sound_cuelist = {"cues": [{"id","category","asset","t_in","t_out", ...}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# The UI-SFX taxonomy: each high-priority UI kind -> the sound-family keywords
# that an accompanying sfx cue's asset/id may contain to count as its pairing.
# (A label/year-card/badge swap is NOT high-priority here — it is ambient UI
# furniture that does not demand a one-shot. Only cards and pins do.)
UI_SFX_TAXONOMY = {
    "character_card":      ("card", "whoosh", "swish", "swoosh", "chime", "shimmer", "reveal"),
    "character_card_pop":  ("card", "whoosh", "swish", "swoosh", "chime", "shimmer", "reveal", "pop"),
    "pin_drop":            ("pin", "tock", "tick", "drop", "impact", "thud", "stamp"),
}

EPSILON = 1e-6


def _num(v) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _interval(cue: dict, k0: str, k1: str) -> Optional[Tuple[float, float]]:
    a, b = _num(cue.get(k0)), _num(cue.get(k1))
    if a is None or b is None:
        return None
    if b < a:
        a, b = b, a
    return (a, b)


def _overlaps(iv_a: Tuple[float, float], iv_b: Tuple[float, float]) -> bool:
    """True iff the two time intervals share any open span."""
    a0, a1 = iv_a
    b0, b1 = iv_b
    return (a0 < b1 - EPSILON) and (b0 < a1 - EPSILON)


def _sfx_text(cue: dict) -> str:
    """Lowercased asset+id, the haystack we match taxonomy keywords against."""
    asset = cue.get("asset") if isinstance(cue.get("asset"), str) else ""
    cid = cue.get("id") if isinstance(cue.get("id"), str) else ""
    return (asset + " " + cid).lower()


def _load_sfx_cues(project_dir: Path) -> List[Tuple[dict, str, Optional[Tuple[float, float]]]]:
    data = load_json(project_dir / "artifacts" / "sound_cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("sound_cuelist.json has no 'cues' array")
    out = []
    for i, c in enumerate(cues):
        if not isinstance(c, dict):
            raise GateInputError("sound_cuelist.json cue #{0} is not an object".format(i))
        if (c.get("category") or "").strip().lower() != "sfx":
            continue
        out.append((c, _sfx_text(c), _interval(c, "t_in", "t_out")))
    return out


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    visual = load_json(project_dir / "artifacts" / "cuelist.json")
    vcues = visual.get("cues")
    if not isinstance(vcues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    sfx = _load_sfx_cues(project_dir)

    findings: List[Finding] = []
    for i, cue in enumerate(vcues):
        if not isinstance(cue, dict):
            raise GateInputError("cuelist.json cue #{0} is not an object".format(i))
        kind = (cue.get("kind") or "").strip().lower()
        families = UI_SFX_TAXONOMY.get(kind)
        if not families:
            continue  # not a high-priority UI element — no SFX obligation

        cid = cue.get("id", "#{0}".format(i))
        ui_iv = _interval(cue, "start_s", "end_s")
        if ui_iv is None:
            # A high-priority UI cue with no timing can't be matched to a sound
            # and can't be cleared as covered -> refuse to silently pass it.
            findings.append(Finding(
                "fail", "ui_cue_untimed",
                "high-priority UI cue (kind={0}) has no numeric start_s/end_s; "
                "cannot confirm a paired SFX".format(kind),
                where=cid,
            ))
            continue

        covered = False
        wrong_family_overlap = False
        for scue, text, s_iv in sfx:
            if s_iv is None or not _overlaps(ui_iv, s_iv):
                continue
            if any(tok in text for tok in families):
                covered = True
                break
            wrong_family_overlap = True

        if covered:
            continue

        if wrong_family_overlap:
            detail = ("the only overlapping sound is the WRONG family — the "
                      "{0} itself has no paired SFX".format(kind))
        else:
            detail = "no overlapping sfx cue at all — it fires in silence"
        findings.append(Finding(
            "fail", "ui_sfx_missing",
            "high-priority UI cue (kind={0}) has no paired SFX per the UI-SFX "
            "taxonomy ({1}). Add a {0} sound effect (one of: {2}) whose window "
            "overlaps this cue.".format(
                kind, detail, ", ".join(families)),
            where=cid,
        ))

    return findings


if __name__ == "__main__":
    run_cli("qa_ui_sfx_coverage", check)
