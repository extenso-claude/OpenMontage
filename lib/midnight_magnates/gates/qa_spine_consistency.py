"""qa_spine_consistency — the recurring brand SPINE (through-line) callback.

Every Midnight Magnates video has ONE recurring through-line it returns to at the
end of each chapter — the per-video replacement for the old hardcoded
"all-presidents map". It may be a recurring map of pins, a recurring case-file
panel, a recurring timeline, a recurring cast-of-players board, or something else
entirely. What matters is the BRAND PROMISE: the chapter closes by returning to
the SAME recurring artifact, advanced by one beat, drawn the SAME way every time.

Rather than hardcode the presidents' roster, this gate reads each chapter
storyboard's top-level ``through_line`` declaration (Wave 1 added it to the
schema)::

    "through_line": {
      "type": "map" | "case_file" | "timeline" | "cast_of_players" | "other",
      "primitive": "<the primitive that renders the recurring spine>",
      "close_phase_kinds": ["return_to_map", "chapter_outro"],   # optional
      "consistency_keys": ["pins", "current"]                    # optional
    }

and enforces three things generically over whatever the through-line declares:

  1. DECLARATION (fail). The brand spine is now MANDATORY: every chapter must
     declare a ``through_line`` (``through_line_missing``), and across all
     chapters its ``type`` AND ``primitive`` must be IDENTICAL
     (``through_line_type_disagreement`` / ``through_line_primitive_disagreement``).
     A chapter that omits the declaration, or declares a different one, fails.

  2. PRESENCE (fail ``close_missing_spine``). Every chapter that HAS a close phase
     (``phase_kind`` in the through-line's ``close_phase_kinds``, default
     ``{return_to_map, chapter_outro}``) MUST carry a layer whose ``primitive``
     equals ``through_line.primitive``. A close phase without the spine means the
     recurring callback never lands.

  3. CONSISTENCY (fail ``spine_drift``). For each param path in
     ``through_line.consistency_keys``, the value at that path inside the spine
     primitive's ``params`` must be DEEP-EQUAL across every chapter's spine usage.
     This is generic structural equality over whatever the through-line declares —
     the pin roster (ids + positions) for a map, the row order for a timeline, the
     node set for a cast board. A chapter that mutates a consistency-key value
     breaks the "same artifact every time" promise and fails.

Distinction (kept sane per the gate contract):
  * a MISSING storyboard directory / unreadable storyboard is a GateInputError
    (the gate cannot run — a BLOCKING input failure);
  * storyboards that are PRESENT but lack / disagree on ``through_line``, or that
    drop the spine / drift a consistency key, are ordinary ``fail`` Findings.

Reads:  <project>/artifacts/storyboard/*.json
"""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

# Default close phases when a through_line omits close_phase_kinds. (Same two
# kinds the old president-specific gate hardcoded.)
DEFAULT_CLOSE_PHASES: Tuple[str, ...] = ("return_to_map", "chapter_outro")


# ---------------------------------------------------------------------------
# Storyboard loading
# ---------------------------------------------------------------------------
def _storyboards(project_dir: Path) -> List[Tuple[str, dict]]:
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        raise GateInputError(
            "required input not found: " + str(sb_dir) + " (no storyboard directory)")
    paths = sorted(sb_dir.glob("*.json"))
    if not paths:
        raise GateInputError(
            "no storyboard files in " + str(sb_dir)
            + " (expected one *.json per chapter)")
    out: List[Tuple[str, dict]] = []
    for p in paths:
        data = load_json(p)
        if not isinstance(data, dict):
            raise GateInputError(str(p) + ": storyboard root is not an object")
        out.append((p.name, data))
    return out


# ---------------------------------------------------------------------------
# through_line declaration parsing
# ---------------------------------------------------------------------------
def _close_phase_kinds(tl: dict) -> frozenset:
    """The phase_kinds that count as a chapter close for this through_line.

    Uses the declaration's close_phase_kinds if it is a non-empty list of
    strings, else the {return_to_map, chapter_outro} default.
    """
    raw = tl.get("close_phase_kinds")
    if isinstance(raw, list):
        kinds = frozenset(k for k in raw if isinstance(k, str) and k.strip())
        if kinds:
            return kinds
    return frozenset(DEFAULT_CLOSE_PHASES)


def _consistency_keys(tl: dict) -> List[str]:
    raw = tl.get("consistency_keys")
    if not isinstance(raw, list):
        return []
    return [k for k in raw if isinstance(k, str) and k.strip()]


# ---------------------------------------------------------------------------
# Generic deep value lookup + equality for consistency keys
# ---------------------------------------------------------------------------
_MISSING = object()  # sentinel: path not present in params


def _value_at(params: dict, key: str) -> Any:
    """Resolve a consistency-key path inside a spine layer's ``params``.

    A bare key (``pins``) resolves ``params["pins"]``. A dotted path
    (``rows.0.label``) walks nested dicts and list indices. A leading ``params.``
    prefix is tolerated so authors may write either ``pins`` or ``params.pins``.
    Returns ``_MISSING`` if any segment is absent / not traversable.
    """
    segments = key.split(".")
    if segments and segments[0] == "params":
        segments = segments[1:]
    cur: Any = params
    for seg in segments:
        if isinstance(cur, dict):
            if seg not in cur:
                return _MISSING
            cur = cur[seg]
        elif isinstance(cur, list):
            try:
                idx = int(seg)
            except ValueError:
                return _MISSING
            if idx < 0 or idx >= len(cur):
                return _MISSING
            cur = cur[idx]
        else:
            return _MISSING
    return cur


def _canon(value: Any) -> str:
    """Order-sensitive, structural canonical form for deep-equality + display.

    JSON object keys are sorted (so key order is irrelevant) but LIST order is
    preserved (so a reordered timeline / roster is a real difference). This makes
    the comparison generic over any shape the through-line's consistency keys
    point at.
    """
    if value is _MISSING:
        return "<missing>"
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Spine-layer collection
# ---------------------------------------------------------------------------
def _spine_layers_by_phase(sb: dict, primitive: str) -> List[Tuple[str, str, Optional[str], List[Tuple[str, dict]]]]:
    """For one storyboard, yield (phase_id, phase_kind, _, spine_layers) per phase.

    spine_layers is the list of (beat_id, layer) whose primitive == ``primitive``.
    """
    out: List[Tuple[str, str, Optional[str], List[Tuple[str, dict]]]] = []
    phases = sb.get("phases")
    if not isinstance(phases, list):
        return out
    for ph in phases:
        if not isinstance(ph, dict):
            continue
        phase_kind = ph.get("phase_kind")
        phase_id = str(ph.get("phase_id") or phase_kind or "phase")
        beats = ph.get("beats")
        beats = beats if isinstance(beats, list) else []
        spine_layers: List[Tuple[str, dict]] = []
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            bid = str(beat.get("beat_id") or "beat")
            layers = beat.get("layers")
            if not isinstance(layers, list):
                continue
            for la in layers:
                if isinstance(la, dict) and la.get("primitive") == primitive:
                    spine_layers.append((bid, la))
        out.append((phase_id, phase_kind, None, spine_layers))
    return out


# ---------------------------------------------------------------------------
# Main check
# ---------------------------------------------------------------------------
def check(project_dir: Path, args: Namespace) -> List[Finding]:
    storyboards = _storyboards(project_dir)
    findings: List[Finding] = []

    # --- pass 1: collect each chapter's through_line declaration -------------
    # decls: chapter_label -> through_line dict (only the well-formed ones).
    decls: List[Tuple[str, dict]] = []
    for name, sb in storyboards:
        cid = str(sb.get("chapter_id") or name)
        tl = sb.get("through_line")
        if not isinstance(tl, dict):
            findings.append(Finding(
                "fail", "through_line_missing",
                "chapter declares no top-level through_line — the recurring brand "
                "spine (the recurring map/case-file/timeline/cast board this video "
                "returns to at every chapter close) is mandatory",
                where=cid))
            continue
        tl_type = tl.get("type")
        tl_prim = tl.get("primitive")
        if not (isinstance(tl_type, str) and tl_type.strip()):
            findings.append(Finding(
                "fail", "through_line_no_type",
                "through_line has no string 'type' (map|case_file|timeline|"
                "cast_of_players|other)", where=cid))
            continue
        if not (isinstance(tl_prim, str) and tl_prim.strip()):
            findings.append(Finding(
                "fail", "through_line_no_primitive",
                "through_line has no string 'primitive' (the primitive that renders "
                "the recurring spine)", where=cid))
            continue
        decls.append((cid, tl))

    # If NO chapter carried a usable through_line, we have already emitted a
    # fail per chapter; nothing further to check.
    if not decls:
        return findings

    # --- pass 2: declaration agreement (type + primitive identical) ----------
    ref_label, ref_tl = decls[0]
    ref_type = str(ref_tl.get("type")).strip()
    ref_prim = str(ref_tl.get("primitive")).strip()
    for label, tl in decls[1:]:
        t = str(tl.get("type")).strip()
        p = str(tl.get("primitive")).strip()
        if t != ref_type:
            findings.append(Finding(
                "fail", "through_line_type_disagreement",
                "through_line.type={0!r} disagrees with {1!r} declared in {2} — "
                "every chapter must return to the SAME kind of brand spine".format(
                    t, ref_type, ref_label),
                where=label))
        if p != ref_prim:
            findings.append(Finding(
                "fail", "through_line_primitive_disagreement",
                "through_line.primitive={0!r} disagrees with {1!r} declared in {2} — "
                "every chapter's spine must be rendered by the SAME primitive".format(
                    p, ref_prim, ref_label),
                where=label))

    # The primitive every chapter's spine is expected to use. (We enforce
    # agreement above; here we use the reference declaration to locate spines.)
    spine_primitive = ref_prim

    # Effective consistency keys: the UNION of every chapter's declared keys, so a
    # key declared anywhere is enforced everywhere (a chapter cannot hide drift by
    # omitting the key). Order preserved by first appearance for stable messages.
    consistency_keys: List[str] = []
    seen_keys = set()
    for _label, tl in decls:
        for k in _consistency_keys(tl):
            if k not in seen_keys:
                seen_keys.add(k)
                consistency_keys.append(k)

    # --- pass 3: presence at close + collect spine params for consistency ----
    # spine_params_for_key[key] -> list of (chapter_label, canon_value)
    spine_uses: List[Tuple[str, dict]] = []  # (where, params) for every spine usage

    # Build a per-chapter lookup of its own through_line (for close_phase_kinds).
    tl_by_label: Dict[str, dict] = {label: tl for label, tl in decls}

    for name, sb in storyboards:
        cid = str(sb.get("chapter_id") or name)
        tl = tl_by_label.get(cid)
        if tl is None:
            # Chapter had no usable through_line (already failed in pass 1) — skip
            # presence/consistency to avoid double-reporting the same problem.
            continue
        close_kinds = _close_phase_kinds(tl)

        for phase_id, phase_kind, _unused, spine_layers in _spine_layers_by_phase(sb, spine_primitive):
            # PRESENCE: a close phase must carry the spine primitive.
            if phase_kind in close_kinds and not spine_layers:
                findings.append(Finding(
                    "fail", "close_missing_spine",
                    "chapter-close phase (phase_kind={0!r}) carries no {1!r} layer — "
                    "the chapter must return to the recurring brand spine "
                    "(through_line.type={2!r})".format(phase_kind, spine_primitive, ref_type),
                    where="{0} :: {1}".format(cid, phase_id)))

            # Record every spine usage (anywhere, not only at close) for the
            # cross-chapter consistency pass.
            for bid, la in spine_layers:
                params = la.get("params")
                params = params if isinstance(params, dict) else {}
                spine_uses.append(("{0} :: {1} :: {2}".format(cid, phase_id, bid), params))

    # --- pass 4: cross-chapter consistency of each declared key --------------
    if consistency_keys and len(spine_uses) >= 2:
        ref_where, ref_params = spine_uses[0]
        for key in consistency_keys:
            ref_val = _value_at(ref_params, key)
            ref_canon = _canon(ref_val)
            for where, params in spine_uses[1:]:
                this_canon = _canon(_value_at(params, key))
                if this_canon != ref_canon:
                    findings.append(Finding(
                        "fail", "spine_drift",
                        "spine consistency key {0!r} differs from {1}: {2} here vs "
                        "{3} there — the recurring spine must carry the SAME value "
                        "for this key in every chapter".format(
                            key, ref_where, this_canon, ref_canon),
                        where=where))

    return findings


if __name__ == "__main__":
    run_cli("qa_spine_consistency", check)
