"""qa_asset_coverage — the cuelist must COVER the story with the RIGHT cue type.

This is the fix for the Vatican "36 cards / 0 photos / 0 maps / 0 charts / 0
animations" miss: a cuelist that is technically full (every cue in bounds, on
the timing spine) but is monotonous text-on-screen — every named figure reduced
to a bare lower_third, no place ever shown on a map, no >=3-way comparison ever
charted, whole chapters with zero bespoke motion. Each individual cue passes its
own gate; the WHOLE is a dead, text-only video. This gate enforces cue-type
DIVERSITY: the named entities the project declared must each resolve to the
treatment that actually carries them.

The named-entity sets are READ FROM THE PROJECT (artifacts/canonical_names.json),
never hardcoded — so this gate ports to any Sleep Network overlay project, not
just the Vatican one it was minted from.

Rules (each is a "fail" unless the entity carries a documented drop — see WAIVER):
  * PEOPLE  — every declared person who is actually MENTIONED in the VO must
              resolve to a photo_card cue OR a treated clip cue (a clip carrying
              both a `frame` and a `grade`/`treatment`). A person present ONLY as
              a bare text lower_third is `figure_text_only_no_visual` — the exact
              Vatican bug. A person with NO bound cue at all is `figure_uncovered`.
              (A person never spoken in the transcript is out of scope and skipped,
              mirroring the source gate; with no transcript, all are in scope.)
  * PLACES  — every declared place must resolve to a `map` cue, else `place_no_map`.
  * EVENTS  — every declared iconic event (events[].iconic != false) must resolve
              to a treated clip cue, else `event_no_clip`.
  * COMPARISONS — every declared comparison with >= MIN_DATAPOINTS data points must
              resolve to a `chart` cue, else `comparison_no_chart`. Comparisons
              with fewer points are not chart-worthy and are skipped.
  * CHAPTERS — every chapter must contain >= 1 `animation` cue. A chapter flagged
              `map_is_animation: true` may substitute a `map` cue (the map IS that
              chapter's dominant motion), else `chapter_no_animation`. Chapter->cue
              binding is by TIME WINDOW (a cue whose t_in falls in the chapter's
              span), not by slug — chapters and their cues do not share an id. The
              window comes from the storyboard
              (vo_start_offset_in_master_s .. +duration_s) or, with no storyboard,
              from canonical_names.chapters[].window [t0,t1] (or t_in/t_out). A cue
              may also bind explicitly via cue["chapter"]/cue["chapter_id"]==id.

A NAMED ENTITY (person/place/event/comparison) binds to a cue when the entity's
id (slug) appears in the cue's `asset_id`, `id`, or `event_cue_id`. CHAPTERS bind
by time window (see above).

WAIVER: any rule is satisfied without the cue if the omission is documented —
either the ENTITY declaration carries `_dropped: true` / a non-empty
`scrap_reason`, OR a cue bound to that entity is itself `_dropped: true` / carries
a `scrap_reason`. An undocumented gap blocks compose; a documented one does not.

Optional render-frame check: none — this gate runs on artifacts alone, so it is
deterministic on the cuelist + canonical-names declaration (no rendered frames
required).

Reads:  <project>/artifacts/cuelist.json          (required)
        <project>/artifacts/canonical_names.json   (required — the entity set)
        <project>/artifacts/whisper/full.json       (optional — scopes PEOPLE to
                                                      those actually spoken; absent
                                                      => every person is in scope)
        <project>/artifacts/storyboard/*.json       (optional — chapter list;
                                                      falls back to canonical_names)
Shapes (only the fields this gate reads):
    cuelist          = {"cues": [{"id","kind","asset_id"?,"event_cue_id"?,
                        "frame"?,"grade"?,"treatment"?,"_dropped"?,"scrap_reason"?}]}
    canonical_names  = {"people":[{"id","canonical_full","canonical_short"?,
                        "first_mention_form"?,"_dropped"?,"scrap_reason"?}],
                        "places":[{"id","canonical", ...}],
                        "events":[{"id","canonical_short","iconic"?, ...}],
                        "comparisons":[{"id","label"?,"datapoints"?(int|list), ...}],
                        "chapters":[{"id","map_is_animation"?, ...}]}
    whisper          = {"words":[{"word": str, "start": float}, ...]}
    storyboard/<f>   = {"chapter_id": str, "map_is_animation"?: bool, ...}
"""

from __future__ import annotations

import re
from argparse import Namespace
from pathlib import Path
from typing import Dict, List, Optional, Set

from ._contract import Finding, GateInputError, load_json, run_cli

# A comparison needs at least this many data points to be worth a chart; a 2-way
# "X vs Y" can ride a text card, but >=3 series wants a chart to be legible.
MIN_DATAPOINTS = 3

# Cue kinds (the canonical overlay cuelist `kind` vocabulary).
PHOTO_CARD_KIND = "photo_card"
LOWER_THIRD_KIND = "lower_third"
CLIP_KIND = "clip"
MAP_KIND = "map"
CHART_KIND = "chart"
ANIMATION_KIND = "animation"


def _norm(s: str) -> str:
    """Lowercase, collapse non-alphanumerics to single spaces, strip."""
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def _norm_tokens(s: str) -> List[str]:
    n = _norm(s)
    return n.split() if n else []


def _is_dropped(obj: dict) -> bool:
    """True if this declaration/cue is documented as intentionally omitted.

    Either `_dropped: true` or a non-empty string `scrap_reason` counts — both
    are the schema's "documented drop, not a silent hole" signal.
    """
    if not isinstance(obj, dict):
        return False
    if obj.get("_dropped") is True:
        return True
    sr = obj.get("scrap_reason")
    return isinstance(sr, str) and sr.strip() != ""


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #
def _load_cues(project_dir: Path) -> List[dict]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")
    out: List[dict] = []
    for i, c in enumerate(cues):
        if not isinstance(c, dict):
            raise GateInputError("cuelist.json: cue[{0}] is not an object".format(i))
        out.append(c)
    return out


def _load_names(project_dir: Path) -> dict:
    data = load_json(project_dir / "artifacts" / "canonical_names.json")
    if not isinstance(data, dict):
        raise GateInputError("canonical_names.json root is not an object")
    return data


def _whisper_norm_text(project_dir: Path) -> Optional[List[str]]:
    """Whisper words as a normalized token list, or None if no transcript.

    None => the gate cannot scope PEOPLE to who is actually spoken, so it treats
    every declared person as in scope (fail-closed, never fail-open).
    """
    path = project_dir / "artifacts" / "whisper" / "full.json"
    if not path.is_file():
        return None
    data = load_json(path)
    words = data.get("words")
    if not isinstance(words, list) or not words:
        raise GateInputError("whisper/full.json has no 'words' array")
    toks: List[str] = []
    for w in words:
        if not isinstance(w, dict):
            raise GateInputError("whisper/full.json: a word entry is not an object")
        raw = w.get("word")
        if not isinstance(raw, str):
            raise GateInputError("whisper/full.json: a word entry has no string 'word'")
        toks.extend(_norm_tokens(raw))
    if not toks:
        raise GateInputError("whisper/full.json: no usable word tokens after normalization")
    return toks


def _num_or_none(v) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _storyboard_chapters(project_dir: Path) -> Optional[List[dict]]:
    """Chapters from storyboard/*.json with their master-timeline window, or None.

    Window = [vo_start_offset_in_master_s, +duration_s). Either may be absent (an
    offset of 0 is assumed when missing); a chapter with no resolvable window
    falls back to whole-timeline matching, which still catches a project with ZERO
    animation cues anywhere — the failure this gate exists to stop.
    """
    sb_dir = project_dir / "artifacts" / "storyboard"
    if not sb_dir.is_dir():
        return None
    paths = sorted(sb_dir.glob("*.json"))
    if not paths:
        return None
    out: List[dict] = []
    for p in paths:
        data = load_json(p)
        if not isinstance(data, dict):
            raise GateInputError(str(p) + ": storyboard root is not an object")
        cid = data.get("chapter_id")
        if not isinstance(cid, str) or not cid.strip():
            raise GateInputError(str(p) + ": storyboard has no string 'chapter_id'")
        t0 = _num_or_none(data.get("vo_start_offset_in_master_s"))
        dur = _num_or_none(data.get("duration_s"))
        t0v = 0.0 if t0 is None else t0
        t1v = (t0v + dur) if dur is not None else None
        out.append({
            "id": cid.strip(),
            "t0": t0v,
            "t1": t1v,
            "map_is_animation": data.get("map_is_animation") is True,
            "_dropped": data.get("_dropped") is True,
            "scrap_reason": data.get("scrap_reason"),
        })
    return out


# --------------------------------------------------------------------------- #
# binding + matching helpers
# --------------------------------------------------------------------------- #
def _cue_binding_text(cue: dict) -> str:
    """The cue's identity fields a slug may appear in, normalized + space-joined."""
    parts = [cue.get("asset_id"), cue.get("id"), cue.get("event_cue_id")]
    return " ".join(_norm(p) for p in parts if isinstance(p, str) and p)


def _slug_matches(slug: str, binding_text: str) -> bool:
    """True if the entity slug appears as a token-substring of the binding text.

    Slug tokens must appear contiguously (so `pius_v` matches `photo pius v`,
    but a stray `v` elsewhere does not). Mirrors the source gate's
    `slug in c.get('asset','')` intent, made whitespace/punctuation tolerant.
    """
    s_toks = _norm_tokens(slug.replace("_", " "))
    if not s_toks:
        return False
    b_toks = binding_text.split()
    n = len(s_toks)
    if n > len(b_toks):
        return False
    for i in range(len(b_toks) - n + 1):
        if b_toks[i:i + n] == s_toks:
            return True
    return False


def _is_treated_clip(cue: dict) -> bool:
    """A clip is 'treated' for coverage purposes if it carries a frame AND a grade.

    (Deep recipe/frame validity is qa_clip_treatment's job; coverage only needs to
    know the figure resolves to a TREATED clip rather than a bare text card.)
    """
    if cue.get("kind") != CLIP_KIND:
        return False
    frame = cue.get("frame")
    grade = cue.get("grade") or cue.get("treatment")
    return (isinstance(frame, str) and frame.strip() != ""
            and isinstance(grade, str) and grade.strip() != "")


def _entity_phrases(ent: dict, name_keys) -> List[str]:
    """Spoken-name surface forms for an entity, from the given declaration keys."""
    out: List[str] = []
    for k in name_keys:
        v = ent.get(k)
        if isinstance(v, str) and v.strip():
            out.append(v)
    return out


def _any_phrase_spoken(phrases: List[str], whisper_toks: List[str]) -> bool:
    """True if any phrase appears as a contiguous token-run in the transcript."""
    for phrase in phrases:
        needle = _norm_tokens(phrase)
        if not needle:
            continue
        n = len(needle)
        if n > len(whisper_toks):
            continue
        for i in range(len(whisper_toks) - n + 1):
            if whisper_toks[i:i + n] == needle:
                return True
    return False


def _datapoint_count(comp: dict) -> int:
    """Number of data points a comparison declares (int directly or len of list)."""
    dp = comp.get("datapoints", comp.get("data_points"))
    if isinstance(dp, bool):
        return 0
    if isinstance(dp, int):
        return dp
    if isinstance(dp, (list, tuple)):
        return len(dp)
    return 0


def _cue_in_chapter(cue: dict, chap: dict) -> bool:
    """True if a cue belongs to a chapter — by explicit field, else by time window.

    Explicit: cue["chapter"] or cue["chapter_id"] equals the chapter id.
    Temporal: the cue's t_in falls in [t0, t1) (or t0<=t_in if the window has no
    end). A chapter with no resolvable window (t1 is None and t0 is 0) matches any
    cue, so a project with zero animation cues anywhere still fails.
    """
    cid = chap["id"]
    for fld in ("chapter", "chapter_id"):
        v = cue.get(fld)
        if isinstance(v, str) and v.strip() == cid:
            return True
    t_in = _num_or_none(cue.get("t_in"))
    if t_in is None:
        return False
    t0 = chap.get("t0")
    t1 = chap.get("t1")
    t0v = 0.0 if t0 is None else float(t0)
    if t_in < t0v:
        return False
    if t1 is not None and t_in >= float(t1):
        return False
    return True


def _entity_id(ent: dict, where_kind: str, idx: int) -> str:
    eid = ent.get("id")
    if not isinstance(eid, str) or not eid.strip():
        raise GateInputError(
            "canonical_names.json: {0}[{1}] has no string 'id'".format(where_kind, idx))
    return eid.strip()


# --------------------------------------------------------------------------- #
# the gate
# --------------------------------------------------------------------------- #
def check(project_dir: Path, args: Namespace) -> List[Finding]:
    cues = _load_cues(project_dir)
    names = _load_names(project_dir)
    whisper_toks = _whisper_norm_text(project_dir)  # None => all people in scope

    findings: List[Finding] = []

    # Pre-index cues by kind for the bound-cue scans.
    photo_cues = [c for c in cues if c.get("kind") == PHOTO_CARD_KIND]
    lower_third_cues = [c for c in cues if c.get("kind") == LOWER_THIRD_KIND]
    clip_cues = [c for c in cues if c.get("kind") == CLIP_KIND]
    map_cues = [c for c in cues if c.get("kind") == MAP_KIND]
    chart_cues = [c for c in cues if c.get("kind") == CHART_KIND]
    animation_cues = [c for c in cues if c.get("kind") == ANIMATION_KIND]

    def _bound(cue_subset: List[dict], slug: str) -> List[dict]:
        return [c for c in cue_subset if _slug_matches(slug, _cue_binding_text(c))]

    def _waived_by_bound_cue(cue_subset_groups, slug: str) -> bool:
        """True if any cue bound to this slug is a documented drop."""
        for group in cue_subset_groups:
            for c in group:
                if _slug_matches(slug, _cue_binding_text(c)) and _is_dropped(c):
                    return True
        return False

    # ---- PEOPLE: photo_card OR treated clip; bare lower_third is the bug. ----
    people = names.get("people") or []
    if not isinstance(people, list):
        raise GateInputError("canonical_names.json 'people' is not an array")
    for idx, person in enumerate(people):
        if not isinstance(person, dict):
            raise GateInputError(
                "canonical_names.json: people[{0}] is not an object".format(idx))
        slug = _entity_id(person, "people", idx)

        # Scope: only enforce on people actually spoken (when we have a transcript).
        if whisper_toks is not None:
            phrases = _entity_phrases(
                person, ("canonical_full", "canonical_short", "first_mention_form"))
            if phrases and not _any_phrase_spoken(phrases, whisper_toks):
                continue  # never mentioned -> out of scope (matches source gate)

        # Documented drop on the declaration waives the requirement.
        if _is_dropped(person):
            continue

        has_photo = bool(_bound(photo_cues, slug))
        has_treated_clip = any(_is_treated_clip(c) for c in _bound(clip_cues, slug))
        if has_photo or has_treated_clip:
            continue
        if _waived_by_bound_cue((photo_cues, clip_cues, lower_third_cues), slug):
            continue  # a bound cue is documented as dropped

        name = person.get("canonical_full") or person.get("canonical_short") or slug
        if _bound(lower_third_cues, slug):
            findings.append(Finding(
                "fail", "figure_text_only_no_visual",
                "named figure {0!r} (id={1}) appears ONLY as a bare text lower_third "
                "with no photo_card or treated clip and no documented scrap_reason — "
                "this is the Vatican 'all cards, no photos' miss. Source a PD photo "
                "(photo_card) or a treated clip, or document a scrap_reason.".format(
                    name, slug),
                where="people/{0}".format(slug)))
        else:
            scope_note = ("is mentioned in the VO but " if whisper_toks is not None
                          else "is declared (no transcript to scope it out) but ")
            findings.append(Finding(
                "fail", "figure_uncovered",
                "named figure {0!r} (id={1}) {2}has NO bound visual cue at all "
                "(no photo_card / treated clip / lower_third) and no documented "
                "scrap_reason.".format(name, slug, scope_note),
                where="people/{0}".format(slug)))

    # ---- PLACES: must resolve to a map cue. ----
    places = names.get("places") or []
    if not isinstance(places, list):
        raise GateInputError("canonical_names.json 'places' is not an array")
    for idx, place in enumerate(places):
        if not isinstance(place, dict):
            raise GateInputError(
                "canonical_names.json: places[{0}] is not an object".format(idx))
        slug = _entity_id(place, "places", idx)
        if _is_dropped(place):
            continue
        if _bound(map_cues, slug):
            continue
        if _waived_by_bound_cue((map_cues,), slug):
            continue
        name = place.get("canonical") or slug
        findings.append(Finding(
            "fail", "place_no_map",
            "named place {0!r} (id={1}) has no bound map cue and no documented "
            "scrap_reason — every named place/journey needs an animated map cue.".format(
                name, slug),
            where="places/{0}".format(slug)))

    # ---- EVENTS: every iconic event must resolve to a treated clip. ----
    events = names.get("events") or []
    if not isinstance(events, list):
        raise GateInputError("canonical_names.json 'events' is not an array")
    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            raise GateInputError(
                "canonical_names.json: events[{0}] is not an object".format(idx))
        slug = _entity_id(event, "events", idx)
        if event.get("iconic") is False:
            continue  # explicitly not an iconic moment -> no clip obligation
        if _is_dropped(event):
            continue
        if any(_is_treated_clip(c) for c in _bound(clip_cues, slug)):
            continue
        if _waived_by_bound_cue((clip_cues,), slug):
            continue
        name = event.get("canonical_short") or event.get("canonical_long") or slug
        findings.append(Finding(
            "fail", "event_no_clip",
            "iconic event {0!r} (id={1}) has no bound treated clip cue (a clip with "
            "both a frame and a grade) and no documented scrap_reason — an iconic "
            "moment must be carried by a transformative-use clip.".format(name, slug),
            where="events/{0}".format(slug)))

    # ---- COMPARISONS: >= MIN_DATAPOINTS data points must resolve to a chart. ----
    comparisons = names.get("comparisons") or []
    if not isinstance(comparisons, list):
        raise GateInputError("canonical_names.json 'comparisons' is not an array")
    for idx, comp in enumerate(comparisons):
        if not isinstance(comp, dict):
            raise GateInputError(
                "canonical_names.json: comparisons[{0}] is not an object".format(idx))
        slug = _entity_id(comp, "comparisons", idx)
        n_dp = _datapoint_count(comp)
        if n_dp < MIN_DATAPOINTS:
            continue  # not chart-worthy
        if _is_dropped(comp):
            continue
        if _bound(chart_cues, slug):
            continue
        if _waived_by_bound_cue((chart_cues,), slug):
            continue
        label = comp.get("label") or slug
        findings.append(Finding(
            "fail", "comparison_no_chart",
            "comparison {0!r} (id={1}) declares {2} data points (>= {3}) but has no "
            "bound chart cue and no documented scrap_reason — a multi-datapoint "
            "comparison must be charted to be legible.".format(
                label, slug, n_dp, MIN_DATAPOINTS),
            where="comparisons/{0}".format(slug)))

    # ---- CHAPTERS: each needs >= 1 animation cue (map may substitute if flagged).
    # Bound by TIME WINDOW, not slug (chapters and their cues share no id).
    chapters = _storyboard_chapters(project_dir)
    chapter_source = "storyboard"
    if chapters is None:
        decl = names.get("chapters") or []
        if not isinstance(decl, list):
            raise GateInputError("canonical_names.json 'chapters' is not an array")
        chapters = []
        for idx, ch in enumerate(decl):
            if not isinstance(ch, dict):
                raise GateInputError(
                    "canonical_names.json: chapters[{0}] is not an object".format(idx))
            window = ch.get("window")
            if isinstance(window, (list, tuple)) and len(window) >= 1:
                t0 = _num_or_none(window[0])
                t1 = _num_or_none(window[1]) if len(window) >= 2 else None
            else:
                t0 = _num_or_none(ch.get("t_in"))
                t1 = _num_or_none(ch.get("t_out"))
            chapters.append({
                "id": _entity_id(ch, "chapters", idx),
                "t0": 0.0 if t0 is None else t0,
                "t1": t1,
                "map_is_animation": ch.get("map_is_animation") is True,
                "_dropped": ch.get("_dropped") is True,
                "scrap_reason": ch.get("scrap_reason"),
            })
        chapter_source = "canonical_names"

    for ch in chapters:
        slug = ch["id"]
        if _is_dropped(ch):
            continue
        if any(_cue_in_chapter(c, ch) for c in animation_cues):
            continue
        if ch.get("map_is_animation") and any(_cue_in_chapter(c, ch) for c in map_cues):
            continue  # the map IS this chapter's dominant motion treatment
        findings.append(Finding(
            "fail", "chapter_no_animation",
            "chapter {0!r} ({1}) has no animation cue in its window (kind='animation') "
            "and is not flagged map_is_animation with a map in its window — every "
            "chapter needs at least one bespoke animation.".format(slug, chapter_source),
            where="chapters/{0}".format(slug)))

    return findings


if __name__ == "__main__":
    run_cli("qa_asset_coverage", check)
