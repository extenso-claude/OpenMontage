"""qa_generation_budget — surface the projected paid-generation bill and BLOCK
runaway spend that no one signed off on.

The bug this prevents: a long episode quietly racks up a large paid-generation
bill before anyone looks at the number. The wan-2.2-s2v avatar is the priciest
element by far (~$0.017 per audio-second ≈ $1/min of avatar), and AI-generated
images stack on top. A 30-minute episode with heavy avatar narration can run
into the tens of dollars without a single approval. This gate honours the
Decision Communication Contract: announce the projected cost up front, and
require an explicit `budget_approved: true` before any spend that exceeds the
cap proceeds. No silent, consequential spend.

Cost model (per the locked pricing):
    * avatar cue (kind == "avatar"):  (t_out - t_in) seconds × $0.017/sec
        — wan-2.2-s2v, the channel-locked avatar generator.
    * AI-generated image cue:          $0.04 each
        — a cue counts as AI-generated when it carries
          sourcing.generation_reason (a documented generation decision) OR a
          top-level "generator" field.
    * other generated kinds:           $0 for now (procedural / library assets
          are free; only metered paid generation is counted).

Logic:
    cap      = cuelist.get("budget_cap_usd", 50.0)
    approved = bool(cuelist.get("budget_approved", False))
    projected_usd = sum of the per-category costs above.
    Always writes <project>/artifacts/cost_estimate.json with the per-category
    breakdown + total (the announce half of the contract).
    * projected_usd > cap and not approved  -> "fail" / "budget_exceeded"
      (message names the total, the cap, and that budget_approved:true is the
      gate to clear it).
    * otherwise                             -> "warn" / "cost_estimate"
      (advisory — the projected total, exit 0).

Reads:  <project>/artifacts/cuelist.json
Shape:  {"cues": [{"id", "kind", "t_in", "t_out", ...,
                    "sourcing"?: {"generation_reason"?}, "generator"?: ...}, ...],
         "budget_cap_usd"?: float, "budget_approved"?: bool}
Writes: <project>/artifacts/cost_estimate.json
"""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import List, Optional

from ._contract import Finding, GateInputError, load_json, run_cli

# Locked pricing for metered paid generation.
AVATAR_USD_PER_SECOND = 0.017  # wan-2.2-s2v, billed per audio-second
AI_IMAGE_USD_EACH = 0.04       # one AI-generated still
DEFAULT_CAP_USD = 50.0


def _num(value) -> Optional[float]:
    """Return value as float, or None if it is not a real number.

    bool is an int subclass, so reject it explicitly — a True t_out is not 1s.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _is_ai_generated_image(cue: dict) -> bool:
    """A cue counts as a paid AI image if it documents a generation decision.

    Either a non-empty ``sourcing.generation_reason`` (the documented-generation
    convention used by qa_asset_sourcing) or a top-level ``generator`` field.
    """
    if cue.get("generator"):
        return True
    sourcing = cue.get("sourcing")
    if isinstance(sourcing, dict) and sourcing.get("generation_reason"):
        return True
    return False


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    data = load_json(project_dir / "artifacts" / "cuelist.json")
    cues = data.get("cues")
    if not isinstance(cues, list):
        raise GateInputError("cuelist.json has no 'cues' array")

    avatar_usd = 0.0
    avatar_seconds = 0.0
    avatar_count = 0
    image_usd = 0.0
    image_count = 0

    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            continue
        cid = cue.get("id", f"#{i}")
        kind = (cue.get("kind") or "").strip().lower()

        if kind == "avatar":
            t_in = _num(cue.get("t_in"))
            t_out = _num(cue.get("t_out"))
            if t_in is None or t_out is None:
                raise GateInputError(
                    f"avatar cue '{cid}' is missing numeric t_in/t_out — cannot "
                    f"project its generation cost"
                )
            dur = t_out - t_in
            if dur < 0:
                raise GateInputError(
                    f"avatar cue '{cid}' has t_out < t_in (negative duration)"
                )
            avatar_seconds += dur
            avatar_usd += dur * AVATAR_USD_PER_SECOND
            avatar_count += 1
        elif _is_ai_generated_image(cue):
            image_usd += AI_IMAGE_USD_EACH
            image_count += 1
        # other kinds: $0 (procedural / library — not metered here)

    projected_usd = round(avatar_usd + image_usd, 4)
    cap = _num(data.get("budget_cap_usd"))
    if cap is None:
        cap = DEFAULT_CAP_USD
    approved = bool(data.get("budget_approved", False))

    # Announce: always write the breakdown, whatever the verdict.
    estimate = {
        "total_usd": projected_usd,
        "budget_cap_usd": round(cap, 4),
        "budget_approved": approved,
        "over_cap": projected_usd > cap,
        "categories": {
            "avatar": {
                "cue_count": avatar_count,
                "seconds": round(avatar_seconds, 3),
                "usd_per_second": AVATAR_USD_PER_SECOND,
                "total_usd": round(avatar_usd, 4),
            },
            "ai_image": {
                "cue_count": image_count,
                "usd_each": AI_IMAGE_USD_EACH,
                "total_usd": round(image_usd, 4),
            },
        },
    }
    out_path = project_dir / "artifacts" / "cost_estimate.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(estimate, f, indent=2)

    breakdown = (
        f"avatar {avatar_count} cue(s) / {avatar_seconds:.1f}s = ${avatar_usd:.2f}; "
        f"AI images {image_count} × ${AI_IMAGE_USD_EACH:.2f} = ${image_usd:.2f}"
    )

    if projected_usd > cap and not approved:
        return [Finding(
            "fail", "budget_exceeded",
            f"projected generation spend ${projected_usd:.2f} exceeds the cap "
            f"${cap:.2f} ({breakdown}). Consequential spend must be announced and "
            f"approved: set \"budget_approved\": true in cuelist.json (or raise "
            f"\"budget_cap_usd\") to authorise this run.",
            where="artifacts/cost_estimate.json",
        )]

    # Advisory: announce the projected total (exit 0).
    note = " (approved)" if approved and projected_usd > cap else ""
    return [Finding(
        "warn", "cost_estimate",
        f"projected generation spend ${projected_usd:.2f} of ${cap:.2f} cap{note} "
        f"— {breakdown}",
        where="artifacts/cost_estimate.json",
    )]


if __name__ == "__main__":
    run_cli("qa_generation_budget", check)
