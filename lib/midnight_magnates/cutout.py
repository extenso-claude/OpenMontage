"""Cutout + border tool — turn a photo/illustration into a map/diorama sprite.

Removes the background (rembg / U2Net) and draws a thin white-gray outline around
the subject's silhouette, so a cut figure or object reads cleanly when animated on
top of a noir map or inside a 2.5D diorama (the channel's recurring treatment).

Output is a transparent RGBA PNG.

    python -m lib.midnight_magnates.cutout --in <image> --out <sprite.png> [--stroke 6] [--gray]

NOTE: rembg downloads its U2Net model (~170MB from GitHub) on first use. On this
machine that needs urllib3<2 (see memory hf-download-urllib3-libressl) — already
installed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageFilter


def cutout(in_path: str, out_path: str, *, stroke_px: int = 6,
           stroke_color: Tuple[int, int, int, int] = (235, 235, 235, 255)) -> dict:
    """Background-remove `in_path` and add a `stroke_px` outline; write RGBA PNG."""
    from rembg import remove  # local import: heavy (onnxruntime); only when used

    src = Image.open(in_path).convert("RGBA")
    cut = remove(src)
    if not isinstance(cut, Image.Image):  # rembg may return bytes depending on input
        import io
        cut = Image.open(io.BytesIO(cut))
    cut = cut.convert("RGBA")

    alpha = cut.split()[3]
    # Dilate the alpha to make an outline ring just outside the subject.
    size = max(3, stroke_px * 2 + 1)
    dilated = alpha.filter(ImageFilter.MaxFilter(size))
    solid = Image.new("RGBA", cut.size, stroke_color)
    transparent = Image.new("RGBA", cut.size, (0, 0, 0, 0))
    stroke_layer = Image.composite(solid, transparent, dilated)  # stroke shaped by dilated alpha
    # Subject sits ON TOP of its outline -> a clean border hugging the figure.
    out = Image.alpha_composite(stroke_layer, cut)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)

    import numpy as np
    a = np.asarray(out.split()[3])
    return {
        "output": str(out_path),
        "size": list(out.size),
        "transparent_px": int((a == 0).sum()),
        "opaque_px": int((a == 255).sum()),
        "stroke_px": stroke_px,
    }


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="midnight_magnates.cutout")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stroke", type=int, default=6)
    ap.add_argument("--gray", action="store_true", help="gray outline (200,200,200) instead of near-white")
    args = ap.parse_args(argv)
    color = (200, 200, 200, 255) if args.gray else (235, 235, 235, 255)
    try:
        res = cutout(args.inp, args.out, stroke_px=args.stroke, stroke_color=color)
    except Exception as exc:
        print("CUTOUT FAILED: {0}".format(exc), file=sys.stderr)
        return 1
    import json
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
