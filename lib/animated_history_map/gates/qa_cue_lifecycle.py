"""qa_cue_lifecycle — every overlay must have a clean exit.

Catches the documented "object left awkwardly on screen, missed its exit" bug:
an overlay whose end_s runs past the end of the timeline (so it never gets
torn down and sits there over the outro), or a non-UI overlay that lingers for
an absurdly long time because someone forgot to give it an exit beat.

Rules (locked, all severity "fail"):
    * start_s < 0                          -> a cue can't begin before the video
    * end_s <= start_s                     -> zero/negative on-screen duration
    * end_s > master_end + 0.5             -> orphaned past the timeline; never exits
    * (end_s - start_s) > 40s              -> lingers forever (NON-persistent kinds only)

master_end = voice_report.total_duration_s if that artifact is present,
otherwise the latest end_s across all cues (the timeline can't be shorter than
its last cue). The 0.5s slack absorbs render tail-padding.

Persistent UI kinds legitimately span the whole timeline, so they are EXEMPT
from the 40s linger check (but NOT from the past-timeline / ordering checks):
    chapter_subject_badge_swap, year_card_update, chapter_timeline_update,
    structure_tree_node_fill, vignette_breath, paper_texture

Reads:  <project>/artifacts/cuelist.json          (required)
        <project>/artifacts/voice_report.json     (optional)
Shape:  {"cues": [{"id","kind","start_s","end_s", ...}, ...]}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

# Tail-padding slack: a cue may legitimately end a hair past the measured
# timeline end (render padding, fade tails) without being "orphaned".
END_SLACK_S = 0.5

# Hard ceiling on how long a transient overlay may sit on screen before it is
# considered a forgotten-exit linger.
MAX_LINGER_S = 40.0

# Persistent UI that is meant to live for the whole video — these own the
# screen by design, so the linger ceiling does not apply to them.
PERSISTENT_KINDS = frozenset({
    "chapter_subject_badge_swap",
    "year_card_update",
    "chapter_timeline_update",
    "structure_tree_node_fill",
    "vignette_breath",
    "paper_texture",
})


def _master_end(project_dir: Path, cues: List[dict]) -> Optional[float]:
    """Resolve the timeline end. Prefer the voice report's total duration; fall
    back to the latest cue end. Returns None only if neither is determinable."""
    vr_path = project_dir / "artifacts" / "voice_report.json"
    if vr_path.exists():
        vr = load_json(vr_path)  # present-but-unreadable -> GateInputError (blocks)
        total = vr.get("total_duration_s")
        if isinstance(total, (int, float)):
            return float(total)
        # Present but malformed: don't silently fall back to a value the bad cue
        # itself defines, which would mask the orphan. Treat as a hard fail.
        raise GateInputError(
            f"voice_report.json present but total_duration_s is missing/non-numeric: {vr_path}"
        )

    ends = [
        float(c["end_s"])
        for c in cues
        if isinstance(c.get("end_s"), (int, float))
    ]
    return max(ends) if ends else None


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    master_end = _master_end(project_dir, cues)

    findings: List[Finding] = []
    for i, cue in enumerate(cues):
        cid = cue.get("id", f"#{i}")
        start, end = cue.get("start_s"), cue.get("end_s")

        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            findings.append(Finding(
                "fail", "missing_timing",
                "cue needs numeric start_s/end_s to verify its lifecycle",
                where=cid,
            ))
            continue
        start = float(start)
        end = float(end)

        if start < 0:
            findings.append(Finding(
                "fail", "negative_start",
                f"start_s={start:.2f} is before the video begins",
                where=cid,
            ))

        if end <= start:
            findings.append(Finding(
                "fail", "non_positive_duration",
                f"end_s={end:.2f} <= start_s={start:.2f}; cue has no on-screen life",
                where=cid,
            ))
            # Duration-dependent checks below are meaningless once this is broken.
            continue

        # Orphaned past the timeline: the overlay never gets torn down and is
        # left sitting on the final frame ("missed its exit").
        if master_end is not None and end > master_end + END_SLACK_S:
            findings.append(Finding(
                "fail", "exit_past_timeline",
                f"end_s={end:.2f} runs past timeline end {master_end:.2f}"
                f" (+{END_SLACK_S:.1f}s slack); overlay never exits the screen",
                where=cid,
            ))

        # Linger: a transient overlay sitting on screen far too long. Persistent
        # UI is exempt — it is supposed to own the screen for the whole video.
        kind = (cue.get("kind") or "")
        if kind not in PERSISTENT_KINDS:
            duration = end - start
            if duration > MAX_LINGER_S:
                findings.append(Finding(
                    "fail", "lingers_too_long",
                    f"{kind or 'cue'} stays on screen {duration:.1f}s"
                    f" (> {MAX_LINGER_S:.0f}s); likely a missed exit",
                    where=cid,
                ))

    return findings


if __name__ == "__main__":
    run_cli("qa_cue_lifecycle", check)
