"""Tests for the speed_paint tool (sketch-then-color reveal animation).

Contract tests are fast and dependency-free. The scaffold test exercises the
real engine (line-art -> coloring-book order map -> HyperFrames scene) on a tiny
raster, and is skipped if opencv/Pillow aren't installed. Neither test invokes
the HyperFrames CLI (no render / network).
"""
from __future__ import annotations

import pytest

from tools.base_tool import ToolStatus
from tools.graphics.speed_paint import SpeedPaint


# ------------------------------------------------------------------ contract


def test_speed_paint_identity():
    t = SpeedPaint()
    assert t.name == "speed_paint"
    assert t.capability == "graphics"
    assert t.provider == "hyperframes"
    assert "hyperframes" in t.agent_skills


def test_speed_paint_schema_and_info():
    t = SpeedPaint()
    assert "source" in t.input_schema["required"]
    props = t.input_schema["properties"]
    assert props["mode"]["enum"] == ["normal", "sleep"]
    assert props["operation"]["enum"] == ["render", "scaffold", "validate"]
    info = t.get_info()
    assert info["determinism"] == "seeded"
    assert "cmd:npx" in info["dependencies"]


def test_speed_paint_discovered_by_registry():
    from tools.tool_registry import registry
    registry.discover()
    assert "speed_paint" in registry._tools
    assert registry._tools["speed_paint"].capability == "graphics"


def test_speed_paint_missing_source():
    res = SpeedPaint().execute({"source": "/no/such/file.svg", "operation": "scaffold"})
    assert res.success is False
    assert "not found" in (res.error or "")


# ------------------------------------------------------------------ engine (guarded)


def test_speed_paint_scaffold_builds_workspace(tmp_path):
    pytest.importorskip("cv2")
    pytest.importorskip("PIL")
    pytest.importorskip("numpy")
    from PIL import Image, ImageDraw

    # tiny illustration: colored blocks with dark outlines so the line-art has structure
    img = Image.new("RGB", (320, 180), (240, 235, 220))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, 150, 140], fill=(200, 40, 40), outline=(10, 10, 10), width=3)
    d.rectangle([180, 30, 280, 110], fill=(40, 90, 200), outline=(10, 10, 10), width=3)
    d.ellipse([180, 120, 250, 160], fill=(230, 200, 40), outline=(10, 10, 10), width=3)
    src = tmp_path / "art.png"
    img.save(src)

    ws = tmp_path / "ws"
    res = SpeedPaint().execute({
        "source": str(src), "operation": "scaffold", "mode": "sleep",
        "out_w": 320, "out_h": 180, "sketch_secs": 1, "paint_secs": 1, "hold_secs": 1,
        "particles": 4, "workspace_path": str(ws),
    })
    assert res.success is True, res.error
    assert (ws / "index.html").exists()
    assert (ws / "assets" / "color.png").exists()
    assert (ws / "assets" / "order.png").exists()
    # raster source -> vectorized strokes + dark line-art
    assert res.data["sketch_source"] == "vectorize"
    html = (ws / "index.html").read_text()
    assert 'data-composition-id="speedpaint"' in html
    assert "__timelines" in html
