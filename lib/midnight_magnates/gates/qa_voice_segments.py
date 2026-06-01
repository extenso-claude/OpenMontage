"""qa_voice_segments — the voice lock. A VO can't proceed on bad/unfixed segments.

The voice QA->fix loop (lib/midnight_magnates/voice_qa.py) synthesizes each
segment, scores it (ASR round-trip WER + word confidence + naturalness MOS +
prosody + artifacts), regenerates bad ones, and writes artifacts/voice_report.json.
This gate is the load-bearing check on that report: a segment that the loop
could not fix must be HUMAN-APPROVED (G-voice) or the build is blocked — the
voiceover is the timing foundation for everything downstream, so it cannot ship
with mispronounced names, dropped words, robotic reads, clipping, or dropouts.

Defense-in-depth: even if the loop mislabels a segment "pass", this gate
re-checks the recorded metrics, so a green status with red numbers still fails.
A human_approved segment is the sole sanctioned override (the human listened and
accepted it).

MM ships USER-PROVIDED finished VO rather than generating it with Inworld, so
the generator-identity requirements (model_id=='inworld-tts-2',
delivery_mode=='CREATIVE') only apply to GENERATED voice. A report flagged
source=='user_provided' (or generated==false) skips those two checks; every
QUALITY check still runs (per-segment WER/MOS/rate/clipping/dropout + track
loudness), and an unfixed segment still needs the G-voice human-approval
override to ship.

Reads:  <project>/artifacts/voice_report.json
Shape:
  {"voice": {"voice_id","delivery_mode"?,"model_id"?,
             "source"?:"user_provided","generated"?:bool},
   "segments": [{"id","status":"pass"|"fail"|"approved","human_approved"?:bool,
                 "fix_iterations"?:int,
                 "metrics": {"wer","min_word_prob","mos","wps","clipping","dropout"}}],
   "track": {"lufs","true_peak_db"}}
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import List

from ._contract import Finding, GateInputError, load_json, run_cli

# Objective thresholds (aligned with the researched stack; see plan §7).
WER_MAX = 0.15
MOS_MIN = 3.2
WPS_MAX = 3.6           # words/sec — faster than this reads as "rushed"
WPS_MIN = 1.8
LUFS_RANGE = (-17.0, -13.0)   # target ~ -16/-15 LUFS
TRUE_PEAK_MAX_DB = -1.0
VALID_STATUS = {"pass", "fail", "approved"}


def _approved(seg: dict) -> bool:
    return seg.get("human_approved") is True or seg.get("status") == "approved"


def _is_user_provided(voice: dict) -> bool:
    """MM ships USER-PROVIDED finished VO (not Inworld generation). A report is
    user-provided when it says so explicitly — source=='user_provided' OR
    generated==false. Anything else (generated voice, or a report that omits both
    flags) is treated as the Inworld-generated path so the historical
    model_id/delivery_mode requirements still bite."""
    return voice.get("source") == "user_provided" or voice.get("generated") is False


def _check_voice(voice: dict) -> List[Finding]:
    out: List[Finding] = []
    # User-provided VO is finished audio we did not synthesize, so the
    # Inworld-specific model_id / delivery_mode requirements do not apply. All of
    # the QUALITY checks (per-segment + track loudness, below) still run — only
    # the generator-identity requirements are skipped here.
    if not _is_user_provided(voice):
        if voice.get("delivery_mode") != "CREATIVE":
            out.append(Finding("fail", "delivery_mode_not_creative",
                               "delivery_mode must be 'CREATIVE', got {0!r}".format(voice.get("delivery_mode")), where="voice"))
        if voice.get("model_id") != "inworld-tts-2":
            out.append(Finding("fail", "model_id_wrong",
                               "model_id must be 'inworld-tts-2', got {0!r}".format(voice.get("model_id")), where="voice"))
    vid = voice.get("voice_id")
    if not (isinstance(vid, str) and vid.strip()):
        out.append(Finding("fail", "voice_id_empty", "voice_id must be a non-empty string", where="voice"))
    return out


def _check_segment(seg: dict) -> List[Finding]:
    sid = seg.get("id", "?")
    status = seg.get("status")
    if status not in VALID_STATUS:
        return [Finding("fail", "bad_status", "unknown status {0!r} (expected pass|fail|approved)".format(status), where=sid)]

    if _approved(seg):
        return []  # human listened and accepted — the sole sanctioned override

    out: List[Finding] = []
    if status == "fail":
        out.append(Finding("fail", "unfixed_segment",
                           "segment still FAILS after the loop ({0} fix iterations) and is not human-approved".format(
                               seg.get("fix_iterations", "?")), where=sid))

    metrics = seg.get("metrics")
    if not isinstance(metrics, dict):
        out.append(Finding("fail", "missing_metrics", "non-approved segment has no metrics to verify", where=sid))
        return out

    wer = metrics.get("wer")
    if isinstance(wer, (int, float)) and wer > WER_MAX:
        out.append(Finding("fail", "high_wer", "WER {0:.2f} > {1:.2f} (dropped/mangled/mispronounced words)".format(wer, WER_MAX), where=sid))
    mos = metrics.get("mos")
    if isinstance(mos, (int, float)) and mos < MOS_MIN:
        out.append(Finding("fail", "low_mos", "naturalness MOS {0:.2f} < {1:.2f} (robotic/unnatural)".format(mos, MOS_MIN), where=sid))
    wps = metrics.get("wps")
    if isinstance(wps, (int, float)) and (wps > WPS_MAX or wps < WPS_MIN):
        out.append(Finding("fail", "bad_rate", "speaking rate {0:.2f} w/s outside [{1},{2}]".format(wps, WPS_MIN, WPS_MAX), where=sid))
    if metrics.get("clipping") is True:
        out.append(Finding("fail", "clipping", "audio clips (true-peak over 0 dBFS)", where=sid))
    if metrics.get("dropout") is True:
        out.append(Finding("fail", "dropout", "audio dropout / dead air inside the segment", where=sid))
    return out


def check(project_dir: Path, args: Namespace) -> List[Finding]:
    report = load_json(project_dir / "artifacts" / "voice_report.json")

    voice = report.get("voice")
    if not isinstance(voice, dict):
        raise GateInputError("voice_report.json has no 'voice' object")
    segments = report.get("segments")
    if not isinstance(segments, list) or not segments:
        raise GateInputError("voice_report.json has no 'segments'")

    findings: List[Finding] = []
    findings.extend(_check_voice(voice))
    for seg in segments:
        if isinstance(seg, dict):
            findings.extend(_check_segment(seg))
        else:
            findings.append(Finding("fail", "malformed_segment", "segment is not an object", where="?"))

    track = report.get("track") or {}
    lufs = track.get("lufs")
    if isinstance(lufs, (int, float)) and not (LUFS_RANGE[0] <= lufs <= LUFS_RANGE[1]):
        findings.append(Finding("fail", "track_loudness",
                               "integrated loudness {0:.1f} LUFS outside [{1},{2}]".format(lufs, *LUFS_RANGE), where="track"))
    tp = track.get("true_peak_db")
    if isinstance(tp, (int, float)) and tp > TRUE_PEAK_MAX_DB:
        findings.append(Finding("fail", "true_peak", "true-peak {0:.1f} dB exceeds {1} dB ceiling".format(tp, TRUE_PEAK_MAX_DB), where="track"))
    return findings


if __name__ == "__main__":
    run_cli("qa_voice_segments", check)
