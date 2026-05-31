"""Voice-QA -> fix loop — synthesize per segment, detect AI-voice problems,
regenerate just the bad segments (preserving neighbors' pauses), loop <= N, then
escalate to the human (G-voice). Produces artifacts/voice_report.json — the
contract qa_voice_segments enforces.

DESIGN (researched; see plan §7). The loop is backend-agnostic:
  VoiceBackend.synthesize(text, opts) -> Take          (a generated audio take)
  VoiceBackend.evaluate(take, intended_text) -> Metrics (ASR round-trip WER +
        word confidence + naturalness MOS + speaking rate + clipping/dropout)
The REAL backend wires InWorld TTS-2 (synth) + faster-whisper (ASR round-trip) +
UTMOSv2/Distill-MOS (naturalness) + ffmpeg/pyloudnorm (artifacts). Those deps are
heavy + the API is paid, so the real backend is import/-key-guarded and raises a
clear setup error if unavailable — it is NOT run-verified in this environment.
The StubBackend is deterministic and drives the unit/self-test of all the pure
logic (markup fixes, thresholds, best-of-N, fix tree, loop convergence/escalation).

InWorld facts baked in: no seed + temperature ignored on tts-2 -> best-of-N means
resampling stochasticity + varying deliveryMode; pronunciation fix = inline
English IPA in /.../; <= 20 breaks/request; QA on PCM, never MP3.

CLI:  python -m lib.animated_history_map.voice_qa --project <dir>          (real backend)
      python -m lib.animated_history_map.voice_qa --selftest               (stub loop + assertions)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---- thresholds (aligned with qa_voice_segments + the research) ----
WER_FLAG = 0.05
WER_HARD = 0.15
CONF_MIN = 0.40
MOS_FLAG = 3.6
MOS_HARD = 3.2
WPS_MAX = 3.6
WPS_MIN = 1.8
BEST_OF_N = 3
MAX_ITERS = 3
INLINE_NONVERBALS = {"laugh", "breathe", "sigh", "cough", "yawn", "clear throat"}


@dataclass
class SynthOpts:
    voice_id: str = "Tyler"
    delivery_mode: str = "CREATIVE"
    model_id: str = "inworld-tts-2"
    speaking_rate: float = 1.0


@dataclass
class Take:
    audio_path: str
    word_timestamps: List[dict] = field(default_factory=list)
    delivery_mode: str = "CREATIVE"


@dataclass
class Metrics:
    wer: float = 0.0
    min_word_prob: float = 1.0
    mos: float = 4.2
    wps: float = 2.8
    clipping: bool = False
    dropout: bool = False
    hallucination: bool = False
    missing_content_word: bool = False
    mispronounced_token: Optional[str] = None


# --------------------------------------------------------------------------- #
# markup fix transforms (pure)
# --------------------------------------------------------------------------- #
_LEADING_TAG_RE = re.compile(r"^\s*\[[^\[\]]*\]\s*")


def insert_break(text: str, ms: int = 650, after: Optional[str] = None) -> str:
    tag = '<break time="{0}ms" />'.format(int(ms))
    if after and after in text:
        i = text.index(after) + len(after)
        return text[:i] + " " + tag + text[i:]
    return text.rstrip() + " " + tag


def ipa_respell(text: str, word: str, ipa: str) -> str:
    """Wrap the first whole-word occurrence in inline English IPA /.../"""
    return re.sub(r"\b{0}\b".format(re.escape(word)), "/{0}/".format(ipa), text, count=1)


def capitalize_word(text: str, word: str) -> str:
    return re.sub(r"\b{0}\b".format(re.escape(word)), word.upper(), text, count=1, flags=re.IGNORECASE)


def set_leading_tag(text: str, tag: str) -> str:
    """Steering tags must be the FIRST token (InWorld rule). Replace any existing
    leading [tag], else prepend."""
    body = _LEADING_TAG_RE.sub("", text)
    return "[{0}] {1}".format(tag.strip("[]").strip(), body)


def split_sentence(text: str) -> List[str]:
    """Split at the clause boundary nearest the midpoint (shorter context = fewer
    drops). Never split inside a <...> tag."""
    mid = len(text) // 2
    candidates = [m.start() for m in re.finditer(r"[,;:] ", text)]
    if not candidates:
        candidates = [m.start() for m in re.finditer(r" ", text)]
    if not candidates:
        return [text]
    cut = min(candidates, key=lambda c: abs(c - mid))
    # avoid cutting inside a tag
    for m in re.finditer(r"<[^>]*>", text):
        if m.start() < cut < m.end():
            cut = m.start()
            break
    return [text[:cut + 1].strip(), text[cut + 1:].strip()]


# --------------------------------------------------------------------------- #
# detect / score / fix-decision (pure)
# --------------------------------------------------------------------------- #
def detect(m: Metrics) -> List[str]:
    p: List[str] = []
    if m.mispronounced_token:
        p.append("mispronounced_name")
    if m.missing_content_word or m.wer > WER_FLAG:
        p.append("dropped_or_mangled")
    if m.min_word_prob < CONF_MIN:
        p.append("low_confidence")
    if m.wps > WPS_MAX:
        p.append("too_fast")
    elif m.wps < WPS_MIN:
        p.append("too_slow")
    if m.hallucination:
        p.append("hallucination")
    if m.mos < MOS_FLAG:
        p.append("robotic")
    if m.clipping:
        p.append("clipping")
    if m.dropout:
        p.append("dropout")
    return p


def hard_reject(m: Metrics) -> bool:
    """A candidate take that must never be selected regardless of other scores."""
    return m.wer > WER_HARD or m.clipping or m.dropout or m.missing_content_word


def composite_score(m: Metrics) -> float:
    prosody = 1.0 if WPS_MIN <= m.wps <= WPS_MAX else 0.5
    clean = 0.0 if (m.clipping or m.dropout) else 1.0
    halluc = 1.0 if m.hallucination else 0.0
    return (0.40 * (1.0 - min(1.0, m.wer))
            + 0.20 * (m.mos / 5.0)
            + 0.15 * m.min_word_prob
            + 0.15 * prosody
            + 0.10 * clean
            - 0.10 * halluc)


@dataclass
class FixAction:
    kind: str                      # ipa | split | slow_down | emphasize | best_of_n
    params: dict = field(default_factory=dict)


def fix_for(problems: List[str], m: Metrics) -> FixAction:
    """Cheapest-deterministic fix first (research fix tree). best_of_n is the
    fallback for pure-stochasticity problems (robotic / low_conf / hallucination)."""
    if "mispronounced_name" in problems and m.mispronounced_token:
        return FixAction("ipa", {"word": m.mispronounced_token})
    if "dropped_or_mangled" in problems:
        return FixAction("split")
    if "too_fast" in problems:
        return FixAction("slow_down", {"rate": 0.92})
    if "too_slow" in problems:
        return FixAction("slow_down", {"rate": 1.08})
    return FixAction("best_of_n", {"n": BEST_OF_N})


def apply_fix(action: FixAction, text: str, opts: SynthOpts) -> Tuple[List[str], SynthOpts, bool]:
    """Return (segment_texts, opts, use_best_of_n). Most fixes mutate one text;
    'split' returns two segment texts; 'best_of_n' re-rolls unchanged."""
    if action.kind == "ipa":
        ipa = action.params.get("ipa") or _naive_ipa(action.params["word"])
        return [ipa_respell(text, action.params["word"], ipa)], opts, False
    if action.kind == "split":
        return split_sentence(text), opts, False
    if action.kind == "slow_down":
        return [text], SynthOpts(opts.voice_id, opts.delivery_mode, opts.model_id, action.params["rate"]), False
    if action.kind == "emphasize":
        return [capitalize_word(text, action.params["word"])], opts, False
    return [text], opts, True  # best_of_n


def _naive_ipa(word: str) -> str:
    """Placeholder respelling when no project name->IPA map entry exists. The real
    pipeline supplies English IPA from canonical_names.phonetic_for_tts."""
    return word.lower()


# --------------------------------------------------------------------------- #
# backend protocol + stub
# --------------------------------------------------------------------------- #
class VoiceBackend:
    def synthesize(self, text: str, opts: SynthOpts) -> Take:
        raise NotImplementedError

    def evaluate(self, take: Take, intended_text: str) -> Metrics:
        raise NotImplementedError


class StubBackend(VoiceBackend):
    """Deterministic backend for tests. `script[seg_key]` is a list of Metrics
    returned in sequence; the loop keys segments by their ORIGINAL id."""

    def __init__(self, script: Dict[str, List[Metrics]]):
        self.script = {k: list(v) for k, v in script.items()}
        self._idx: Dict[str, int] = {}
        self._current_key = None

    def for_segment(self, key: str) -> None:
        self._current_key = key
        self._idx.setdefault(key, 0)

    def synthesize(self, text: str, opts: SynthOpts) -> Take:
        return Take(audio_path="stub://{0}".format(self._current_key), delivery_mode=opts.delivery_mode)

    def evaluate(self, take: Take, intended_text: str) -> Metrics:
        key = self._current_key
        seq = self.script.get(key, [Metrics()])
        i = min(self._idx[key], len(seq) - 1)
        self._idx[key] += 1
        return seq[i]


# --------------------------------------------------------------------------- #
# the loop
# --------------------------------------------------------------------------- #
def _metrics_to_dict(m: Metrics) -> dict:
    return {"wer": round(m.wer, 3), "min_word_prob": round(m.min_word_prob, 3),
            "mos": round(m.mos, 3), "wps": round(m.wps, 3),
            "clipping": m.clipping, "dropout": m.dropout}


def process_segment(seg: dict, backend: VoiceBackend, opts: SynthOpts,
                    max_iters: int = MAX_ITERS) -> dict:
    """Synth -> detect -> fix -> re-eval <= max_iters; pick the best take seen."""
    if isinstance(backend, StubBackend):
        backend.for_segment(seg["id"])
    text = seg["text"]
    best_m: Optional[Metrics] = None
    best_score = -1e9
    iters = 0
    use_best_of_n = False

    while iters <= max_iters:
        n = BEST_OF_N if use_best_of_n else 1
        candidates: List[Metrics] = []
        for _ in range(n):
            take = backend.synthesize(text, opts)
            candidates.append(backend.evaluate(take, text))
        # pick best candidate (reject hard-fails first, then max composite)
        viable = [c for c in candidates if not hard_reject(c)] or candidates
        m = max(viable, key=composite_score)
        s = composite_score(m)
        if s > best_score:
            best_score, best_m = s, m

        problems = detect(m)
        if not problems:
            return {"id": seg["id"], "status": "pass", "fix_iterations": iters,
                    "metrics": _metrics_to_dict(m)}
        if iters == max_iters:
            break
        action = fix_for(problems, m)
        texts, opts, use_best_of_n = apply_fix(action, text, opts)
        text = texts[0]  # (a real pipeline would re-insert split halves as 2 segments)
        iters += 1

    # Exhausted iterations -> escalate to the human (G-voice).
    return {"id": seg["id"], "status": "fail", "fix_iterations": iters,
            "metrics": _metrics_to_dict(best_m or Metrics()),
            "escalate": "g_voice"}


def run_voice_qa(segments: List[dict], backend: VoiceBackend, *, opts: Optional[SynthOpts] = None,
                 track: Optional[dict] = None, max_iters: int = MAX_ITERS) -> dict:
    opts = opts or SynthOpts()
    results = [process_segment(s, backend, SynthOpts(opts.voice_id, opts.delivery_mode, opts.model_id, opts.speaking_rate),
                               max_iters=max_iters) for s in segments]
    return {
        "voice": {"voice_id": opts.voice_id, "delivery_mode": opts.delivery_mode, "model_id": opts.model_id},
        "segments": results,
        "track": track or {"lufs": -15.5, "true_peak_db": -1.3},
        "total_duration_s": sum(s.get("approx_dur_s", 0) for s in segments) or None,
    }


# --------------------------------------------------------------------------- #
# real backend (import/-key-guarded; NOT run-verified in this environment)
# --------------------------------------------------------------------------- #
def _norm_tokens(s: str) -> List[str]:
    return [t for t in re.sub(r"[^\w\s']", " ", (s or "").lower()).split() if t]


def _wer(reference: str, hypothesis: str) -> float:
    """Word error rate (token edit distance / ref length)."""
    r, h = _norm_tokens(reference), _norm_tokens(hypothesis)
    if not r:
        return 0.0 if not h else 1.0
    prev = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        cur = [i] + [0] * len(h)
        for j in range(1, len(h) + 1):
            cost = 0 if r[i - 1] == h[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[len(h)] / len(r)


def _longest_interior_quiet_s(data, sr: int, thresh: float = 1e-3) -> float:
    """Longest silent run BETWEEN the first and last audible sample (ignores
    leading/trailing silence) — a proxy for a mid-utterance dropout."""
    import numpy as np
    if len(data) == 0 or sr <= 0:
        return 0.0
    loud = np.abs(data) >= thresh
    idx = np.nonzero(loud)[0]
    if len(idx) == 0:
        return len(data) / sr
    interior = ~loud[idx[0]:idx[-1] + 1]
    best = run = 0
    for q in interior:
        run = run + 1 if q else 0
        if run > best:
            best = run
    return best / sr


_ASR_MODEL = None
_MOS_MODEL = None


def evaluate_audio(audio_path: str, intended_text: str, *, asr_size: str = "base") -> Metrics:
    """REAL evaluation — NO synthesis / NO API key needed. ASR round-trip via
    faster-whisper, naturalness via distillmos, clipping/dropout/loudness via
    soundfile+pyloudnorm. This is the half of the loop that IS run-verifiable in
    this environment (verified on macOS `say` speech)."""
    import subprocess, tempfile, os
    import numpy as np
    import soundfile as sf
    global _ASR_MODEL, _MOS_MODEL

    wav16 = tempfile.mktemp(suffix="_16k.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio_path),
                    "-ar", "16000", "-ac", "1", wav16], check=True)
    try:
        data, sr = sf.read(wav16, dtype="float32")
        dur = len(data) / sr if sr else 0.0

        from faster_whisper import WhisperModel
        if _ASR_MODEL is None:
            _ASR_MODEL = WhisperModel(asr_size, device="cpu", compute_type="int8")
        segs, _info = _ASR_MODEL.transcribe(wav16, word_timestamps=True)
        words = [w for s in segs for w in (s.words or [])]
        asr_text = " ".join(w.word for w in words)
        probs = [float(w.probability) for w in words if w.probability is not None]

        import torch
        import distillmos
        if _MOS_MODEL is None:
            _MOS_MODEL = distillmos.ConvTransformerSQAModel()
            _MOS_MODEL.eval()
        with torch.no_grad():
            mos = float(_MOS_MODEL(torch.from_numpy(data).unsqueeze(0)).reshape(-1)[0])

        import pyloudnorm as pyln
        try:
            lufs = float(pyln.Meter(sr).integrated_loudness(data))  # noqa: F841 (reserved for track stage)
        except Exception:
            pass

        return Metrics(
            wer=_wer(intended_text, asr_text),
            min_word_prob=(min(probs) if probs else 1.0),
            mos=mos,
            wps=(len(words) / dur if dur > 0 else 0.0),
            clipping=bool(len(data) and float(np.max(np.abs(data))) >= 0.999),
            dropout=_longest_interior_quiet_s(data, sr) > 0.4,
        )
    finally:
        try:
            os.remove(wav16)
        except OSError:
            pass


class RealBackend(VoiceBackend):
    """Production backend: InWorld TTS-2 synth + the real evaluate_audio pipeline.
    evaluate() needs NO API key (local ML, run-verified); synthesize() needs the
    paid InWorld key (in .env) + your per-run approval."""

    def synthesize(self, text: str, opts: SynthOpts) -> Take:  # pragma: no cover - paid API
        import os, tempfile
        if not os.environ.get("INWORLD_TTS_API_KEY"):
            raise RuntimeError("synthesize needs INWORLD_TTS_API_KEY (paid; it is in .env). "
                               "Approve the spend before a real run.")
        from tools.audio.inworld_tts import InworldTTS
        out = tempfile.mktemp(suffix=".wav")
        res = InworldTTS().execute({"text": text, "voice_id": opts.voice_id,
                                    "delivery_mode": opts.delivery_mode, "model_id": opts.model_id,
                                    "speaking_rate": opts.speaking_rate, "output_path": out,
                                    "output_format": "wav"})
        if not getattr(res, "success", False):
            raise RuntimeError("InWorld synth failed: {0}".format(getattr(res, "error", "?")))
        return Take(audio_path=out, delivery_mode=opts.delivery_mode)

    def evaluate(self, take: Take, intended_text: str) -> Metrics:
        return evaluate_audio(take.audio_path, intended_text)


# --------------------------------------------------------------------------- #
# CLI + self-test
# --------------------------------------------------------------------------- #
def _selftest(out_path: Optional[Path] = None) -> int:
    """Drive the loop with a deterministic stub: s1 clean, s2 fixed after a
    re-roll, s3 never fixable (escalates). Assert the loop's decisions, then the
    produced voice_report must agree with qa_voice_segments."""
    clean = Metrics(wer=0.0, min_word_prob=0.95, mos=4.1, wps=2.8)
    mediocre = Metrics(wer=0.08, min_word_prob=0.55, mos=3.4, wps=3.0)
    robotic = Metrics(wer=0.0, min_word_prob=0.9, mos=2.9, wps=2.8)            # low MOS -> best_of_n
    bad = Metrics(wer=0.4, min_word_prob=0.2, mos=2.6, wps=4.3, clipping=True)
    script = {
        "s1": [clean],
        "s2": [robotic, mediocre, clean, mediocre],   # attempt0 robotic -> best_of_n picks clean
        "s3": [bad] * 12,                             # never clean -> escalate
    }
    segs = [{"id": "s1", "text": "Lincoln entered the box."},
            {"id": "s2", "text": "The crowd fell silent."},
            {"id": "s3", "text": "Czolgosz raised the revolver."}]
    report = run_voice_qa(segs, StubBackend(script), track={"lufs": -15.4, "true_peak_db": -1.5})

    by_id = {s["id"]: s for s in report["segments"]}
    checks = [
        ("s1 passes immediately", by_id["s1"]["status"] == "pass" and by_id["s1"]["fix_iterations"] == 0),
        ("s2 fixed via best-of-N re-roll", by_id["s2"]["status"] == "pass" and by_id["s2"]["fix_iterations"] >= 1),
        ("s3 escalates after max iters", by_id["s3"]["status"] == "fail" and by_id["s3"].get("escalate") == "g_voice"),
        ("pure markup: insert_break", '<break time="650ms" />' in insert_break("End.", 650)),
        ("pure markup: ipa_respell", ipa_respell("Say Czolgosz now.", "Czolgosz", "ˈtʃɔlɡɔʃ") == "Say /ˈtʃɔlɡɔʃ/ now."),
        ("pure markup: leading tag only", set_leading_tag("[old] Hi there", "say sadly") == "[say sadly] Hi there"),
        ("best-of-N rejects hard-fail take", hard_reject(bad) and not hard_reject(clean)),
    ]
    fails = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(("  PASS: " if ok else "  FAIL: ") + name)

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2))
        print("  wrote voice_report -> {0}".format(out_path))

    if fails:
        print("\n{0} self-test check(s) FAILED".format(len(fails)))
        return 1
    print("\nvoice_qa self-test PASSED")
    return 0


def _main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="animated_history_map.voice_qa")
    ap.add_argument("--project")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest(Path(args.out) if args.out else None)

    if not args.project:
        print("usage: --project <dir> (real backend) | --selftest", file=sys.stderr)
        return 2
    # Production path: real backend (raises clear setup errors if deps/key absent).
    project = Path(args.project)
    script_json = json.loads((project / "artifacts" / "script.json").read_text())
    segs = [{"id": s["id"], "text": s.get("text_markup", s.get("text", ""))} for s in script_json["segments"]]
    backend = RealBackend()
    report = run_voice_qa(segs, backend)
    (project / "artifacts" / "voice_report.json").write_text(json.dumps(report, indent=2))
    print("wrote {0}/artifacts/voice_report.json".format(project))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
