"""qa_physics — objects don't pass through each other / off the map unless intended.

Reads the diorama engine's motion-path scene-graphs (sampled actor bboxes over
time + static prop footprints + frame bounds) and checks the geometry the user
led with: "objects shouldn't move through other objects unless specified;
objects + text shouldn't overlap unless specified." We don't simulate physics —
the diorama makes geometry explicit and this gate verifies it.

Checks (all "fail"):
  1. OUT-OF-BOUNDS: any actor sample bbox leaves [0,bounds.w] x [0,bounds.h].
  2. ACTOR-PROP CLIP-THROUGH: an actor bbox intersects a non-walkable prop
     footprint on the same/adjacent layer (e.g. the buggy drives through the
     theatre). Reports the first offending timestamp.
  3. ACTOR-ACTOR CLIP-THROUGH: two actors on the same/adjacent layer whose
     bboxes intersect at a shared timestamp, neither listing the other in
     can_overlap (intended contact). First offending timestamp.
  4. FACING MISMATCH: an actor that declares facing "left"/"right" but travels
     net the other way (memory: motion_direction_qa_required).

A project with NO diorama scene-graphs passes with an informational note —
physics only applies where there are dioramas (NOT a missing-input failure).

Reads:  <project>/artifacts/diorama/*.scene_graph.json
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

FACING_DX_MIN = 20.0  # ignore sub-pixel jitter when judging net travel direction


def _rects_intersect(a: dict, b: dict) -> bool:
    return not (
        a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]
        or a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"]
    )


def _adjacent(la: int, lb: int) -> bool:
    return abs(int(la) - int(lb)) <= 1


def _check_scene(name: str, graph: dict) -> List[Finding]:
    findings: List[Finding] = []
    bounds = graph.get("bounds") or {"w": 1920, "h": 1080}
    bw, bh = float(bounds.get("w", 1920)), float(bounds.get("h", 1080))
    actors = graph.get("actors") or []
    props = graph.get("props") or []

    # 1 + 2 + 4: per-actor checks
    for actor in actors:
        aid = actor.get("id", "?")
        layer = actor.get("layer", 2)
        samples = actor.get("samples") or []

        # 4: facing vs net travel
        facing = actor.get("facing")
        net_dx = float(actor.get("net_dx", 0) or 0)
        if facing == "left" and net_dx > FACING_DX_MIN:
            findings.append(Finding("fail", "facing_mismatch",
                "actor faces 'left' but travels net +{0:.0f}px (rightward)".format(net_dx), where="{0}:{1}".format(name, aid)))
        elif facing == "right" and net_dx < -FACING_DX_MIN:
            findings.append(Finding("fail", "facing_mismatch",
                "actor faces 'right' but travels net {0:.0f}px (leftward)".format(net_dx), where="{0}:{1}".format(name, aid)))

        oob_reported = False
        prop_hit_reported = False
        for s in samples:
            bb = s.get("bbox")
            if not isinstance(bb, dict):
                continue
            # 1: out of bounds
            if not oob_reported and (bb["x"] < -0.5 or bb["y"] < -0.5
                                     or bb["x"] + bb["w"] > bw + 0.5 or bb["y"] + bb["h"] > bh + 0.5):
                findings.append(Finding("fail", "out_of_bounds",
                    "actor leaves the {0:.0f}x{1:.0f} frame at t={2}s (bbox x={3:.0f},y={4:.0f})".format(
                        bw, bh, s.get("t"), bb["x"], bb["y"]), where="{0}:{1}".format(name, aid)))
                oob_reported = True
            # 2: actor-prop clip-through
            if not prop_hit_reported:
                for prop in props:
                    if prop.get("walkable"):
                        continue
                    if not _adjacent(layer, prop.get("layer", 1)):
                        continue
                    if _rects_intersect(bb, prop["footprint"]):
                        findings.append(Finding("fail", "clip_through_prop",
                            "actor passes THROUGH prop '{0}' (layer {1}) at t={2}s — drives through a solid object".format(
                                prop.get("id"), prop.get("layer"), s.get("t")),
                            where="{0}:{1}".format(name, aid)))
                        prop_hit_reported = True
                        break

    # 3: actor-actor clip-through (same shared timestamps)
    for i in range(len(actors)):
        for j in range(i + 1, len(actors)):
            a, b = actors[i], actors[j]
            if not _adjacent(a.get("layer", 2), b.get("layer", 2)):
                continue
            if b.get("id") in (a.get("can_overlap") or []) or a.get("id") in (b.get("can_overlap") or []):
                continue
            bmap: Dict[float, dict] = {}
            for s in b.get("samples") or []:
                if isinstance(s.get("bbox"), dict):
                    bmap[round(float(s["t"]), 3)] = s["bbox"]
            hit = False
            for s in a.get("samples") or []:
                if hit:
                    break
                bb = s.get("bbox")
                ob = bmap.get(round(float(s.get("t", -1)), 3))
                if isinstance(bb, dict) and ob is not None and _rects_intersect(bb, ob):
                    findings.append(Finding("fail", "clip_through_actor",
                        "actors '{0}' and '{1}' collide at t={2}s (same/adjacent layer, no can_overlap)".format(
                            a.get("id"), b.get("id"), s.get("t")),
                        where="{0}:{1}x{2}".format(name, a.get("id"), b.get("id"))))
                    hit = True
    return findings


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    d = project_dir / "artifacts" / "diorama"
    graphs = sorted(d.glob("*.scene_graph.json")) if d.is_dir() else []
    if not graphs:
        # No dioramas in this project — physics has nothing to verify. Pass, but say so.
        return [Finding("warn", "no_dioramas", "no diorama scene-graphs found; nothing to physics-check")]

    findings: List[Finding] = []
    for g in graphs:
        graph = load_json(g)  # unreadable -> GateInputError (blocking) — a present-but-broken graph must not pass
        findings.extend(_check_scene(g.name, graph))
    return findings


if __name__ == "__main__":
    run_cli("qa_physics", check)
