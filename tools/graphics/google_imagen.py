"""Google image generation via Gemini API.

Supports two endpoint families on the same API key:
  * Imagen line  (imagen-4.0-*)            -> :predict       endpoint
  * Gemini Image (gemini-2.5-flash-image,
                  gemini-3-pro-image-*,
                  aka 'Nano Banana')       -> :generateContent endpoint
"""

from __future__ import annotations

import base64
import io
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

# Aspect ratio to approximate pixel dimensions (for cost/reporting only)
ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "3:4": (896, 1152),
    "4:3": (1152, 896),
    "9:16": (768, 1344),
    "16:9": (1344, 768),
}

# Gemini Image (Nano Banana) model IDs. Endpoint: :generateContent.
GEMINI_IMAGE_MODELS = {
    "gemini-2.5-flash-image",
    "gemini-2.5-flash-image-preview",
    "gemini-3-pro-image-preview",          # "Nano Banana 2"
    "gemini-3.0-pro-image-preview",
}


def _is_gemini_image_model(model: str) -> bool:
    return model.startswith("gemini-") and "image" in model


def _dims_to_aspect_ratio(width: int, height: int) -> str:
    """Convert width/height to the nearest supported aspect ratio."""
    target = width / height
    best = "1:1"
    best_diff = float("inf")
    for ratio, (w, h) in ASPECT_RATIOS.items():
        diff = abs(target - w / h)
        if diff < best_diff:
            best_diff = diff
            best = ratio
    return best


class GoogleImagen(BaseTool):
    name = "google_imagen"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "google_imagen"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.API

    dependencies = []  # checked dynamically via env var
    install_instructions = (
        "Set GOOGLE_API_KEY (or GEMINI_API_KEY) to your Google AI API key.\n"
        "  Get one at https://aistudio.google.com/apikey"
    )
    agent_skills = []

    capabilities = ["generate_image", "generate_illustration", "text_to_image"]
    supports = {
        "negative_prompt": False,
        "seed": False,
        "custom_size": False,
        "aspect_ratio": True,
    }
    best_for = [
        "high-quality photorealistic images",
        "Google ecosystem integration",
        "fast generation with multiple aspect ratios",
    ]
    not_good_for = [
        "negative prompt control (not supported)",
        "exact pixel dimensions (uses aspect ratios)",
        "offline generation",
    ]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "description": "Image description (max 480 tokens)"},
            "aspect_ratio": {
                "type": "string",
                "enum": ["1:1", "3:4", "4:3", "9:16", "16:9"],
                "default": "1:1",
                "description": "Aspect ratio of generated image",
            },
            "width": {
                "type": "integer",
                "description": "Desired width in pixels — mapped to nearest aspect ratio",
            },
            "height": {
                "type": "integer",
                "description": "Desired height in pixels — mapped to nearest aspect ratio",
            },
            "model": {
                "type": "string",
                "enum": [
                    "imagen-4.0-generate-001",
                    "imagen-4.0-fast-generate-001",
                    "imagen-4.0-ultra-generate-001",
                    "gemini-2.5-flash-image",
                    "gemini-2.5-flash-image-preview",
                    "gemini-3-pro-image-preview",
                    "gemini-3.0-pro-image-preview",
                ],
                "default": "imagen-4.0-generate-001",
                "description": (
                    "Model variant. imagen-4.0-* uses :predict endpoint with "
                    "native aspect_ratio support. gemini-*-image uses "
                    ":generateContent (Nano Banana family) — aspect ratio is "
                    "supplied via the prompt and the result is resized to the "
                    "requested width/height post-hoc."
                ),
            },
            "number_of_images": {
                "type": "integer",
                "default": 1,
                "minimum": 1,
                "maximum": 4,
            },
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=100, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "aspect_ratio", "model"]
    side_effects = ["writes image file to output_path", "calls Google Generative AI API"]
    user_visible_verification = ["Inspect generated image for relevance and quality"]

    def _get_api_key(self) -> str | None:
        return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    def get_status(self) -> ToolStatus:
        if self._get_api_key():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        model = inputs.get("model", "imagen-4.0-generate-001")
        n = inputs.get("number_of_images", 1)
        if _is_gemini_image_model(model):
            # Gemini 2.5 Flash Image / Nano Banana 2: ~$0.039/image (1290 output tokens × $30/M).
            # Gemini 3 Pro Image preview: similar order of magnitude.
            return 0.04 * n
        if "ultra" in model:
            return 0.06 * n
        if "fast" in model:
            return 0.02 * n
        return 0.04 * n

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        api_key = self._get_api_key()
        if not api_key:
            return ToolResult(
                success=False,
                error="No Google API key found. " + self.install_instructions,
            )

        start = time.time()
        model = inputs.get("model", "imagen-4.0-generate-001")
        prompt = inputs["prompt"]

        # Resolve aspect ratio: explicit > derived from width/height > default
        import logging
        logger = logging.getLogger(__name__)

        if "aspect_ratio" in inputs:
            aspect_ratio = inputs["aspect_ratio"]
        elif "width" in inputs and "height" in inputs:
            requested_ratio = f"{inputs['width']}x{inputs['height']}"
            aspect_ratio = _dims_to_aspect_ratio(inputs["width"], inputs["height"])
            logger.info(
                "google_imagen: remapped %s to nearest supported aspect ratio %s",
                requested_ratio, aspect_ratio,
            )
        else:
            aspect_ratio = "1:1"

        number_of_images = inputs.get("number_of_images", 1)
        output_path = Path(inputs.get("output_path", "generated_image.png"))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if _is_gemini_image_model(model):
            return self._execute_gemini_image(
                api_key=api_key,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                number_of_images=number_of_images,
                output_path=output_path,
                width=inputs.get("width"),
                height=inputs.get("height"),
                start=start,
            )
        return self._execute_imagen(
            api_key=api_key,
            model=model,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            number_of_images=number_of_images,
            output_path=output_path,
            start=start,
        )

    def _execute_imagen(
        self,
        *,
        api_key: str,
        model: str,
        prompt: str,
        aspect_ratio: str,
        number_of_images: int,
        output_path: Path,
        start: float,
    ) -> ToolResult:
        import requests

        parameters: dict[str, Any] = {
            "sampleCount": number_of_images,
            "aspectRatio": aspect_ratio,
        }

        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key,
                },
                json={
                    "instances": [{"prompt": prompt}],
                    "parameters": parameters,
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            predictions = data.get("predictions", [])
            if not predictions:
                return ToolResult(success=False, error="No images returned from Imagen API")

            image_bytes = base64.b64decode(predictions[0]["bytesBase64Encoded"])
            output_path.write_bytes(image_bytes)

        except Exception as e:
            return ToolResult(success=False, error=f"Imagen generation failed: {e}")

        return ToolResult(
            success=True,
            data={
                "provider": "google_imagen",
                "model": model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "output": str(output_path),
                "images_generated": len(predictions),
            },
            artifacts=[str(output_path)],
            cost_usd=self.estimate_cost({"model": model, "number_of_images": number_of_images}),
            duration_seconds=round(time.time() - start, 2),
            model=model,
        )

    def _execute_gemini_image(
        self,
        *,
        api_key: str,
        model: str,
        prompt: str,
        aspect_ratio: str,
        number_of_images: int,
        output_path: Path,
        width: int | None,
        height: int | None,
        start: float,
    ) -> ToolResult:
        """Generate via Gemini Flash Image (Nano Banana) :generateContent endpoint.

        Aspect ratio is appended to the prompt because the API does not have a
        native aspectRatio param for image-out generations the way Imagen does.
        If the caller passed width/height, the result is resized to those dims
        post-hoc so the rest of the pipeline can rely on exact dimensions.
        """
        import requests

        # Embed aspect-ratio guidance in the prompt for Nano Banana.
        prompt_with_ratio = f"{prompt}\n\nAspect ratio: {aspect_ratio}, framed for {aspect_ratio} composition."

        artifacts: list[str] = []
        try:
            for i in range(number_of_images):
                this_path = (
                    output_path
                    if number_of_images == 1
                    else output_path.with_name(f"{output_path.stem}_{i+1}{output_path.suffix}")
                )

                response = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": api_key,
                    },
                    json={
                        "contents": [{"parts": [{"text": prompt_with_ratio}]}],
                        "generationConfig": {"responseModalities": ["IMAGE"]},
                    },
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()

                candidates = data.get("candidates") or []
                if not candidates:
                    feedback = data.get("promptFeedback")
                    return ToolResult(
                        success=False,
                        error=f"Gemini Image returned no candidates. promptFeedback={feedback}",
                    )

                inline = None
                for part in candidates[0].get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        inline = part["inlineData"]
                        break
                    if "inline_data" in part:
                        inline = part["inline_data"]
                        break
                if not inline:
                    text_parts = [
                        p.get("text", "") for p in candidates[0].get("content", {}).get("parts", [])
                    ]
                    return ToolResult(
                        success=False,
                        error=(
                            "Gemini Image returned no inline image data. "
                            f"Text response: {' '.join(text_parts)[:300]}"
                        ),
                    )

                image_bytes = base64.b64decode(inline.get("data") or inline.get("bytes", ""))

                # Optional post-hoc resize to honor explicit width/height.
                if width and height:
                    try:
                        from PIL import Image  # type: ignore

                        img = Image.open(io.BytesIO(image_bytes))
                        if img.size != (width, height):
                            img = img.resize((width, height), Image.LANCZOS)
                            buf = io.BytesIO()
                            fmt = "PNG" if this_path.suffix.lower() == ".png" else "JPEG"
                            img.save(buf, format=fmt)
                            image_bytes = buf.getvalue()
                    except Exception as resize_err:  # noqa: BLE001
                        # Fall back to native size if PIL is unavailable; not fatal.
                        import logging
                        logging.getLogger(__name__).warning(
                            "google_imagen: post-hoc resize failed (%s); writing native size",
                            resize_err,
                        )

                this_path.write_bytes(image_bytes)
                artifacts.append(str(this_path))

        except Exception as e:
            return ToolResult(success=False, error=f"Gemini Image generation failed: {e}")

        return ToolResult(
            success=True,
            data={
                "provider": "google_imagen",
                "model": model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "output": artifacts[0] if artifacts else str(output_path),
                "outputs": artifacts,
                "images_generated": len(artifacts),
            },
            artifacts=artifacts,
            cost_usd=self.estimate_cost({"model": model, "number_of_images": number_of_images}),
            duration_seconds=round(time.time() - start, 2),
            model=model,
        )
