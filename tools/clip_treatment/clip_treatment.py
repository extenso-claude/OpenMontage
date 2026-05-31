"""ClipTreatment BaseTool — registers the transformative-use toolkit with the registry.

Three operations:
  - apply_filter:   FFmpeg color grade / film look on a clip
  - apply_audio:    FFmpeg pitch shift / EQ / reverb on an audio track (auto-loudnorm to -14 LUFS)
  - wrap_in_frame:  HyperFrames composite — render a clip inside one of the 8 approved frames

Defaults are locked in approved_toolkit.json; the agent should reach for the rule before
choosing a recipe. See skills/core/clip-treatments.md for the workflow.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolStability,
    ToolStatus,
    ToolTier,
)

# Recipes live alongside this file (canonical home, copied from the R&D sprint project).
_HERE = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(_HERE))
from filters import RECIPES as FILTER_RECIPES, apply_filter as _apply_filter  # type: ignore
from audio_recipes import RECIPES as AUDIO_RECIPES, apply_audio_treatment as _apply_audio  # type: ignore


APPROVED_FRAMES = [
    "tv-vintage", "dossier", "newspaper", "fireside",
    "surveillance", "boardroom", "magnifier", "library",
]
FRAMES_DIR = _HERE / "frames"
APPROVED_TOOLKIT_JSON = _HERE / "approved_toolkit.json"


class ClipTreatment(BaseTool):
    name = "clip_treatment"
    version = "1.0.0"
    tier = ToolTier.CORE
    capability = "video_post"
    provider = "ffmpeg+hyperframes"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC

    dependencies = ["cmd:ffmpeg", "cmd:npx"]
    install_instructions = (
        "ffmpeg + Node ≥ 22 + npx hyperframes. All three are required for the wrap_in_frame "
        "operation. apply_filter and apply_audio only need ffmpeg."
    )
    agent_skills = ["core/clip-treatments"]

    capabilities = ["apply_filter", "apply_audio", "wrap_in_frame", "list_recipes", "load_defaults"]

    input_schema = {
        "type": "object",
        "required": ["operation"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["apply_filter", "apply_audio", "wrap_in_frame",
                         "list_recipes", "load_defaults"],
                "description": (
                    "apply_filter: FFmpeg color grade/film look on a video clip. "
                    "apply_audio: FFmpeg audio recipe on an audio track (auto-loudnorm to -14 LUFS). "
                    "wrap_in_frame: render a clip inside one of the 8 approved HyperFrames frames. "
                    "list_recipes: dump available filter + audio recipe names. "
                    "load_defaults: return the locked-defaults dict from approved_toolkit.json."
                ),
            },
            "input_path":  {"type": "string", "description": "Source video or audio path."},
            "output_path": {"type": "string", "description": "Destination file path."},
            "recipe": {
                "type": "string",
                "description": (
                    "Recipe name. For apply_filter: any of filters.py RECIPES (e.g. "
                    "'grade_cyan_orange' [default for video], 'grade_crushed_warm' "
                    "[default for image]). For apply_audio: any of audio_recipes.py "
                    "(e.g. 'pitch_up_1st' [LOCKED default for copyrighted audio])."
                ),
            },
            "frame": {
                "type": "string",
                "enum": APPROVED_FRAMES,
                "description": "Frame name when operation=wrap_in_frame. One of the 8 approved.",
            },
            "clip_duration": {
                "type": "number",
                "description": "Clip duration in seconds (for wrap_in_frame). Default 5.",
            },
        },
    }

    output_schema = {
        "type": "object",
        "properties": {
            "operation": {"type": "string"},
            "output_path": {"type": "string"},
            "recipe": {"type": "string"},
            "frame": {"type": "string"},
            "stderr_tail": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=1024, network_required=False)

    def get_status(self) -> ToolStatus:
        import shutil
        if not shutil.which("ffmpeg"):
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        op = inputs.get("operation", "")
        if op == "wrap_in_frame":
            return 30.0  # hyperframes single-worker draft
        if op in ("apply_filter", "apply_audio"):
            return 10.0
        return 0.5

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        op = inputs["operation"]
        t0 = time.time()

        if op == "list_recipes":
            return ToolResult(success=True, data={
                "filters": sorted(FILTER_RECIPES.keys()),
                "audio": sorted(AUDIO_RECIPES.keys()),
                "approved_frames": APPROVED_FRAMES,
            })

        if op == "load_defaults":
            try:
                cfg = json.loads(APPROVED_TOOLKIT_JSON.read_text())
                return ToolResult(success=True, data=cfg)
            except FileNotFoundError as e:
                return ToolResult(success=False, error=f"approved_toolkit.json not found: {e}")

        if op == "apply_filter":
            r = _apply_filter(
                input_path=inputs["input_path"],
                output_path=inputs["output_path"],
                recipe_name=inputs["recipe"],
            )
            return ToolResult(success=r["success"],
                              error=None if r["success"] else r.get("stderr_tail", ""),
                              data={**r, "elapsed_s": round(time.time() - t0, 2)})

        if op == "apply_audio":
            # output_path determines codec (mp3/m4a/wav handled inside the recipe runner)
            r = _apply_audio(
                input_path=inputs["input_path"],
                output_path=inputs["output_path"],
                recipe_name=inputs["recipe"],
                keep_video=False,
            )
            return ToolResult(success=r["success"],
                              error=None if r["success"] else r.get("stderr_tail", ""),
                              data={**r, "elapsed_s": round(time.time() - t0, 2)})

        if op == "wrap_in_frame":
            frame = inputs["frame"]
            if frame not in APPROVED_FRAMES:
                return ToolResult(success=False,
                                  error=f"Frame '{frame}' is not in the 8 approved frames: {APPROVED_FRAMES}")
            frame_html = FRAMES_DIR / f"frame-{frame}.html"
            if not frame_html.exists():
                return ToolResult(success=False, error=f"Frame composition missing: {frame_html}")
            return self._wrap_in_frame(
                input_path=Path(inputs["input_path"]),
                output_path=Path(inputs["output_path"]),
                frame_html=frame_html,
                clip_duration=float(inputs.get("clip_duration", 5)),
                t_start=t0,
            )

        return ToolResult(success=False, error=f"Unknown operation: {op}")

    def _wrap_in_frame(self, input_path: Path, output_path: Path, frame_html: Path,
                       clip_duration: float, t_start: float) -> ToolResult:
        """Substitute the clip src in the composition's <video> tag, then render via npx hyperframes.

        Uses single-worker draft mode per the 8 GB RAM rule
        (memory: hyperframes_render_workers_ram).
        """
        # Stage a per-render copy of the composition with the user-supplied clip path.
        work = output_path.parent / "_clip_treatment_work"
        work.mkdir(parents=True, exist_ok=True)
        staged_html = work / frame_html.name
        text = frame_html.read_text()
        # The frames all reference ../assets/clips/clip_demo.mp4 — swap to absolute user path.
        text = text.replace('src="../assets/clips/clip_demo.mp4"', f'src="{input_path.resolve()}"')
        # Update data-duration to match the actual clip.
        text = text.replace('data-duration="5"', f'data-duration="{clip_duration}"')
        staged_html.write_text(text)

        # Render via npx hyperframes
        proc = subprocess.run(
            ["npx", "hyperframes", "render",
             "-c", str(staged_html),
             "-o", str(output_path),
             "-q", "draft",
             "-w", "1",       # single worker — 8 GB RAM ceiling
             "--quiet"],
            cwd=staged_html.parent,
            capture_output=True, text=True,
        )
        ok = proc.returncode == 0 and output_path.exists() and output_path.stat().st_size > 10000
        return ToolResult(
            success=ok,
            error=None if ok else "\n".join(proc.stderr.splitlines()[-10:]),
            data={
                "operation": "wrap_in_frame",
                "output_path": str(output_path),
                "frame": frame_html.stem.replace("frame-", ""),
                "elapsed_s": round(time.time() - t_start, 2),
                "stderr_tail": "\n".join(proc.stderr.splitlines()[-10:]) if proc.stderr else "",
            },
        )

    examples = [
        {
            "description": "Apply locked video filter to a copyrighted clip",
            "inputs": {"operation": "apply_filter", "input_path": "raw_clip.mp4",
                       "output_path": "graded.mp4", "recipe": "grade_cyan_orange"},
        },
        {
            "description": "Apply locked audio treatment to copyrighted dialogue",
            "inputs": {"operation": "apply_audio", "input_path": "clip_audio.mp3",
                       "output_path": "treated.mp3", "recipe": "pitch_up_1st"},
        },
        {
            "description": "Wrap a treated clip inside the dossier frame for an intelligence reveal",
            "inputs": {"operation": "wrap_in_frame", "input_path": "graded.mp4",
                       "output_path": "wrapped.mp4", "frame": "dossier", "clip_duration": 6},
        },
    ]

    verification_steps = [
        "ClipTreatment().execute({'operation': 'list_recipes'}) returns >=22 filters + >=13 audio + 8 frames",
        "ClipTreatment().execute({'operation': 'load_defaults'}) returns the locked rules dict",
        "qa_pass.py brightness_in_band: mean luma 25–50 on treated clip",
    ]
