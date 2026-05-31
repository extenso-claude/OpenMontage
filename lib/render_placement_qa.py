"""Post-render placement QA: detect black-band positioning bugs.

Catches the common failure mode where a hero image is rendered into a band
(top/bottom strip stays pure black) instead of filling the canvas — a silent
CSS/composition mistake that the agent visually misses if rendered frames
happen to have dim sky/floor regions.

Usage from a compose-director skill (or video_compose post-render):

    from lib.render_placement_qa import check_clip, check_dir
    finding = check_clip(Path("renders/final.mp4"))
    if finding["flag"]:
        # surface to user — composition has a placement bug
        ...

API:
    check_clip(mp4) -> dict with top_near_black, bottom_near_black, flag (bool)
    check_dir(dir_path, pattern="*.mp4") -> list of findings

A flag fires when ≥85% of pixels in the top 80 rows or bottom 80 rows of the
mid-frame are near-black (RGB all < 22). That's a near-impossible state for
a properly-composited image-led clip (even noir scenes have stars or texture
in the top region) — so any flag indicates a real bug.
"""
from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable


NEAR_BLACK_THRESHOLD = 8   # RGB component value below this = pure-black (#000-#070707).
                           # Tight threshold so legitimate noir backdrops (#080c16 navy etc.) don't flag.
ROW_SAMPLE_COUNT = 80      # rows from top and bottom to sample
FLAG_THRESHOLD = 0.92      # ≥92% pure-black pixels in band = flag (with low variance, see below)
VARIANCE_THRESHOLD = 4     # max stddev across sampled pixels for a band to be "uniformly black".
                           # A real black band has stddev ≈ 0. A dark noir backdrop with stars/texture
                           # has stddev > 4 even when most pixels are dark.


def _extract_frame(mp4: Path, time_s: float = 2.5) -> Path:
    """Extract a single frame at time_s as a temp JPG. Caller must unlink."""
    tmp = Path(tempfile.mkstemp(suffix=".jpg")[1])
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-ss", f"{time_s}", "-i", str(mp4),
         "-vframes", "1", "-q:v", "3", str(tmp)],
        check=True,
    )
    return tmp


def _band_stats(jpg: Path, *, band: str = "top", rows: int = ROW_SAMPLE_COUNT) -> tuple[float, float]:
    """Return (near_black_ratio, stddev) for the top/bottom band of jpg.

    A true placement bug has both metrics extreme: near_black_ratio ≈ 1.0
    (almost every pixel is #000-#070707) AND stddev ≈ 0 (uniform black band).
    A dark noir backdrop has high near_black_ratio but nonzero stddev because
    stars / texture / grain inject brighter pixels.
    """
    tmp = Path(tempfile.mkstemp(suffix=".ppm")[1])
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(jpg),
             "-vf", "scale=320:-1,format=rgb24", "-f", "image2", str(tmp)],
            check=True,
        )
        data = tmp.read_bytes()
        i = 0
        while data[i:i + 1] != b"\n":
            i += 1
        i += 1

        def _read_token(i):
            while data[i:i + 1] in (b" ", b"\n", b"\t"):
                i += 1
            j = i
            while data[j:j + 1] not in (b" ", b"\n", b"\t"):
                j += 1
            return data[i:j].decode(), j

        w_s, i = _read_token(i)
        h_s, i = _read_token(i)
        _m_s, i = _read_token(i)
        i += 1
        W, H = int(w_s), int(h_s)
        row_range = range(0, min(rows, H)) if band == "top" else range(max(0, H - rows), H)
        near_black = 0
        sampled = 0
        sum_v = 0
        sum_v2 = 0
        for r in row_range:
            row_start = i + r * W * 3
            for c in range(0, W, 4):
                px = row_start + c * 3
                v = (data[px] + data[px + 1] + data[px + 2]) // 3  # luminance approx
                if (data[px] < NEAR_BLACK_THRESHOLD
                        and data[px + 1] < NEAR_BLACK_THRESHOLD
                        and data[px + 2] < NEAR_BLACK_THRESHOLD):
                    near_black += 1
                sum_v += v
                sum_v2 += v * v
                sampled += 1
        if not sampled:
            return 0.0, 0.0
        mean = sum_v / sampled
        var = (sum_v2 / sampled) - (mean * mean)
        stddev = var ** 0.5 if var > 0 else 0.0
        return near_black / sampled, stddev
    finally:
        tmp.unlink(missing_ok=True)


def check_clip(mp4: Path, *, time_s: float = 2.5) -> dict:
    """Return a finding dict for one clip.

    A clip is flagged only when BOTH conditions hit:
      - near_black_ratio in a band > FLAG_THRESHOLD (≥92% pure-black pixels)
      - stddev in that band < VARIANCE_THRESHOLD (uniform — no stars/texture)

    Two conditions together identify a true placement bug while letting
    legitimate noir backdrops (which have stars/grain texture) pass.
    """
    frame = _extract_frame(mp4, time_s=time_s)
    try:
        top_ratio, top_std = _band_stats(frame, band="top")
        bot_ratio, bot_std = _band_stats(frame, band="bottom")
        top_flag = top_ratio > FLAG_THRESHOLD and top_std < VARIANCE_THRESHOLD
        bot_flag = bot_ratio > FLAG_THRESHOLD and bot_std < VARIANCE_THRESHOLD
        return {
            "file": str(mp4),
            "top_near_black": round(top_ratio, 3),
            "top_stddev": round(top_std, 2),
            "bottom_near_black": round(bot_ratio, 3),
            "bottom_stddev": round(bot_std, 2),
            "flag": top_flag or bot_flag,
        }
    finally:
        frame.unlink(missing_ok=True)


def check_dir(dir_path: Path, *, pattern: str = "*.mp4") -> list[dict]:
    """Check every clip in a directory. Returns list of findings."""
    findings = []
    for mp4 in sorted(dir_path.glob(pattern)):
        try:
            findings.append(check_clip(mp4))
        except Exception as e:
            findings.append({"file": str(mp4), "error": str(e), "flag": True})
    return findings


def format_summary(findings: Iterable[dict]) -> str:
    """Human-readable summary string."""
    findings = list(findings)
    flagged = [f for f in findings if f.get("flag")]
    if not flagged:
        return f"placement QA: {len(findings)} clips checked, 0 flagged ✓"
    lines = [f"placement QA: {len(flagged)}/{len(findings)} clips FLAGGED — placement bug suspected:"]
    for f in flagged:
        if "error" in f:
            lines.append(f"  {Path(f['file']).name}: ERROR {f['error']}")
        else:
            lines.append(
                f"  {Path(f['file']).name}: top={f['top_near_black']:.2f} bottom={f['bottom_near_black']:.2f}"
            )
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import json

    p = argparse.ArgumentParser()
    p.add_argument("path", help="path to .mp4 or a directory containing .mp4 files")
    p.add_argument("--json", action="store_true", help="emit JSON instead of summary")
    args = p.parse_args()
    target = Path(args.path)
    if target.is_file():
        findings = [check_clip(target)]
    else:
        findings = check_dir(target)
    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        print(format_summary(findings))
