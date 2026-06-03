"""Speed-paint tool — turn a still illustration into a sketch-then-color reveal video.

Reproduces the a1d.ai "Speed Painter" effect locally (HyperFrames/GSAP), at full HD,
license-clean and free: a blank canvas, the image drawn on as a pencil sketch ONE
stroke at a time, then colored in ONE whole coloring-book area at a time, then the
finished still is held while a slow camera push + ambient life bring it alive.

Two presets:
  - normal: light paper, graphite ink (general videos)
  - sleep:  dark blackboard canvas + pale chalk ink, TRUE-to-source colors
            (Sleep Network night-designed art)

HARD RULES (see skills/core/speed-paint.md): no camera movement or effects while
sketching or coloring — the frame is locked until coloring finishes; the camera
push + glow + motes play ONLY on the held final still.

Engine: lib/speedpaint/. Layer-2 guidance: skills/core/speed-paint.md.
"""
from __future__ import annotations

import os
from typing import Any

from tools.base_tool import (
    BaseTool, ToolResult, ToolTier, ToolStability, ToolRuntime,
    ExecutionMode, Determinism, ResourceProfile,
)


class SpeedPaint(BaseTool):
    name = "speed_paint"
    version = "1.0.0"
    tier = ToolTier.GENERATE
    capability = "graphics"
    provider = "hyperframes"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.LOCAL

    dependencies = ["cmd:npx", "cmd:ffmpeg", "cmd:rsvg-convert", "python:cv2", "python:PIL", "python:numpy"]
    install_instructions = (
        "Needs Node.js >= 22 + FFmpeg (HyperFrames CLI via `npx hyperframes`), "
        "`rsvg-convert` (brew install librsvg / apt install librsvg2-bin — only for SVG "
        "sources), and Python opencv-python + Pillow + numpy. Verify HyperFrames with "
        "`npx hyperframes doctor`."
    )
    agent_skills = ["hyperframes", "hyperframes-cli", "gsap-core", "gsap-timeline"]

    capabilities = ["scaffold", "validate", "render"]
    best_for = [
        "Speed-draw / speed-paint reveals of an illustration (sketch then color)",
        "Sleep-documentary openers and beat transitions (use mode='sleep')",
        "Bringing a static illustration to life with a held final + slow camera push",
        "A faithful, full-HD, license-clean local alternative to a1d.ai Speed Painter",
    ]
    not_good_for = [
        "Photoreal footage (this is an illustration reveal effect)",
        "Element-level motion like a fluttering flag (needs layered/rigged source art)",
    ]
    fallback_tools = ["hyperframes_compose"]

    input_schema = {
        "type": "object",
        "required": ["source"],
        "properties": {
            "operation": {"type": "string", "enum": ["render", "scaffold", "validate"], "default": "render",
                          "description": "render: build workspace + validate + render MP4. scaffold: build workspace only. validate: build + browser-validate."},
            "source": {"type": "string", "description": "Path to the source illustration: an SVG (preferred — crisp strokes) or a raster (PNG/JPG)."},
            "mode": {"type": "string", "enum": ["normal", "sleep"], "default": "normal",
                     "description": "sleep = dark blackboard canvas + pale chalk ink, true-to-source colors (night-designed art)."},
            "workspace_path": {"type": "string", "description": "HyperFrames workspace dir (e.g. projects/<name>/hyperframes/). Defaults next to output_path."},
            "output_path": {"type": "string", "description": "Output MP4 path (required for operation='render')."},
            "sketch_secs": {"type": "number", "default": 5.0},
            "paint_secs": {"type": "number", "default": 5.0},
            "hold_secs": {"type": "number", "default": 3.0, "description": "Seconds to hold the finished still; set per script beat. Camera + life play only here."},
            "focus_x": {"type": "number", "default": 0.5, "description": "Camera focal point X (0..1) for the hold push-in."},
            "focus_y": {"type": "number", "default": 0.42},
            "zoom": {"type": "number", "default": 1.08, "description": "Hold camera push-in scale (1.0 = none)."},
            "particles": {"type": "integer", "default": 16, "description": "Drifting dust motes on the held still."},
            "life": {"type": "boolean", "default": True, "description": "Camera push + glow + motes on the held still (false = static hold)."},
            "stroke": {"type": "number", "default": 1.5, "description": "Pencil stroke width."},
            "quality": {"type": "string", "enum": ["draft", "standard", "high"], "default": "standard"},
            "fps": {"type": "integer", "default": 30},
            "out_w": {"type": "integer", "default": 1920},
            "out_h": {"type": "integer", "default": 1080},
            # advanced (usually leave on auto)
            "sketch_source": {"type": "string", "enum": ["auto", "svg", "vectorize"], "default": "auto",
                              "description": "auto: clean vector SVG -> its own paths; raster/8k-patch -> vectorize line-art."},
            "lineart_method": {"type": "string", "enum": ["auto", "canny", "dark"], "default": "auto",
                               "description": "auto: flat vector -> canny edges; inked/vectorized-raster -> extract dark ink."},
            "min_area": {"type": "integer", "default": 1000, "description": "Coloring-book cell merge threshold (bigger = chunkier fills)."},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=4, ram_mb=2048, disk_mb=200, network_required=True)

    user_visible_verification = [
        "Play the MP4: blank canvas -> pencil sketch (one stroke at a time) -> color fills one area at a time -> finished still holds, then a slow camera push + ambient glow/motes.",
        "Confirm NOTHING moves (no zoom/effects) until coloring is fully finished.",
    ]

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        q = inputs.get("quality", "standard")
        return 12.0 + {"draft": 12.0, "standard": 25.0, "high": 60.0}.get(q, 25.0)

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        import time
        from lib.speedpaint import build_speedpaint, validate as sp_validate, render as sp_render

        t0 = time.time()
        op = inputs.get("operation", "render")
        source = inputs.get("source")
        if not source or not os.path.exists(source):
            return ToolResult(success=False, error=f"source not found: {source!r}")

        workspace = inputs.get("workspace_path")
        output = inputs.get("output_path")
        if not workspace:
            if output:
                workspace = os.path.join(os.path.dirname(os.path.abspath(output)) or ".", "speedpaint_ws")
            else:
                return ToolResult(success=False, error="provide workspace_path or output_path")

        try:
            info = build_speedpaint(
                source, workspace,
                mode=inputs.get("mode", "normal"),
                out_w=int(inputs.get("out_w", 1920)), out_h=int(inputs.get("out_h", 1080)),
                sketch_secs=float(inputs.get("sketch_secs", 5.0)),
                paint_secs=float(inputs.get("paint_secs", 5.0)),
                hold_secs=float(inputs.get("hold_secs", 3.0)),
                focus_x=float(inputs.get("focus_x", 0.5)), focus_y=float(inputs.get("focus_y", 0.42)),
                zoom=float(inputs.get("zoom", 1.08)), particles=int(inputs.get("particles", 16)),
                life=bool(inputs.get("life", True)), stroke=float(inputs.get("stroke", 1.5)),
                title=inputs.get("title", "Speed Paint"),
                sketch_source=inputs.get("sketch_source", "auto"),
                lineart_method=inputs.get("lineart_method", "auto"),
                min_area=int(inputs.get("min_area", 1000)),
            )
        except Exception as e:  # noqa: BLE001
            return ToolResult(success=False, error=f"scaffold failed: {e}")

        data = {k: info[k] for k in ("workspace", "index_html", "duration", "sketch_source", "lineart_method", "n_paths")}
        artifacts = [info["index_html"]]

        if op in ("validate", "render"):
            ok, vout = sp_validate(workspace)
            data["validate_ok"] = ok
            if not ok:
                return ToolResult(success=False, error=f"hyperframes validate failed:\n{vout}", data=data, artifacts=artifacts)

        if op == "render":
            if not output:
                output = os.path.join(workspace, "renders", "speedpaint.mp4")
            try:
                mp4 = sp_render(workspace, output, quality=inputs.get("quality", "standard"), fps=int(inputs.get("fps", 30)))
            except Exception as e:  # noqa: BLE001
                return ToolResult(success=False, error=str(e), data=data, artifacts=artifacts)
            data["mp4"] = mp4
            artifacts.append(mp4)

        return ToolResult(success=True, data=data, artifacts=artifacts,
                          duration_seconds=time.time() - t0, seed=424242)
