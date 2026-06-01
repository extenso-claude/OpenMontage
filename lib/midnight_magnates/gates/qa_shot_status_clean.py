"""qa_shot_status_clean — the self-QA loop is a real BLOCK, not prose.

The animation-director skill defines a per-shot ``qa_status`` and states "The
runner BLOCKS advancing past animation/render while any shot is ``pending_qa``"
— but until now that promise lived only in prose the runner ignored. A shot left
at ``pending_qa`` (or escalated to ``needs_human``, or never given a status at
all) would sail straight into render. This gate makes the self-QA verdict
load-bearing: the ONLY clean status is ``self_qa_pass``, and a ``self_qa_pass``
must have the rendered evidence behind it (the skill: "Never hand-set
``self_qa_pass`` without the clean rendered pass behind it").

``qa_status`` lives in a shot's brief / cuelist entry, so this gate reads BOTH:
  * artifacts/shot_status.json — the canonical per-shot self-QA index (REQUIRED;
    a missing/unreadable one is a blocking fail — a gate that cannot run must
    never silently pass), and
  * artifacts/cuelist.json — any cue that ALSO carries a ``qa_status`` is folded
    in (optional; absent cuelist is fine). A cue may not contradict its shot:
    if both name the same id, both must be clean.

Rule (fail):
  * `shot_pending_qa` — any shot/cue whose ``qa_status`` is not exactly
    ``self_qa_pass`` (``pending_qa`` / ``needs_human`` / missing / any other
    value). A blank/absent status is NOT a pass: an unreviewed shot blocks.
  * `self_qa_pass_without_evidence` — a shot/cue marked ``self_qa_pass`` whose
    ``evidence`` is missing, not an object, or lacks the proof the loop produces
    (a ``rendered_frame`` reference AND a ``pixel_gate_log``). A clean status
    with nothing behind it is exactly the hand-set pass the skill forbids.
  * `no_shots` — shot_status.json has a ``shots`` array but it is empty AND no
    cuelist cue carries a ``qa_status`` (nothing was self-QA'd; the loop never
    ran), which must not silently pass.

Reads:  <project>/artifacts/shot_status.json   (required)
        <project>/artifacts/cuelist.json        (optional)
Shapes (only the fields this gate reads):
    shot_status = {"shots": [
        {"shot_id", "qa_status",
         "evidence"?: {"rendered_frame", "pixel_gate_log", ...}}, ...]}
    cuelist     = {"cues":  [
        {"id", "qa_status"?, "evidence"?: {...}, ...}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

# The single status that lets a shot proceed. Everything else — including a
# missing/blank status — blocks, by design.
CLEAN_STATUS = "self_qa_pass"

# Evidence keys a real self-QA pass leaves behind: the frame it inspected and
# the per-tier pixel-gate log that exited 0 on the shot. Both must be present
# (and non-empty) for a self_qa_pass to be trusted.
REQUIRED_EVIDENCE_KEYS = ("rendered_frame", "pixel_gate_log")


def _status_of(entry: dict) -> str:
    """Normalized qa_status string ('' if absent / not a string)."""
    s = entry.get("qa_status")
    return s.strip().lower() if isinstance(s, str) else ""


def _evidence_problem(entry: dict) -> Optional[str]:
    """Return a human reason the self_qa_pass evidence is insufficient, else None.

    A real pass leaves a rendered_frame it inspected AND a pixel_gate_log that
    exited 0. A missing object, a non-object, or an empty/absent required key
    means there is no clean rendered pass behind the green status.
    """
    ev = entry.get("evidence")
    if ev is None:
        return "no evidence object"
    if not isinstance(ev, dict):
        return "evidence is not an object"
    missing = [k for k in REQUIRED_EVIDENCE_KEYS if not _nonempty(ev.get(k))]
    if missing:
        return "evidence missing " + " + ".join(missing)
    return None


def _nonempty(v) -> bool:
    """True for a present, non-empty value (string/list/dict/number/bool)."""
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, (list, dict)):
        return len(v) > 0
    # numbers / bools count as present (e.g. pixel_gate_log: 0 exit recorded as a
    # structured object is the normal case, but a bare value is still "present").
    return True


def _judge(entry: dict, ident: str, where: str) -> List[Finding]:
    """Apply the clean-status + evidence rule to one shot/cue entry."""
    status = _status_of(entry)
    if status != CLEAN_STATUS:
        shown = status if status else "<missing>"
        return [Finding(
            "fail", "shot_pending_qa",
            "qa_status is {0!r} (not {1!r}) — the self-QA loop has not produced a "
            "clean pass for this shot; the runner must not advance past "
            "animation/render".format(shown, CLEAN_STATUS),
            where=where,
        )]

    problem = _evidence_problem(entry)
    if problem is not None:
        return [Finding(
            "fail", "self_qa_pass_without_evidence",
            "marked {0!r} but {1} — a clean status with no rendered pass behind "
            "it (need a rendered_frame + a pixel_gate_log); never hand-set "
            "{0!r}".format(CLEAN_STATUS, problem),
            where=where,
        )]
    return []


def _load_cuelist_statuses(project_dir: Path) -> List[tuple]:
    """Return [(cue_id, cue_dict), ...] for cues that carry a qa_status.

    The cuelist is optional here — its qa_status is a supplementary place the
    same verdict can live. An absent cuelist is fine; a present-but-malformed
    one is a blocking fail (it cannot be trusted to be silently skipped).
    """
    path = project_dir / "artifacts" / "cuelist.json"
    if not path.exists():
        return []
    data = load_json(path)  # GateInputError on unreadable/invalid JSON
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")
    out: List[tuple] = []
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            raise GateInputError("cuelist.json cue #{0} is not an object".format(i))
        if "qa_status" in cue:  # only cues that opt into a status are judged here
            cid = str(cue.get("id") or "cue[{0}]".format(i))
            out.append((cid, cue))
    return out


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    # shot_status.json is the canonical, REQUIRED input. A missing/unreadable
    # one is a blocking fail (GateInputError) — a gate that cannot run must
    # never silently pass.
    data = load_json(project_dir / "artifacts" / "shot_status.json")
    shots = data.get("shots")
    if not isinstance(shots, list):
        raise GateInputError("shot_status.json has no 'shots' array")

    findings: List[Finding] = []
    for i, shot in enumerate(shots):
        if not isinstance(shot, dict):
            findings.append(Finding(
                "fail", "malformed_shot", "shot entry is not an object",
                where="shots[{0}]".format(i)))
            continue
        sid = str(shot.get("shot_id") or "shots[{0}]".format(i))
        findings.extend(_judge(shot, sid, where=sid))

    # Fold in any cuelist cue that ALSO carries a qa_status.
    cue_entries = _load_cuelist_statuses(project_dir)
    for cid, cue in cue_entries:
        findings.extend(_judge(cue, cid, where="cuelist::{0}".format(cid)))

    # Nothing was self-QA'd anywhere -> the loop never ran; don't pass on empty.
    if not shots and not cue_entries:
        findings.append(Finding(
            "fail", "no_shots",
            "shot_status.json 'shots' is empty and no cuelist cue carries a "
            "qa_status — the self-QA loop produced no verdict for any shot",
            where="artifacts/shot_status.json"))
    return findings


if __name__ == "__main__":
    run_cli("qa_shot_status_clean", check)
