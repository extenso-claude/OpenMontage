"""IndexTTS-2 zero-shot voice cloning TTS via Replicate (lucataco/indextts-2).

Exposes the full Replicate input schema so an assistant can sweep parameters to
dial in a target voice:
  - emotion control (3 modes: emotion_audio clip, emotion_text via Qwen, or
    an 8-weight emotion_vector)
  - sampling controls (temperature, top_p, top_k, num_beams, repetition_penalty,
    length_penalty)
  - pacing controls (interval_silence_ms, max_mel_tokens,
    max_text_tokens_per_segment)

For scripts longer than a single segment, set ``chunk_long_text=true``. The
tool splits text at paragraph/sentence boundaries, fans out parallel Replicate
predictions, and stitches the WAVs together with ffmpeg.

Pricing: ~$0.006 per call on L40S, ~7s predict time.
Reference: https://replicate.com/lucataco/indextts-2
"""

from __future__ import annotations

import concurrent.futures
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)


class IndexTTS2Replicate(BaseTool):
    name = "indextts2_replicate"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "indextts2"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set REPLICATE_API_KEY (or REPLICATE_API_TOKEN) to your Replicate API "
        "token. Get one at https://replicate.com/account/api-tokens"
    )
    fallback = "elevenlabs_tts"
    fallback_tools = ["elevenlabs_tts", "openai_tts", "piper_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "zero_shot_voice_clone",
        "emotion_control",
        "duration_control",
    ]
    supports = {
        "voice_cloning": True,
        "emotion_control": True,
        "long_form_chunking": True,
        "offline": False,
        "native_audio": True,
    }
    best_for = [
        "zero-shot voice cloning from a 16-48 kHz reference clip",
        "emotion-controlled narration (emotion_text or emotion_vector)",
        "parameter-sweep experiments to dial in a target voice",
        "cheap iterative testing ($0.006/run)",
    ]
    not_good_for = [
        "fully offline production",
        "privacy-constrained local-only workflows",
    ]

    MODEL_SLUG = "lucataco/indextts-2"
    DEFAULT_VERSION = "b219b0f22f95fd97cb2c8e3bbea6827a450a7fff05674c996d83171d70b3f685"

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string", "description": "Text to synthesize."},
            # Speaker reference accepts a URL or a local file path. Local files
            # are uploaded to Replicate's Files API automatically.
            "speaker_audio": {
                "type": "string",
                "description": "Reference audio for the target speaker. URL or local file path (16-48 kHz WAV/MP3).",
            },
            "voice_id": {
                "type": "string",
                "description": "Alias for speaker_audio (tts_selector compatibility).",
            },
            # Emotion control (three modes)
            "emotion_audio": {
                "type": "string",
                "description": "Optional separate emotion reference clip. URL or local path. Defaults to speaker_audio when omitted.",
            },
            "emotion_scale": {
                "type": "number", "minimum": 0, "maximum": 1, "default": 1,
                "description": "Blend ratio for the emotion reference when both speaker and emotion prompts are used.",
            },
            "emotion_text": {
                "type": "string",
                "description": "Plain-English emotion description; auto-classified via Qwen.",
            },
            "emotion_vector": {
                "type": "string",
                "description": "Direct 8-weight vector, CSV or JSON list (happy, angry, sad, fear, disgust, surprised, calm, neutral).",
            },
            "randomize_emotion": {
                "type": "boolean", "default": False,
                "description": "Pick emotion embeddings randomly instead of nearest-neighbour selection.",
            },
            # Sampling
            "temperature": {
                "type": "number", "minimum": 0, "maximum": 2, "default": 0.8,
                "description": "GPT-stage sampling temperature.",
            },
            "top_p": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.8},
            "top_k": {"type": "integer", "minimum": 1, "maximum": 200, "default": 30},
            "num_beams": {
                "type": "integer", "minimum": 1, "maximum": 8, "default": 3,
                "description": "Beam width on the GPT stage.",
            },
            "length_penalty": {
                "type": "number", "minimum": 0, "maximum": 5, "default": 0,
                "description": "Beam search length penalty.",
            },
            "repetition_penalty": {
                "type": "number", "minimum": 1, "maximum": 30, "default": 10,
                "description": "Penalty for repeated tokens.",
            },
            # Pacing / segment
            "interval_silence_ms": {
                "type": "integer", "minimum": 0, "maximum": 2000, "default": 200,
                "description": "Silence inserted between auto-split segments (ms).",
            },
            "max_mel_tokens": {
                "type": "integer", "minimum": 256, "maximum": 4096, "default": 1500,
                "description": "Maximum mel tokens per segment.",
            },
            "max_text_tokens_per_segment": {
                "type": "integer", "minimum": 32, "maximum": 300, "default": 120,
                "description": "Max BPE tokens per autoregressive segment.",
            },
            # Long-form chunking
            "chunk_long_text": {
                "type": "boolean", "default": False,
                "description": "Split text at paragraph/sentence boundaries, fan out parallel predictions, and stitch the WAVs.",
            },
            "chunk_target_chars": {
                "type": "integer", "default": 600, "minimum": 100, "maximum": 4000,
                "description": "Target characters per chunk when chunk_long_text=true.",
            },
            "chunk_concurrency": {
                "type": "integer", "default": 4, "minimum": 1, "maximum": 20,
                "description": "Max concurrent Replicate predictions during chunked synthesis.",
            },
            # Misc
            "model_version": {
                "type": "string",
                "description": "Override the pinned Replicate model version.",
            },
            "output_path": {
                "type": "string",
                "description": "Local path to write the output WAV.",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=200, network_required=True,
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = [
        "text", "speaker_audio", "emotion_text", "emotion_vector",
        "temperature", "top_p", "top_k", "num_beams",
    ]
    side_effects = ["writes audio file to output_path", "calls Replicate API"]
    user_visible_verification = [
        "Listen to the output for voice match, naturalness, pacing, and artifacts",
    ]

    # ------------------------------------------------------------------ env

    def _get_api_token(self) -> str | None:
        return (
            os.environ.get("REPLICATE_API_TOKEN")
            or os.environ.get("REPLICATE_API_KEY")
        )

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if self._get_api_token() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        if inputs.get("chunk_long_text"):
            text = inputs.get("text", "")
            target = inputs.get("chunk_target_chars", 600)
            n = max(1, (len(text) + target - 1) // target)
            return round(0.006 * n, 4)
        return 0.006

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        if inputs.get("chunk_long_text"):
            text = inputs.get("text", "")
            target = inputs.get("chunk_target_chars", 600)
            n = max(1, (len(text) + target - 1) // target)
            concurrency = max(1, int(inputs.get("chunk_concurrency", 4)))
            return round((n / concurrency) * 12, 1)
        return 10.0

    # ----------------------------------------------------- file handling

    def _resolve_audio_input(self, value: str, token: str) -> str:
        """Return a URL Replicate can fetch. Upload local files automatically."""
        if value.startswith(("http://", "https://", "data:")):
            return value
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Audio reference not found: {path}")
        return self._upload_to_replicate(path, token)

    def _upload_to_replicate(self, path: Path, token: str) -> str:
        import requests
        with open(path, "rb") as f:
            resp = requests.post(
                "https://api.replicate.com/v1/files",
                headers={"Authorization": f"Bearer {token}"},
                files={"content": (path.name, f, self._content_type(path))},
                timeout=180,
            )
        resp.raise_for_status()
        data = resp.json()
        url = data.get("urls", {}).get("get") or data.get("url")
        if not url:
            raise RuntimeError(f"Replicate upload response missing URL: {data}")
        return url

    @staticmethod
    def _content_type(path: Path) -> str:
        return {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
        }.get(path.suffix.lower(), "application/octet-stream")

    # ----------------------------------------------------- text chunking

    @staticmethod
    def _split_text(text: str, target_chars: int) -> list[str]:
        """Split text at paragraph then sentence then comma boundaries."""
        text = text.strip()
        if len(text) <= target_chars:
            return [text]

        chunks: list[str] = []
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        for para in paragraphs:
            if len(para) <= target_chars:
                chunks.append(para)
                continue
            sentences = re.split(r"(?<=[.!?])\s+", para)
            buf = ""
            for s in sentences:
                if len(buf) + len(s) + 1 <= target_chars:
                    buf = f"{buf} {s}".strip() if buf else s
                else:
                    if buf:
                        chunks.append(buf)
                    if len(s) <= target_chars:
                        buf = s
                    else:
                        # Sentence longer than target — split at commas
                        for piece in re.split(r"(?<=,)\s+", s):
                            if len(buf) + len(piece) + 1 <= target_chars:
                                buf = f"{buf} {piece}".strip() if buf else piece
                            else:
                                if buf:
                                    chunks.append(buf)
                                buf = piece
            if buf:
                chunks.append(buf)
        return chunks

    # ----------------------------------------------------- replicate call

    def _predict_one(
        self,
        text: str,
        replicate_input: dict[str, Any],
        token: str,
        version: str,
        timeout: int = 300,
    ) -> bytes:
        """Submit one prediction and return audio bytes."""
        import requests
        from tools.audio._replicate_common import replicate_post_with_retry

        payload_input = {**replicate_input, "text": text}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "wait=60",
        }
        submit = replicate_post_with_retry(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json_payload={"version": version, "input": payload_input},
            timeout=90,
        )
        pred = submit.json()

        deadline = time.time() + timeout
        while pred.get("status") in ("starting", "processing"):
            if time.time() > deadline:
                raise TimeoutError(f"Replicate prediction timed out after {timeout}s")
            time.sleep(2)
            get_url = pred.get("urls", {}).get("get")
            if not get_url:
                raise RuntimeError("Replicate response missing poll URL")
            poll = requests.get(get_url, headers=headers, timeout=30)
            poll.raise_for_status()
            pred = poll.json()

        if pred.get("status") != "succeeded":
            raise RuntimeError(
                f"Replicate prediction {pred.get('status')}: {pred.get('error')}"
            )

        output = pred.get("output")
        audio_url = output[0] if isinstance(output, list) else output
        if not isinstance(audio_url, str):
            raise RuntimeError(f"Unexpected Replicate output shape: {output!r}")

        audio_resp = requests.get(audio_url, timeout=180)
        audio_resp.raise_for_status()
        return audio_resp.content

    # ----------------------------------------------------- stitch

    @staticmethod
    def _stitch_wavs(parts: list[bytes], output_path: Path) -> None:
        """Concat WAVs with ffmpeg filter_complex (re-encodes for safety)."""
        if len(parts) == 1:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(parts[0])
            return

        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            paths: list[Path] = []
            for i, b in enumerate(parts):
                p = tdp / f"part_{i:04d}.wav"
                p.write_bytes(b)
                paths.append(p)

            cmd: list[str] = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            ]
            for p in paths:
                cmd.extend(["-i", str(p)])
            inputs_str = "".join(f"[{i}:a]" for i in range(len(paths)))
            cmd.extend([
                "-filter_complex",
                f"{inputs_str}concat=n={len(paths)}:v=0:a=1[a]",
                "-map", "[a]",
                "-c:a", "pcm_s16le",
                str(output_path),
            ])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(cmd, check=True)

    # ------------------------------------------------------------ main

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        token = self._get_api_token()
        if not token:
            return ToolResult(
                success=False,
                error="REPLICATE_API_KEY/REPLICATE_API_TOKEN not set. " + self.install_instructions,
            )

        text = (inputs.get("text") or "").strip()
        if not text:
            return ToolResult(success=False, error="Empty text")

        speaker_audio = inputs.get("speaker_audio") or inputs.get("voice_id")
        if not speaker_audio:
            return ToolResult(
                success=False,
                error=(
                    "speaker_audio (or voice_id) is required — provide a URL "
                    "or local path to a 16-48 kHz WAV/MP3 reference clip of "
                    "the target voice."
                ),
            )

        start = time.time()
        version = inputs.get("model_version") or self.DEFAULT_VERSION

        # Upload any local reference files to Replicate's Files API.
        try:
            speaker_url = self._resolve_audio_input(speaker_audio, token)
            emotion_audio = inputs.get("emotion_audio")
            emotion_url = (
                self._resolve_audio_input(emotion_audio, token) if emotion_audio else None
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Audio reference upload failed: {e}")

        # Build the Replicate input — only include user-set fields so we don't
        # override the model's tuned defaults.
        rep_input: dict[str, Any] = {"speaker_audio": speaker_url}
        if emotion_url:
            rep_input["emotion_audio"] = emotion_url
        passthrough = [
            "emotion_scale", "emotion_text", "emotion_vector", "randomize_emotion",
            "temperature", "top_p", "top_k", "num_beams", "length_penalty",
            "repetition_penalty", "interval_silence_ms", "max_mel_tokens",
            "max_text_tokens_per_segment",
        ]
        for key in passthrough:
            if key in inputs and inputs[key] is not None:
                rep_input[key] = inputs[key]

        output_path = Path(inputs.get("output_path") or f"indextts2_{int(start)}.wav")

        try:
            if inputs.get("chunk_long_text"):
                target = int(inputs.get("chunk_target_chars", 600))
                concurrency = max(1, int(inputs.get("chunk_concurrency", 4)))
                chunks = self._split_text(text, target)
                with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
                    futures = [
                        ex.submit(self._predict_one, chunk, rep_input, token, version)
                        for chunk in chunks
                    ]
                    parts: list[bytes] = []
                    for fut in futures:
                        parts.append(fut.result())
                self._stitch_wavs(parts, output_path)
                n_chunks = len(chunks)
            else:
                audio_bytes = self._predict_one(text, rep_input, token, version)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(audio_bytes)
                n_chunks = 1
        except Exception as e:
            return ToolResult(success=False, error=f"IndexTTS-2 synthesis failed: {e}")

        params_used = {
            k: v for k, v in rep_input.items()
            if k not in ("speaker_audio", "emotion_audio")
        }
        return ToolResult(
            success=True,
            data={
                "provider": "indextts2",
                "gateway": "replicate",
                "model": self.MODEL_SLUG,
                "model_version": version,
                "output": str(output_path),
                "output_path": str(output_path),
                "format": "wav",
                "n_chunks": n_chunks,
                "speaker_audio_url": speaker_url,
                "emotion_audio_url": emotion_url,
                "params_used": params_used,
            },
            artifacts=[str(output_path)],
            cost_usd=round(0.006 * n_chunks, 4),
            duration_seconds=round(time.time() - start, 2),
            model=self.MODEL_SLUG,
        )
