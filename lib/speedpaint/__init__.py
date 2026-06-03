"""Speed-paint engine: turn a still illustration into a sketch-then-color reveal video.

Promoted from projects/speedpaint-poc/. Used by tools/graphics/speed_paint.py and
usable directly:

    from lib.speedpaint import build_speedpaint, validate, render
    info = build_speedpaint("art.svg", "workspace/", mode="sleep", hold_secs=3,
                            focus_x=0.56, focus_y=0.30)
    render(info["workspace"], "out.mp4")

See skills/core/speed-paint.md for when/how + the hard rules.
"""
from .pipeline import prepare_assets, build_speedpaint, validate, render
from .scene import build_scene

__all__ = ["prepare_assets", "build_speedpaint", "validate", "render", "build_scene"]
