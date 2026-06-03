#!/usr/bin/env python3
"""Coloring-book segmentation -> a reveal "order map".

Uses the line-art as barriers, finds the enclosed cells (connected components of
the non-line area), merges tiny cells into their nearest real cell, groups cells
into a handful of OBJECTS (k-means on position+color), and orders them so color
fills ONE whole area at a time (background forced last).

Outputs a grayscale PNG `order map`: each pixel's value (0..255) = the moment in
the paint phase it should be revealed. Within a cell the value blooms from the
center outward, so the runtime reveal looks like an organic fill that completes
the whole cell before the next begins.

Also writes a debug `*_objects.png` colorizing the object grouping.
"""
import argparse, os
import cv2
import numpy as np


def nearest_label_fill(seed_mask):
    """For every pixel, label of nearest connected component of seed_mask (True=seed)."""
    inv = (~seed_mask).astype(np.uint8)          # 0 at seeds
    # DIST_LABEL_CCOMP: one label per connected component of seeds (i.e. per cell),
    # NOT per pixel — every pixel gets the label of its nearest cell.
    _, lbl = cv2.distanceTransformWithLabels(inv, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_CCOMP)
    return lbl


def segment(color_png, lineart_png, out_order, out_debug, min_area=900, k_objects=9, line_dilate=2):
    color = cv2.imread(color_png, cv2.IMREAD_COLOR)
    H, W = color.shape[:2]
    la = cv2.imread(lineart_png, cv2.IMREAD_UNCHANGED)
    if la.ndim == 3 and la.shape[2] == 4:
        lines = (la[..., 3] > 40).astype(np.uint8)
    else:
        g = cv2.cvtColor(la, cv2.COLOR_BGR2GRAY) if la.ndim == 3 else la
        lines = (g < 90).astype(np.uint8)
    if line_dilate > 0:
        lines = cv2.dilate(lines, np.ones((line_dilate, line_dilate), np.uint8))

    free = (lines == 0).astype(np.uint8)
    n, labels = cv2.connectedComponents(free, connectivity=4)

    # sizes; keep big cells as seeds, fill everything (incl. lines & tiny cells) to nearest big cell
    sizes = np.bincount(labels.ravel(), minlength=n)
    big_ids = [i for i in range(1, n) if sizes[i] >= min_area]
    if not big_ids:
        big_ids = list(range(1, n))
    big_mask = np.isin(labels, big_ids)
    merged = nearest_label_fill(big_mask)          # every pixel -> a big cell (renumbered)

    ids = [i for i in np.unique(merged) if i != 0]
    # per-cell stats
    lab_color = cv2.cvtColor(color, cv2.COLOR_BGR2LAB)
    cells = []
    for cid in ids:
        m = merged == cid
        area = int(m.sum())
        ys, xs = np.where(m)
        cx, cy = xs.mean(), ys.mean()
        mean = lab_color[m].mean(axis=0)
        touches_border = (xs.min() == 0 or ys.min() == 0 or xs.max() == W - 1 or ys.max() == H - 1)
        cells.append(dict(id=cid, area=area, cx=cx, cy=cy, lab=mean, border=touches_border))

    # group cells into objects (kmeans on position + color)
    feat = np.array([[c["cx"] / W * 1.2, c["cy"] / H * 1.2,
                      c["lab"][0] / 255, c["lab"][1] / 255, c["lab"][2] / 255] for c in cells], np.float32)
    K = int(min(k_objects, len(cells)))
    if K >= 2:
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.5)
        _, lab_idx, _ = cv2.kmeans(feat, K, None, crit, 4, cv2.KMEANS_PP_CENTERS)
        lab_idx = lab_idx.ravel()
    else:
        lab_idx = np.zeros(len(cells), int)
    for c, oi in zip(cells, lab_idx):
        c["obj"] = int(oi)

    # background object = the one whose cells are big, light, and touch the border
    obj_ids = sorted(set(c["obj"] for c in cells))
    def obj_area(o): return sum(c["area"] for c in cells if c["obj"] == o)
    def obj_is_bg(o):
        cs = [c for c in cells if c["obj"] == o]
        light = np.mean([c["lab"][0] for c in cs]) > 150
        border = any(c["border"] and c["area"] > 0.02 * W * H for c in cs)
        return light and border
    bg_objs = [o for o in obj_ids if obj_is_bg(o)]
    fg_objs = [o for o in obj_ids if o not in bg_objs]
    fg_objs.sort(key=obj_area, reverse=True)        # big objects first
    order_objs = fg_objs + bg_objs                  # background last

    # final cell order: object order, then by size desc within object
    ordered_cells = []
    for o in order_objs:
        cs = sorted([c for c in cells if c["obj"] == o], key=lambda c: c["area"], reverse=True)
        ordered_cells.extend(cs)
    N = len(ordered_cells)

    # build order map: per-cell window + center-out bloom
    order = np.zeros((H, W), np.float32)
    for rank, c in enumerate(ordered_cells):
        m = merged == c["id"]
        dt = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 3)
        mx = dt.max() if dt.max() > 0 else 1.0
        bloom = 1.0 - (dt / mx)                      # center 0 (first) -> edge 1 (last)
        order[m] = (rank + bloom[m]) / N

    order = np.clip(order, 0, 1)
    order_u8 = (1 + order * 254).astype(np.uint8)    # 1..255
    cv2.imwrite(out_order, order_u8)

    # debug objects colorized
    rng = np.random.default_rng(7)
    palette = rng.integers(40, 230, size=(N + 1, 3))
    dbg = np.zeros((H, W, 3), np.uint8)
    for rank, c in enumerate(ordered_cells):
        dbg[merged == c["id"]] = palette[rank]
    cv2.imwrite(out_debug, dbg)
    print(f"{os.path.basename(color_png)}: {N} cells in {len(order_objs)} objects (bg={len(bg_objs)}) -> {out_order}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--color", required=True)
    ap.add_argument("--lineart", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--debug", required=True)
    ap.add_argument("--min-area", type=int, default=900)
    ap.add_argument("--objects", type=int, default=9)
    ap.add_argument("--line-dilate", type=int, default=2)
    args = ap.parse_args()
    segment(args.color, args.lineart, args.out, args.debug, args.min_area, args.objects, args.line_dilate)
