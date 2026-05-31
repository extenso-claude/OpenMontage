"""qa_pin_label_pulse_align — a pin, its pulse halo, and its leader line must agree.

The lead found map pins where the parts that are SUPPOSED to mark one spot did not
line up: Ford's closing pin had its pulse halo drawn around the teardrop TIP while
the visible head disc sat ~28px higher, and the Garrett pin's ring was offset from
its head. On screen that reads as a glowing ring floating off the marker, or a
leader line that points to empty parchment beside the dot. The geometry is fully
declared in the shot HTML (inline px + the id/class rules), so this is checkable
without rendering.

What it checks, per shot HTML under ``hyperframes/**/shots/*.html``:

  A pin GROUP is a marker element (``.pin``, ``#*_pin``, ``data-qa-role="pin"``,
  or a translate(-50%,-50%) round dot like ``#dot``) together with:
    * its MARKER center — the head/body disc center (``.pin-body`` / ``.head`` /
      ``.core`` / ``.pin-head`` child if present, else the pin container center);
    * every PULSE it owns — a ring/ripple/halo (``.pin-ring`` / ``.ripple`` /
      ``.halo`` / ``.pulse`` / ``data-qa-role="pulse"``), whether nested inside the
      pin OR a sibling halo linked by id-prefix (``#fords_halo`` -> ``#fords_pin``)
      or an explicit ``data-qa-pin``;
    * any LEADER line aimed at it — the outer endpoint of a ``.leader <line>`` in a
      label, associated to the pin by ``data-qa-pin``, by id-suffix
      (``#lbl_surratt`` -> ``#pin_surratt``), or by landing within tolerance.

  FAIL (``misaligned_pulse``)  if a pulse center is > TOL_PX from the marker center.
  FAIL (``misaligned_leader``) if a leader endpoint is > LEADER_TOL_PX from it.

Tolerance is a few pixels (sub-pixel rounding in the authored px is fine; a real
offset is tens of px, as in the bugs above).

Reads:   <project>/hyperframes/**/shots/*.html   (parsed by _shot_html)
A project with no shots passes with an informational note (nothing to align).
"""

from __future__ import annotations

import math
from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, run_cli
from ._shot_html import Element, ParsedShot, iter_shot_html_files, parse_shot

# A pulse must sit on the marker within this many px (authored px round to <1px;
# the real bugs were 16-28px off).
TOL_PX = 3.0
# Leader lines are hand-aimed; allow a slightly looser landing on the pin.
LEADER_TOL_PX = 4.0

# Class / id hints.
_MARKER_HEAD_CLASSES = ("pin-body", "head", "core", "pin-head")
_PULSE_CLASSES = ("pin-ring", "ripple", "halo", "pulse")
_PIN_CLASSES = ("pin",)
_PIN_ID_SUFFIX = "_pin"
_HALO_ID_SUFFIX = "_halo"


def _dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _is_pin_container(el: Element) -> bool:
    if el.data.get("data-qa-role") == "pin":
        return True
    if any(c in el.classes for c in _PIN_CLASSES):
        return True
    # A round translate-centred travelling dot (e.g. #dot) is a marker too, but
    # only treat an element as a pin container when it actually owns a pulse child;
    # that is decided by the caller. Here we accept the explicit signals only.
    return False


def _marker_center(shot: ParsedShot, pin: Element) -> Optional[Tuple[float, float]]:
    """The visible marker center: the head/body disc if the pin has one, else the
    pin container's own center. A teardrop head is the box CENTER (not the tip)."""
    for child in shot.descendants_of(pin):
        if any(c in child.classes for c in _MARKER_HEAD_CLASSES) or child.data.get("data-qa-role") == "marker":
            c = shot.abs_center(child)
            if c is not None:
                return c
            # head often fills the pin via inset:0 (no own size) -> use pin center.
            break
    return shot.abs_center(pin)


def _pulses_for(shot: ParsedShot, pin: Element, all_pulses: List[Element]) -> List[Element]:
    """Every pulse that belongs to this pin: nested pulses + sibling halos linked
    by data-qa-pin or by id-prefix (#fords_halo -> #fords_pin)."""
    owned: List[Element] = []
    nested_ids = {id(d) for d in shot.descendants_of(pin)}
    pin_stub = pin.id[:-len(_PIN_ID_SUFFIX)] if pin.id.endswith(_PIN_ID_SUFFIX) else None
    for p in all_pulses:
        if id(p) in nested_ids:
            owned.append(p)
            continue
        linked = p.data.get("data-qa-pin")
        if linked and linked == pin.id:
            owned.append(p)
            continue
        if pin_stub and p.id.endswith(_HALO_ID_SUFFIX) and p.id[:-len(_HALO_ID_SUFFIX)] == pin_stub:
            owned.append(p)
    return owned


def _leader_endpoint(shot: ParsedShot, label: Element, line: Element) -> Optional[Tuple[float, float]]:
    """Screen-space coordinate of the leader line's OUTER endpoint (the one aimed at
    the pin). The <line> sits at its label box origin (the .leader SVG fills the
    label via inset:0); we add the more 'outlying' endpoint to that origin. The
    label is auto-sized, so we use abs_origin (no width/height required)."""
    origin = shot.abs_origin(label)
    if origin is None:
        return None
    ox, oy = origin
    try:
        x1 = float(line.attrs.get("x1", "nan")); y1 = float(line.attrs.get("y1", "nan"))
        x2 = float(line.attrs.get("x2", "nan")); y2 = float(line.attrs.get("y2", "nan"))
    except ValueError:
        return None
    if any(math.isnan(v) for v in (x1, y1, x2, y2)):
        return None
    # The endpoint that reaches OUT of the label toward the pin is the one poking
    # furthest past the label's own box. Use the label width when declared; else
    # fall back to whichever endpoint is most extreme from the SVG x-origin (0).
    w = label._len("width", None)
    if w is None:
        w = 0.0
    def outwardness(px: float) -> float:
        return max(-px, px - w)  # how far it pokes left of 0 or right of width
    p1 = (ox + x1, oy + y1)
    p2 = (ox + x2, oy + y2)
    return p1 if outwardness(x1) >= outwardness(x2) else p2


def _label_pin(shot: ParsedShot, label: Element, pins: List[Element]) -> Optional[Element]:
    """Associate a label to its pin: explicit data-qa-pin, then id-suffix match
    (#lbl_surratt -> #pin_surratt / #*surratt*pin), else None (caller may fall back
    to nearest-pin)."""
    linked = label.data.get("data-qa-pin")
    if linked:
        return shot.by_id(linked)
    lid = label.id
    # strip a leading 'lbl_' / 'lab_' / 'label_' to get the stub
    for pre in ("lbl_", "lab_", "label_"):
        if lid.startswith(pre):
            stub = lid[len(pre):]
            for p in pins:
                if stub and stub in p.id:
                    return p
            break
    return None


def _check_shot(shot: ParsedShot) -> List[Finding]:
    findings: List[Finding] = []
    where_base = shot.path.name

    pins = [e for e in shot.elements if _is_pin_container(e)]
    pin_idx = {p.index for p in pins}          # identity set (Element is value-eq)
    all_pulses = [
        e for e in shot.elements
        if any(c in e.classes for c in _PULSE_CLASSES)
        or e.data.get("data-qa-role") == "pulse"
        or e.id.endswith(_HALO_ID_SUFFIX)      # a sibling halo div (#fords_halo) with no pulse class
    ]

    # Also admit translate-centred round dots (#dot-like) that own a pulse, so the
    # travelling-lantern halo is checked even though the dot has no .pin class.
    for e in shot.elements:
        if e.index in pin_idx:
            continue
        owns = _pulses_for(shot, e, all_pulses)
        if owns and shot.abs_center(e) is not None and "translate(-50%,-50%)" in e.transform.replace(" ", ""):
            pins.append(e)
            pin_idx.add(e.index)

    for pin in pins:
        marker = _marker_center(shot, pin)
        if marker is None:
            continue  # geometry not resolvable -> nothing to align against
        pid = pin.id or "<pin>"
        for pulse in _pulses_for(shot, pin, all_pulses):
            pc = shot.abs_center(pulse)
            if pc is None:
                continue
            d = _dist(marker, pc)
            if d > TOL_PX:
                pulse_id = pulse.id or ("." + "/".join(pulse.classes) if pulse.classes else "pulse")
                findings.append(Finding(
                    "fail", "misaligned_pulse",
                    "pulse '{0}' center ({1:.0f},{2:.0f}) is {3:.0f}px off the pin "
                    "marker ({4:.0f},{5:.0f}) — the halo/ring does not sit on the "
                    "marker (tol {6:.0f}px).".format(
                        pulse_id, pc[0], pc[1], d, marker[0], marker[1], TOL_PX),
                    where="{0} :: {1}".format(where_base, pid)))

    # Leader lines -> their pin.
    labels = [e for e in shot.elements if "lbl" in e.classes or "map-label" in e.classes
              or e.data.get("data-qa-role") == "label"]
    for label in labels:
        lines = [d for d in shot.descendants_of(label) if d.tag == "line"]
        if not lines:
            continue
        target = _label_pin(shot, label, pins)
        target_center = _marker_center(shot, target) if target is not None else None
        for line in lines:
            ep = _leader_endpoint(shot, label, line)
            if ep is None:
                continue
            if target_center is None:
                # no declared/inferable pin link — fall back to the nearest pin and
                # only flag if it lands near NONE of them (a leader to nowhere).
                nearest = None
                for pin in pins:
                    mc = _marker_center(shot, pin)
                    if mc is None:
                        continue
                    dd = _dist(ep, mc)
                    if nearest is None or dd < nearest[0]:
                        nearest = (dd, pin)
                if nearest is None:
                    continue
                if nearest[0] > LEADER_TOL_PX:
                    findings.append(Finding(
                        "fail", "misaligned_leader",
                        "leader line endpoint ({0:.0f},{1:.0f}) from label '{2}' lands "
                        "{3:.0f}px from the nearest pin '{4}' — it points beside the "
                        "marker, not at it (tol {5:.0f}px).".format(
                            ep[0], ep[1], label.id or "label", nearest[0],
                            nearest[1].id or "<pin>", LEADER_TOL_PX),
                        where="{0} :: {1}".format(where_base, label.id or "label")))
            else:
                d = _dist(ep, target_center)
                if d > LEADER_TOL_PX:
                    findings.append(Finding(
                        "fail", "misaligned_leader",
                        "leader line endpoint ({0:.0f},{1:.0f}) from label '{2}' is "
                        "{3:.0f}px off its pin '{4}' marker ({5:.0f},{6:.0f}) — the "
                        "leader misses the pin (tol {7:.0f}px).".format(
                            ep[0], ep[1], label.id or "label", d,
                            target.id or "<pin>", target_center[0], target_center[1],
                            LEADER_TOL_PX),
                        where="{0} :: {1}".format(where_base, label.id or "label")))
    return findings


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    shots = iter_shot_html_files(project_dir)
    if not shots:
        return [Finding("warn", "no_shots",
                        "no per-shot HTML under hyperframes/**/shots/; nothing to align-check")]
    findings: List[Finding] = []
    for path in shots:
        shot = parse_shot(path)
        findings.extend(_check_shot(shot))
    return findings


if __name__ == "__main__":
    run_cli("qa_pin_label_pulse_align", check)
