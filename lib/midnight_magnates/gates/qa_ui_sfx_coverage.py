"""qa_ui_sfx_coverage — high-priority UI moments must be SCORED on their frame, not just sounded somewhere nearby.

Catches the "UI element fired with no sound" bug AND its quieter cousin, the
"sound is in the room but not on the frame" bug: a character card slams in or a
location pin drops onto the map, but no sound-effect cue lands on it, so the most
tactile beats of the piece happen in silence — or worse, the right sound exists
but its attack is a third of a second late, so the card visibly hits before you
hear the whoosh and the moment falls apart. The animation reads as unfinished —
the editor expects a card-whoosh and a pin "tock" ON the impact frame.
lint/validate check the visual cuelist and the sound cuelist separately and never
cross them, so a pin dropping into dead air (or a pin whose only sound onsets a
beat off) sails through.

This gate cross-references the two cuelists against a small UI-SFX TAXONOMY:
each high-priority UI kind declares the family of sound that must accompany it.

UI-SFX taxonomy (the high-priority pairings this gate enforces):
    character_card / character_card_pop  -> a card-reveal accent
        (asset/id contains: card | whoosh | swish | chime | shimmer | reveal | swoosh)
    pin_drop                             -> a pin/impact accent
        (asset/id contains: pin | tock | tick | drop | impact | thud | stamp)

A high-priority UI visual cue is COVERED iff there exists an sfx cue (category
"sfx") whose asset or id matches that UI kind's sound family AND whose ONSET
lands on the cue's visual EVENT frame. The onset is ``t_in`` plus any
``transient_offset_ms`` (the lead-in before the attack, same convention as
qa_sfx_event_sync); the event time is the UI cue's ``start_s`` (when it fires,
not the middle of the window it lingers in). The onset must sit within
``TOL_S`` (0.15s) of the event — tightened to ``IMPULSIVE_TOL_S`` (0.08s, a
frame-lock) when the sfx is an impulsive one-shot, because a percussive card
slam / pin tock has a hard attack the eye expects on the exact frame. A sound
that merely OVERLAPS the cue's window but whose attack is far from the event no
longer counts: the card/pin still visually hits in silence.

An uncovered high-priority UI cue is a "fail" (a silent — or mistimed — card/pin).
A UI cue whose only candidate sound is the WRONG family (e.g. a chapter-transition
swell under a pin drop) is uncovered. A UI cue whose right-family sound exists but
onsets outside tolerance is ALSO uncovered, and the finding reports the nearest
right-family onset and how far off it is so the fix is obvious (nudge t_in).

Reads:  <project>/artifacts/cuelist.json         (visual UI cues; required)
        <project>/artifacts/sound_cuelist.json    (sfx cues; required)
Shapes (only the fields this gate reads):
    cuelist       = {"cues": [{"id","kind","start_s","end_s", ...}, ...]}
    sound_cuelist = {"cues": [
        {"id","category","asset","t_in","t_out","transient_offset_ms"?, ...}, ...]}
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from .. import vocab
from ._contract import Finding, GateInputError, load_json, run_cli


def _prim(name: str) -> str:
    """Bind a UI-SFX taxonomy key to a real storyboard primitive.

    Keying the taxonomy off vocab guarantees a rename of any of these primitives
    in the storyboard schema (mirrored in vocab.PRIMITIVES) is caught HERE at
    import: the renamed kind would no longer be a member, so this assertion trips
    and names the stale string — the gate can't silently stop matching a UI kind
    that the rest of the pipeline now calls something else.
    """
    assert name in vocab.PRIMITIVES, (
        "qa_ui_sfx_coverage UI-SFX taxonomy references {0!r}, which is not a "
        "vocab.PRIMITIVES primitive (renamed/removed in the storyboard schema?)"
        .format(name)
    )
    return name


# The UI-SFX taxonomy: each high-priority UI kind -> the sound-family keywords
# that an accompanying sfx cue's asset/id may contain to count as its pairing.
# (A label/year-card/badge swap is NOT high-priority here — it is ambient UI
# furniture that does not demand a one-shot. Only cards and pins do.)
# Keys are bound through _prim() so they stay locked to vocab.PRIMITIVES.
UI_SFX_TAXONOMY = {
    _prim("character_card"):     ("card", "whoosh", "swish", "swoosh", "chime", "shimmer", "reveal"),
    _prim("character_card_pop"): ("card", "whoosh", "swish", "swoosh", "chime", "shimmer", "reveal", "pop"),
    _prim("pin_drop"):           ("pin", "tock", "tick", "drop", "impact", "thud", "stamp"),
}

# Onset-proximity budgets between a UI cue's visual event (start_s) and the
# covering sfx's transient onset (t_in + transient_offset_ms). The default is
# loose enough to absorb seek/quantization slop on a soft reveal; the impulsive
# budget is a frame-lock (mirrors qa_sfx_event_sync's TOL_S) because a percussive
# one-shot's hard attack must hit the exact impact frame.
TOL_S = 0.15
IMPULSIVE_TOL_S = 0.08

# How close (in seconds) a right-family sfx onset must be to a UI cue to count as
# that cue's intended-but-mistimed near-miss (-> ui_sfx_desync, "nudge t_in")
# rather than an unrelated sound that happens to share the family elsewhere in the
# timeline (-> ui_sfx_missing, "fires in silence"). A right-family hit landing
# inside this window of the event is plainly meant for THIS cue; one many seconds
# away is a different beat's sound, not a fixable near-miss of this one.
VICINITY_S = 2.0

# Impulsive (percussive one-shot) keyword set: an sfx whose asset/id reads as a
# hard-attack hit (tock/impact/stamp/slam/...) is held to the tighter frame-lock.
# Kept in sync with qa_sfx_event_sync's notion of "impulsive".
IMPULSIVE_RE = re.compile(
    r"(gun ?shot|gunfire|impact|tock|tick|\bpin\b|\bcard\b|stamp|"
    r"door|slam|crack|snap|thud|bang|click|knock|whip|clap|smack|pop|"
    r"hammer|gavel|punch|hit|drop)",
    re.IGNORECASE,
)


def _num(v) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _sfx_text(cue: dict) -> str:
    """Lowercased asset+id, the haystack we match taxonomy keywords against."""
    asset = cue.get("asset") if isinstance(cue.get("asset"), str) else ""
    cid = cue.get("id") if isinstance(cue.get("id"), str) else ""
    return (asset + " " + cid).lower()


def _onset(cue: dict) -> Optional[float]:
    """The sfx's transient onset = t_in + (transient_offset_ms or 0)/1000.

    None when t_in is non-numeric (no attack to place against the event).
    """
    t_in = _num(cue.get("t_in"))
    if t_in is None:
        return None
    off_ms = _num(cue.get("transient_offset_ms"))
    return t_in + (off_ms / 1000.0 if off_ms is not None else 0.0)


def _load_sfx_cues(project_dir: Path) -> List[Tuple[str, Optional[float], bool]]:
    """Each sfx cue -> (lowercased asset+id text, transient onset, is_impulsive)."""
    data = load_json(project_dir / "artifacts" / "sound_cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("sound_cuelist.json has no 'cues' array")
    out: List[Tuple[str, Optional[float], bool]] = []
    for i, c in enumerate(cues):
        if not isinstance(c, dict):
            raise GateInputError("sound_cuelist.json cue #{0} is not an object".format(i))
        if (c.get("category") or "").strip().lower() != "sfx":
            continue
        text = _sfx_text(c)
        out.append((text, _onset(c), IMPULSIVE_RE.search(text) is not None))
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
        event_t = _num(cue.get("start_s"))
        if event_t is None:
            # A high-priority UI cue with no event time can't be matched to a
            # sound and can't be cleared as covered -> refuse to silently pass it.
            findings.append(Finding(
                "fail", "ui_cue_untimed",
                "high-priority UI cue (kind={0}) has no numeric start_s; "
                "cannot confirm a paired SFX onsets on its event frame".format(kind),
                where=cid,
            ))
            continue

        # Score by ONSET PROXIMITY: the right-family sfx whose transient onset is
        # closest to the visual event, and whether that closest onset lands within
        # the (impulsive-tightened) tolerance. A right-family onset is only counted
        # as THIS cue's near-miss when it is in the cue's vicinity (within VICINITY_S
        # of the event); a same-family hit many seconds away belongs to a different
        # beat and leaves this cue genuinely silent.
        covered = False
        best_delta: Optional[float] = None   # nearest IN-VICINITY right-family delta
        best_tol: Optional[float] = None     # the tolerance that onset was judged by
        wrong_family_near = False            # a wrong-family sound IS near the event
        for text, onset, is_impulsive in sfx:
            if onset is None:
                continue
            delta = abs(onset - event_t)
            near_event = delta <= max(TOL_S, IMPULSIVE_TOL_S)
            right_family = any(tok in text for tok in families)
            if not right_family:
                if near_event:
                    wrong_family_near = True
                continue
            tol = IMPULSIVE_TOL_S if is_impulsive else TOL_S
            if delta <= tol:
                covered = True
                break
            if delta <= VICINITY_S and (best_delta is None or delta < best_delta):
                best_delta, best_tol = delta, tol

        if covered:
            continue

        if best_delta is not None:
            # The right sound exists but its attack misses the event frame.
            detail = ("the nearest {0} sound onsets {1:.3f}s from the event "
                      "(> {2:.3f}s tolerance) — the {0} visually hits before/after "
                      "the sound; nudge its t_in onto the event frame".format(
                          kind, best_delta, best_tol))
            code = "ui_sfx_desync"
        elif wrong_family_near:
            detail = ("the only sound near the event is the WRONG family — the "
                      "{0} itself has no paired SFX on its frame".format(kind))
            code = "ui_sfx_missing"
        else:
            detail = "no {0} sfx onsets near the event at all — it fires in silence".format(kind)
            code = "ui_sfx_missing"
        findings.append(Finding(
            "fail", code,
            "high-priority UI cue (kind={0}) is not SFX-covered on its event "
            "frame ({1}). Add a {0} sound effect (one of: {2}) whose transient "
            "onset (t_in [+transient_offset_ms]) lands on this cue's start_s.".format(
                kind, detail, ", ".join(families)),
            where=cid,
        ))

    return findings


if __name__ == "__main__":
    run_cli("qa_ui_sfx_coverage", check)
