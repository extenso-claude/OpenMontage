"""qa_skill_gate_refs — forbid phantom gates (no rule may live only as prose).

A rule the director skills *describe* but that has no runnable gate behind it is a
phantom: the prose claims the pipeline checks something, the swarm trusts it, and
nothing actually enforces it. The Lincoln-era qa-director skill is the proof — it
lists "all 17 gates" as `scripts/qa_timing_anchors.py`, `scripts/qa_gap_coverage.py`,
... none of which exist as files and none of which the runner can shell. That is the
exact "rule lives only in prose" hole this gate closes: every `qa_*` token a skill
cites MUST resolve to a real gate module on disk, written in the import form the
runner uses — never as a dead `scripts/qa_*.py` path.

Rule (fail):
  Scan every ``*.md`` under the target skills dir for ``qa_[a-z_]+`` tokens. For
  each DISTINCT (token, occurrence-form) cited:
    * ``scripts_path_gate`` — the token is written as a ``scripts/qa_*.py`` path.
      The whole pipeline runs gates as ``lib.midnight_magnates.gates.<name>``; a
      ``scripts/`` path points at a file the runner never executes (and, in this
      fork, does not even exist). This form is forbidden regardless of whether a
      same-named module happens to exist.
    * ``phantom_gate`` — the token is cited as a bare gate name but there is no
      file ``lib/midnight_magnates/gates/<token>.py``. The rule lives only as
      prose; nothing enforces it.
  A skill that cites only real, import-form gate names passes.

To avoid false positives on incidental ``qa_``-prefixed words (``qa_report.json``,
``gates_passed``, code/JSON identifiers), only tokens that read as a gate citation
are considered: either a ``scripts/qa_*.py`` path, or a ``qa_<name>`` token that is
NOT immediately followed by a word character / ``.`` (so ``qa_report.json`` and
``qa_status:`` are ignored, while ``qa_min_hold`` and ``qa_drift,`` are cited). The
scan is deliberately conservative — its job is to catch named-but-unbuilt gates, not
to lint every string that starts with ``qa_``.

A gate that cannot run must never silently pass:
    * the skills dir does not exist / is not a directory  -> GateInputError
    * the skills dir contains no ``*.md`` files            -> GateInputError
    * a cited ``*.md`` cannot be read                      -> GateInputError

Reads:   the canonical skills dir (see --skills-dir below)
Checks:  lib/midnight_magnates/gates/<token>.py  (this gate's own directory)

Arg:
    --skills-dir PATH   Directory of director skills to scan.

        * When PASSED EXPLICITLY (the production case), it is resolved against the
          CURRENT WORKING DIRECTORY — which the runner sets to the repo root —
          unless it is already absolute. The manifest therefore passes
          ``--skills-dir skills/pipelines/midnight-magnates-doc`` and the gate
          scans the canonical ``<repo>/skills/pipelines/midnight-magnates-doc``
          tree, NOT a (nonexistent) ``<project>/skills`` tree. This is the bug the
          path fix closes: an explicit skills dir is a path the operator gives in
          the shell, so CWD-relative (or absolute) is the only sane contract.

        * When OMITTED, it falls back to ``<project>/skills/pipelines/
          midnight-magnates-doc`` (project-relative). This keeps the self-contained
          regression fixtures working: they stage their ``.md`` under
          ``<project>/skills/...`` and invoke the gate with only ``--project``.

    --project is still resolved/honored by the shared harness (used for the
    relative-path display in findings and the default fallback above).

Allowed: Python stdlib only.
"""

from __future__ import annotations

import re
import sys
from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, run_cli

# Canonical skills subtree. An EXPLICIT --skills-dir is resolved against CWD (the
# runner sets CWD to the repo root) or taken absolute; when --skills-dir is OMITTED
# this same relative path is resolved against --project (keeps fixtures self-
# contained — see the module docstring).
DEFAULT_SKILLS_DIR = "skills/pipelines/midnight-magnates-doc"

# The directory every real gate module lives in — this file's own directory. A
# cited token is "real" iff <this dir>/<token>.py exists.
_GATES_DIR = Path(__file__).resolve().parent

# A gate citation written as a forbidden scripts/ path, e.g. `scripts/qa_foo.py`.
# Captures the bare gate name (qa_foo) for the existence check / message.
_SCRIPTS_PATH_RE = re.compile(r"scripts/(qa_[a-z_]+)\.py")

# A bare gate-name citation: a qa_<name> token NOT immediately followed by a word
# char or a '.' (so `qa_report.json`, `qa_status_v2` continuations are excluded)
# and NOT immediately preceded by a word char (so `xqa_foo` is not a citation).
# The trailing name is normalized to drop any trailing underscore.
_BARE_TOKEN_RE = re.compile(r"(?<!\w)(qa_[a-z_]*[a-z])(?![\w.])")


def _norm_gate_name(name: str) -> str:
    """Strip a trailing underscore so `qa_foo_` resolves like `qa_foo`."""
    return name.rstrip("_")


def _gate_file_exists(name: str) -> bool:
    return (_GATES_DIR / (name + ".py")).is_file()


def _parse_skills_dir(argv: Optional[List[str]]) -> Tuple[Optional[str], List[str]]:
    """Pull an optional ``--skills-dir VALUE`` (or ``--skills-dir=VALUE``) out of
    ``argv`` and return (skills_dir_or_None, remaining_argv).

    Returns ``None`` for skills_dir when the flag is ABSENT — that sentinel lets
    check() distinguish "operator gave an explicit dir" (resolve against CWD/abs)
    from "use the project-relative default". A passed-but-empty value is still an
    error.

    The shared run_cli parser only knows --project/--pipeline/--json, so this
    gate-specific flag is consumed here and the rest is handed to run_cli intact
    (no edits to the shared contract, no unknown-arg crash)."""
    source = list(sys.argv[1:] if argv is None else argv)
    skills_dir: Optional[str] = None
    out: List[str] = []
    i = 0
    while i < len(source):
        tok = source[i]
        if tok == "--skills-dir":
            if i + 1 >= len(source):
                raise GateInputError("--skills-dir requires a value")
            skills_dir = source[i + 1]
            i += 2
            continue
        if tok.startswith("--skills-dir="):
            skills_dir = tok.split("=", 1)[1]
            i += 1
            continue
        out.append(tok)
        i += 1
    if skills_dir is not None and not skills_dir.strip():
        raise GateInputError("--skills-dir value is empty")
    return skills_dir, out


def _iter_citations(text: str):
    """Yield (kind, gate_name, snippet) for each gate citation in ``text``.

    kind is "scripts" (a scripts/qa_*.py path) or "bare" (a qa_<name> token).
    A token already captured as a scripts/ path on the same span is not also
    yielded as a bare token (the scripts/ verdict wins for that occurrence)."""
    consumed_spans: List[Tuple[int, int]] = []
    for m in _SCRIPTS_PATH_RE.finditer(text):
        consumed_spans.append(m.span())
        yield "scripts", _norm_gate_name(m.group(1)), m.group(0)
    for m in _BARE_TOKEN_RE.finditer(text):
        s, e = m.span()
        # Skip if this token sits inside a scripts/qa_*.py match already reported.
        if any(cs <= s and e <= ce for cs, ce in consumed_spans):
            continue
        yield "bare", _norm_gate_name(m.group(1)), m.group(0)


def _resolve_skills_dir(project_dir: Path, skills_arg: Optional[str]) -> Path:
    """Resolve the directory to scan.

    EXPLICIT --skills-dir  -> absolute path as-is, else CWD-relative (the runner
                              runs gates with CWD = repo root, so the manifest's
                              ``skills/pipelines/midnight-magnates-doc`` lands on
                              the canonical repo tree — NOT under <project>).
    OMITTED (sentinel None) -> <project>/<DEFAULT_SKILLS_DIR> (project-relative),
                              which is what the self-contained fixtures stage.
    """
    if skills_arg is None:
        return (project_dir / DEFAULT_SKILLS_DIR).resolve()
    p = Path(skills_arg)
    base = p if p.is_absolute() else (Path.cwd() / p)
    return base.resolve()


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    skills_arg = getattr(args, "skills_dir", None)
    skills_dir = _resolve_skills_dir(project_dir, skills_arg)

    if not skills_dir.is_dir():
        raise GateInputError(
            "required input not found: {0} (no skills directory to scan for "
            "phantom gate references)".format(skills_dir)
        )
    md_files = sorted(skills_dir.rglob("*.md"))
    if not md_files:
        raise GateInputError(
            "no *.md files under {0} — a gate that cannot read the skill prose it "
            "polices must not silently pass".format(skills_dir)
        )

    findings: List[Finding] = []
    # De-duplicate so one phantom cited ten times reports once per (file, name).
    seen: set = set()
    for md in md_files:
        try:
            text = md.read_text(errors="strict")
        except (OSError, UnicodeDecodeError) as exc:
            raise GateInputError("could not read skill file {0}: {1}".format(md, exc))
        # Display path anchored at the skills dir (always a parent of md via
        # rglob). project_dir is NOT a valid anchor once --skills-dir points at
        # the repo tree (production), so relative_to(project_dir) would raise.
        rel = str(md.relative_to(skills_dir))
        for kind, name, snippet in _iter_citations(text):
            if kind == "scripts":
                key = ("scripts", rel, name)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(Finding(
                    "fail", "scripts_path_gate",
                    "skill cites gate {0!r} as a scripts/ path ({1!r}); gates run as "
                    "lib.midnight_magnates.gates.{0} — a scripts/qa_*.py path points at "
                    "a file the runner never executes. Rewrite it as the import-form "
                    "gate name (and build the gate if it does not exist).".format(
                        name, snippet),
                    where=rel,
                ))
            else:  # bare token
                if _gate_file_exists(name):
                    continue  # cites a real, import-form gate -> fine
                key = ("phantom", rel, name)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(Finding(
                    "fail", "phantom_gate",
                    "skill cites gate {0!r} but there is no file "
                    "lib/midnight_magnates/gates/{0}.py — the rule lives only as prose "
                    "(nothing enforces it). Build the gate or stop citing it.".format(name),
                    where=rel,
                ))
    return findings


if __name__ == "__main__":
    _skills_dir, _rest = _parse_skills_dir(None)

    def _check(project_dir: Path, args: Namespace) -> List[Finding]:
        # Inject the consumed --skills-dir onto args for check() to read.
        setattr(args, "skills_dir", _skills_dir)
        return check(project_dir, args)

    run_cli("qa_skill_gate_refs", _check, argv=_rest)
