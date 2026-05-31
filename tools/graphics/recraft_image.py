"""Recraft image generation via DIRECT API (external.api.recraft.ai).

Promoted May 2026 from `experiments/recraft/recraft_direct.py` after the
Iran-hook test workflow validated V4.1 quality. Replaces the earlier
fal.ai gateway implementation per `recraft_direct_api_rule` memory.

Models supported (cost ceiling 80 credits / $0.08 per image):

  Raster:                            Vector:
    recraftv4_1  (default)             recraftv4_1_vector
    recraftv4_1_utility                recraftv4_1_utility_vector
    recraftv4                          recraftv4_vector
    recraftv3                          recraftv3_vector
    recraftv2                          recraftv2_vector

  Pro variants (recraftv4_1_pro, recraftv4_1_pro_vector, etc.) are BANNED
  per recraft_pricing_rule — they cost $0.25–$0.30 per image.

V4+ schema diff: V4+ models do NOT accept `style`, `substyle`, `style_id`,
`negative_prompt`, or `text_layout`. The wrapper silently strips those.
V2/V3 still accepts all params. Exclusions for V4+ must be baked into the
positive prompt.

See memories:
- `recraft_v4_1_upgrade` — schema details, model strings, supported sizes
- `midnight_magnates_style_locked_v2` — MM channel default style
- `recraft_pricing_rule` — cost ceiling 80 credits = $0.08
- `recraft_direct_api_rule` — must use direct API, fal.ai banned
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


API_BASE = "https://external.api.recraft.ai/v1"
MAX_CREDITS_PER_IMAGE = 80  # ceiling — Pro tier ($0.25+) is banned

V4_PLUS_PREFIXES = ("recraftv4", "recraftv4_1")


def _is_v4_plus(model: str) -> bool:
    return any(model.startswith(p) for p in V4_PLUS_PREFIXES)


def _is_vector_model(model: str) -> bool:
    return model.endswith("_vector")


class RecraftImage(BaseTool):
    name = "recraft_image"
    version = "1.0.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "recraft"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []
    install_instructions = (
        "Set RECRAFT_API_KEY to your Recraft API key.\n"
        "  Get one at https://www.recraft.ai/profile/api"
    )
    agent_skills = ["bfl-api", "flux-best-practices"]  # adjacent reference skills

    capabilities = [
        "generate_image",
        "generate_logo",
        "generate_vector",
        "text_to_image",
    ]
    supports = {
        "svg_output": True,
        "text_rendering": True,
        "color_palette": True,
        "custom_size": True,
        "v4_1": True,
    }
    best_for = [
        "Midnight Magnates / Sleep Network noir illustrations (V4.1)",
        "Vector backgrounds for HyperFrames compositions (recraftv4_1_vector)",
        "Animated subject sprites with transparent PNG (recraftv4_1 raster)",
        "Flat segmented color illustration style",
    ]
    not_good_for = [
        "Photorealistic images",
        "Offline generation",
        "Rendering text inside the image (use HF/Remotion overlays instead)",
    ]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "description": "Scene description. Style addendum should be prepended by the caller for V4+."},
            "model": {
                "type": "string",
                "enum": [
                    "recraftv4_1",         # V4.1 raster — DEFAULT (May 2026 lock)
                    "recraftv4_1_vector",  # V4.1 vector — for backgrounds
                    "recraftv4_1_utility",
                    "recraftv4_1_utility_vector",
                    "recraftv4",
                    "recraftv4_vector",
                    "recraftv3",
                    "recraftv3_vector",
                ],
                "default": "recraftv4_1",
            },
            "size": {
                "type": "string",
                "description": (
                    "WxH string. V4.1 16:9 max = 1344x768. V3 16:9 max = 1820x1024. "
                    "If omitted, picks model-appropriate default."
                ),
            },
            "style": {
                "type": "string",
                "description": "V2/V3 ONLY. Ignored for V4+ models.",
                "enum": [
                    "any", "realistic_image", "digital_illustration",
                    "vector_illustration", "icon",
                ],
            },
            "substyle": {
                "type": "string",
                "description": "V2/V3 ONLY. e.g. 'editorial', 'linocut', 'engraving'.",
            },
            "negative_prompt": {
                "type": "string",
                "description": "V2/V3 ONLY. Ignored for V4+ — bake into positive prompt instead.",
            },
            "controls_colors": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Optional palette nudge — list of {rgb: [r,g,b]} dicts.",
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=100, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "model", "size"]
    side_effects = [
        "writes image file to output_path",
        "calls external.api.recraft.ai (direct, no gateway)",
    ]
    user_visible_verification = [
        "Inspect generated image for brand accuracy",
        "Verify no AI-rendered text appeared (Recraft V4.1 is better but still hallucinates occasionally)",
        "Check that requested exclusions (no aircraft, no people, etc.) were respected",
    ]

    def _get_api_key(self) -> str | None:
        return os.environ.get("RECRAFT_API_KEY")

    def get_status(self) -> ToolStatus:
        if self._get_api_key():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "recraftv4_1")
        if _is_vector_model(model):
            return 0.08
        # V2 raster is cheaper, but we default everything to current V4.1 pricing
        return 0.04

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(
                success=False,
                error="RECRAFT_API_KEY not set. " + self.install_instructions,
            )

        import requests

        start = time.time()
        prompt = inputs["prompt"]
        model = inputs.get("model", "recraftv4_1")
        is_v4 = _is_v4_plus(model)

        # Default size by model family
        size = inputs.get("size")
        if not size:
            if is_v4:
                size = "1344x768" if not _is_vector_model(model) else "1344x768"
            else:
                size = "1820x1024"

        payload: dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "size": size,
            "n": 1,
            "response_format": "url",
        }

        if is_v4:
            # V4+ schema strips style / substyle / style_id / negative_prompt
            if inputs.get("controls_colors"):
                payload["controls"] = {"colors": inputs["controls_colors"]}
        else:
            # V2/V3 schema accepts the legacy params
            if inputs.get("style"):
                payload["style"] = inputs["style"]
            if inputs.get("substyle"):
                payload["substyle"] = inputs["substyle"]
            if inputs.get("negative_prompt"):
                payload["negative_prompt"] = inputs["negative_prompt"]
            if inputs.get("controls_colors"):
                payload["controls"] = {"colors": inputs["controls_colors"]}

        try:
            response = requests.post(
                f"{API_BASE}/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=180,
            )
            if response.status_code != 200:
                return ToolResult(
                    success=False,
                    error=f"Recraft API {response.status_code}: {response.text[:600]}",
                )
            data = response.json()

            credits = data.get("credits", 40 if not _is_vector_model(model) else 80)
            if credits > MAX_CREDITS_PER_IMAGE:
                return ToolResult(
                    success=False,
                    error=(
                        f"Credits {credits} exceeds ceiling {MAX_CREDITS_PER_IMAGE} — "
                        f"likely hit Pro pricing (banned per recraft_pricing_rule)."
                    ),
                )

            image_url = data["data"][0]["url"]
            image_response = requests.get(image_url, timeout=60)
            image_response.raise_for_status()

            ext = "svg" if _is_vector_model(model) else "png"
            output_path = Path(inputs.get("output_path", f"generated_image.{ext}"))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image_response.content)

        except Exception as e:
            return ToolResult(success=False, error=f"Recraft generation failed: {e}")

        return ToolResult(
            success=True,
            data={
                "provider": "recraft",
                "model": model,
                "schema": "V4+" if is_v4 else "V2/V3",
                "prompt": prompt,
                "output": str(output_path),
                "credits": credits,
            },
            artifacts=[str(output_path)],
            cost_usd=credits / 1000.0,
            duration_seconds=round(time.time() - start, 2),
            model=model,
        )
