"""Gap-coverage QA for HyperFrames master compositions.

Walks a master `index.html`, parses every `.clip` element with `data-start` +
`data-duration` (visual tracks only — excludes audio tracks), and reports any
time range with no active clip. Built because `npx hyperframes lint` and
`validate` don't catch coverage gaps — they're not contract violations, but in
a continuous-narration master any visual gap is a bug (the frame goes black).

Mandatory before declaring any sequenced/master composition ready to render.
Mentioned in `skills/meta/visual-design-quality.md` → AI Image Generation Rules
and indexed in `MEMORY.md` as `gap_coverage_qa_required`.

Usage:
    python lib/hf_coverage_qa.py <path/to/index.html>
    python lib/hf_coverage_qa.py <path/to/index.html> --threshold 0.05

Exits non-zero if any visual gap > threshold seconds exists. Default threshold
is 0.05s (anything bigger than a frame at 24fps is a real gap).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Match any <div ... class="... clip ..." ... data-start="X" data-duration="Y" ... data-track-index="Z" ...>
# Tolerant to attribute order.
CLIP_RE = re.compile(
    r'<(?:div|svg|img|video|audio)\b'                # tag
    r'[^>]*?\bclass="[^"]*\bclip\b[^"]*"'           # class includes "clip"
    r'[^>]*>',
    re.DOTALL,
)
ATTR_RE = re.compile(r'\b(data-start|data-duration|data-track-index|data-composition-id|id)="([^"]+)"')

# Audio is on a known high track index by convention; skip those for visual coverage.
# Anything with data-track-index in {0,1,2,3,4,5,6} counts as visual unless audio_only.
AUDIO_TRACK_INDICES = {20}  # by convention in this project; adjust if needed


def parse_clips(html: str) -> list[dict]:
    """Extract every .clip element as a dict of attrs."""
    clips: list[dict] = []
    for m in CLIP_RE.finditer(html):
        tag = m.group(0)
        attrs = dict(ATTR_RE.findall(tag))
        if "data-start" not in attrs or "data-duration" not in attrs:
            continue
        clips.append({
            "id": attrs.get("id") or attrs.get("data-composition-id") or "?",
            "start": float(attrs["data-start"]),
            "duration": float(attrs["data-duration"]),
            "track": int(attrs.get("data-track-index", "0")),
            "is_audio": tag.lstrip("<").startswith("audio") or
                         int(attrs.get("data-track-index", "0")) in AUDIO_TRACK_INDICES,
        })
    return clips


def find_gaps(clips: list[dict], total_duration: float, threshold: float) -> list[tuple[float, float, float]]:
    """Walk visual clips sorted by start, find gaps > threshold.

    Returns list of (gap_start, gap_end, gap_duration).
    Treats clips on ANY visual track as covering — a gap means NO visual clip
    is active across any track.
    """
    visual = [c for c in clips if not c["is_audio"]]
    if not visual:
        return [(0.0, total_duration, total_duration)]

    # Build coverage intervals
    intervals = sorted([(c["start"], c["start"] + c["duration"]) for c in visual])

    # Merge overlapping/adjacent intervals
    merged: list[tuple[float, float]] = []
    for s, e in intervals:
        if merged and s <= merged[-1][1] + 1e-6:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # Find gaps
    gaps: list[tuple[float, float, float]] = []
    cursor = 0.0
    for s, e in merged:
        if s - cursor > threshold:
            gaps.append((cursor, s, s - cursor))
        cursor = max(cursor, e)
    if total_duration - cursor > threshold:
        gaps.append((cursor, total_duration, total_duration - cursor))

    return gaps


def check(path: Path, threshold: float = 0.05, as_json: bool = False) -> int:
    html = path.read_text()

    # Find master data-duration on the root composition
    root_match = re.search(
        r'<div[^>]*data-composition-id="[^"]+"[^>]*data-duration="([\d.]+)"',
        html, re.DOTALL,
    )
    if not root_match:
        # Try other attribute orderings
        for m in re.finditer(r'<div[^>]*data-composition-id="[^"]+"[^>]*>', html, re.DOTALL):
            d = re.search(r'data-duration="([\d.]+)"', m.group(0))
            if d:
                root_match = d
                break
    if not root_match:
        print("ERROR: could not find root data-duration", file=sys.stderr)
        return 2
    total = float(root_match.group(1))

    clips = parse_clips(html)
    gaps = find_gaps(clips, total, threshold)

    visual_clips = [c for c in clips if not c["is_audio"]]
    audio_clips = [c for c in clips if c["is_audio"]]

    if as_json:
        print(json.dumps({
            "file": str(path),
            "master_duration": total,
            "visual_clip_count": len(visual_clips),
            "audio_clip_count": len(audio_clips),
            "threshold_s": threshold,
            "gap_count": len(gaps),
            "gaps": [{"start": s, "end": e, "duration_s": d} for s, e, d in gaps],
            "ok": len(gaps) == 0,
        }, indent=2))
    else:
        print(f"=== Coverage QA: {path} ===")
        print(f"  master duration:       {total:.2f}s")
        print(f"  visual clips parsed:   {len(visual_clips)}")
        print(f"  audio clips (skipped): {len(audio_clips)}")
        print(f"  gap threshold:         > {threshold}s")
        if gaps:
            print(f"\n  FOUND {len(gaps)} VISUAL GAP(S):")
            for s, e, d in gaps:
                print(f"    {s:6.2f}s → {e:6.2f}s   ({d:.2f}s of black frame)")
            print("\n  Fix: extend the previous shot's data-duration OR add a clip to fill the gap.")
        else:
            print(f"\n  ✓ No visual gaps. Master is continuously covered.")

    return 1 if gaps else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("file", type=Path, help="Path to HyperFrames index.html")
    p.add_argument("--threshold", type=float, default=0.05,
                   help="Gap threshold in seconds (default 0.05 = one frame at ~20fps)")
    p.add_argument("--json", action="store_true", help="JSON output")
    args = p.parse_args()
    sys.exit(check(args.file, args.threshold, args.json))


if __name__ == "__main__":
    main()
