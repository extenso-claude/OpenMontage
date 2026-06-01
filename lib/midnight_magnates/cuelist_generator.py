"""cuelist_generator — coverage-driven draft cuelist (Strategy: diversity by default).

Inverts qa_asset_coverage. Instead of CHECKING cue-type diversity AFTER the agent
hand-builds a cuelist (where a PIL text card is the path of least resistance — the
Vatican "36 cards / 0 photos / 0 maps / 0 charts / 0 animations" failure), this EMITS
a draft cuelist with the required cue PRE-STUBBED per canonical entity, anchored to its
first Whisper mention:

    person             -> photo_card   (or lower_third if the entity carries a scrap_reason)
    place              -> map
    event (iconic)     -> treated clip (frame + grade stubbed "TBD")
    comparison (>=3 dp)-> chart
    chapter            -> animation    (skipped when map_is_animation: a map IS the motion)

The agent then fills real asset_ids + bboxes + frames/grades + refines. Diversity becomes
the default the agent prunes from, not a step they must remember to add. The emitted draft
passes qa_asset_coverage by construction (verified against the qa_asset_coverage fixtures).

Reads:  <project>/artifacts/canonical_names.json (required)
        <project>/artifacts/whisper/full.json     (optional — scopes people to those actually
                                                    spoken, and anchors each cue to first-mention)
Writes: <project>/artifacts/cuelist.draft.json     (NOT cuelist.json — the agent reviews + promotes)
CLI:    python -m lib.midnight_magnates.cuelist_generator --project <dir> [--channel <name>]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

_MIN_CHART_DATAPOINTS = 3
_HOLD_S = 5.0
_EDGE = ".,!?;:\"'`()[]{}<>—–…“”‘’"


def _norm_tokens(s) -> List[str]:
    """Lowercase, split on any non-alphanumeric (so slugs like `pius_v` and asset_ids
    like `photo_pius_v` tokenize the same way qa_asset_coverage matches them)."""
    out: List[str] = []
    for raw in str(s).split():
        for part in re.split(r"[^a-z0-9]+", raw.lower().strip().strip(_EDGE)):
            if part:
                out.append(part)
    return out


def _load(project_dir: Path, rel: str) -> Optional[dict]:
    p = project_dir / rel
    if not p.is_file():
        return None
    with open(p) as f:
        return json.load(f)


def _whisper_stream(data: Optional[dict]) -> List[Tuple[str, float]]:
    if not data:
        return []
    out: List[Tuple[str, float]] = []
    for w in data.get("words", []):
        if isinstance(w, dict) and isinstance(w.get("word"), str):
            start = w.get("start", 0.0)
            start = float(start) if isinstance(start, (int, float)) else 0.0
            for tok in _norm_tokens(w["word"]):
                out.append((tok, start))
    return out


def _find_mention(forms: List[str], stream: List[Tuple[str, float]]) -> Tuple[Optional[float], Optional[str]]:
    """Earliest contiguous token-run of any form -> (start_s, the matched form). Else (None, None)."""
    toks = [t for t, _ in stream]
    best: Optional[float] = None
    best_form: Optional[str] = None
    for form in [f for f in forms if f]:
        needle = _norm_tokens(form)
        n = len(needle)
        if not n:
            continue
        for i in range(len(toks) - n + 1):
            if toks[i:i + n] == needle:
                start = stream[i][1]
                if best is None or start < best:
                    best, best_form = start, form
                break
    return best, best_form


def _has_scrap(o: dict) -> bool:
    sr = o.get("scrap_reason")
    return bool(sr and str(sr).strip()) or o.get("_dropped") is True


def generate(names: dict, whisper: Optional[dict], channel: str = "") -> dict:
    """Return a draft cuelist (dict) with one required-kind cue per in-scope entity."""
    stream = _whisper_stream(whisper)
    have_whisper = bool(stream)
    cues: List[dict] = []

    def anchored_t(forms: List[str]) -> Tuple[float, Optional[str], bool]:
        st, form = _find_mention(forms, stream)
        return (st if st is not None else 0.0), form, (st is not None)

    # PEOPLE -> photo_card (or documented lower_third when the entity carries a scrap_reason)
    for p in names.get("people", []):
        pid = p.get("id")
        if not pid:
            continue
        forms = [p.get("first_mention_form"), p.get("canonical_full"), p.get("canonical_short")]
        t_in, form, found = anchored_t(forms)
        # Whisper scopes people: an unspoken figure is out of scope (not required on screen).
        if have_whisper and not found:
            continue
        if _has_scrap(p):
            cues.append({
                "id": f"lt_{pid}", "kind": "lower_third", "t_in": round(t_in, 2),
                "t_out": round(t_in + _HOLD_S, 2), "asset_id": f"lt_{pid}",
                "text": p.get("canonical_short") or p.get("canonical_full") or pid,
                "anchor_phrase": form or p.get("canonical_short") or pid,
                "scrap_reason": p.get("scrap_reason"),
            })
        else:
            cues.append({
                "id": f"photo_{pid}", "kind": "photo_card", "t_in": round(t_in, 2),
                "t_out": round(t_in + _HOLD_S, 2), "asset_id": f"photo_{pid}",
                "anchor_phrase": form or p.get("canonical_full") or pid,
                "sourcing": {"searched_copyright": False}, "_stub": True,
            })

    # PLACES -> map
    for pl in names.get("places", []):
        plid = pl.get("id")
        if not plid or _has_scrap(pl):
            continue
        t_in, form, _ = anchored_t([pl.get("canonical")])
        cues.append({
            "id": f"map_{plid}", "kind": "map", "t_in": round(t_in, 2),
            "t_out": round(t_in + _HOLD_S, 2), "asset_id": f"map_{plid}",
            "anchor_phrase": form or pl.get("canonical") or plid, "_stub": True,
        })

    # EVENTS (iconic) -> treated clip (frame + grade)
    for e in names.get("events", []):
        eid = e.get("id")
        if not eid or _has_scrap(e) or e.get("iconic") is False:
            continue
        t_in, form, _ = anchored_t([e.get("canonical_short"), e.get("canonical_full")])
        cues.append({
            "id": f"clip_{eid}", "kind": "clip", "t_in": round(t_in, 2),
            "t_out": round(t_in + _HOLD_S, 2), "asset_id": f"clip_{eid}", "event_cue_id": eid,
            "frame": "TBD", "grade": "TBD", "audio_role": "vo-over",
            "anchor_phrase": form or e.get("canonical_short") or eid,
            "sourcing": {"searched_copyright": False}, "_stub": True,
        })

    # COMPARISONS (>= 3 datapoints) -> chart
    for c in names.get("comparisons", []):
        cid = c.get("id")
        if not cid or _has_scrap(c):
            continue
        dp = c.get("datapoints")
        n = dp if isinstance(dp, int) else (len(dp) if isinstance(dp, list) else 0)
        if n < _MIN_CHART_DATAPOINTS:
            continue
        t_in, form, _ = anchored_t([c.get("label")])
        cues.append({
            "id": f"chart_{cid}", "kind": "chart", "t_in": round(t_in, 2),
            "t_out": round(t_in + _HOLD_S, 2), "asset_id": f"chart_{cid}",
            "anchor_phrase": form or c.get("label") or cid, "_stub": True,
        })

    # CHAPTERS -> >=1 animation. A map_is_animation chapter is satisfied when a map cue
    # already lands in its window (the map IS the motion); otherwise emit the animation so
    # coverage holds even if no place-map anchored into the window.
    _map_t_ins = [c["t_in"] for c in cues if c["kind"] == "map"]
    for ch in names.get("chapters", []):
        chid = ch.get("id")
        if not chid or _has_scrap(ch):
            continue
        win = ch.get("window") or [0.0, 0.0]
        t_in = float(win[0])
        t_out = float(win[1]) if len(win) > 1 and win[1] > win[0] else t_in + _HOLD_S
        if ch.get("map_is_animation") is True and any(t_in <= mt <= t_out for mt in _map_t_ins):
            continue  # a map in this window is the chapter's motion
        aph = None
        for tok, stt in stream:
            if t_in <= stt <= t_out:
                aph = tok
                break
        cues.append({
            "id": f"anim_{chid}", "kind": "animation", "t_in": round(t_in, 2),
            "t_out": round(max(t_out, t_in + _HOLD_S), 2), "asset_id": f"anim_{chid}",
            "chapter_id": chid, "anchor_phrase": aph or chid, "_stub": True,
        })

    cues.sort(key=lambda c: (c["t_in"], c["id"]))
    return {"version": "draft-1", "channel": channel or names.get("channel", ""),
            "_generated": True, "cues": cues}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="cuelist_generator")
    ap.add_argument("--project", required=True)
    ap.add_argument("--channel", default="")
    a = ap.parse_args(argv)
    proj = Path(a.project)
    names = _load(proj, "artifacts/canonical_names.json")
    if names is None:
        print("ERROR: artifacts/canonical_names.json not found under " + str(proj), file=sys.stderr)
        return 2
    whisper = _load(proj, "artifacts/whisper/full.json")
    draft = generate(names, whisper, a.channel)
    out = proj / "artifacts" / "cuelist.draft.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(draft, f, indent=2)
    print(f"wrote {out} with {len(draft['cues'])} stub cues "
          f"({sum(1 for c in draft['cues'] if c['kind'] == 'photo_card')} photo, "
          f"{sum(1 for c in draft['cues'] if c['kind'] == 'map')} map, "
          f"{sum(1 for c in draft['cues'] if c['kind'] == 'chart')} chart, "
          f"{sum(1 for c in draft['cues'] if c['kind'] == 'clip')} clip, "
          f"{sum(1 for c in draft['cues'] if c['kind'] == 'animation')} anim, "
          f"{sum(1 for c in draft['cues'] if c['kind'] == 'lower_third')} lt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
