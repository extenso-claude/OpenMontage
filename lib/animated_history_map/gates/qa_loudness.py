"""qa_loudness — the final mix must sit at broadcast loudness, not hot/clipping.

A render can pass every visual and timing gate and still ship a mix that is
either crushed-loud (fatiguing, and an inauthentic-content signal on a sleep
channel) or peaking into distortion. "Final" loudness is the last thing the
viewer's ears judge, and lint/validate never listen — so this gate measures the
finished file against EBU R128.

Rule (fail):
    * integrated loudness outside [-17.0, -13.0] LUFS (target ~ -15/-16), OR
    * true-peak > -1.0 dBFS (no inter-sample clipping headroom).

Measurement: a single ffmpeg pass with the EBU R128 meter,
    ffmpeg -nostats -i <mp4> -af ebur128=peak=true -f null -
and parse the SUMMARY block on stderr:
    Integrated loudness:
        I:         -15.0 LUFS      <- integrated
    True peak:
        Peak:       -1.5 dBFS      <- true peak
Per-frame log lines also carry an "I:" token, so we anchor on the "Summary:"
marker and only read the values that follow it.

A gate that cannot run must never silently pass, so:
    * neither renders/final.mp4 nor renders/master.mp4 present -> GateInputError
    * ffmpeg not on PATH                                       -> GateInputError
    * ebur128 output missing the I:/Peak: summary values       -> GateInputError
        (a mix we can't measure is not a mix we can clear)

Reads:   <project>/renders/final.mp4   (fallback <project>/renders/master.mp4)
Allowed: subprocess + ffmpeg (no required pip deps).
"""

from __future__ import annotations

import re
import shutil
import subprocess
from argparse import Namespace
from pathlib import Path
from typing import List, Optional, Tuple

from ._contract import Finding, GateInputError, load_json, run_cli  # noqa: F401

# Integrated-loudness window for a finished mix. The channel target is ~ -15/-16
# LUFS; this band leaves +/-2 LU of tolerance before a mix reads as too hot
# (fatiguing / inauthentic-content signal) or too quiet (viewer cranks volume).
MIN_INTEGRATED_LUFS = -17.0
MAX_INTEGRATED_LUFS = -13.0

# True-peak ceiling. Anything above this has no headroom for inter-sample peaks
# and risks audible clipping on consumer DACs.
MAX_TRUE_PEAK_DBFS = -1.0

EBUR128_TIMEOUT_S = 300

# Values live in the SUMMARY block (after the literal "Summary:" line):
#     I:         -15.0 LUFS
#     Peak:       -1.5 dBFS
# Signed/optional-sign float, tolerant of the variable run of spaces ffmpeg uses.
_FLOAT = r"(-?\d+(?:\.\d+)?)"
_INTEGRATED_RE = re.compile(r"^\s*I:\s*" + _FLOAT + r"\s*LUFS", re.MULTILINE)
_TRUE_PEAK_RE = re.compile(r"^\s*Peak:\s*" + _FLOAT + r"\s*dBFS", re.MULTILINE)


def _find_render(project_dir: Path) -> Path:
    """renders/final.mp4 preferred, renders/master.mp4 fallback.

    Neither present is a BLOCKING input error: there is no mix to measure, and a
    loudness gate that finds no render must not report a pass."""
    renders = project_dir / "renders"
    final = renders / "final.mp4"
    master = renders / "master.mp4"
    if final.exists() and final.is_file():
        return final
    if master.exists() and master.is_file():
        return master
    raise GateInputError(
        "no render found: neither renders/final.mp4 nor renders/master.mp4 "
        "exists (cannot measure loudness without a rendered video)"
    )


def _measure_ebur128(mp4: Path) -> str:
    """Run the EBU R128 meter over the whole file; return ffmpeg's stderr text.

    ebur128 writes its running log and the SUMMARY block to stderr; the muxer
    sink is the null device so nothing is written to disk.
    """
    proc = subprocess.run(
        [
            "ffmpeg", "-nostats", "-nostdin",
            "-i", str(mp4),
            "-af", "ebur128=peak=true",
            "-f", "null", "-",
        ],
        capture_output=True, timeout=EBUR128_TIMEOUT_S,
    )
    # ffmpeg can exit non-zero for benign muxer/stream quirks while still having
    # produced a valid SUMMARY; the parse below is the real arbiter, so we do not
    # gate on returncode here.
    return proc.stderr.decode("utf-8", "replace")


def _parse_summary(stderr_text: str) -> Tuple[Optional[float], Optional[float]]:
    """Pull integrated LUFS and true-peak dBFS from the SUMMARY block.

    Per-frame log lines also contain an "I:" token (and FTPK/TPK, but never the
    "Peak:" label), so we slice from the "Summary:" marker forward and read only
    the trailing values. Returns (integrated, true_peak); either may be None if
    the corresponding line is absent.
    """
    marker = stderr_text.rfind("Summary:")
    summary = stderr_text[marker:] if marker != -1 else ""

    integrated: Optional[float] = None
    true_peak: Optional[float] = None

    m_i = _INTEGRATED_RE.search(summary)
    if m_i:
        try:
            integrated = float(m_i.group(1))
        except ValueError:
            integrated = None

    m_p = _TRUE_PEAK_RE.search(summary)
    if m_p:
        try:
            true_peak = float(m_p.group(1))
        except ValueError:
            true_peak = None

    return integrated, true_peak


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    mp4 = _find_render(project_dir)
    rel = mp4.relative_to(project_dir).as_posix()

    if shutil.which("ffmpeg") is None:
        raise GateInputError(
            "ffmpeg not found on PATH; cannot measure loudness of {0}".format(rel)
        )

    try:
        stderr_text = _measure_ebur128(mp4)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise GateInputError("ffmpeg ebur128 failed on {0}: {1}".format(rel, exc))

    integrated, true_peak = _parse_summary(stderr_text)

    # A mix we cannot measure is a mix we cannot clear -> blocking, never a pass.
    if integrated is None or true_peak is None:
        missing = []
        if integrated is None:
            missing.append("integrated loudness (I: ... LUFS)")
        if true_peak is None:
            missing.append("true peak (Peak: ... dBFS)")
        raise GateInputError(
            "could not parse {0} from ebur128 SUMMARY for {1} "
            "(meter output unreadable; mix not verifiable)".format(
                " and ".join(missing), rel
            )
        )

    findings: List[Finding] = []

    if integrated < MIN_INTEGRATED_LUFS or integrated > MAX_INTEGRATED_LUFS:
        findings.append(Finding(
            "fail", "loudness_out_of_range",
            "integrated loudness {0:.1f} LUFS is outside the broadcast window "
            "[{1:.1f}, {2:.1f}] LUFS (target ~ -15/-16)".format(
                integrated, MIN_INTEGRATED_LUFS, MAX_INTEGRATED_LUFS
            ),
            where=rel,
        ))

    if true_peak > MAX_TRUE_PEAK_DBFS:
        findings.append(Finding(
            "fail", "true_peak_too_hot",
            "true peak {0:.1f} dBFS exceeds the ceiling {1:.1f} dBFS "
            "(no headroom; risks inter-sample clipping)".format(
                true_peak, MAX_TRUE_PEAK_DBFS
            ),
            where=rel,
        ))

    return findings


if __name__ == "__main__":
    run_cli("qa_loudness", check)
