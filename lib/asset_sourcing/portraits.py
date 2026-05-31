"""Source PD portraits for named people, autonomously, via a fallback chain.

Promoted from `experiments/iran-hook-shotplan/source_portraits.py` (May 2026)
after the Iran-hook test validated the Wikipedia REST → Commons API → LoC search
chain. Used by any pipeline that needs character-card portraits without
shipping placeholder gradient blocks (per `never_placeholder_portraits` rule).

## Quickstart

```python
from lib.asset_sourcing.portraits import source

result = source(
    name="Allen Dulles",                     # Wikipedia article title (also tries variants)
    lastname_slug="dulles",                  # used in output filename
    out_dir=Path("projects/.../assets"),     # where to save portrait_<slug>.jpg
    commons_filenames=[                       # OPTIONAL extra Commons filenames to try
        "Allen W. Dulles official photo.jpg",
        "Allen Welsh Dulles.jpg",
    ],
)
if result:
    print(f"Sourced from {result['source']}: {result['path']}")
```

Returns `dict` with keys `path`, `source`, `url`, `license`, `size_bytes` on success,
or `None` if no source produced a valid image. Also writes a sidecar credit file
`portrait_<lastname_slug>_credit.txt` with full attribution.

## Source chain (in order)

1. **Wikipedia REST API** — `/api/rest_v1/page/summary/<title>` returns the article's lead image. Free, no auth, usually highest-quality available.
2. **Wikimedia Commons File: API** — for specific named files (`File:Allen W Dulles.jpg`).
3. **Library of Congress search** — `loc.gov/photos/` query returns matching PD photos.

Each step gracefully falls through to the next on failure. The first source
that returns a valid image (>5KB, recognized as `image/*`) wins.

## Memory references

- `never_placeholder_portraits` — the rule this satisfies
- `project_archival_assets_process` — three-tier sourcing for any archival imagery

## CLI usage

```bash
python -m lib.asset_sourcing.portraits "Allen Dulles" dulles ./out_dir
```
"""
from __future__ import annotations
import json, sys, subprocess, urllib.parse, pathlib
from typing import Optional
import requests

UA = "OpenMontage/1.0 (asset-sourcing; +https://example.local)"
MIN_BYTES = 5000


def _try_wiki_rest(title: str) -> Optional[dict]:
    """Wikipedia REST page summary — returns the article's lead image URL."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        if r.status_code != 200:
            return None
        data = r.json()
    except Exception:
        return None
    # Prefer originalimage (full res), fall back to thumbnail
    img = data.get("originalimage") or data.get("thumbnail")
    if not img:
        return None
    return {
        "url": img["source"],
        "source": f"Wikipedia ({title})",
        "license": "Verify at " + data.get("content_urls", {}).get("desktop", {}).get("page", ""),
    }


def _try_commons_file(filename: str) -> Optional[dict]:
    """Wikimedia Commons File: lookup — resolves the actual hashed URL."""
    api = (
        "https://commons.wikimedia.org/w/api.php"
        f"?action=query&titles=File:{urllib.parse.quote(filename)}"
        "&prop=imageinfo&iiprop=url&format=json"
    )
    try:
        r = requests.get(api, headers={"User-Agent": UA}, timeout=20)
        if r.status_code != 200:
            return None
        data = r.json()
    except Exception:
        return None
    for _, page in data.get("query", {}).get("pages", {}).items():
        info = page.get("imageinfo")
        if info:
            return {
                "url": info[0]["url"],
                "source": f"Commons (File:{filename})",
                "license": "https://commons.wikimedia.org/wiki/File:" + filename.replace(" ", "_"),
            }
    return None


def _try_loc_search(query: str) -> Optional[dict]:
    """Library of Congress photo search."""
    url = f"https://www.loc.gov/photos/?q={urllib.parse.quote(query)}&fo=json&c=5"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
        if r.status_code != 200:
            return None
        data = r.json()
    except Exception:
        return None
    for item in data.get("results", []):
        imgs = item.get("image_url")
        if imgs and isinstance(imgs, list) and imgs:
            url_candidate = imgs[-1] if "http" in imgs[-1] else imgs[0]
            return {
                "url": url_candidate,
                "source": "Library of Congress",
                "license": item.get("rights", "PD (LoC default)"),
            }
    return None


def _download(url: str, out: pathlib.Path) -> int:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=60)
    except Exception:
        return 0
    if r.status_code != 200:
        return 0
    out.write_bytes(r.content)
    return len(r.content)


def _is_image(path: pathlib.Path) -> bool:
    """Crude check via `file` so we don't accept HTML error pages as images."""
    try:
        ftype = subprocess.run(
            ["file", "-b", str(path)], capture_output=True, text=True
        ).stdout.strip().lower()
        return "image" in ftype
    except Exception:
        return False


def source(
    name: str,
    lastname_slug: str,
    out_dir: pathlib.Path | str,
    *,
    commons_filenames: Optional[list[str]] = None,
    loc_query: Optional[str] = None,
    verbose: bool = True,
) -> Optional[dict]:
    """Try the source-chain in order; download the first valid image.

    Args:
        name: Wikipedia article title (e.g. "Allen Dulles", "Kermit Roosevelt Jr.")
        lastname_slug: Used in the output filename (e.g. "dulles" → portrait_dulles.jpg)
        out_dir: Directory to save the portrait + credit sidecar into. Created if missing.
        commons_filenames: Optional extra File:... names to try after the Wikipedia REST.
        loc_query: LoC search query if Wikipedia + Commons fail. Defaults to `name`.
        verbose: Print progress to stdout.

    Returns:
        dict with `path`, `source`, `url`, `license`, `size_bytes` on success, OR
        None if all sources fail.
    """
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"portrait_{lastname_slug}.jpg"
    log = print if verbose else (lambda *a, **k: None)

    candidates: list[tuple[str, callable]] = [
        (f"Wikipedia REST: {name}",        lambda: _try_wiki_rest(name)),
        # Title-with-underscores variant
        (f"Wikipedia REST: {name.replace(' ', '_')}",
                                           lambda: _try_wiki_rest(name.replace(" ", "_"))),
    ]
    for fname in (commons_filenames or []):
        candidates.append((f"Commons File:{fname}", lambda f=fname: _try_commons_file(f)))
    candidates.append((
        f"LoC search '{loc_query or name}'",
        lambda: _try_loc_search(loc_query or name),
    ))

    log(f"\n=== Sourcing portrait: {name} → {out_path.name} ===")
    for label, fn in candidates:
        log(f"  trying {label}...")
        result = fn()
        if not result:
            log(f"    no match")
            continue
        size = _download(result["url"], out_path)
        if size < MIN_BYTES:
            log(f"    downloaded {size} bytes — too small, skipping")
            continue
        if not _is_image(out_path):
            log(f"    not a recognized image, skipping")
            continue
        log(f"    ✓ {size} bytes from {result['source']}")
        # Write credit sidecar
        sidecar = out_dir / f"portrait_{lastname_slug}_credit.txt"
        sidecar.write_text(
            f"Source: {result['source']}\n"
            f"URL: {result['url']}\n"
            f"License: {result['license']}\n"
        )
        return {
            "path": str(out_path),
            "source": result["source"],
            "url": result["url"],
            "license": result["license"],
            "size_bytes": size,
        }

    log(f"  FAILED — no valid source found for {name}")
    return None


# ---------------------------------------------------------------------------
# CLI

def _cli() -> None:
    if len(sys.argv) < 4:
        print(
            "Usage: python -m lib.asset_sourcing.portraits <Wikipedia title> <lastname_slug> <out_dir>\n"
            "Example: python -m lib.asset_sourcing.portraits 'Allen Dulles' dulles ./assets",
            file=sys.stderr,
        )
        sys.exit(1)
    name, slug, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    result = source(name, slug, out_dir)
    if result:
        print(json.dumps(result, indent=2))
        sys.exit(0)
    sys.exit(2)


if __name__ == "__main__":
    _cli()
