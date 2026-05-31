"""Animation catalog — 19 chosen recipes, channel-agnostic via themes.

Generates branded animation clips by combining:
  - Recraft V4 raster ($0.04/image) for the base scene when image_path=None — palette
    + style + scene-prompt driven by a channel theme module (see catalog/themes/)
  - HyperFrames procedural overlays + GSAP motion via mm_motion.js
  - Mandatory placement QA via lib.render_placement_qa

Channels supported (theme parameter):
  - "midnight-magnates" (default): noir documentary on dark histories of wealth
  - "grandpa-huxley":              sleep-documentary, warm earth tones
  - add a new channel:             drop tools/animation/catalog/themes/<slug>.py
                                   exposing THEME and register it in KNOWN_THEMES

Usage:
    tool = AnimationCatalog()
    result = tool.execute({
        "format_id": 23,
        "out_path": "renders/title.mp4",
        "theme": "midnight-magnates",
        "duration": 6.0,
        "scene_overrides": {
            "title": "DARK MONEY",
            "subtitle": "the dark histories of wealth",
        },
        "version": "recraft",
        "quality": "draft",
    })

Output: ToolResult with .data["output_path"] = rendered MP4, plus placement_qa results.

This catalog is the production-blessed subset from the May 2026 99-format R&D
sprint (experiments/animation-format-test). The 19 chosen formats are the
ones that earned WINNER or strong-VIABLE verdicts.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

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
from tools.animation.catalog.composer import write_composition, vignette_html
from tools.animation.catalog.format_dispatch import FORMATS
from tools.animation.catalog.themes import load_theme, KNOWN_THEMES


# The 19 chosen formats from the R&D sprint — channel-agnostic structure.
# Theme provides the channel-specific scene prompt + default copy.
CHOSEN_FORMATS: dict[int, dict] = {
    1:   {"name": "Living scene",          "version": "recraft+hf",        "use_case": "Exterior establishing — saloon/cottage at night"},
    2:   {"name": "Aged document",         "version": "hyperframes",       "use_case": "Will / contract / journal reveal"},
    3:   {"name": "Mood loop",             "version": "recraft+hf",        "use_case": "Atmospheric backdrop with slow drift"},
    8:   {"name": "Moving train window",   "version": "recraft+hf",        "use_case": "Interior + exterior landscape parallaxing past"},
    9:   {"name": "Diorama shadow box",    "version": "hyperframes+image", "use_case": "Layered scene with sweep light"},
    17:  {"name": "Tarot card draw",       "version": "hyperframes",       "use_case": "Three-card narrative reveal"},
    18:  {"name": "Wanted poster slap",    "version": "hyperframes",       "use_case": "Slam-in poster (wanted / carnival / event)"},
    20:  {"name": "Polaroid scatter",      "version": "hyperframes",       "use_case": "Photo archive / evidence layout"},
    21:  {"name": "Tier list ranking",     "version": "hyperframes",       "use_case": "S/A/B/C/D ranked items"},
    31:  {"name": "Recipe steps",          "version": "hyperframes",       "use_case": "3-step process — recipe, blueprint"},
    44:  {"name": "Pulse halo character",  "version": "recraft+hf",        "use_case": "Speaker at pulpit / podium with VO pulse"},
    46:  {"name": "iMessage scroll",       "version": "hyperframes",       "use_case": "Chat thread / dialogue exchange"},
    48:  {"name": "Search query",          "version": "hyperframes",       "use_case": "Faux Google search + auto-complete + results"},
    53:  {"name": "Newspaper unfold",      "version": "hyperframes",       "use_case": "Headline reveal (era / event)"},
    55:  {"name": "Old-film projector",    "version": "hyperframes+image", "use_case": "Archival reel with sprocket + scratches"},
    58:  {"name": "Inventory slot reveal", "version": "hyperframes",       "use_case": "6-slot grid of branded items"},
    67:  {"name": "Equation derivation",   "version": "hyperframes",       "use_case": "Formula / lecture-hall chalkboard"},
    107: {"name": "Photo album spread",    "version": "hyperframes",       "use_case": "Family album / period photo collage"},
    111: {"name": "Shadow puppet",         "version": "hyperframes+image", "use_case": "Silhouette + drifting wall-shadow"},
}


def _slug(s: str) -> str:
    return s.lower().replace(" ", "_").replace("/", "_").replace("'", "")


class AnimationCatalog(BaseTool):
    name = "animation_catalog"
    version = "2.0.0"
    tier = ToolTier.GENERATE
    capability = "video_post"
    provider = "animation_catalog"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["bin:npx", "bin:ffmpeg"]
    install_instructions = (
        "Requires Node ≥22 (for npx hyperframes) and ffmpeg.\n"
        "  Recraft API: set RECRAFT_API_KEY in .env for AI-image versions."
    )
    agent_skills = ["animation_catalog"]

    capabilities = [
        "generate_named_animation",
        "branded_clip",
        "themed_animation_catalog",
    ]
    supports = {
        "themes": KNOWN_THEMES,
        "render_engines": ["hyperframes"],
        "ai_image_provider": "recraft_v4_raster",
        "palette_per_channel": True,
    }
    best_for = [
        "Branded clip generation per channel using a named recipe + channel theme",
        "Reusable named animation building-blocks (title cards, document reveals, etc.)",
        "Production-blessed subset of the 99-format R&D sprint",
    ]
    not_good_for = [
        "One-off creative scenes outside the 19-format catalog (use general image_selector + hyperframes_compose)",
        "Channels without a registered theme — add a theme module first",
    ]

    input_schema = {
        "type": "object",
        "required": ["format_id", "out_path"],
        "properties": {
            "format_id": {"type": "integer", "enum": sorted(CHOSEN_FORMATS.keys())},
            "out_path": {"type": "string", "description": "where to write the .mp4"},
            "theme": {"type": "string", "enum": KNOWN_THEMES, "default": "midnight-magnates"},
            "duration": {"type": "number", "default": 6.0},
            "version": {"type": "string", "enum": ["recraft", "hyperframes"], "default": "recraft"},
            "quality": {"type": "string", "enum": ["draft", "standard"], "default": "draft"},
            "scene_overrides": {"type": "object", "description": "Override default scene params (title, subtitle, glow positions, etc.)"},
            "recraft_image_path": {"type": "string", "description": "Override Recraft image (skip generation, use existing PNG)"},
            "recraft_prompt": {"type": "string", "description": "Override the default Recraft scene prompt"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=1024, vram_mb=0, disk_mb=200, network_required=True,
    )
    retry_policy = RetryPolicy(max_retries=1, retryable_errors=["timeout"])
    idempotency_key_fields = ["format_id", "theme", "version", "scene_overrides", "recraft_prompt"]
    side_effects = [
        "writes .mp4 to out_path",
        "writes .html composition to a temp workspace",
        "calls Recraft API (only when version=recraft and no recraft_image_path supplied) — ~$0.04",
    ]
    user_visible_verification = [
        "Watch the rendered mp4 end-to-end",
        "Confirm placement QA returned 0 flagged (the tool runs it automatically)",
    ]

    def get_status(self) -> ToolStatus:
        if not shutil.which("npx"):
            return ToolStatus.UNAVAILABLE
        if not shutil.which("ffmpeg"):
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        if inputs.get("version") == "recraft" and not inputs.get("recraft_image_path"):
            return 0.04
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        t0 = time.time()
        format_id = inputs["format_id"]
        if format_id not in CHOSEN_FORMATS:
            return ToolResult(
                success=False,
                error=f"format_id {format_id} not in chosen catalog. Allowed: {sorted(CHOSEN_FORMATS.keys())}",
            )
        if format_id not in FORMATS:
            return ToolResult(success=False, error=f"format_id {format_id} missing dispatcher entry")

        theme_slug = inputs.get("theme", "midnight-magnates")
        try:
            theme = load_theme(theme_slug)
        except ValueError as e:
            return ToolResult(success=False, error=str(e))

        out_path = Path(inputs["out_path"])
        version = inputs.get("version", "recraft")
        duration = float(inputs.get("duration", 6.0))
        quality = inputs.get("quality", "draft")
        scene_overrides = inputs.get("scene_overrides") or {}
        recraft_image_path: Optional[Path] = (
            Path(inputs["recraft_image_path"]) if inputs.get("recraft_image_path") else None
        )

        # Pull default copy + scene prompt from theme, then layer caller overrides on top
        default_copy = theme.get("default_copy", {}).get(format_id, {})
        recipe_fn, default_kwargs = FORMATS[format_id]
        kwargs = {**default_kwargs}
        # Theme-provided title/subtitle override the default_kwargs (which still hold MM-era copy from the sprint)
        if "title" in default_copy:
            kwargs["title"] = default_copy["title"]
        if "subtitle" in default_copy:
            kwargs["subtitle"] = default_copy["subtitle"]
        # Caller scene_overrides win over everything
        kwargs.update(scene_overrides)

        # Generate Recraft image if needed
        image_rel: Optional[str] = None
        cost = 0.0
        if version == "recraft":
            if not recraft_image_path:
                from tools.animation.catalog.recraft_gen import gen
                prompt = (
                    inputs.get("recraft_prompt")
                    or scene_overrides.get("recraft_prompt")
                    or theme.get("default_scenes", {}).get(format_id)
                    or f"Themed noir scene for format {format_id}"
                )
                image_path = out_path.parent / "assets" / f"format_{format_id:03d}_hero.png"
                image_path.parent.mkdir(parents=True, exist_ok=True)
                res = gen(prompt=prompt, out_path=image_path, theme=theme)
                cost += float(res.get("cost_usd", 0.04))
                recraft_image_path = image_path
            image_rel = str(recraft_image_path)

        # Build composition HTML in a workspace directory next to out_path
        workspace = out_path.parent / "_catalog_workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "assets" / "shared").mkdir(parents=True, exist_ok=True)
        (workspace / "compositions").mkdir(exist_ok=True)
        (workspace / "renders").mkdir(exist_ok=True)

        catalog_assets = Path(__file__).parent / "catalog" / "assets"
        # Universal tokens.css + motion.js
        shutil.copy(catalog_assets / "mm_tokens.css", workspace / "assets" / "tokens.css")
        shutil.copy(catalog_assets / "mm_motion.js", workspace / "assets" / "shared" / "mm_motion.js")
        # Per-theme palette overlay — emit a small CSS that overrides tokens.css :root vars
        theme_css = workspace / "assets" / "theme_palette.css"
        css_lines = [":root {"]
        css_lines += [f"  {k}: {v};" for k, v in theme.get("palette_css", {}).items()]
        css_lines.append("}")
        css_lines.append(f".hero, .noir-grade {{ filter: {theme.get('noir_filter_css', '')}; }}")
        theme_css.write_text("\n".join(css_lines))
        shutil.copy(catalog_assets / "index.html", workspace / "index.html")
        # hyperframes.json marker
        (workspace / "hyperframes.json").write_text(json.dumps({
            "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
            "paths": {"blocks": "compositions", "assets": "assets"},
        }))

        cid = f"catalog_{theme_slug.replace('-', '_')}_{format_id:03d}_{version}"
        comp_path = workspace / "compositions" / f"{cid}.html"

        if image_rel:
            rel_img_dir = workspace / "assets" / f"recraft_{format_id:03d}"
            rel_img_dir.mkdir(parents=True, exist_ok=True)
            target_img = rel_img_dir / "hero.png"
            shutil.copy(image_rel, target_img)
            image_for_recipe = f"../assets/recraft_{format_id:03d}/hero.png"
        else:
            image_for_recipe = None

        structural = {"layers_data", "steps", "card_html", "ui_html", "lines", "kind",
                      "direction", "name", "role", "dates", "frame_color", "show_stamp"}
        pass_through = {k: v for k, v in kwargs.items() if k in structural}
        opts_dict = {k: v for k, v in kwargs.items() if k not in structural}

        entry_for_recipe = {"n": format_id, "dur": duration, "name": CHOSEN_FORMATS[format_id]["name"]}
        result = recipe_fn(entry_for_recipe, version, image_for_recipe, opts=opts_dict, **pass_through)

        # Inject theme palette CSS link into the composition's scene_css
        extra_css_inject = '\n  /* Theme palette overlay */\n  @import url("../assets/theme_palette.css");\n'
        result_css = (result.get("scene_css", "") or "") + extra_css_inject

        label = (f"#{format_id} — {CHOSEN_FORMATS[format_id]['name'].upper()} — "
                 f"{theme['display_name'].upper()} — "
                 f"{'RECRAFT' if version == 'recraft' else 'HYPERFRAMES ONLY'}")
        write_composition(
            comp_path,
            cid=cid,
            label=label,
            dur=duration,
            scene_css=result_css,
            scene_html=result["scene_html"],
            tl_js=result["tl_js"],
            deco_html=result.get("deco_html") if "deco_html" in result else vignette_html(),
        )

        # Render via npx hyperframes
        render_out = workspace / "renders" / out_path.name
        cmd = [
            "npx", "hyperframes", "render", "-w", "1", "-q", quality,
            "-c", str(comp_path.relative_to(workspace)),
            "-o", str(render_out.relative_to(workspace)),
        ]
        rt0 = time.time()
        r = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True, timeout=900)
        render_dt = round(time.time() - rt0, 1)
        if r.returncode != 0:
            return ToolResult(
                success=False,
                error=f"HyperFrames render failed: {r.stderr[-800:]}",
                duration_seconds=round(time.time() - t0, 2),
            )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(render_out), str(out_path))

        # MANDATORY placement QA
        from lib.render_placement_qa import check_clip
        try:
            qa = check_clip(out_path)
        except Exception as e:
            qa = {"error": str(e), "flag": False}

        if qa.get("flag"):
            return ToolResult(
                success=False,
                error=(
                    f"Placement QA FLAGGED — black-band bug suspected.\n"
                    f"  top_near_black={qa.get('top_near_black')} (stddev={qa.get('top_stddev')})\n"
                    f"  bottom_near_black={qa.get('bottom_near_black')} (stddev={qa.get('bottom_stddev')})\n"
                    f"Re-render before shipping. See render_placement_qa_required memory rule for fix patterns."
                ),
                artifacts=[str(out_path)],
                data={"placement_qa": qa, "render_seconds": render_dt, "theme": theme_slug},
                duration_seconds=round(time.time() - t0, 2),
            )

        return ToolResult(
            success=True,
            data={
                "format_id": format_id,
                "format_name": CHOSEN_FORMATS[format_id]["name"],
                "theme": theme_slug,
                "channel": theme["display_name"],
                "version": version,
                "quality": quality,
                "output_path": str(out_path),
                "render_seconds": render_dt,
                "placement_qa": qa,
                "cost_usd": cost,
            },
            artifacts=[str(out_path)],
            cost_usd=cost,
            duration_seconds=round(time.time() - t0, 2),
            model=f"animation_catalog/{theme_slug}/{version}",
        )
