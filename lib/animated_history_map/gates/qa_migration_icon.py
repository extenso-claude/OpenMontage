"""qa_migration_icon — a route the VO calls a *journey* must show a traveler (A11).

The documented failure: the narrator says "Booth fled south on horseback through
the Maryland countryside" and the map draws a bare dashed line crawling from DC to
the barn — no rider, no carriage, no ship. A migration_arrow that the narration
frames as travel reads as an abstract diagram instead of a person making a journey.

HARD RULE: for every beat that contains a `migration_arrow` layer, if the beat's
narration (or the arrow's own params) NAMES A TRAVEL METHOD
(horseback/ride/rode/carriage/coach/wagon/ship/sail/boat/flee/fled/escape/escaped
/march/marched/gallop/...), that arrow MUST declare a transportation / character
icon that travels the polyline — `params.character_icon`, an object identifying
the traveler (an asset_id or an icon/label, e.g. Booth on horseback). A migration
arrow with a travel-method VO and no character_icon is a FAIL, UNLESS the layer
documents why with a non-empty `params.no_icon_rationale` (e.g. "abstract
troop-movement summary, no single traveler"). The rationale is the deliberate
escape hatch so a legitimately icon-less arrow can pass on the record.

The beat's spoken span is resolved exactly as the compiler resolves it
(start_anchor / end_anchor -> Whisper word time, else fallback_absolute_s); the VO
text is the Whisper words inside [start, end]. If the transcript is absent, we fall
back to scanning the arrow's params text (path/label/caption/note) for a travel
method so the gate still bites on an obviously-travel route even pre-transcript.

Reads:  <project>/artifacts/storyboard/*.json
        <project>/artifacts/whisper/full.json   (optional)
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli

_EDGE_PUNCT = ".,!?;:\"'`()[]{}<>—–…“”‘’"

# Travel-method markers. Whole-word matched (so "shipment"/"marshal" don't trip
# "ship"/"march", and "carriage" still matches as its own token). Covers explicit
# conveyances AND the motion/escape verbs real escape-narration actually uses
# ("slips across the Potomac", "disappears into the thicket", "rode south") — the
# Lincoln Ch.1 escape beat used none of the conveyance words, only these verbs,
# which is exactly how a bare-dashed-line escape route slipped past detection.
TRAVEL_METHODS = frozenset({
    # conveyances / mounts
    "horseback", "horse", "horses", "ride", "rode", "riding", "rider", "mount", "mounted",
    "gallop", "galloped", "galloping", "carriage", "coach", "wagon", "buggy", "cart",
    "ship", "sail", "sailed", "sailing", "boat", "steamer", "ferry", "schooner", "vessel",
    "caravan", "convoy", "train", "rail", "railroad", "steamboat", "rowboat", "canoe", "raft",
    # flight / escape
    "flee", "fled", "fleeing", "flight", "escape", "escaped", "escaping",
    "pursued", "pursuit", "chase", "chased", "manhunt", "hunted",
    # locomotion verbs (the real Booth route used these, not conveyance nouns)
    "march", "marched", "marching", "trek", "trekked", "journey", "journeyed",
    "rides", "crosses", "crossed", "crossing", "slips", "slipped", "slipping",
    "disappears", "disappeared", "vanishes", "vanished", "travels", "traveled",
    "travelled", "treks", "moves", "moved", "moving", "headed", "heading",
    "route", "trail", "across",
})


def _norm(tok: str) -> str:
    return tok.lower().strip().strip(_EDGE_PUNCT)


def _tokens(text: str) -> List[str]:
    out: List[str] = []
    for raw in text.split():
        t = _norm(raw)
        if t:
            out.append(t)
    return out


def _whisper_words(project_dir: Path) -> Optional[List[Tuple[str, float]]]:
    path = project_dir / "artifacts" / "whisper" / "full.json"
    if not path.is_file():
        return None
    data = load_json(path)
    words = data.get("words")
    if not isinstance(words, list) or not words:
        raise GateInputError("whisper/full.json has no 'words' array")
    out: List[Tuple[str, float]] = []
    for w in words:
        if not isinstance(w, dict):
            raise GateInputError("whisper/full.json: a word entry is not an object")
        raw = w.get("word")
        start = w.get("start")
        if not isinstance(raw, str) or not isinstance(start, (int, float)) or isinstance(start, bool):
            raise GateInputError("whisper/full.json: a word entry lacks string 'word' / numeric 'start'")
        out.append((str(raw), float(start)))
    return out


def _resolve_anchor(anchor: Optional[dict], words: List[Tuple[str, float]]) -> Optional[float]:
    if not isinstance(anchor, dict):
        return None
    offset = 0.0
    off_raw = anchor.get("offset_ms", 0)
    if isinstance(off_raw, (int, float)) and not isinstance(off_raw, bool):
        offset = float(off_raw) / 1000.0
    toks = _tokens(str(anchor.get("phrase", "")))
    if toks and words:
        norm_words = [_norm(w) for w, _ in words]
        n = len(toks)
        for i in range(len(norm_words) - n + 1):
            if norm_words[i:i + n] == toks:
                return max(0.0, words[i][1] + offset)
    fb = anchor.get("fallback_absolute_s")
    if isinstance(fb, (int, float)) and not isinstance(fb, bool):
        return max(0.0, float(fb) + offset)
    return None


def _beat_vo_tokens(words: List[Tuple[str, float]], start_s: float, end_s: float) -> List[str]:
    return [_norm(raw) for raw, t in words if start_s <= t <= end_s and _norm(raw)]


def _params_text_tokens(la: dict) -> List[str]:
    """Travel words sometimes live only in the arrow's own params (label/caption/
    note/path ids) — scan those so the gate works even with no transcript."""
    p = la.get("params") or {}
    parts: List[str] = []
    for k in ("label", "caption", "note", "title", "method", "mode"):
        v = p.get(k)
        if isinstance(v, str):
            parts.append(v)
    path = p.get("path")
    if isinstance(path, list):
        parts.extend(str(x) for x in path if isinstance(x, (str, int, float)))
    return _tokens(" ".join(parts).replace("_", " "))


def _names_travel(tokens: List[str]) -> Optional[str]:
    for t in tokens:
        if t in TRAVEL_METHODS:
            return t
    return None


# A multi-leg route (>= this many waypoints) is itself a journey across the map —
# a person/army moving through a sequence of places — regardless of the exact VO
# verb. This is the structural backstop that catches travel beats whose narration
# uses motion the keyword list doesn't enumerate.
MULTI_WAYPOINT_MIN = 3


def _waypoint_count(la: dict) -> int:
    path = (la.get("params") or {}).get("path")
    return len(path) if isinstance(path, list) else 0


def _icon_declared(la: dict) -> bool:
    """True iff the layer declares a non-empty character/transportation icon."""
    p = la.get("params") or {}
    icon = p.get("character_icon")
    if not isinstance(icon, dict):
        return False
    # Any of these identifies the traveler that rides the polyline.
    for k in ("asset_id", "icon", "sprite", "label", "character_id", "emoji"):
        v = icon.get(k)
        if isinstance(v, str) and v.strip():
            return True
    return False


def _rationale(la: dict) -> Optional[str]:
    p = la.get("params") or {}
    r = p.get("no_icon_rationale")
    if isinstance(r, str) and r.strip():
        return r.strip()
    return None


def _storyboards(project_dir: Path) -> List[Tuple[str, dict]]:
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        raise GateInputError("required input not found: " + str(sb_dir) + " (no storyboard directory)")
    paths = sorted(sb_dir.glob("*.json"))
    if not paths:
        raise GateInputError("no storyboard files in " + str(sb_dir) + " (expected one *.json per chapter)")
    out: List[Tuple[str, dict]] = []
    for p in paths:
        data = load_json(p)
        if not isinstance(data, dict):
            raise GateInputError(str(p) + ": storyboard root is not an object")
        out.append((p.name, data))
    return out


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    storyboards = _storyboards(project_dir)
    words = _whisper_words(project_dir)  # None -> params-only travel detection

    findings: List[Finding] = []
    for name, sb in storyboards:
        cid = str(sb.get("chapter_id") or name)
        phases = sb.get("phases")
        if not isinstance(phases, list):
            continue
        for ph in phases:
            beats = ph.get("beats") if isinstance(ph, dict) else None
            if not isinstance(beats, list):
                continue
            phase_id = str(ph.get("phase_id") or "phase")
            for beat in beats:
                if not isinstance(beat, dict):
                    continue
                layers = beat.get("layers")
                if not isinstance(layers, list):
                    continue
                arrows = [la for la in layers
                          if isinstance(la, dict) and la.get("primitive") == "migration_arrow"]
                if not arrows:
                    continue

                # VO tokens for this beat (if a transcript resolves the anchors).
                vo_tokens: List[str] = []
                if words is not None:
                    s = _resolve_anchor(beat.get("start_anchor"), words)
                    e = _resolve_anchor(beat.get("end_anchor"), words)
                    if s is not None and e is not None and e >= s:
                        vo_tokens = _beat_vo_tokens(words, s, e)

                bid = str(beat.get("beat_id") or "beat")
                for ai, la in enumerate(arrows):
                    method = _names_travel(vo_tokens) or _names_travel(_params_text_tokens(la))
                    wp = _waypoint_count(la)
                    if method is None and wp >= MULTI_WAYPOINT_MIN:
                        method = "multi-leg route ({0} waypoints)".format(wp)
                    if method is None:
                        continue  # route not framed as travel -> no icon required
                    if _icon_declared(la):
                        continue  # a traveler rides the polyline -> satisfied
                    rationale = _rationale(la)
                    where = "{0} :: {1} :: {2} :: migration_arrow[{3}]".format(cid, phase_id, bid, ai)
                    if rationale is not None:
                        findings.append(Finding(
                            "warn", "iconless_route_documented",
                            "migration_arrow on a travel line (VO/params name {0!r}) has no "
                            "character_icon, but a rationale is documented: {1!r}".format(method, rationale),
                            where=where,
                        ))
                        continue
                    findings.append(Finding(
                        "fail", "migration_arrow_missing_icon",
                        "the VO/params frame this route as travel ({0!r}) but the migration_arrow "
                        "declares NO params.character_icon — a transportation/character icon (e.g. "
                        "the rider on horseback) must travel the polyline, or set "
                        "params.no_icon_rationale to document why it is icon-less.".format(method),
                        where=where,
                    ))
    return findings


if __name__ == "__main__":
    run_cli("qa_migration_icon", check)
