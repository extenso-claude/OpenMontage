"""qa_stray_mover — no element may race across/off the frame without a reason.

Catches the documented "stray cavalry circles racing off-screen" bug
(b12_manhunt): two `cavalry` actors were given raw-pixel paths that travel a long
way and exit the frame, with NOTHING tying that motion to the narration — no
geo grounding to a place the VO names, no anchor phrase, no label, no narrative
role. The audience sees two dots shoot off the edge for no reason. The contrast
in the SAME scene is `booth_dot`: it moves just as far, but along a `geo_path`
(its motion IS the narrated manhunt route from DC to the Garrett farm), so it is
anchored and legitimate.

A "mover" is an actor whose authored path actually translates it across the
frame (start->end displacement, or any sample, exceeds a small jitter
threshold). A static/jittering actor (a flickering lantern that holds position)
is not a mover and is out of scope.

Rule (fail): a mover is STRAY — and fails — when it both
  * lacks any narrative anchor, AND
  * its motion is "big": it travels a long screen distance OR leaves the frame.
A mover is ANCHORED (and cleared) if ANY of:
  * it carries a `geo_path` (geo-grounded — its motion tracks real places the
    map/VO follow); OR
  * it declares a narrative anchor field: anchor_phrase / vo / vo_synced /
    anchor / narrative / role / beat / sync_anchor (a non-empty value); OR
  * it carries a non-empty human label (`label`).
"big motion" = max per-sample displacement from the start point exceeds
BIG_TRAVEL_FRAC of the frame's larger dimension, OR any sample's bbox/footprint
crosses outside the frame bounds (off-screen). A small anchored-or-not nudge is
never flagged; an off-frame exit with no anchor always is.

Reads:  <project>/**/<scene>.scene.json   (the authored diorama/scene specs)
Shape (only the fields this gate reads):
    scene = {"ground"|"bounds": {"width"|"w","height"|"h"},
             "actors": [{"id","kind","size"?:{"w","h"},
                         "path"?:[{"t","x","y"}, ...],
                         "geo_path"?:[...],
                         "anchor_phrase"?|"vo"?|"label"?|"narrative"? ...}]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# Below this start->sample displacement (as a fraction of the frame's larger
# side) a path is a hold/jitter, not travel. ~6% of 1920 ≈ 115px.
BIG_TRAVEL_FRAC = 0.18

# A sample translating less than this many px from the start point is jitter, not
# motion — used to decide whether an actor is a "mover" at all.
MOVER_MIN_PX = 24.0

# Fields whose non-empty presence marks the motion as narratively intended.
_ANCHOR_FIELDS = (
    "anchor_phrase", "vo", "vo_synced", "anchor", "narrative",
    "role", "beat", "sync_anchor", "anchor_id",
)

# How far OUTSIDE the frame an actor's box must go to count as "off-frame".
# A few px of overhang (a marker whose edge kisses the border) is tolerated.
OFFSCREEN_SLACK_PX = 8.0


def _num(v) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _frame_dims(scene: dict) -> Tuple[float, float]:
    """Frame (width, height). Reads ground.{width,height} or bounds.{w,h}.
    Defaults to 1920x1080 (the locked channel canvas) if unspecified."""
    for key in ("ground", "bounds"):
        node = scene.get(key)
        if isinstance(node, dict):
            w = _num(node.get("width")) or _num(node.get("w"))
            h = _num(node.get("height")) or _num(node.get("h"))
            if w and h:
                return w, h
    return 1920.0, 1080.0


def _has_anchor(actor: dict) -> bool:
    """True iff the actor declares any non-empty narrative-anchor field."""
    for f in _ANCHOR_FIELDS:
        v = actor.get(f)
        if isinstance(v, str) and v.strip():
            return True
        if isinstance(v, (list, dict)) and v:
            return True
        if isinstance(v, bool) and v:
            return True
    label = actor.get("label")
    if isinstance(label, str) and label.strip():
        return True
    return False


def _size(actor: dict) -> Tuple[float, float]:
    sz = actor.get("size")
    if isinstance(sz, dict):
        w = _num(sz.get("w")) or 0.0
        h = _num(sz.get("h")) or 0.0
        return w, h
    return 0.0, 0.0


def _path_points(actor: dict) -> List[Tuple[float, float]]:
    """Return [(x,y), ...] for a raw-pixel `path`. geo_path is geo-grounded and
    is handled as an anchor, not measured in pixels here."""
    path = actor.get("path")
    if not isinstance(path, list):
        return []
    pts: List[Tuple[float, float]] = []
    for s in path:
        if not isinstance(s, dict):
            continue
        x, y = _num(s.get("x")), _num(s.get("y"))
        if x is not None and y is not None:
            pts.append((x, y))
    return pts


def _max_travel(pts: List[Tuple[float, float]]) -> float:
    """Largest distance any sample sits from the first sample."""
    if len(pts) < 2:
        return 0.0
    x0, y0 = pts[0]
    return max(((x - x0) ** 2 + (y - y0) ** 2) ** 0.5 for x, y in pts)


def _goes_offscreen(pts: List[Tuple[float, float]], sz: Tuple[float, float],
                    fw: float, fh: float) -> bool:
    """True iff the actor's box (centered on a sample) leaves the frame by more
    than the slack. Footprint paths are treated as center points + size box."""
    half_w, half_h = sz[0] / 2.0, sz[1] / 2.0
    for x, y in pts:
        left, right = x - half_w, x + half_w
        top, bottom = y - half_h, y + half_h
        if (left < -OFFSCREEN_SLACK_PX or top < -OFFSCREEN_SLACK_PX
                or right > fw + OFFSCREEN_SLACK_PX or bottom > fh + OFFSCREEN_SLACK_PX):
            return True
    return False


def _iter_scene_files(project_dir: Path):
    """Every *.scene.json under the project (authored scene specs)."""
    for p in sorted(project_dir.rglob("*.scene.json")):
        if p.is_file():
            yield p


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    findings: List[Finding] = []
    scene_files = list(_iter_scene_files(project_dir))
    # A lint over scene specs: a project with no scene files is a clean pass
    # (other gates own the presence of scenes).
    for path in scene_files:
        scene = load_json(path)  # unreadable/invalid -> GateInputError (blocks)
        if not isinstance(scene, dict):
            raise GateInputError("{0}: scene root is not an object".format(
                path.relative_to(project_dir)))
        actors = scene.get("actors")
        if not isinstance(actors, list):
            continue  # no actors -> no movers to police
        fw, fh = _frame_dims(scene)
        big_px = BIG_TRAVEL_FRAC * max(fw, fh)
        rel = str(path.relative_to(project_dir))

        for i, actor in enumerate(actors):
            if not isinstance(actor, dict):
                raise GateInputError("{0}: actor #{1} is not an object".format(rel, i))
            aid = actor.get("id", "#{0}".format(i))

            # Anchored motion (geo_path counts as a geo anchor) is always fine.
            if isinstance(actor.get("geo_path"), list) and actor.get("geo_path"):
                continue
            if _has_anchor(actor):
                continue

            pts = _path_points(actor)
            travel = _max_travel(pts)
            if travel < MOVER_MIN_PX:
                continue  # not a mover (holds position / jitters) — out of scope

            sz = _size(actor)
            offscreen = _goes_offscreen(pts, sz, fw, fh)
            big = travel >= big_px or offscreen

            if big:
                why = []
                if offscreen:
                    why.append("its box leaves the {0:.0f}x{1:.0f} frame".format(fw, fh))
                if travel >= big_px:
                    why.append("it travels {0:.0f}px (>= {1:.0f}px)".format(travel, big_px))
                findings.append(Finding(
                    "fail", "stray_mover",
                    "actor '{0}' (kind={1}) races across/off the frame ({2}) with NO "
                    "narrative anchor — no geo_path, no anchor_phrase/vo/anchor, no "
                    "label. Decorative off-frame motion with nothing tying it to the "
                    "narration. Either ground it on a geo_path, give it a VO anchor, "
                    "or remove it.".format(
                        aid, actor.get("kind", "?"), " and ".join(why)),
                    where="{0} :: {1}".format(rel, aid),
                ))

    return findings


if __name__ == "__main__":
    run_cli("qa_stray_mover", check)
