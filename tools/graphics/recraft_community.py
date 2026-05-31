"""Recraft community gallery scraper.

Browses Recraft's public community gallery via their internal HTTP API and
downloads the rendered SVG assets. No API key required — the gallery endpoint
is unauthenticated and the per-image asset URLs are server-signed and embedded
in the SSR detail page.

Pipeline:
    1. list_gallery(...)        -> public JSON feed, returns image_ids + prompts
    2. get_signed_svg_url(id)   -> scrapes SSR detail page for signed @svg URL
    3. download_svg(id, path)   -> writes SVG bytes to disk

Reverse-engineered against recraft.ai on 2026-05-15. Endpoints are private
and may break without notice.

Licensing reminder: community SVGs are authored by other Recraft users. The
JSON response includes `public_commercial_use` per item — respect it. For
monetized YouTube usage, prefer "harvest prompts as inspiration, regenerate
via your own Recraft API key" over reusing raw community assets.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

GALLERY_API = "https://api.recraft.ai/gallery"
DETAIL_PAGE = "https://www.recraft.ai/community"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)

# Full vector_illustration substyle taxonomy as Recraft's own UI sends it.
# Sourced from the live request when selecting the "Vector art" tab.
VECTOR_ILLUSTRATION_STYLES = [
    "vector_illustration",
    "vector_illustration_line_art",
    "vector_illustration_linocut",
    "vector_illustration_line_circuit",
    "vector_illustration_engraving",
    "vector_illustration_bold_stroke",
    "vector_illustration_chemistry",
    "vector_illustration_colored_stencil",
    "vector_illustration_cosmics",
    "vector_illustration_cutout",
    "vector_illustration_depressive",
    "vector_illustration_editorial",
    "vector_illustration_emotional_flat",
    "vector_illustration_marker_outline",
    "vector_illustration_mosaic",
    "vector_illustration_naivector",
    "vector_illustration_roundish_flat",
    "vector_illustration_segmented_colors",
    "vector_illustration_sharp_contrast",
    "vector_illustration_thin",
    "vector_illustration_vector_photo",
    "vector_illustration_vivid_shapes",
    "vector_illustration_seamless",
    "vector_illustration_cartoon",
    "vector_illustration_flat_2",
    "vector_illustration_kawaii",
    "vector_illustration_doodle_line_art",
]

ICON_STYLES = ["icon"]


@dataclass
class GalleryItem:
    image_id: str
    prompt: str
    image_type: str
    width: int
    height: int
    likes_count: int
    dislikes_count: int
    public_commercial_use: bool
    transform_model: str | None
    create_time: str
    raw: dict = field(repr=False, default_factory=dict)


def _http_get(url: str, accept: str = "application/json") -> bytes:
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urlopen(req, timeout=30) as resp:
        return resp.read()


def list_gallery(
    image_types: Iterable[str] = VECTOR_ILLUSTRATION_STYLES,
    gallery_tags: str = "vector_illustration",
    limit: int = 30,
    offset: int = 0,
    gallery_type: str = "community",
) -> list[GalleryItem]:
    """Fetch one page of community gallery items.

    Pagination is offset-based. Server tops out somewhere — empty list signals end.
    """
    params: list[tuple[str, str]] = [("type", gallery_type)]
    for t in image_types:
        params.append(("image_types", t))
    params.append(("gallery_tags", gallery_tags))
    params.append(("limit", str(limit)))
    params.append(("offset", str(offset)))

    url = f"{GALLERY_API}?{urlencode(params)}"
    raw = _http_get(url, accept="application/json")
    payload = json.loads(raw)
    items = []
    for entry in payload.get("gallery_items", []):
        img = entry.get("image", {})
        items.append(GalleryItem(
            image_id=img.get("image_id"),
            prompt=img.get("prompt", ""),
            image_type=img.get("image_type", ""),
            width=img.get("width", 0),
            height=img.get("height", 0),
            likes_count=img.get("likes_count", 0),
            dislikes_count=img.get("dislikes_count", 0),
            public_commercial_use=bool(img.get("public_commercial_use", False)),
            transform_model=img.get("transform_model"),
            create_time=img.get("create_time", ""),
            raw=img,
        ))
    return items


def iter_gallery(
    image_types: Iterable[str] = VECTOR_ILLUSTRATION_STYLES,
    gallery_tags: str = "vector_illustration",
    max_items: int = 300,
    page_size: int = 30,
    sleep_between_pages: float = 0.5,
) -> Iterator[GalleryItem]:
    """Yield gallery items across pages until max_items or end of feed."""
    fetched = 0
    offset = 0
    image_types = list(image_types)
    while fetched < max_items:
        batch = list_gallery(
            image_types=image_types,
            gallery_tags=gallery_tags,
            limit=min(page_size, max_items - fetched),
            offset=offset,
        )
        if not batch:
            return
        for item in batch:
            yield item
            fetched += 1
            if fetched >= max_items:
                return
        offset += len(batch)
        time.sleep(sleep_between_pages)


_SIGNED_SVG_RE = re.compile(
    r'https://img\.recraft\.ai/[A-Za-z0-9_\-]+/[^"\'\s]+@svg'
)
_SIGNED_JPG_RE = re.compile(
    r'https://img\.recraft\.ai/[A-Za-z0-9_\-]+/[^"\'\s]+@jpg'
)


def get_signed_urls(image_id: str) -> dict[str, str | None]:
    """Fetch the SSR detail page and extract signed asset URLs.

    Returns {'svg': <url|None>, 'jpg': <url|None>}.
    """
    url = f"{DETAIL_PAGE}?imageId={image_id}"
    html = _http_get(url, accept="text/html").decode("utf-8", errors="ignore")
    # The SSR page embeds both the full-res signed @svg URL and an og:image @jpg
    # thumbnail. Both differ per imageId — signatures aren't constructable.
    svg_match = _SIGNED_SVG_RE.search(html)
    jpg_match = _SIGNED_JPG_RE.search(html)
    return {
        "svg": svg_match.group(0) if svg_match else None,
        "jpg": jpg_match.group(0) if jpg_match else None,
    }


def download_svg(image_id: str, out_path: str | Path) -> Path:
    """Download the full-res SVG for an image_id."""
    urls = get_signed_urls(image_id)
    if not urls["svg"]:
        raise RuntimeError(f"No signed SVG URL found for {image_id}")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(_http_get(urls["svg"], accept="image/svg+xml"))
    return out_path


def _cli() -> int:
    p = argparse.ArgumentParser(description="Recraft community gallery scraper")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list", help="List gallery items (one page)")
    pl.add_argument("--limit", type=int, default=10)
    pl.add_argument("--offset", type=int, default=0)
    pl.add_argument("--style-set", choices=["vector", "icon"], default="vector")
    pl.add_argument("--json", action="store_true")

    pi = sub.add_parser("iter", help="Iterate across pages, print imageIds + prompts")
    pi.add_argument("--max", type=int, default=60)
    pi.add_argument("--style-set", choices=["vector", "icon"], default="vector")

    pu = sub.add_parser("urls", help="Print signed asset URLs for an imageId")
    pu.add_argument("image_id")

    pd = sub.add_parser("download", help="Download SVG for an imageId")
    pd.add_argument("image_id")
    pd.add_argument("--out", required=True, help="Output .svg path")

    pb = sub.add_parser("batch", help="List+download top N SVGs into a directory")
    pb.add_argument("--count", type=int, default=10)
    pb.add_argument("--out-dir", required=True)
    pb.add_argument("--style-set", choices=["vector", "icon"], default="vector")
    pb.add_argument("--sleep", type=float, default=0.4)

    args = p.parse_args()

    style_map = {"vector": VECTOR_ILLUSTRATION_STYLES, "icon": ICON_STYLES}

    if args.cmd == "list":
        items = list_gallery(image_types=style_map[args.style_set],
                             limit=args.limit, offset=args.offset)
        if args.json:
            print(json.dumps([asdict(i) for i in items], default=str, indent=2))
        else:
            for it in items:
                print(f"{it.image_id}  ({it.image_type}, {it.width}x{it.height}, "
                      f"likes={it.likes_count}, commercial={it.public_commercial_use})")
                print(f"  {it.prompt[:140]}")
        return 0

    if args.cmd == "iter":
        for it in iter_gallery(image_types=style_map[args.style_set], max_items=args.max):
            print(f"{it.image_id}\t{it.image_type}\t{it.prompt[:120]}")
        return 0

    if args.cmd == "urls":
        urls = get_signed_urls(args.image_id)
        print(json.dumps(urls, indent=2))
        return 0

    if args.cmd == "download":
        path = download_svg(args.image_id, args.out)
        size = path.stat().st_size
        print(f"saved {path} ({size:,} bytes)")
        return 0

    if args.cmd == "batch":
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest = []
        for it in iter_gallery(image_types=style_map[args.style_set],
                               max_items=args.count, page_size=min(30, args.count)):
            try:
                fname = f"{it.image_id}.svg"
                path = download_svg(it.image_id, out_dir / fname)
                manifest.append({
                    "image_id": it.image_id,
                    "file": str(path),
                    "image_type": it.image_type,
                    "prompt": it.prompt,
                    "likes_count": it.likes_count,
                    "public_commercial_use": it.public_commercial_use,
                    "width": it.width,
                    "height": it.height,
                })
                print(f"OK  {it.image_id}  ({path.stat().st_size:,} bytes)")
            except (HTTPError, URLError, RuntimeError) as e:
                print(f"ERR {it.image_id}  {e}", file=sys.stderr)
            time.sleep(args.sleep)
        manifest_path = out_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"\nwrote {manifest_path} ({len(manifest)} items)")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(_cli())
