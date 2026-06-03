#!/usr/bin/env python3
"""Turn a raster line-art PNG into a set of vector STROKE paths (an SVG).

findContours traces the boundary of every ink region, so a filled black shape
(e.g. the knight's horse) becomes a clean OUTLINE we can draw stroke-by-stroke
during the sketch phase (then the color layer fills it). Output is an SVG whose
<path>s are ready to feed into build_speedpaint.py as the sketch source.
"""
import argparse, os
import cv2
import numpy as np


def contours_to_svg(lineart_png, out_svg, width, height, min_len=70, epsilon=1.4):
    im = cv2.imread(lineart_png, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SystemExit(f"cannot read {lineart_png}")
    if im.ndim == 3 and im.shape[2] == 4:
        mask = (im[..., 3] > 40).astype(np.uint8) * 255
    else:
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) if im.ndim == 3 else im
        mask = (gray < 90).astype(np.uint8) * 255

    cnts, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    paths = []
    for c in cnts:
        if cv2.arcLength(c, True) < min_len:
            continue
        ap = cv2.approxPolyDP(c, epsilon, True).reshape(-1, 2)
        if len(ap) < 2:
            continue
        d = "M %d %d " % (ap[0][0], ap[0][1]) + " ".join("L %d %d" % (x, y) for x, y in ap[1:]) + " Z"
        paths.append((cv2.arcLength(c, True), d))

    # longest first is irrelevant here (generator reorders); keep stable
    body = "\n".join(f'<path class="stroke" d="{d}" />' for _, d in paths)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}">\n{body}\n</svg>\n')
    os.makedirs(os.path.dirname(out_svg) or ".", exist_ok=True)
    with open(out_svg, "w") as f:
        f.write(svg)
    print(f"wrote {out_svg} | {len(paths)} strokes (min_len={min_len})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lineart", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--min-len", type=float, default=70)
    ap.add_argument("--epsilon", type=float, default=1.4)
    args = ap.parse_args()
    contours_to_svg(args.lineart, args.out, args.width, args.height, args.min_len, args.epsilon)
