"""Inworld TTS-2 text-to-speech provider tool.

Wraps the Inworld TTS-2 REST API at https://api.inworld.ai/tts/v1/voice.
Supports CREATIVE/BALANCED/STABLE delivery modes and inline emotion /
non-verbal tags (e.g. ``[breathe]``, ``[laugh]``) for documentary-grade VO.

Inworld enforces a 2000-character cap per request. This tool transparently
splits longer text on sentence boundaries, generates each chunk as MP3, then
concatenates the chunks into a single output file via ffmpeg's concat demuxer.
"""

from __future__ import annotations

import base64
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


# Inworld TTS-2 hard cap per request body. Anything longer must be chunked.
_MAX_CHARS_PER_REQUEST = 2000

# Sentence-boundary splitter. We split AFTER one of these delimiters when
# followed by whitespace, keeping the delimiter attached to the left chunk.
# Order matters slightly (em-dash first so we don't double-match), but the
# regex below alternates with non-overlapping matches.
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?—])\s+|\n+")


def _split_into_sentences(text: str) -> list[str]:
    """Split text on sentence-ish boundaries: `. `, `? `, `! `, em-dash + space, newlines."""
    parts = [p.strip() for p in _SENTENCE_BOUNDARY_RE.split(text) if p and p.strip()]
    return parts


def _chunk_text(text: str, max_chars: int = _MAX_CHARS_PER_REQUEST) -> list[str]:
    """Pack sentences into chunks <= max_chars without splitting a sentence.

    If a single sentence is itself longer than max_chars (e.g. a comma-heavy
    paragraph with no terminal punctuation), we hard-split it on the last
    whitespace before the cap.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    sentences = _split_into_sentences(text)
    chunks: list[str] = []
    buf = ""

    def _flush() -> None:
        nonlocal buf
        if buf.strip():
            chunks.append(buf.strip())
        buf = ""

    for sentence in sentences:
        # Hard-split oversized single sentences.
        while len(sentence) > max_chars:
            head = sentence[:max_chars]
            cut = head.rfind(" ")
            if cut == -1:
                # No whitespace at all - just hard cut.
                cut = max_chars
            _flush()
            chunks.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()

        # Would adding this sentence (plus a space) exceed the cap?
        if buf and len(buf) + 1 + len(sentence) > max_chars:
            _flush()
        buf = sentence if not buf else f"{buf} {sentence}"

    _flush()
    return chunks


class InworldTTS(BaseTool):
    name = "inworld_tts"
    version = "0.1.0"
    tier = ToolTier.VOICE
    capability = "tts"
    provider = "inworld"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = ["env:INWORLD_TTS_API_KEY", "cmd:ffmpeg"]
    install_instructions = (
        "Set the INWORLD_TTS_API_KEY environment variable in .env:\n"
        "  INWORLD_TTS_API_KEY=<base64-encoded-key>\n"
        "The key is pre-encoded base64 and is sent as `Authorization: Basic <key>`.\n"
        "Also requires ffmpeg on PATH for chunk concatenation."
    )
    fallback = "elevenlabs_tts"
    fallback_tools = ["elevenlabs_tts", "openai_tts", "piper_tts"]
    agent_skills = ["text-to-speech"]

    capabilities = [
        "text_to_speech",
        "voice_selection",
        "inline_emotion_tags",
        "delivery_mode_control",
        "long_form_chunking",
    ]
    supports = {
        "voice_cloning": False,
        "multilingual": True,
        "offline": False,
        "native_audio": True,
        "inline_tags": True,
        "delivery_modes": ["STABLE", "BALANCED", "CREATIVE"],
    }
    best_for = [
        "long-form documentary narration",
        "expressive VO with inline [breathe] / [laugh] tags",
        "Tyler-style measured documentary delivery",
    ]
    not_good_for = [
        "fully offline production",
        "ultra-low-latency real-time speech",
    ]

    input_schema = {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {
                "type": "string",
                "description": (
                    "Text to convert to speech. May contain inline emotion / "
                    "non-verbal tags like [breathe], [laugh], [sigh]. "
                    "Text longer than 2000 chars is auto-chunked on sentence "
                    "boundaries and concatenated via ffmpeg."
                ),
            },
            "voice_id": {
                "type": "string",
                "default": "Tyler",
                "description": "Inworld voice id (e.g. 'Tyler').",
            },
            "model_id": {
                "type": "string",
                "default": "inworld-tts-2",
                "description": "Inworld TTS model id.",
            },
            "delivery_mode": {
                "type": "string",
                "default": "CREATIVE",
                "enum": ["STABLE", "BALANCED", "CREATIVE"],
                "description": "TTS-2 delivery mode. CREATIVE = most expressive.",
            },
            "speaking_rate": {
                "type": "number",
                "default": 1.0,
                "minimum": 0.5,
                "maximum": 2.0,
                "description": "Speaking rate multiplier.",
            },
            "language": {
                "type": "string",
                "default": "en-US",
                "description": "BCP-47 language tag.",
            },
            "apply_text_normalization": {
                "type": "string",
                "default": "ON",
                "enum": ["ON", "OFF"],
            },
            "output_path": {
                "type": "string",
                "description": "Where to write the final audio file.",
            },
            "output_format": {
                "type": "string",
                "default": "mp3",
                "enum": ["mp3", "wav"],
                "description": "mp3 -> MP3 @ 48000 Hz; wav -> LINEAR16 @ 48000 Hz.",
            },
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=100, network_required=True
    )
    retry_policy = RetryPolicy(
        max_retries=3,
        backoff_seconds=2.0,
        retryable_errors=["rate_limit", "timeout", "server_error"],
    )
    idempotency_key_fields = ["text", "voice_id", "model_id", "delivery_mode", "speaking_rate"]
    side_effects = [
        "writes audio file to output_path",
        "calls Inworld TTS API (paid)",
        "writes temporary per-chunk MP3 files then concatenates via ffmpeg",
    ]
    user_visible_verification = [
        "Listen to generated audio for natural delivery + tag execution",
        "Verify chunk boundaries are seamless (no audible click)",
    ]

    DEFAULT_VOICE_ID = "Tyler"
    DEFAULT_MODEL = "inworld-tts-2"
    ENDPOINT = "https://api.inworld.ai/tts/v1/voice"
    # ~ $0.000020 per character per Inworld's tiered pricing (rough heuristic).
    COST_PER_CHAR_USD = 0.000020

    # ---- Status & cost ----

    def get_status(self) -> ToolStatus:
        if not os.environ.get("INWORLD_TTS_API_KEY"):
            return ToolStatus.UNAVAILABLE
        # check_dependencies also walks the cmd:ffmpeg entry.
        try:
            self.check_dependencies()
        except Exception:
            return ToolStatus.DEGRADED
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        chars = len(inputs.get("text", ""))
        return round(chars * self.COST_PER_CHAR_USD, 6)

    # ---- Execute ----

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = os.environ.get("INWORLD_TTS_API_KEY")
        if not api_key:
            return ToolResult(
                success=False,
                error="No Inworld API key. " + self.install_instructions,
            )

        text = inputs.get("text", "").strip()
        if not text:
            return ToolResult(success=False, error="Inworld TTS requires non-empty text.")

        start = time.time()
        try:
            result = self._generate(inputs, api_key, text)
        except Exception as exc:
            return ToolResult(success=False, error=f"Inworld TTS failed: {exc}")

        result.duration_seconds = round(time.time() - start, 2)
        result.cost_usd = self.estimate_cost(inputs)
        return result

    # ---- Internal ----

    def _api_audio_config(self, output_format: str, speaking_rate: float) -> dict[str, Any]:
        if output_format == "wav":
            return {
                "audioEncoding": "LINEAR16",
                "sampleRateHertz": 48000,
                "speakingRate": speaking_rate,
            }
        return {
            "audioEncoding": "MP3",
            "sampleRateHertz": 48000,
            "speakingRate": speaking_rate,
        }

    def _build_body(self, inputs: dict[str, Any], chunk_text: str) -> dict[str, Any]:
        return {
            "text": chunk_text,
            "voiceId": inputs.get("voice_id", self.DEFAULT_VOICE_ID),
            "modelId": inputs.get("model_id", self.DEFAULT_MODEL),
            "audioConfig": self._api_audio_config(
                inputs.get("output_format", "mp3"),
                float(inputs.get("speaking_rate", 1.0)),
            ),
            "deliveryMode": inputs.get("delivery_mode", "CREATIVE"),
            "applyTextNormalization": inputs.get("apply_text_normalization", "ON"),
            "language": inputs.get("language", "en-US"),
            "timestampType": "WORD",
        }

    def _post_with_retries(
        self, body: dict[str, Any], api_key: str
    ) -> "requests.Response":  # type: ignore[name-defined]
        import requests

        # Auth header: pass the key EXACTLY as stored (already base64-encoded).
        headers = {
            "Authorization": f"Basic {api_key}",
            "Content-Type": "application/json",
        }

        max_retries = self.retry_policy.max_retries
        backoff = self.retry_policy.backoff_seconds
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(self.ENDPOINT, headers=headers, json=body, timeout=180)
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error = exc
                if attempt < max_retries:
                    time.sleep(backoff * (2 ** attempt))
                    continue
                raise

            # Retry on 429 / 5xx.
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                last_error = RuntimeError(
                    f"Inworld API {resp.status_code}: {resp.text[:300]}"
                )
                if attempt < max_retries:
                    time.sleep(backoff * (2 ** attempt))
                    continue
                raise last_error

            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Inworld API {resp.status_code}: {resp.text[:500]}"
                )

            return resp

        # Should never reach here, but safeguard.
        if last_error:
            raise last_error
        raise RuntimeError("Inworld TTS: exhausted retries with no response")

    def _generate(
        self, inputs: dict[str, Any], api_key: str, text: str
    ) -> ToolResult:
        output_format = inputs.get("output_format", "mp3")
        ext = "mp3" if output_format == "mp3" else "wav"

        output_path = Path(
            inputs.get("output_path") or f"inworld_tts_output.{ext}"
        ).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        chunks = _chunk_text(text)

        # Fast path: single chunk -> write directly.
        if len(chunks) == 1:
            body = self._build_body(inputs, chunks[0])
            resp = self._post_with_retries(body, api_key)
            audio_bytes = self._decode_audio(resp)
            output_path.write_bytes(audio_bytes)
            return ToolResult(
                success=True,
                data={
                    "provider": self.provider,
                    "model": body["modelId"],
                    "voice_id": body["voiceId"],
                    "delivery_mode": body["deliveryMode"],
                    "text_length": len(text),
                    "chunks": 1,
                    "output": str(output_path),
                    "format": output_format,
                    "bytes": len(audio_bytes),
                },
                artifacts=[str(output_path)],
                model=body["modelId"],
            )

        # Multi-chunk path: generate each, then ffmpeg-concat.
        with tempfile.TemporaryDirectory(prefix="inworld_tts_") as tmpdir:
            tmpdir_path = Path(tmpdir)
            part_paths: list[Path] = []
            for i, chunk in enumerate(chunks):
                body = self._build_body(inputs, chunk)
                resp = self._post_with_retries(body, api_key)
                audio_bytes = self._decode_audio(resp)
                part = tmpdir_path / f"chunk_{i:04d}.{ext}"
                part.write_bytes(audio_bytes)
                part_paths.append(part)

            self._ffmpeg_concat(part_paths, output_path, output_format)

        total_bytes = output_path.stat().st_size
        return ToolResult(
            success=True,
            data={
                "provider": self.provider,
                "model": inputs.get("model_id", self.DEFAULT_MODEL),
                "voice_id": inputs.get("voice_id", self.DEFAULT_VOICE_ID),
                "delivery_mode": inputs.get("delivery_mode", "CREATIVE"),
                "text_length": len(text),
                "chunks": len(chunks),
                "output": str(output_path),
                "format": output_format,
                "bytes": total_bytes,
            },
            artifacts=[str(output_path)],
            model=inputs.get("model_id", self.DEFAULT_MODEL),
        )

    @staticmethod
    def _decode_audio(response: "requests.Response") -> bytes:  # type: ignore[name-defined]
        """Inworld returns either JSON with a base64 `audioContent` field or
        raw binary audio depending on the deployment. Handle both."""
        ctype = response.headers.get("Content-Type", "")
        if "application/json" in ctype or response.content.lstrip().startswith(b"{"):
            payload = response.json()
            b64 = payload.get("audioContent")
            if not b64:
                raise RuntimeError(
                    f"Inworld response missing 'audioContent': {str(payload)[:300]}"
                )
            return base64.b64decode(b64)
        return response.content

    @staticmethod
    def _ffmpeg_concat(
        parts: list[Path], output_path: Path, output_format: str
    ) -> None:
        """Concatenate chunk audio files via ffmpeg's concat demuxer.

        For MP3 we use stream-copy (no re-encode); for WAV we let ffmpeg
        re-mux. The output is a single contiguous file at output_path.
        """
        if not parts:
            raise RuntimeError("ffmpeg concat: no input parts")

        # Write the concat list file alongside the parts.
        listfile = parts[0].parent / "concat_list.txt"
        listfile.write_text(
            "\n".join(f"file '{p.as_posix()}'" for p in parts) + "\n",
            encoding="utf-8",
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listfile),
        ]
        if output_format == "mp3":
            cmd += ["-c", "copy"]
        else:
            cmd += ["-c:a", "pcm_s16le"]
        cmd += [str(output_path)]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                f"ffmpeg concat failed (exit {proc.returncode}): {proc.stderr.strip()}"
            )
