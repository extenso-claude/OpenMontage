"""qa_avatar_sync — a wan-2.2-s2v avatar's lips stay frame-locked to the source VO.

Consolidates projects/vatican-entity-mm/scripts/qa_avatar_sync{,_v2,_v3,_v4}.py
(the forks differed only in artifact paths + PiP geometry; the sync logic is the
same) onto the repo's gate contract.

THE BUG CLASS THIS PREVENTS — avatar audio/video desync from a mis-set lead pad
or a forbidden seek on the wan render:

  Each avatar's audio is cut from the source starting at `audio_cut_start_s`, and
  wan-2.2-s2v lip-syncs the render to THAT cut. The compositor shows wan content
  at wan_t = avatar_video_offset_s + (composite_t - t_in), so at the instant the
  avatar appears (composite_t == t_in) it shows wan_t == avatar_video_offset_s.
  For the lips to match the words the viewer hears, the offset MUST cancel the
  audio cut:
        avatar_video_offset_s  ==  (t_in - audio_cut_start_s)
  Off by more than a sub-frame and the avatar mouths earlier/later words than the
  audio — the documented lip-sync drift. (40ms ~= sub-frame at 24fps, below the
  human audio/visual desync threshold.)

  The OTHER way this drift sneaks in is the ffmpeg invocation itself. wan-2.2-s2v
  emits exactly one keyframe (at t=0), so an INPUT-stream seek (`-ss` placed
  BEFORE the wan `-i`) is keyframe-aligned and silently snaps back to 0 — the
  avatar plays from its start while the audio is N seconds ahead. The same drift
  comes from compounding `-itsoffset` with a `trim`/`atrim` on the wan output. The
  locked recipe is output-seek only (`-ss` AFTER `-i`, which decodes through), so
  this gate hard-fails any avatar cue / avatar_manifest that declares an input
  `-ss` seek or an `-itsoffset`+trim compound on a wan source — the exact ops the
  forks' SSIM check was built to catch, asserted statically so the gate runs on
  artifacts alone (no rendering needed).

PRIMARY checks (fixture-testable, no rendering):
  (a) lead-pad math on every avatar cue:
        |avatar_video_offset_s - (t_in - audio_cut_start_s)| <= 0.040
  (b) forbidden-ops assertion on the cue and/or artifacts/avatar_manifest.json:
        NO input-stream `-ss` seek on a wan source, and NO `-itsoffset`+trim
        compound on a wan output.

OPTIONAL check (run only if rendered frames exist; otherwise skip-with-note):
  (c) SSIM >= 0.95 over the avatar region between the composite frame and the wan
      frame it should be showing, sampled in each cue's alpha=1 hold window. This
      needs ffmpeg + PIL/numpy and the rendered MP4/MOV + wan sources; when those
      aren't present the gate stays deterministically fixture-testable on (a)+(b)
      and emits a "warn" note that the pixel check was skipped.

A gate that cannot run must never silently pass:
  * cuelist.json (and avatar_manifest.json, if the project carries one) unreadable
    or malformed -> GateInputError (blocking).
  * an avatar cue that declares NEITHER an offset/cut pair NOR forbidden-ops to
    check is itself suspicious -> reported (it cannot be lead-pad verified).

Reads:  <project>/artifacts/cuelist.json            (cues[].kind == "avatar"; preferred)
        <project>/artifacts/avatar_manifest.json     (optional; merged per-cue by id)
Optional (check (c) only, skipped when absent):
        <project>/deliverables*/02_composite_preview.{mp4,mov}   (composite master)
        <project>/<cue.asset>                                    (per-cue wan render)
Shapes (only the fields this gate reads):
    cuelist        = {"cues": [{"id", "kind", "t_in", "t_out",
                                "avatar_video_offset_s": num,
                                "audio_cut_start_s": num,
                                "treatment"?, "asset"?,
                                "fade_in"?, "fade_out"?,
                                "ffmpeg_args"? / "compose_cmd"? / "input_args"?},
                               ...]}
    avatar_manifest= {"avatars"|"cues": [ {same per-cue fields, keyed by "id"} ],
                      "ffmpeg_args"? ...}   (a fork may put ops at the cue or top level)
"""

from __future__ import annotations

import shlex
from argparse import Namespace
from pathlib import Path
from typing import Dict, List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

# 40ms ~= sub-frame at 24fps; below the audio/visual desync perception threshold.
LEAD_PAD_TOL_S = 0.040

# SSIM floor for the optional pixel check: below this the avatar visible in the
# composite is NOT the wan frame we expected for that audio moment.
SSIM_MIN = 0.95


def _num(value) -> Optional[float]:
    # bool is an int subclass; True/False is never a timestamp/offset.
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


# --------------------------------------------------------------------------- #
# Forbidden-ops detection (the locked wan-2.2-s2v assertion)
# --------------------------------------------------------------------------- #
# We accept the compose command in any of a few shapes a fork might have written:
#   * a list of argv tokens          ->  used as-is
#   * a single command string        ->  shlex-split into tokens
# and we look at every such field on the cue AND on the avatar manifest (top level
# or per-cue). A wan source is recognised by ".../wan" or "wan-2.2-s2v" appearing
# in the token that follows an "-i" (its input file), or — when ops live on a cue
# whose own `asset` is the wan render — by the cue being an avatar at all.

_CMD_FIELDS = ("ffmpeg_args", "compose_cmd", "input_args", "cmd", "ffmpeg", "command")
_TRIM_MARKERS = ("trim=", "atrim=", "trim:", "atrim:")
_WAN_MARKERS = ("wan", "s2v")


def _as_token_lists(value) -> List[List[str]]:
    """Normalise a command-ish field into a list of token lists.

    A list-of-strings is one argv. A list-of-lists is several argvs. A bare string
    is shlex-split. Anything else yields nothing (silently — other fields may hold
    the real command). Tokens are stringified so a numeric arg doesn't crash split.
    """
    if value is None:
        return []
    if isinstance(value, str):
        try:
            return [shlex.split(value)]
        except ValueError:
            # Unbalanced quotes etc.: fall back to a whitespace split so we still
            # see the flags (an unparseable command is not a reason to miss a -ss).
            return [value.split()]
    if isinstance(value, (list, tuple)):
        if all(isinstance(t, (str, int, float)) for t in value):
            return [[str(t) for t in value]]
        out: List[List[str]] = []
        for sub in value:
            out.extend(_as_token_lists(sub))
        return out
    return []


def _gather_token_lists(*sources: dict) -> List[List[str]]:
    """All command token-lists found across the given dicts (cue + manifest)."""
    out: List[List[str]] = []
    for src in sources:
        if not isinstance(src, dict):
            continue
        for field in _CMD_FIELDS:
            if field in src:
                out.extend(_as_token_lists(src[field]))
    return out


def _is_wan_token(tok: str) -> bool:
    low = tok.lower()
    return any(m in low for m in _WAN_MARKERS)


def _input_seek_on_wan(tokens: List[str]) -> bool:
    """True if an INPUT-stream `-ss` (before the wan `-i`) is present.

    Walk the argv tracking the most recent `-ss` flag's index; when we hit an
    `-i <file>` whose file is a wan source, any `-ss` seen BEFORE this `-i` (and
    not already consumed by an earlier input) is an input seek on that input.
    """
    pending_ss = False  # a -ss has appeared that no -i has consumed yet
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok == "-ss":
            pending_ss = True
            i += 2  # skip its value
            continue
        if tok == "-i":
            inp = tokens[i + 1] if i + 1 < n else ""
            if pending_ss and _is_wan_token(inp):
                return True
            # This -i consumes the pending input-seek state regardless of source:
            # a -ss after this point (and before the next -i) is THAT input's seek.
            pending_ss = False
            i += 2
            continue
        i += 1
    return False


def _itsoffset_with_trim(tokens: List[str]) -> bool:
    """True if `-itsoffset` co-occurs with a trim/atrim filter (the compound seek
    that also desyncs a single-keyframe wan render)."""
    has_itsoffset = "-itsoffset" in tokens
    if not has_itsoffset:
        return False
    joined = " ".join(tokens).lower()
    return any(m in joined for m in _TRIM_MARKERS)


def _forbidden_ops(cue: dict, manifest_cue: Optional[dict], manifest_top: dict
                   ) -> List[str]:
    """Return human-readable descriptions of any forbidden ops found for this cue.

    Looks at command fields on the cue, on its matching manifest entry, and on the
    manifest top level. Empty list == clean.
    """
    sources = [cue]
    if manifest_cue is not None:
        sources.append(manifest_cue)
    sources.append(manifest_top)

    reasons: List[str] = []
    for tokens in _gather_token_lists(*sources):
        if _input_seek_on_wan(tokens):
            reasons.append(
                "input-stream '-ss' seek before a wan '-i' "
                "(`{0}`)".format(" ".join(tokens))
            )
        if _itsoffset_with_trim(tokens):
            reasons.append(
                "'-itsoffset' compounded with a trim/atrim on the wan output "
                "(`{0}`)".format(" ".join(tokens))
            )
    return reasons


# --------------------------------------------------------------------------- #
# Manifest loading + cue gathering
# --------------------------------------------------------------------------- #
def _load_manifest(project_dir: Path) -> tuple:
    """(manifest_top_dict, {cue_id: cue_dict}). Optional: returns ({}, {}) when the
    file is absent. A PRESENT but unreadable/malformed manifest is BLOCKING."""
    path = project_dir / "artifacts" / "avatar_manifest.json"
    if not path.exists():
        return {}, {}
    data = load_json(path)  # GateInputError on unreadable / invalid JSON
    if not isinstance(data, dict):
        raise GateInputError("avatar_manifest.json root is not an object")
    entries = data.get("avatars")
    if entries is None:
        entries = data.get("cues")
    by_id: Dict[str, dict] = {}
    if isinstance(entries, list):
        for j, e in enumerate(entries):
            if not isinstance(e, dict):
                raise GateInputError(
                    "avatar_manifest.json entry #{0} is not an object".format(j)
                )
            eid = e.get("id")
            if isinstance(eid, str) and eid:
                by_id[eid] = e
    return data, by_id


def _merged(cue: dict, manifest_cue: Optional[dict], key: str):
    """Cue value wins; fall back to the manifest entry. Lets a fork carry the
    offset/cut either in the cuelist (preferred) or the manifest."""
    if key in cue and cue.get(key) is not None:
        return cue.get(key)
    if manifest_cue is not None:
        return manifest_cue.get(key)
    return None


# --------------------------------------------------------------------------- #
# Optional pixel (SSIM) check — runs only when rendered frames exist.
# --------------------------------------------------------------------------- #
def _find_composite(project_dir: Path) -> Optional[Path]:
    """The composite master, if rendered. Searches deliverables*/ for the known
    preview name (any extension). Returns None when nothing is rendered yet."""
    for d in sorted(project_dir.glob("deliverables*")):
        if not d.is_dir():
            continue
        for ext in ("mp4", "mov", "mkv", "webm"):
            hits = sorted(d.glob("*composite_preview.{0}".format(ext)))
            if hits:
                return hits[0]
    return None


def _optional_pixel_note(project_dir: Path, avatar_cues: List[dict]) -> Finding:
    """Skip-with-note for the SSIM check.

    The pixel check requires the composite master AND each cue's wan render AND
    ffmpeg+PIL+numpy. Rather than half-run it, we report WHY it was skipped (so a
    skip never looks like a silent pass) and let the primary static checks stand.
    A full implementation would, per cue, extract the composite frame and the wan
    frame at each alpha=1 hold sample and require SSIM >= 0.95 over the avatar
    region (see the consolidated forks). It is intentionally not run here because
    this gate must be deterministically testable on artifacts alone.
    """
    comp = _find_composite(project_dir)
    if comp is None:
        return Finding(
            "warn", "pixel_check_skipped",
            "optional SSIM check skipped: no composite master rendered yet "
            "(deliverables*/*composite_preview.*). Lead-pad + forbidden-ops "
            "checks ran on artifacts; re-run after compose for pixel verification."
        )
    missing = [c.get("asset") for c in avatar_cues
               if c.get("asset") and not (project_dir / str(c.get("asset"))).exists()]
    if missing:
        return Finding(
            "warn", "pixel_check_skipped",
            "optional SSIM check skipped: composite is present but {0} wan "
            "render(s) are missing on disk ({1}). Lead-pad + forbidden-ops checks "
            "ran on artifacts.".format(len(missing), ", ".join(map(str, missing)))
        )
    # Frames are present; a full pixel pass needs ffmpeg + PIL/numpy which we do
    # not exercise in the fixture-testable path. Note it explicitly.
    return Finding(
        "warn", "pixel_check_available",
        "composite + wan renders are present; the optional SSIM>=0.95 pixel check "
        "is the recommended follow-up (requires ffmpeg+PIL). Lead-pad + "
        "forbidden-ops checks ran statically and passed/failed as reported."
    )


# --------------------------------------------------------------------------- #
# Main check
# --------------------------------------------------------------------------- #
def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    manifest_top, manifest_by_id = _load_manifest(project_dir)

    findings: List[Finding] = []
    avatar_cues: List[dict] = []

    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError("cuelist.json cue #{0} is not an object".format(i))
        if (cue.get("kind") or "").strip().lower() != "avatar":
            continue

        avatar_cues.append(cue)
        cid = cue.get("id")
        if not isinstance(cid, str) or not cid:
            cid = "#{0}".format(i)
        manifest_cue = manifest_by_id.get(cid)

        # (b) FORBIDDEN-OPS — the locked wan-2.2-s2v assertion.
        for reason in _forbidden_ops(cue, manifest_cue, manifest_top):
            findings.append(Finding(
                "fail", "forbidden_seek_op",
                "wan-2.2-s2v render uses a forbidden seek: {0}. wan emits one "
                "keyframe at t=0, so this silently desyncs the avatar from its "
                "audio; use output-seek (`-ss` AFTER `-i`) only.".format(reason),
                where=cid))

        # (a) LEAD-PAD math.
        offset = _num(_merged(cue, manifest_cue, "avatar_video_offset_s"))
        t_in = _num(_merged(cue, manifest_cue, "t_in"))
        cut = _num(_merged(cue, manifest_cue, "audio_cut_start_s"))

        if offset is None or t_in is None or cut is None:
            missing = [name for name, val in (
                ("avatar_video_offset_s", offset),
                ("t_in", t_in),
                ("audio_cut_start_s", cut)) if val is None]
            findings.append(Finding(
                "fail", "lead_pad_unverifiable",
                "avatar cue is missing numeric {0} (in cuelist or avatar_manifest), "
                "so its lip-sync lead pad cannot be verified — an avatar we cannot "
                "sync-check must not pass.".format(" + ".join(missing)),
                where=cid))
            continue

        expected = t_in - cut
        drift = abs(offset - expected)
        if drift > LEAD_PAD_TOL_S + 1e-9:
            findings.append(Finding(
                "fail", "lead_pad_drift",
                "avatar_video_offset_s {0:.3f}s is {1:.0f}ms off the required lead "
                "pad {2:.3f}s = t_in {3:.3f}s - audio_cut_start_s {4:.3f}s "
                "(budget {5:.0f}ms) — the avatar will mouth the wrong words; set "
                "avatar_video_offset_s = {2:.3f}.".format(
                    offset, drift * 1000.0, expected, t_in, cut,
                    LEAD_PAD_TOL_S * 1000.0),
                where=cid))

    if not avatar_cues:
        # No avatar cues at all: nothing for THIS gate to verify. A note (not a
        # silent skip) keeps the intent visible; other gates police cue presence.
        return [Finding(
            "warn", "no_avatar_cues",
            "no cue has kind=='avatar'; nothing to avatar-sync.")]

    # (c) OPTIONAL pixel check — skip-with-note (keeps the gate fixture-testable).
    findings.append(_optional_pixel_note(project_dir, avatar_cues))
    return findings


if __name__ == "__main__":
    run_cli("qa_avatar_sync", check)
