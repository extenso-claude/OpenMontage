"""TADA (HumeAI) zero-shot voice cloning TTS via Replicate.

Calls extenso-claude/tada-voice — a self-hosted deployment of HumeAI/tada built
from the fork at https://github.com/extenso-claude/tada. The fork adds
``cog.yaml`` + ``predict.py`` that surface the full TADA InferenceOptions
parameter set.

Self-host setup is a one-time UI step on Replicate; see the fork's
``REPLICATE_DEPLOY.md``.

Pricing: per-second L40S billing (~$0.001125/sec) only while running.
Predict time scales with text length and ``num_acoustic_candidates`` —
roughly 5-10 s for 10 s of speech at N=1.
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


class TadaReplicate(BaseTool):
    name = "tada_replicate"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "tada"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "1) Set REPLICATE_API_KEY (or REPLICATE_API_TOKEN) — get one at "
        "https://replicate.com/account/api-tokens\n"
        "2) Self-host extenso-claude/tada-voice on Replicate — see "
        "https://github.com/extenso-claude/tada/blob/main/REPLICATE_DEPLOY.md\n"
        "3) (Optional) Set TADA_MODEL_SLUG to override the default Replicate "
        "model path (default: extenso-claude/tada-voice)."
    )
    fallback_tools = ["indextts2_replicate", "elevenlabs_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "zero_shot_voice_clone",
        "duration_control",
        "multilingual",
        "speech_continuation",
    ]
    supports = {
        "voice_cloning": True,
        "multilingual": True,
        "long_form_chunking": True,
        "offline": False,
        "seed": True,
    }
    best_for = [
        "natural prosody via 1:1 token-to-audio alignment",
        "voice cloning with strong speaker-verification scoring (num_acoustic_candidates>1)",
        "multilingual narration (en/ar/ch/de/es/fr/it/ja/pl/pt)",
        "speech continuation (num_extra_steps)",
    ]
    not_good_for = [
        "fully offline production",
        "first-second latency-critical apps (cold start ~1-2 min)",
    ]

    DEFAULT_MODEL_SLUG = "extenso-claude/tada-voice"

    input_schema = {
        "type": "object",
        "required": ["text", "prompt_audio", "prompt_transcript"],
        "properties": {
            "text": {"type": "string", "description": "Text to synthesize."},
            # Reference voice
            "prompt_audio": {
                "type": "string",
                "description": "Reference voice clip. URL or local path (10-30 s WAV/MP3, mono, 16-48 kHz).",
            },
            "voice_id": {
                "type": "string",
                "description": "Alias for prompt_audio (tts_selector compatibility).",
            },
            "prompt_transcript": {
                "type": "string",
                "description": "Verbatim transcript of prompt_audio (required for forced alignment).",
            },
            "language": {
                "type": "string",
                "enum": ["en", "ar", "ch", "de", "es", "fr", "it", "ja", "pl", "pt"],
                "default": "en",
                "description": "Aligner language for the prompt.",
            },
            # LM sampling
            "text_do_sample": {"type": "boolean", "default": True},
            "text_temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.6},
            "text_top_k": {"type": "integer", "minimum": 0, "maximum": 200, "default": 0},
            "text_top_p": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.9},
            "text_repetition_penalty": {"type": "number", "minimum": 1, "maximum": 5, "default": 1.1},
            # Acoustic / CFG
            "acoustic_cfg_scale": {"type": "number", "minimum": 0, "maximum": 5, "default": 1.6},
            "duration_cfg_scale": {"type": "number", "minimum": 0, "maximum": 5, "default": 1.0},
            "cfg_schedule": {
                "type": "string", "enum": ["constant", "linear", "cosine"], "default": "cosine",
            },
            # Flow matching
            "noise_temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.9},
            "num_flow_matching_steps": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            "time_schedule": {
                "type": "string", "enum": ["uniform", "cosine", "logsnr"], "default": "logsnr",
            },
            # Candidates / scoring
            "num_acoustic_candidates": {
                "type": "integer", "minimum": 1, "maximum": 8, "default": 1,
                "description": "Quality booster — N>1 generates N variants and ranks via scorer (N x cost + time).",
            },
            "scorer": {
                "type": "string",
                "enum": ["spkr_verification", "likelihood", "duration_median"],
                "default": "likelihood",
            },
            "spkr_verification_weight": {"type": "number", "minimum": 0, "maximum": 5, "default": 1.0},
            # Misc
            "speed_up_factor": {
                "type": "number", "default": 0.0,
                "description": "Global pacing speedup. 0 = disabled. 1.05-1.3 for faster delivery.",
            },
            "negative_condition_source": {
                "type": "string",
                "enum": ["negative_step_output", "prompt", "zero"],
                "default": "negative_step_output",
            },
            "text_only_logit_scale": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.0},
            "num_extra_steps": {
                "type": "integer", "minimum": 0, "maximum": 200, "default": 0,
                "description": "Speech continuation steps after the text ends.",
            },
            "normalize_text": {"type": "boolean", "default": True},
            "seed": {"type": "integer", "default": -1, "description": "-1 = random."},
            # Long-form chunking (client-side; TADA doesn't auto-chunk)
            "chunk_long_text": {
                "type": "boolean", "default": False,
                "description": "Split text at paragraph/sentence boundaries, fan out parallel predictions, stitch the WAVs.",
            },
            "chunk_target_chars": {"type": "integer", "default": 600, "minimum": 100, "maximum": 4000},
            "chunk_concurrency": {"type": "integer", "default": 4, "minimum": 1, "maximum": 20},
            # Endpoint
            "model_slug": {
                "type": "string",
                "description": "Override Replicate model slug. Default: extenso-claude/tada-voice (or TADA_MODEL_SLUG env).",
            },
            "model_version": {
                "type": "string",
                "description": "Pin a specific Replicate version. Defaults to latest.",
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=200, network_required=True,
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = [
        "text", "prompt_audio", "prompt_transcript", "language",
        "text_temperature", "acoustic_cfg_scale", "noise_temperature", "seed",
    ]
    side_effects = ["writes audio file to output_path", "calls Replicate API"]
    user_visible_verification = [
        "Listen for voice match, prosody naturalness, artifacts",
    ]

    # ------------------------------------------------------------------ env

    def _get_api_token(self) -> str | None:
        return (
            os.environ.get("REPLICATE_API_TOKEN")
            or os.environ.get("REPLICATE_API_KEY")
        )

    def _model_slug(self, inputs: dict[str, Any]) -> str:
        return (
            inputs.get("model_slug")
            or os.environ.get("TADA_MODEL_SLUG")
            or self.DEFAULT_MODEL_SLUG
        )

    def get_status(self) -> ToolStatus:
        if not self._get_api_token():
            return ToolStatus.UNAVAILABLE
        # The self-hosted Replicate model may or may not be live. Mark
        # DEGRADED rather than UNAVAILABLE so the registry still surfaces it.
        # The execute() call will surface a clear error if the model 404s.
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        # L40S ~$0.001125/sec; predict time ~5-10 s for ~10 s of audio at N=1.
        candidates = max(1, int(inputs.get("num_acoustic_candidates", 1)))
        per_call = 0.012 * candidates
        if inputs.get("chunk_long_text"):
            text = inputs.get("text", "")
            target = int(inputs.get("chunk_target_chars", 600))
            n = max(1, (len(text) + target - 1) // target)
            return round(per_call * n, 4)
        return round(per_call, 4)

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        candidates = max(1, int(inputs.get("num_acoustic_candidates", 1)))
        if inputs.get("chunk_long_text"):
            text = inputs.get("text", "")
            target = int(inputs.get("chunk_target_chars", 600))
            n = max(1, (len(text) + target - 1) // target)
            concurrency = max(1, int(inputs.get("chunk_concurrency", 4)))
            return round((n / concurrency) * 12 * candidates, 1)
        return 10.0 * candidates

    # ----------------------------------------------------- file handling

    def _resolve_audio_input(self, value: str, token: str) -> str:
        if value.startswith(("http://", "https://", "data:")):
            return value
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"prompt_audio not found: {path}")
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
            raise RuntimeError(f"Replicate upload missing URL: {data}")
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

    # ----------------------------------------------------- chunking

    @staticmethod
    def _split_text(text: str, target_chars: int) -> list[str]:
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

    def _resolve_version(self, slug: str, token: str) -> str:
        """Look up latest version id for a model slug."""
        import requests
        resp = requests.get(
            f"https://api.replicate.com/v1/models/{slug}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if resp.status_code == 404:
            raise RuntimeError(
                f"Replicate model {slug} not found. Has the self-host been "
                "created and built? See "
                "https://github.com/extenso-claude/tada/blob/main/REPLICATE_DEPLOY.md"
            )
        resp.raise_for_status()
        version = resp.json().get("latest_version", {}).get("id")
        if not version:
            raise RuntimeError(
                f"Replicate model {slug} has no latest_version — build may "
                "still be in progress."
            )
        return version

    def _predict_one(
        self,
        text: str,
        replicate_input: dict[str, Any],
        token: str,
        version: str,
        timeout: int = 600,
    ) -> bytes:
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
            time.sleep(3)
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

        audio_resp = requests.get(audio_url, timeout=300)
        audio_resp.raise_for_status()
        return audio_resp.content

    # ----------------------------------------------------- stitch

    @staticmethod
    def _stitch_wavs(parts: list[bytes], output_path: Path) -> None:
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
            cmd: list[str] = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
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

        prompt_audio = inputs.get("prompt_audio") or inputs.get("voice_id")
        if not prompt_audio:
            return ToolResult(
                success=False,
                error="prompt_audio (or voice_id) is required — URL or local path to the reference voice clip.",
            )

        prompt_transcript = inputs.get("prompt_transcript")
        language = inputs.get("language", "en")
        if not prompt_transcript and language != "en":
            return ToolResult(
                success=False,
                error=f"prompt_transcript is required for language={language!r} (TADA's built-in ASR is English-only).",
            )

        slug = self._model_slug(inputs)
        start = time.time()

        try:
            version = inputs.get("model_version") or self._resolve_version(slug, token)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

        try:
            prompt_audio_url = self._resolve_audio_input(prompt_audio, token)
        except Exception as e:
            return ToolResult(success=False, error=f"prompt_audio upload failed: {e}")

        rep_input: dict[str, Any] = {
            "prompt_audio": prompt_audio_url,
            "prompt_transcript": prompt_transcript or "",
            "language": language,
        }
        passthrough = [
            "text_do_sample", "text_temperature", "text_top_k", "text_top_p",
            "text_repetition_penalty", "acoustic_cfg_scale", "duration_cfg_scale",
            "cfg_schedule", "noise_temperature", "num_flow_matching_steps",
            "time_schedule", "num_acoustic_candidates", "scorer",
            "spkr_verification_weight", "speed_up_factor",
            "negative_condition_source", "text_only_logit_scale",
            "num_extra_steps", "normalize_text", "seed",
        ]
        for key in passthrough:
            if key in inputs and inputs[key] is not None:
                rep_input[key] = inputs[key]

        output_path = Path(inputs.get("output_path") or f"tada_{int(start)}.wav")

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
                    parts = [f.result() for f in futures]
                self._stitch_wavs(parts, output_path)
                n_chunks = len(chunks)
            else:
                audio_bytes = self._predict_one(text, rep_input, token, version)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(audio_bytes)
                n_chunks = 1
        except Exception as e:
            return ToolResult(success=False, error=f"TADA synthesis failed: {e}")

        params_used = {
            k: v for k, v in rep_input.items()
            if k not in ("prompt_audio",)
        }
        return ToolResult(
            success=True,
            data={
                "provider": "tada",
                "gateway": "replicate",
                "model": slug,
                "model_version": version,
                "output": str(output_path),
                "output_path": str(output_path),
                "format": "wav",
                "n_chunks": n_chunks,
                "prompt_audio_url": prompt_audio_url,
                "params_used": params_used,
            },
            artifacts=[str(output_path)],
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            model=slug,
        )
