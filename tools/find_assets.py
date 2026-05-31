"""
find_assets.py — Multi-source search for YouTube-monetization-safe images
and video. Spin up for any video where you need copyright-free / free-licensed
assets.

Queries the following sources in parallel:
  • Wikimedia Commons     (PD + CC, no API key)
  • Openverse             (CC + PD aggregator across Flickr Commons, Wikimedia, etc.)
  • Internet Archive      (PD newsreels, archived sites, Prelinger Archives)
  • Library of Congress   (PD photo + film archive)
  • Smithsonian Open Access (4.5M CC0 items — needs free key)
  • NASA Image Library    (PD space imagery)
  • Pexels                (free stock photos + video — needs free key)
  • Pixabay               (free stock photos + video — needs free key)

License taxonomy filters to YouTube-monetization-compatible only:
  ALLOWED: PD, CC0, CC-BY, CC-BY-SA, PEXELS, PIXABAY, MIXKIT, NASA, GOV
  REJECTED: CC-BY-NC, CC-BY-ND, unknown commercial, paid stock

Usage:
  python find_assets.py --query "charles manson 1969"
  python find_assets.py --query "hale-bopp comet" --type image --limit 30
  python find_assets.py --queries-from artifacts/cuelist.json --out qa.csv
  python find_assets.py --query "spahn ranch" --type video --download top3

Env vars (optional — sources skip if missing):
  PEXELS_KEY        https://www.pexels.com/api/
  PIXABAY_KEY       https://pixabay.com/api/docs/
  SMITHSONIAN_KEY   https://api.si.edu/openaccess/api/v1.0/
"""
from __future__ import annotations
import argparse, csv, json, os, pathlib, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict

UA = "MidnightMagnatesAssetFinder/1.0 (educational, sleep-doc YouTube)"
TIMEOUT = 12

# ─── License taxonomy ─────────────────────────────────────────────────────

# License keys we explicitly ALLOW for YouTube monetization
ALLOWED_LICENSES = {"PD", "CC0", "CC-BY", "CC-BY-SA",
                    "PEXELS", "PIXABAY", "MIXKIT",
                    "NASA-PD", "GOV-PD"}
# License keys we REJECT (will be filtered out)
REJECTED_LICENSES = {"CC-BY-NC", "CC-BY-NC-SA", "CC-BY-NC-ND",
                     "CC-BY-ND", "PROPRIETARY", "GETTY", "AP-WIRE"}

# Score map — higher = better
SCORE = {
    "PD": 100, "CC0": 100, "NASA-PD": 100, "GOV-PD": 95,
    "MIXKIT": 95, "PIXABAY": 90, "PEXELS": 90,
    "CC-BY": 80, "CC-BY-SA": 70, "UNKNOWN": 30,
}

def normalize_license(raw: str) -> str:
    """Map a raw license string to our normalized taxonomy."""
    if not raw: return "UNKNOWN"
    r = raw.lower().strip()
    # Order matters — check most-specific first
    if "publicdomain" in r or "public domain" in r or r == "pdm": return "PD"
    if "cc0" in r or r == "cczero": return "CC0"
    if "cc-by-nc-sa" in r or "cc by-nc-sa" in r: return "CC-BY-NC-SA"
    if "cc-by-nc-nd" in r or "cc by-nc-nd" in r: return "CC-BY-NC-ND"
    if "cc-by-nc" in r or "cc by-nc" in r: return "CC-BY-NC"
    if "cc-by-nd" in r or "cc by-nd" in r: return "CC-BY-ND"
    if "cc-by-sa" in r or "cc by-sa" in r: return "CC-BY-SA"
    if "cc-by" in r or "cc by" in r: return "CC-BY"
    if "pexels" in r: return "PEXELS"
    if "pixabay" in r: return "PIXABAY"
    if "mixkit" in r: return "MIXKIT"
    if "nasa" in r and "public" in r: return "NASA-PD"
    if "gov" in r and ("work" in r or "domain" in r): return "GOV-PD"
    return "UNKNOWN"

# ─── Asset model ──────────────────────────────────────────────────────────

@dataclass
class Asset:
    source: str            # e.g. "wikimedia", "pexels", "internet_archive"
    kind: str              # "image" or "video"
    title: str
    url: str               # direct download or source page
    thumbnail: str         # preview thumbnail URL
    license_raw: str       # source-reported license string
    license_norm: str      # our normalized taxonomy
    attribution: str       # required attribution text or ""
    width: int = 0
    height: int = 0
    duration_s: float = 0.0
    score: int = 0
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        self.license_norm = normalize_license(self.license_raw)
        self.score = SCORE.get(self.license_norm, 0)
        # Resolution bonus
        if self.width >= 1920: self.score += 10
        elif self.width >= 1280: self.score += 5

    @property
    def monetization_safe(self) -> bool:
        return self.license_norm in ALLOWED_LICENSES

# ─── Generic HTTP helper ──────────────────────────────────────────────────

def _get_json(url: str, headers: dict | None = None) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ⚠ {url[:60]}…  {e}", file=sys.stderr)
        return None

# ─── Per-source search functions ──────────────────────────────────────────

def search_wikimedia(query: str, limit: int, kind: str) -> list[Asset]:
    """Wikimedia Commons via the MediaWiki API. PD + CC, no auth."""
    if kind == "video":
        # Wikimedia has a few PD video files but they're rare. Skip for video-first runs.
        return []
    url = (f"https://commons.wikimedia.org/w/api.php?action=query&format=json"
            f"&generator=search&gsrnamespace=6&gsrlimit={limit}"
            f"&gsrsearch={urllib.parse.quote(query + ' filetype:bitmap')}"
            f"&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=800")
    data = _get_json(url)
    if not data: return []
    out = []
    pages = (data.get("query") or {}).get("pages", {})
    for p in pages.values():
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        license_raw = (meta.get("LicenseShortName") or {}).get("value", "")
        attribution = (meta.get("Artist") or {}).get("value", "")
        out.append(Asset(
            source="wikimedia",
            kind="image",
            title=p.get("title", ""),
            url=info.get("url", ""),
            thumbnail=info.get("thumburl") or info.get("url", ""),
            license_raw=license_raw,
            license_norm="",
            attribution=attribution,
            width=info.get("width", 0),
            height=info.get("height", 0),
        ))
    return out

def search_openverse(query: str, limit: int, kind: str) -> list[Asset]:
    """Openverse — CC + PD aggregator (Flickr Commons, Wikimedia, etc.). No auth."""
    if kind == "video":
        return []   # Openverse currently indexes images + audio, no video
    url = (f"https://api.openverse.org/v1/images/"
            f"?q={urllib.parse.quote(query)}&page_size={limit}"
            f"&license=cc0,pdm,by,by-sa")  # filter on-server to safe licenses
    data = _get_json(url)
    if not data: return []
    out = []
    for r in data.get("results", []):
        out.append(Asset(
            source="openverse",
            kind="image",
            title=r.get("title", ""),
            url=r.get("url", ""),
            thumbnail=r.get("thumbnail", ""),
            license_raw=r.get("license", ""),
            license_norm="",
            attribution=r.get("creator", ""),
            width=r.get("width", 0),
            height=r.get("height", 0),
            extra={"foreign_landing_url": r.get("foreign_landing_url")},
        ))
    return out

def search_internet_archive(query: str, limit: int, kind: str) -> list[Asset]:
    """Internet Archive advanced search. Includes Prelinger PD ephemeral film collection."""
    mt = "movies" if kind == "video" else "image"
    q = f'({query}) AND mediatype:({mt})'
    url = (f"https://archive.org/advancedsearch.php?q={urllib.parse.quote(q)}"
            f"&fl[]=identifier&fl[]=title&fl[]=licenseurl&fl[]=creator&fl[]=mediatype"
            f"&rows={limit}&page=1&output=json")
    data = _get_json(url)
    if not data: return []
    out = []
    for d in (data.get("response") or {}).get("docs", []):
        ident = d.get("identifier", "")
        license_raw = d.get("licenseurl", "") or ""
        # Internet Archive often lists creativecommons.org/publicdomain/zero/ etc.
        if "publicdomain" in license_raw: license_raw = "publicdomain"
        elif "cc0" in license_raw: license_raw = "cc0"
        elif "/by/" in license_raw: license_raw = "cc-by"
        elif "/by-sa/" in license_raw: license_raw = "cc-by-sa"
        elif "/by-nc/" in license_raw: license_raw = "cc-by-nc"
        elif "/by-nd/" in license_raw: license_raw = "cc-by-nd"
        out.append(Asset(
            source="internet_archive",
            kind=kind,
            title=d.get("title", ""),
            url=f"https://archive.org/details/{ident}",
            thumbnail=f"https://archive.org/services/img/{ident}",
            license_raw=license_raw,
            license_norm="",
            attribution=str(d.get("creator", "")),
        ))
    return out

def search_loc(query: str, limit: int, kind: str) -> list[Asset]:
    """Library of Congress search. PD-by-default for most pre-1929 items + LOC publications."""
    fa = "online" if kind == "image" else "online,format:film"
    url = (f"https://www.loc.gov/photos/?q={urllib.parse.quote(query)}&fo=json"
            f"&c={limit}&fa={urllib.parse.quote(fa)}")
    data = _get_json(url)
    if not data: return []
    out = []
    for r in data.get("results", [])[:limit]:
        rights = r.get("rights_advisory") or r.get("rights", "")
        if isinstance(rights, list): rights = " ".join(map(str, rights))
        # LOC items are generally PD or "no known restrictions"
        license_norm = "PD" if ("no known" in rights.lower() or "public domain" in rights.lower()) else "UNKNOWN"
        out.append(Asset(
            source="library_of_congress",
            kind=kind,
            title=r.get("title", ""),
            url=r.get("url", ""),
            thumbnail=(r.get("image_url") or [""])[0] if isinstance(r.get("image_url"), list) else r.get("image_url", ""),
            license_raw=rights or "No known restrictions",
            license_norm="",
            attribution="Library of Congress",
        ))
        # Force our normalized value (otherwise the dataclass normalize misses LOC's phrasing)
        out[-1].license_norm = license_norm
        out[-1].score = SCORE.get(license_norm, 0)
    return out

def search_nasa(query: str, limit: int, kind: str) -> list[Asset]:
    """NASA Image Library — `images-api.nasa.gov`. Mostly PD (with some exceptions)."""
    media = "video" if kind == "video" else "image"
    url = (f"https://images-api.nasa.gov/search?q={urllib.parse.quote(query)}"
            f"&media_type={media}&page_size={limit}")
    data = _get_json(url)
    if not data: return []
    out = []
    for r in (data.get("collection") or {}).get("items", [])[:limit]:
        links = r.get("links") or [{}]
        thumb = links[0].get("href", "")
        d0 = (r.get("data") or [{}])[0]
        out.append(Asset(
            source="nasa",
            kind=kind,
            title=d0.get("title", ""),
            url=thumb,
            thumbnail=thumb,
            license_raw="NASA public domain",
            license_norm="",
            attribution=d0.get("center", "NASA"),
        ))
    return out

def search_smithsonian(query: str, limit: int, kind: str) -> list[Asset]:
    """Smithsonian Open Access — needs free API key."""
    key = os.environ.get("SMITHSONIAN_KEY")
    if not key: return []
    type_filter = "Videos" if kind == "video" else "Images"
    url = (f"https://api.si.edu/openaccess/api/v1.0/search?q={urllib.parse.quote(query)}"
            f"&rows={limit}&api_key={key}")
    data = _get_json(url)
    if not data: return []
    out = []
    for r in (data.get("response") or {}).get("rows", [])[:limit]:
        content = (r.get("content") or {}).get("descriptiveNonRepeating", {})
        title = (content.get("title") or {}).get("content", "")
        # Smithsonian Open Access items are CC0 by definition
        media = content.get("online_media", {}).get("media", [{}])
        if not media: continue
        m0 = media[0]
        out.append(Asset(
            source="smithsonian",
            kind="image" if (m0.get("type") or "").lower() == "images" else kind,
            title=title,
            url=m0.get("content", ""),
            thumbnail=(m0.get("thumbnail") or m0.get("content", "")),
            license_raw="CC0 (Smithsonian Open Access)",
            license_norm="",
            attribution="Smithsonian Open Access",
        ))
    return out

def search_pexels(query: str, limit: int, kind: str) -> list[Asset]:
    """Pexels API — needs free key. Returns Pexels-licensed free stock."""
    key = os.environ.get("PEXELS_KEY")
    if not key: return []
    base = "videos" if kind == "video" else "v1"
    sub = "search"
    url = f"https://api.pexels.com/{base}/{sub}?query={urllib.parse.quote(query)}&per_page={limit}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Authorization": key,
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print(f"  ⚠ pexels: {e}", file=sys.stderr)
        return []
    out = []
    if kind == "video":
        for v in data.get("videos", []):
            files = v.get("video_files", [])
            hd = next((f for f in files if f.get("width", 0) >= 1920 and f.get("quality") == "hd"), files[0] if files else {})
            out.append(Asset(
                source="pexels",
                kind="video",
                title=v.get("url", "").split("/")[-2].replace("-", " ")[:80],
                url=hd.get("link", ""),
                thumbnail=v.get("image", ""),
                license_raw="Pexels License",
                license_norm="",
                attribution=(v.get("user") or {}).get("name", "Pexels"),
                width=v.get("width", 0),
                height=v.get("height", 0),
                duration_s=v.get("duration", 0.0),
            ))
    else:
        for p in data.get("photos", []):
            out.append(Asset(
                source="pexels",
                kind="image",
                title=p.get("alt", ""),
                url=(p.get("src") or {}).get("original", ""),
                thumbnail=(p.get("src") or {}).get("medium", ""),
                license_raw="Pexels License",
                license_norm="",
                attribution=(p.get("photographer", "")),
                width=p.get("width", 0),
                height=p.get("height", 0),
            ))
    return out

def search_pixabay(query: str, limit: int, kind: str) -> list[Asset]:
    """Pixabay API — needs free key."""
    key = os.environ.get("PIXABAY_KEY")
    if not key: return []
    if kind == "video":
        url = f"https://pixabay.com/api/videos/?key={key}&q={urllib.parse.quote(query)}&per_page={limit}&safesearch=true"
    else:
        url = f"https://pixabay.com/api/?key={key}&q={urllib.parse.quote(query)}&per_page={limit}&image_type=photo&safesearch=true"
    data = _get_json(url)
    if not data: return []
    out = []
    for r in data.get("hits", []):
        if kind == "video":
            vids = r.get("videos", {})
            best = vids.get("large") or vids.get("medium") or {}
            out.append(Asset(
                source="pixabay",
                kind="video",
                title=r.get("tags", "")[:80],
                url=best.get("url", ""),
                thumbnail=r.get("userImageURL") or f"https://i.vimeocdn.com/video/{r.get('picture_id', '')}_640.jpg",
                license_raw="Pixabay License",
                license_norm="",
                attribution=r.get("user", "Pixabay"),
                width=best.get("width", 0),
                height=best.get("height", 0),
                duration_s=r.get("duration", 0.0),
            ))
        else:
            out.append(Asset(
                source="pixabay",
                kind="image",
                title=r.get("tags", "")[:80],
                url=r.get("largeImageURL", ""),
                thumbnail=r.get("webformatURL", ""),
                license_raw="Pixabay License",
                license_norm="",
                attribution=r.get("user", "Pixabay"),
                width=r.get("imageWidth", 0),
                height=r.get("imageHeight", 0),
            ))
    return out

# ─── Orchestrator ─────────────────────────────────────────────────────────

SOURCES = [
    ("wikimedia", search_wikimedia),
    ("openverse", search_openverse),
    ("internet_archive", search_internet_archive),
    ("library_of_congress", search_loc),
    ("nasa", search_nasa),
    ("smithsonian", search_smithsonian),
    ("pexels", search_pexels),
    ("pixabay", search_pixabay),
]

def search_all(query: str, kind: str, limit_per_source: int = 10) -> list[Asset]:
    """Run every source in parallel. Returns ranked, filtered results."""
    results: list[Asset] = []
    with ThreadPoolExecutor(max_workers=len(SOURCES)) as pool:
        futures = {pool.submit(fn, query, limit_per_source, kind): name
                    for name, fn in SOURCES}
        for fut in as_completed(futures):
            name = futures[fut]
            try:
                got = fut.result()
                results.extend(got)
                print(f"  ✓ {name:22s}  {len(got)} hits", file=sys.stderr)
            except Exception as e:
                print(f"  ✗ {name:22s}  {e}", file=sys.stderr)
    # Filter to monetization-safe, then sort by score desc
    safe = [a for a in results if a.monetization_safe]
    safe.sort(key=lambda a: a.score, reverse=True)
    return safe

# ─── Output ───────────────────────────────────────────────────────────────

def write_csv(assets: list[Asset], path: pathlib.Path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "score", "source", "kind", "license_norm", "license_raw",
            "title", "url", "thumbnail", "width", "height", "duration_s",
            "attribution",
        ])
        w.writeheader()
        for a in assets:
            w.writerow({k: getattr(a, k) for k in w.fieldnames})

def write_json(assets: list[Asset], path: pathlib.Path):
    path.write_text(json.dumps([asdict(a) for a in assets], indent=2))

# ─── CLI ──────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Multi-source free-asset search for YouTube-safe images + video")
    ap.add_argument("--query", help="Single search query")
    ap.add_argument("--queries-from", help="JSON file with [{query, kind, id}, …]")
    ap.add_argument("--type", choices=["image", "video", "both"], default="both")
    ap.add_argument("--limit", type=int, default=10,
                     help="Max results PER SOURCE (default 10)")
    ap.add_argument("--out", default="found_assets.csv",
                     help="Output CSV path (default found_assets.csv)")
    ap.add_argument("--out-json", help="Also write JSON to this path")
    args = ap.parse_args()

    if not args.query and not args.queries_from:
        ap.error("Need either --query or --queries-from")

    queries: list[tuple[str, str]] = []
    if args.query:
        if args.type == "both":
            queries.extend([(args.query, "image"), (args.query, "video")])
        else:
            queries.append((args.query, args.type))
    if args.queries_from:
        data = json.loads(pathlib.Path(args.queries_from).read_text())
        for entry in data:
            q = entry["query"]
            k = entry.get("kind", "both")
            if k == "both":
                queries.extend([(q, "image"), (q, "video")])
            else:
                queries.append((q, k))

    all_assets: list[Asset] = []
    for q, k in queries:
        print(f"\n=== Searching: {q!r} ({k}) ===", file=sys.stderr)
        all_assets.extend(search_all(q, k, args.limit))

    out_path = pathlib.Path(args.out)
    write_csv(all_assets, out_path)
    print(f"\n✓ Wrote {len(all_assets)} monetization-safe results → {out_path}", file=sys.stderr)
    if args.out_json:
        write_json(all_assets, pathlib.Path(args.out_json))
        print(f"✓ Also wrote JSON → {args.out_json}", file=sys.stderr)

    # Print top 10 to stdout for quick scanning
    print("\nTop 10 by score:", file=sys.stderr)
    for a in all_assets[:10]:
        print(f"  [{a.score}] {a.source:18s} {a.license_norm:8s} {a.kind:6s} {a.title[:70]}", file=sys.stderr)
        print(f"      {a.url}", file=sys.stderr)

if __name__ == "__main__":
    main()
