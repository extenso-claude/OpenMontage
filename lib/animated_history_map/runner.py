"""The gate runner — the load-bearing spine.

Responsibilities:
  * run_gates()  — shell every hard_gate declared for a stage (or the whole
                   pipeline), capture REAL exit codes, and write a
                   machine-authored qa_report.json (validated against its
                   schema). The agent never authors this file.
  * run_stage()  — refuse to advance past a stage that requires_human_approval
                   without an approval artifact, then run that stage's gates.
  * assert_green_and_fresh()  — the render-lock: a final render is only legal if
                   qa_report.json is all-green AND its input_hashes still match
                   the artifacts on disk (a stale green from old inputs fails).

CLI:
  python -m lib.animated_history_map.runner run-gates  --pipeline P --project D [--stage S]
  python -m lib.animated_history_map.runner run-stage  --pipeline P --project D --stage S
  python -m lib.animated_history_map.runner check-lock --pipeline P --project D
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lib.pipeline_loader import load_pipeline  # noqa: E402
from schemas.artifacts import validate_artifact  # noqa: E402
from lib.animated_history_map import __version__  # noqa: E402

RUNNER_SIGNATURE = f"animated_history_map.runner@{__version__}"
GATE_TIMEOUT_S = 600

# Artifacts whose content the gates depend on. Hashed into the report so the
# render-lock can detect a report that went stale after the artifacts changed.
_HASH_CANDIDATES = [
    "artifacts/script.json",
    "artifacts/cuelist.json",
    "artifacts/asset_manifest.json",
    "artifacts/theme.json",
    "artifacts/geography.json",
    "artifacts/canonical_names.json",
    "hyperframes/index.html",
]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _compute_input_hashes(project_dir: Path) -> dict:
    hashes = {}
    rel_paths = list(_HASH_CANDIDATES)
    rel_paths += [
        str(p.relative_to(project_dir).as_posix())
        for p in sorted((project_dir / "artifacts" / "storyboard").glob("*.json"))
    ]
    for rel in rel_paths:
        p = project_dir / rel
        if p.is_file():
            hashes[rel] = _sha256(p)
    return hashes


def _collect_gates(manifest: dict, stage: Optional[str]) -> List[dict]:
    gates: List[dict] = []
    seen = set()
    for st in manifest.get("stages", []):
        name = st.get("name") or st.get("id")
        if stage is not None and name != stage:
            continue
        for g in st.get("hard_gates", []) or []:
            key = (g["name"], g["cmd"])
            if key in seen:
                continue
            seen.add(key)
            gates.append({**g, "_stage": name})
    return gates


def _stage_def(manifest: dict, stage: str) -> Optional[dict]:
    for st in manifest.get("stages", []):
        if (st.get("name") or st.get("id")) == stage:
            return st
    return None


# --------------------------------------------------------------------------- #
# run gates
# --------------------------------------------------------------------------- #
def run_gates(
    pipeline: str,
    project_dir: Path,
    stage: Optional[str] = None,
    write_report: bool = True,
) -> dict:
    project_dir = Path(project_dir).resolve()
    manifest = load_pipeline(pipeline)  # validates the manifest itself first
    gates = _collect_gates(manifest, stage)

    results = []
    for g in gates:
        # shlex.quote the substituted values: this repo (and many real projects)
        # live under a path with spaces (".../Claude code/Video Editing/..."). With
        # shell=True an unquoted {project_dir} is word-split by the shell and breaks
        # every gate's --project arg (exit 2, "unrecognized arguments").
        cmd = g["cmd"].format(
            project_dir=shlex.quote(str(project_dir)),
            pipeline=shlex.quote(str(pipeline)),
        )
        expect = int(g.get("expect_exit", 0))
        blocks = bool(g.get("blocks", True))
        start = datetime.now()
        try:
            proc = subprocess.run(
                cmd, shell=True, cwd=str(_REPO_ROOT),
                capture_output=True, text=True, timeout=GATE_TIMEOUT_S,
            )
            exit_code = proc.returncode
            out, err = proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            exit_code, out, err = 124, "", f"gate timed out after {GATE_TIMEOUT_S}s"
        dur_ms = (datetime.now() - start).total_seconds() * 1000.0
        results.append({
            "name": g["name"],
            "cmd": cmd,
            "exit_code": exit_code,
            "expected": expect,
            "passed": exit_code == expect,
            "blocks": blocks,
            "duration_ms": round(dur_ms, 1),
            "stdout_tail": (out or "")[-800:],
            "stderr_tail": (err or "")[-800:],
        })

    all_passed = all(r["passed"] for r in results if r["blocks"])

    report = {
        "pipeline": pipeline,
        "stage": stage or "ALL",
        "ran_at": datetime.now().isoformat(),
        "runner_signature": RUNNER_SIGNATURE,
        "input_hashes": _compute_input_hashes(project_dir),
        "gates": results,
        "all_passed": all_passed,
    }

    # Dogfood: the report must validate against its own schema.
    validate_artifact("animated_history_map_qa_report", report)

    if write_report:
        out_path = project_dir / "artifacts" / "qa_report.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
    return report


# --------------------------------------------------------------------------- #
# run stage (approval gate + gates)
# --------------------------------------------------------------------------- #
def run_stage(pipeline: str, project_dir: Path, stage: str) -> dict:
    project_dir = Path(project_dir).resolve()
    manifest = load_pipeline(pipeline)
    st = _stage_def(manifest, stage)
    if st is None:
        raise ValueError(f"stage {stage!r} not found in pipeline {pipeline!r}")

    blockers: List[str] = []
    if st.get("requires_human_approval"):
        approval = project_dir / "artifacts" / "approvals" / f"{stage}.json"
        if not approval.is_file():
            blockers.append(f"missing human approval: {approval}")
        else:
            try:
                with open(approval) as f:
                    if not json.load(f).get("approved") is True:
                        blockers.append(f"approval artifact present but approved != true: {approval}")
            except (json.JSONDecodeError, OSError) as exc:
                blockers.append(f"approval artifact unreadable: {exc}")

    report = run_gates(pipeline, project_dir, stage=stage) if not blockers else None
    ok = (not blockers) and (report is not None and report["all_passed"])
    return {"stage": stage, "ok": ok, "approval_blockers": blockers, "report": report}


# --------------------------------------------------------------------------- #
# render-lock
# --------------------------------------------------------------------------- #
def assert_green_and_fresh(pipeline: str, project_dir: Path) -> Tuple[bool, List[str]]:
    """The render-lock. True only if qa_report.json is all-green AND fresh."""
    project_dir = Path(project_dir).resolve()
    reasons: List[str] = []
    report_path = project_dir / "artifacts" / "qa_report.json"
    if not report_path.is_file():
        return False, ["no qa_report.json — gates were never run by the runner"]

    try:
        with open(report_path) as f:
            report = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        return False, [f"qa_report.json unreadable: {exc}"]

    try:
        validate_artifact("animated_history_map_qa_report", report)
    except Exception as exc:
        return False, [f"qa_report.json fails schema (not a genuine runner report): {exc}"]

    if not report.get("all_passed"):
        failed = [g["name"] for g in report.get("gates", []) if g.get("blocks") and not g.get("passed")]
        reasons.append(f"qa_report.all_passed is false; failing gates: {failed or '?'}")

    current = _compute_input_hashes(project_dir)
    stored = report.get("input_hashes", {})
    if current != stored:
        changed = sorted(set(current) ^ set(stored)) or [
            k for k in current if stored.get(k) != current.get(k)
        ]
        reasons.append(f"qa_report is STALE — inputs changed since gates ran: {changed}")

    return (len(reasons) == 0), reasons


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="animated_history_map.runner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run-gates", "run-stage", "check-lock"):
        sp = sub.add_parser(name)
        sp.add_argument("--pipeline", default="animated-history-map")
        sp.add_argument("--project", required=True)
        if name != "check-lock":
            sp.add_argument("--stage", default=None)
    args = ap.parse_args(argv)
    project = Path(args.project)

    if args.cmd == "run-gates":
        report = run_gates(args.pipeline, project, stage=args.stage)
        print(json.dumps(report, indent=2))
        return 0 if report["all_passed"] else 1

    if args.cmd == "run-stage":
        if not args.stage:
            print("run-stage requires --stage", file=sys.stderr)
            return 2
        res = run_stage(args.pipeline, project, args.stage)
        print(json.dumps({k: v for k, v in res.items() if k != "report"}, indent=2))
        if res["approval_blockers"]:
            for b in res["approval_blockers"]:
                print(f"BLOCKED: {b}", file=sys.stderr)
        return 0 if res["ok"] else 1

    if args.cmd == "check-lock":
        ok, reasons = assert_green_and_fresh(args.pipeline, project)
        if ok:
            print("RENDER-LOCK: GREEN — all blocking gates passed and report is fresh.")
            return 0
        print("RENDER-LOCK: BLOCKED", file=sys.stderr)
        for r in reasons:
            print(f"  - {r}", file=sys.stderr)
        return 1

    return 2


if __name__ == "__main__":
    sys.exit(_main())
