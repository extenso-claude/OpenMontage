"""Topaz video upscale via fal.ai (Proteus / Starlight family).

The 1080p fallback path for OpenMontage. Any AI generator whose wrapper is
720p-capped (currently `seedance_video` on fal.ai, `runway_video`,
`kling_video`, `minimax_video`) can route its output through this tool to
satisfy the 1080p-minimum delivery rule.

Pricing (fal.ai, verified May 2026):
  - $0.01/s for output up to 720p
  - $0.02/s for output 720p -> 1080p
  - $0.08/s for output above 1080p (e.g. 4K)
  - Doubled when target_fps is 60+
  - Gaia 2 model gets a 50% discount

Per 5-second clip at 1080p / 30fps: $0.10 — still tiny compared to Tier-3
generation. Cheap enough that it's the default route for any 720p-capped
generator when delivery_promise.min_resolution >= 1080p.

The fal.ai endpoint takes `upscale_factor` (a float multiplier), so the
wrapper probes the source video's dimensions and picks the smallest factor
that hits the requested target_resolution. If ffprobe isn't available we
fall back to the user-supplied `upscale_factor`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
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


_FAL_MODEL = "fal-ai/topaz/upscale/video"

# Dollars per output-second by output resolution band, at 24-30 fps.
# Doubles for 60fps (handled in estimate_cost).
_USD_PER_SECOND_BY_OUTPUT = {
    "720p_or_below": 0.01,
    "720p_to_1080p": 0.02,
    "above_1080p": 0.08,
}


class TopazUpscale(BaseTool):
    name = "topaz_upscale"
    version = "0.2.0"
    tier = ToolTier.ENHANCE
    capability = "enhancement"
    provider = "topaz"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set FAL_KEY (or FAL_AI_API_KEY) to your fal.ai API key.\n"
        "  Get one at https://fal.ai/dashboard/keys\n"
        "Same key already powers seedance_video, kling_video, etc."
    )
    agent_skills = ["ffmpeg"]

    capabilities = ["video_upscale", "frame_interpolation"]
    supports = {
        "video_upscale": True,
        "ai_generated_input": True,         # Tuned for AI artifacts, not live action
        "max_input_resolution": "any",
        "max_output_resolution": "4k",
        "min_output_resolution": "720p",
        "frame_interpolation": True,        # via target_fps
    }
    best_for = [
        "satisfying the 1080p minimum delivery rule when a generator outputs 720p",
        "upscaling AI-generated clips from Seedance / Kling / MiniMax / Runway / LTX",
        "frame interpolation up to 60 fps for smoother motion",
        "selective upscale of approved takes — iterate cheap, finalize sharp",
    ]
    not_good_for = [
        "live-action footage cleanup (use Real-ESRGAN local or Topaz desktop)",
        "free-tier workflows — costs fal.ai credits",
        "clips already at target resolution — adds tax for no gain",
    ]
    fallback_tools = ["upscale"]   # Real-ESRGAN local fallback
    quality_score = 0.9

    # Models exposed by fal.ai's Topaz endpoint. Default is Starlight Precise
    # 2.5 — the AI-tuned creative upscaler that handles diffusion artifacts
    # better than the live-action-tuned Proteus default.
    _MODELS = [
        "Proteus",
        "Artemis HQ", "Artemis MQ", "Artemis LQ",
        "Nyx", "Nyx Fast", "Nyx XL", "Nyx HF",
        "Gaia HQ", "Gaia CG", "Gaia 2",
        "Starlight Precise 1", "Starlight Precise 2", "Starlight Precise 2.5",
        "Starlight HQ", "Starlight Mini", "Starlight Sharp",
        "Starlight Fast 1", "Starlight Fast 2",
    ]

    input_schema = {
        "type": "object",
        "properties": {
            "video_url": {
                "type": "string",
                "description": "Public URL of the source video. Preferred over video_path.",
            },
            "video_path": {
                "type": "string",
                "description": "Local path to source video. Auto-uploaded to fal.ai storage.",
            },
            "target_resolution": {
                "type": "string",
                "enum": ["720p", "1080p", "1440p", "4k"],
                "default": "1080p",
                "description": (
                    "Convenience input. Wrapper probes source dimensions and picks "
                    "the smallest upscale_factor that hits the requested band. "
                    "Ignored if upscale_factor is provided explicitly."
                ),
            },
            "upscale_factor": {
                "type": "number",
                "minimum": 1.0,
                "maximum": 8.0,
                "description": (
                    "Direct multiplier (e.g. 1.5 to go 720p->1080p, 2.0 for 720p->1440p). "
                    "If set, takes precedence over target_resolution."
                ),
            },
            "target_fps": {
                "type": "integer",
                "minimum": 15,
                "maximum": 120,
                "description": (
                    "If set, enables Apollo frame interpolation. Common values: 30 (default "
                    "for most AI generators), 60 (smooth motion — 2x cost on fal.ai)."
                ),
            },
            "model": {
                "type": "string",
                "enum": _MODELS,
                "default": "Starlight Precise 2.5",
                "description": (
                    "Enhancement model. Starlight Precise 2.5 is best for AI-generated input "
                    "(diffusion artifact aware). Proteus / Artemis are for live-action."
                ),
            },
            "h264_output": {
                "type": "boolean",
                "default": True,
                "description": "Use H.264 (default). False uses H.265 (smaller files, less compatible).",
            },
            "output_path": {
                "type": "string",
                "description": "Where to save the upscaled mp4. Defaults to <input>_upscaled.mp4.",
            },
            "duration_hint_seconds": {
                "type": "number",
                "description": "Source clip duration in seconds. Improves cost estimate accuracy.",
            },
            "poll_interval_seconds": {"type": "integer", "minimum": 2, "default": 5},
            "timeout_seconds": {"type": "integer", "minimum": 60, "default": 900},
        },
        # Either video_url or video_path is required — enforced in execute().
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=2000, network_required=True,
    )
    retry_policy = RetryPolicy(
        max_retries=2, backoff_seconds=10.0,
        retryable_errors=["rate_limit", "timeout", "server_error"],
    )
    idempotency_key_fields = [
        "video_url", "video_path", "target_resolution", "upscale_factor", "target_fps", "model",
    ]
    side_effects = ["writes upscaled video to output_path", "calls fal.ai API"]
    user_visible_verification = [
        "Confirm output resolution via ffprobe (must be >= 1920x1080 for 1080p target)",
        "Spot-check upscaled clip for diffusion artifacts vs source",
    ]

    # ------------------------------------------------------------------
    # Status & cost
    # ------------------------------------------------------------------

    def _get_api_key(self) -> str | None:
        return os.environ.get("FAL_KEY") or os.environ.get("FAL_AI_API_KEY")

    def get_status(self) -> ToolStatus:
        return ToolStatus.AVAILABLE if self._get_api_key() else ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        # Source duration. Fall back to 5s if unknown.
        duration = float(inputs.get("duration_hint_seconds") or 5.0)

        target_resolution = inputs.get("target_resolution", "1080p").lower()
        if target_resolution in ("720p",):
            band = "720p_or_below"
        elif target_resolution in ("1080p",):
            band = "720p_to_1080p"
        else:
            band = "above_1080p"
        rate = _USD_PER_SECOND_BY_OUTPUT[band]

        # 60fps target doubles the price.
        target_fps = inputs.get("target_fps")
        if target_fps and int(target_fps) >= 60:
            rate *= 2.0

        # Gaia 2 gets a 50% discount per fal docs.
        if inputs.get("model") == "Gaia 2":
            rate *= 0.5

        return round(rate * duration, 4)

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        # Diffusion-based Topaz is roughly real-time per source frame on
        # fal's GPUs. 5s clip @ 30fps = 150 frames; budget ~2-3 min wall-clock.
        return 180.0

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(
                success=False,
                error="FAL_KEY not set. " + self.install_instructions,
            )

        video_url = inputs.get("video_url")
        video_path = inputs.get("video_path")
        if not video_url and not video_path:
            return ToolResult(
                success=False,
                error="topaz_upscale requires video_url or video_path",
            )

        import requests

        start = time.time()

        # 1. Get a public URL for the source clip.
        try:
            if not video_url:
                from tools.video._shared import upload_image_fal
                # upload_image_fal works for any binary; fal.ai storage is content-type aware.
                video_url = self._upload_video_fal(video_path, api_key)
        except Exception as e:
            return ToolResult(success=False, error=f"fal.ai upload failed: {e}")

        # 2. Decide upscale_factor: explicit input wins, else derive from target_resolution.
        upscale_factor = inputs.get("upscale_factor")
        if upscale_factor is None:
            try:
                upscale_factor = self._compute_upscale_factor(
                    video_path or video_url,
                    target_resolution=inputs.get("target_resolution", "1080p"),
                )
            except Exception:
                # Couldn't probe — pick a safe default that hits 1080p from 720p.
                upscale_factor = 1.5

        # 3. Build payload.
        payload: dict[str, Any] = {
            "video_url": video_url,
            "upscale_factor": float(upscale_factor),
            "model": inputs.get("model", "Starlight Precise 2.5"),
            "H264_output": bool(inputs.get("h264_output", True)),
        }
        if inputs.get("target_fps"):
            payload["target_fps"] = int(inputs["target_fps"])

        headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        }

        poll_interval = max(2, int(inputs.get("poll_interval_seconds", 5)))
        timeout = max(60, int(inputs.get("timeout_seconds", 900)))

        try:
            submit = requests.post(
                f"https://queue.fal.run/{_FAL_MODEL}",
                headers=headers,
                json=payload,
                timeout=60,
            )
            submit.raise_for_status()
            queue_data = submit.json()
            status_url = queue_data.get("status_url")
            response_url = queue_data.get("response_url")
            if not status_url or not response_url:
                return ToolResult(
                    success=False,
                    error=f"fal.ai queue response missing URLs: {queue_data}",
                )

            deadline = start + timeout
            while True:
                if time.time() > deadline:
                    return ToolResult(
                        success=False,
                        error=f"Topaz upscale timed out after {timeout}s",
                    )
                time.sleep(poll_interval)
                status_resp = requests.get(status_url, headers=headers, timeout=30)
                status_resp.raise_for_status()
                status = status_resp.json().get("status", "UNKNOWN")
                if status == "COMPLETED":
                    break
                if status in ("FAILED", "CANCELLED"):
                    return ToolResult(
                        success=False,
                        error=f"Topaz upscale {status.lower()}: {status_resp.text}",
                    )

            result_resp = requests.get(response_url, headers=headers, timeout=60)
            result_resp.raise_for_status()
            data = result_resp.json()
            output_video_url = (data.get("video") or {}).get("url")
            if not isinstance(output_video_url, str):
                return ToolResult(
                    success=False,
                    error=f"Unexpected fal.ai response shape: {data}",
                )

            video_response = requests.get(output_video_url, timeout=300)
            video_response.raise_for_status()

            output_path = Path(self._resolve_output_path(inputs, video_path))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(video_response.content)

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Topaz upscale failed: {e}",
            )

        from tools.video._shared import probe_output

        probed = probe_output(output_path)
        return ToolResult(
            success=True,
            data={
                "provider": "topaz",
                "gateway": "fal.ai",
                "model": payload["model"],
                "input_video_url": video_url,
                "upscale_factor": payload["upscale_factor"],
                "target_fps": payload.get("target_fps"),
                "output": str(output_path),
                "output_path": str(output_path),
                "format": "mp4",
                **probed,
            },
            artifacts=[str(output_path)],
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            model=_FAL_MODEL,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_output_path(inputs: dict[str, Any], video_path: str | None) -> str:
        if inputs.get("output_path"):
            return inputs["output_path"]
        if video_path:
            src = Path(video_path)
            return str(src.with_stem(f"{src.stem}_upscaled"))
        return f"topaz_upscaled_{int(time.time())}.mp4"

    @staticmethod
    def _upload_video_fal(video_path: str, api_key: str) -> str:
        """Upload a local video to fal.ai storage and return a public URL."""
        import requests

        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        suffix = path.suffix.lower().lstrip(".")
        content_type = {
            "mp4": "video/mp4",
            "mov": "video/quicktime",
            "webm": "video/webm",
            "m4v": "video/x-m4v",
        }.get(suffix, "video/mp4")

        init_resp = requests.post(
            "https://rest.alpha.fal.ai/storage/upload/initiate",
            headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
            json={"content_type": content_type, "file_name": path.name},
            timeout=30,
        )
        init_resp.raise_for_status()
        data = init_resp.json()

        put_resp = requests.put(
            data["upload_url"],
            headers={"Content-Type": content_type},
            data=path.read_bytes(),
            timeout=600,
        )
        put_resp.raise_for_status()

        return data["file_url"]

    @staticmethod
    def _compute_upscale_factor(video_ref: str, target_resolution: str) -> float:
        """Probe source dimensions and pick the smallest factor hitting target.

        Accepts either a local path (uses ffprobe) or a URL (also works with
        ffprobe if reachable). Returns a float in [1.0, 8.0].
        """
        target_short_edge = {
            "720p": 720,
            "1080p": 1080,
            "1440p": 1440,
            "4k": 2160,
        }.get(target_resolution.lower(), 1080)

        if not shutil.which("ffprobe"):
            return 1.5  # safe default — covers most 720p->1080p cases

        try:
            proc = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height",
                    "-of", "json",
                    str(video_ref),
                ],
                capture_output=True, text=True, timeout=30, check=True,
            )
            stream = json.loads(proc.stdout).get("streams", [{}])[0]
            w = int(stream.get("width") or 0)
            h = int(stream.get("height") or 0)
            short_edge = min(w, h) if w and h else 0
            if not short_edge:
                return 1.5
            factor = target_short_edge / short_edge
            # Clamp to fal.ai's supported range and round to a sensible step.
            return max(1.0, min(8.0, round(factor + 1e-6, 2)))
        except Exception:
            return 1.5
