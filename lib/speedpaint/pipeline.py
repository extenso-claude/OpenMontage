#!/usr/bin/env python3
"""Speed-paint orchestrator: source image/SVG -> HyperFrames workspace -> MP4.

Flow:
  1. rasterize SVG (or load raster) -> color.png
  2. derive line-art (canny for clean flat vector / dark-ink for inked or
     vectorized-raster art)
  3. sketch strokes: use the source SVG paths directly for clean vector art, or
     vectorize the line-art into stroke contours for raster / 8k-patch art
  4. coloring-book order map (segment.py)
  5. build the HyperFrames scene (scene.py)
  6. (optional) validate + render to MP4 via the HyperFrames CLI

Public API: prepare_assets(), build_speedpaint(), validate(), render().
"""
import os
import subprocess

from PIL import Image

from . import prep, vectorize, segment, scene


def _is_svg(path):
    return str(path).lower().endswith(".svg")


def _count_paths(svg):
    try:
        with open(svg, encoding="utf-8", errors="ignore") as f:
            return f.read().count("<path")
    except OSError:
        return 0


def prepare_assets(source, assets_dir, out_w=1920, out_h=1080, *,
                   sketch_source="auto", lineart_method="auto",
                   min_area=1000, k_objects=9, stroke_min_len=75):
    """Produce color.png, lineart.png, order.png and a sketch SVG in assets_dir."""
    os.makedirs(assets_dir, exist_ok=True)
    color = os.path.join(assets_dir, "color.png")
    lineart = os.path.join(assets_dir, "lineart.png")
    proof = os.path.join(assets_dir, "lineart_proof.png")
    order = os.path.join(assets_dir, "order.png")
    debug = os.path.join(assets_dir, "order_debug.png")
    strokes = os.path.join(assets_dir, "strokes.svg")

    is_svg = _is_svg(source)
    n_paths = _count_paths(source) if is_svg else 0
    clean_vector = is_svg and 0 < n_paths < 1500

    if sketch_source == "auto":
        sketch_source = "svg" if clean_vector else "vectorize"
    if lineart_method == "auto":
        lineart_method = "canny" if clean_vector else "dark"

    # 1) color raster at output size
    if is_svg:
        prep.rasterize(source, color, out_w, out_h)
    else:
        Image.open(source).convert("RGB").resize((out_w, out_h)).save(color)

    # 2) line-art (segmentation barriers + optional stroke source)
    prep.make_lineart(color, lineart, proof, method=lineart_method)

    # 3) sketch strokes
    if sketch_source == "svg":
        sketch_svg = source
    else:
        vectorize.contours_to_svg(lineart, strokes, out_w, out_h, min_len=stroke_min_len)
        sketch_svg = strokes

    # 4) coloring-book order map
    segment.segment(color, lineart, order, debug, min_area=min_area, k_objects=k_objects)

    return {
        "color": color, "lineart": lineart, "order": order, "strokes": sketch_svg,
        "sketch_source": sketch_source, "lineart_method": lineart_method,
        "clean_vector": clean_vector, "n_paths": n_paths,
    }


def build_speedpaint(source, workspace, *, mode="normal", out_w=1920, out_h=1080,
                     sketch_secs=5.0, gap=0.4, paint_secs=5.0, hold_secs=3.0,
                     focus_x=0.5, focus_y=0.42, zoom=1.08, particles=16, life=True,
                     stroke=1.5, comp="speedpaint", title="Speed Paint",
                     sketch_source="auto", lineart_method="auto",
                     min_area=1000, k_objects=9, stroke_min_len=75):
    """Materialize a complete HyperFrames speed-paint workspace (no render)."""
    assets_dir = os.path.join(workspace, "assets")
    a = prepare_assets(source, assets_dir, out_w, out_h, sketch_source=sketch_source,
                       lineart_method=lineart_method, min_area=min_area,
                       k_objects=k_objects, stroke_min_len=stroke_min_len)
    index_html = os.path.join(workspace, "index.html")
    total = scene.build_scene(
        a["strokes"], a["color"], a["order"], index_html,
        title=title, comp=comp, out_w=out_w, out_h=out_h, canvas_w=out_w, canvas_h=out_h,
        sketch_secs=sketch_secs, gap=gap, paint_secs=paint_secs, hold_secs=hold_secs,
        mode=mode, stroke=stroke, focus_x=focus_x, focus_y=focus_y,
        zoom=zoom, particles=particles, life=life,
    )
    return {"workspace": workspace, "index_html": index_html, "duration": total, **a}


def _hf(args, cwd, timeout):
    proc = subprocess.run(["npx", "--yes", "hyperframes", *args], cwd=cwd,
                          capture_output=True, text=True, timeout=timeout)
    return proc


def validate(workspace, *, contrast=False, timeout=300):
    """Run `hyperframes validate` (browser-based). Returns (ok, output)."""
    args = ["validate"] + ([] if contrast else ["--no-contrast"])
    proc = _hf(args, workspace, timeout)
    out = (proc.stdout + proc.stderr)
    ok = proc.returncode == 0 and "error(s)" not in out.lower().replace("0 error(s)", "")
    return ok, out.strip()[-1200:]


def render(workspace, output, *, quality="standard", fps=30, timeout=1200):
    """Render the workspace to `output` MP4 via the HyperFrames CLI."""
    output = os.path.abspath(output)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    proc = _hf(["render", "--quality", quality, "--fps", str(fps), "--output", output],
               workspace, timeout)
    if proc.returncode != 0 or not os.path.exists(output):
        raise RuntimeError(f"hyperframes render failed:\n{(proc.stderr or proc.stdout)[-1000:]}")
    return output
