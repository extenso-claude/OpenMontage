#!/usr/bin/env python3
"""Speed-paint asset prep: SVG -> color PNG + derived line-art PNG.

Produces, for a given source SVG:
  <name>_color.png        full-color raster (the final painted image)
  <name>_lineart.png      RGBA: dark pencil lines on transparent (the sketch layer)
  <name>_lineart_proof.png line-art composited on cream paper (for human inspection)

Line-art methods:
  canny  - edges at every color boundary (best for clean FLAT vector art, e.g. saloon)
  dark   - extract existing black ink outlines (best for ink-outlined art, e.g. knight)
  combo  - max(canny, dark)
"""
import argparse, subprocess, os
import cv2
import numpy as np


def rasterize(svg, out_png, w, h):
    subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), svg, "-o", out_png], check=True)


def make_lineart(color_png, out_png, proof_png, method="canny",
                 canny_lo=40, canny_hi=120, dark_thresh=60, weight=2, soften=0.6):
    img = cv2.imread(color_png, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    edges = np.zeros_like(gray)
    if method in ("canny", "combo"):
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(blur, canny_lo, canny_hi)
    dark = np.zeros_like(gray)
    if method in ("dark", "combo"):
        dark = ((gray < dark_thresh).astype(np.uint8)) * 255

    if method == "canny":
        lines = edges
    elif method == "dark":
        lines = dark
    else:
        lines = cv2.max(edges, dark)

    if weight > 1:
        lines = cv2.dilate(lines, np.ones((weight, weight), np.uint8), iterations=1)
    if soften > 0:
        lines = cv2.GaussianBlur(lines, (0, 0), soften)

    h, w = lines.shape
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., 0:3] = 38          # dark graphite (BGR, equal -> neutral)
    rgba[..., 3] = lines         # alpha = line strength
    cv2.imwrite(out_png, rgba)

    # proof: composite over cream paper so a human can judge sketch quality
    paper = np.full((h, w, 3), (210, 228, 240), np.uint8)  # BGR cream
    a = (lines.astype(np.float32) / 255.0)[..., None]
    ink = np.full((h, w, 3), 38, np.uint8)
    proof = (paper * (1 - a) + ink * a).astype(np.uint8)
    cv2.imwrite(proof_png, proof)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--svg", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--out", default="hyperframes/assets")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--method", default="canny")
    ap.add_argument("--canny-lo", type=int, default=40)
    ap.add_argument("--canny-hi", type=int, default=120)
    ap.add_argument("--dark-thresh", type=int, default=60)
    ap.add_argument("--weight", type=int, default=2)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    color = os.path.join(args.out, f"{args.name}_color.png")
    lineart = os.path.join(args.out, f"{args.name}_lineart.png")
    proof = os.path.join(args.out, f"{args.name}_lineart_proof.png")
    rasterize(args.svg, color, args.width, args.height)
    make_lineart(color, lineart, proof, args.method, args.canny_lo, args.canny_hi,
                 args.dark_thresh, args.weight)
    print("wrote:", color, lineart, proof)
