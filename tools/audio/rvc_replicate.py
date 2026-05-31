"""RVC v2 voice conversion via Replicate (pseudoram/rvc-v2).

This is voice CONVERSION (audio -> audio in target voice), not TTS. Typical
chain in OpenMontage:
  IndexTTS-2 / TADA / ElevenLabs ── synth text in any voice ──>
    rvc_replicate ── convert into Huxley / Mr. Calder voice ──> final WAV

The trained RVC model is supplied as ``custom_rvc_model_download_url`` — a
public URL to a ZIP containing ``.pth`` + ``.index`` files produced by RVC
training. Built-in presets (Obama/Trump/Sandy/Rogan) are also exposed but the
expected flow is CUSTOM.

Pricing: ~$0.01-0.03 per minute of source audio on Replicate (varies by
``f0_method``). Predict time scales roughly with input length.
Reference: https://replicate.com/pseudoram/rvc-v2
"""

from __future__ import annotations

import os
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


class RVCReplicate(BaseTool):
    name = "rvc_replicate"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "voice_conversion"
    provider = "rvc"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set REPLICATE_API_KEY (or REPLICATE_API_TOKEN) to your Replicate API "
        "token. Get one at https://replicate.com/account/api-tokens"
    )
    fallback_tools = []
    agent_skills = ["text-to-speech"]

    capabilities = [
        "voice_conversion",
        "custom_voice_model_loading",
        "pitch_shift",
    ]
    supports = {
        "voice_conversion": True,
        "custom_trained_models": True,
        "pitch_shift": True,
        "offline": False,
    }
    best_for = [
        "converting a synthesized or recorded audio file into a custom-trained voice",
        "applying Grandpa Huxley / Mr. Calder RVC models to TTS output",
        "post-processing TTS to match a specific trained character voice",
    ]
    not_good_for = [
        "fully offline production",
        "text-to-speech (this is voice conversion — use IndexTTS-2 or TADA for TTS)",
    ]

    MODEL_SLUG = "pseudoram/rvc-v2"
    DEFAULT_VERSION = "d18e2e0a6a6d3af183cc09622cebba8555ec9a9e66983261fc64c8b1572b7dce"

    input_schema = {
        "type": "object",
        "required": ["input_audio"],
        "properties": {
            "input_audio": {
                "type": "string",
                "description": "Source audio to convert. URL or local file path (WAV/MP3).",
            },
            # Voice model selection
            "rvc_model": {
                "type": "string",
                "enum": ["Obama", "Trump", "Sandy", "Rogan", "CUSTOM"],
                "default": "CUSTOM",
                "description": "Built-in preset, or CUSTOM with custom_rvc_model_download_url.",
            },
            "custom_rvc_model_download_url": {
                "type": "string",
                "description": "URL to a ZIP containing .pth + .index files from RVC training. Required when rvc_model=CUSTOM.",
            },
            # Pitch
            "pitch_change": {
                "type": "number", "default": 0,
                "description": "Pitch shift in semitones (+/-). Use +12 for octave up, -12 down. 0 keeps source pitch.",
            },
            # Voice character knobs
            "index_rate": {
                "type": "number", "minimum": 0, "maximum": 1, "default": 0.5,
                "description": "How much of the trained accent to leave in. 0 = none, 1 = full.",
            },
            "filter_radius": {
                "type": "integer", "minimum": 0, "maximum": 7, "default": 3,
                "description": "If >=3, median-filter harvested pitch results.",
            },
            "rms_mix_rate": {
                "type": "number", "minimum": 0, "maximum": 1, "default": 0.25,
                "description": "0 = preserve original loudness contour, 1 = fixed loudness.",
            },
            "f0_method": {
                "type": "string",
                "enum": ["rmvpe", "mangio-crepe"],
                "default": "rmvpe",
                "description": "Pitch detection. rmvpe = vocal clarity. mangio-crepe = smoother vocals.",
            },
            "crepe_hop_length": {
                "type": "integer", "default": 128,
                "description": "How often mangio-crepe checks pitch (ms). Only used when f0_method=mangio-crepe.",
            },
            "protect": {
                "type": "number", "minimum": 0, "maximum": 0.5, "default": 0.33,
                "description": "Preserve breath / voiceless consonants from source. 0.5 disables.",
            },
            # Output
            "output_format": {
                "type": "string",
                "enum": ["mp3", "wav"],
                "default": "mp3",
                "description": "wav for best quality (larger), mp3 for smaller file size.",
            },
            "model_version": {
                "type": "string",
                "description": "Override pinned Replicate model version.",
            },
            "output_path": {
                "type": "string",
                "description": "Local path to write the converted audio.",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=300, network_required=True,
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = [
        "input_audio", "custom_rvc_model_download_url", "rvc_model",
        "pitch_change", "index_rate", "f0_method",
    ]
    side_effects = ["writes audio file to output_path", "calls Replicate API"]
    user_visible_verification = [
        "Listen to the output for voice match, naturalness, pitch, and artifacts",
        "Compare against a reference clip of the target voice",
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
        # Replicate bills per second on T4/A40. Roughly $0.015 per minute of
        # source audio for default rmvpe pitch detection.
        return 0.02

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 30.0

    # ----------------------------------------------------- file handling

    def _resolve_audio_input(self, value: str, token: str) -> str:
        if value.startswith(("http://", "https://", "data:")):
            return value
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Input audio not found: {path}")
        return self._upload_to_replicate(path, token)

    def _upload_to_replicate(self, path: Path, token: str) -> str:
        import requests
        with open(path, "rb") as f:
            resp = requests.post(
                "https://api.replicate.com/v1/files",
                headers={"Authorization": f"Bearer {token}"},
                files={"content": (path.name, f, self._content_type(path))},
                timeout=300,
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

    # ----------------------------------------------------- replicate call

    def _predict(
        self,
        replicate_input: dict[str, Any],
        token: str,
        version: str,
        timeout: int = 600,
    ) -> bytes:
        import requests
        from tools.audio._replicate_common import replicate_post_with_retry

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "wait=60",
        }
        submit = replicate_post_with_retry(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json_payload={"version": version, "input": replicate_input},
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
            raise RuntimeError(f"Unexpected Replicate output: {output!r}")

        audio_resp = requests.get(audio_url, timeout=600)
        audio_resp.raise_for_status()
        return audio_resp.content

    # ------------------------------------------------------------ main

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        token = self._get_api_token()
        if not token:
            return ToolResult(
                success=False,
                error="REPLICATE_API_KEY/REPLICATE_API_TOKEN not set. " + self.install_instructions,
            )

        input_audio = inputs.get("input_audio")
        if not input_audio:
            return ToolResult(success=False, error="input_audio is required (URL or local path)")

        rvc_model = inputs.get("rvc_model", "CUSTOM")
        custom_url = inputs.get("custom_rvc_model_download_url")
        if rvc_model == "CUSTOM" and not custom_url:
            return ToolResult(
                success=False,
                error="rvc_model=CUSTOM requires custom_rvc_model_download_url (ZIP with .pth + .index)",
            )

        start = time.time()
        version = inputs.get("model_version") or self.DEFAULT_VERSION

        try:
            input_url = self._resolve_audio_input(input_audio, token)
        except Exception as e:
            return ToolResult(success=False, error=f"Input audio upload failed: {e}")

        rep_input: dict[str, Any] = {"input_audio": input_url, "rvc_model": rvc_model}
        if custom_url:
            rep_input["custom_rvc_model_download_url"] = custom_url
        for key in [
            "pitch_change", "index_rate", "filter_radius", "rms_mix_rate",
            "f0_method", "crepe_hop_length", "protect", "output_format",
        ]:
            if key in inputs and inputs[key] is not None:
                rep_input[key] = inputs[key]

        output_format = inputs.get("output_format", "mp3")
        suffix = ".mp3" if output_format == "mp3" else ".wav"
        output_path = Path(
            inputs.get("output_path") or f"rvc_{int(start)}{suffix}"
        )

        try:
            audio_bytes = self._predict(rep_input, token, version)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(audio_bytes)
        except Exception as e:
            return ToolResult(success=False, error=f"RVC v2 conversion failed: {e}")

        params_used = {
            k: v for k, v in rep_input.items()
            if k not in ("input_audio", "custom_rvc_model_download_url")
        }
        return ToolResult(
            success=True,
            data={
                "provider": "rvc",
                "gateway": "replicate",
                "model": self.MODEL_SLUG,
                "model_version": version,
                "output": str(output_path),
                "output_path": str(output_path),
                "format": output_format,
                "input_audio_url": input_url,
                "custom_rvc_model_download_url": custom_url,
                "rvc_model": rvc_model,
                "params_used": params_used,
            },
            artifacts=[str(output_path)],
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            model=self.MODEL_SLUG,
        )
