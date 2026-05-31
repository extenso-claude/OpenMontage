"""Recraft V4.1 wrapper for the animation catalog.

Channel-agnostic. Each call takes a `theme` dict (see themes/*.py) that
provides palette + style addendum + negative prompt. Hard cost ceiling
keeps us at the 80-credit ($0.08) Vector or 40-credit ($0.04) Raster tiers —
never Pro ($0.25–$0.30, BANNED).

Direct API only (no fal.ai gateway) — uses RECRAFT_API_KEY from .env.

Model defaults (May 2026, post-V4.1 release):
- Raster (default): `recraftv4_1` — best for animated subjects + transparent PNGs
- Vector:            `recraftv4_1_vector` — best for backgrounds (SVG scales cleanly)

V4+ schema notes: V4+ models do NOT accept `style`, `substyle`, `style_id`,
`negative_prompt`, or `text_layout` in the payload. The wrapper auto-strips
those when routing to V4+. Exclusions must be baked into the positive prompt
via the scene description (the theme's negative_prompt is still passed at the
*theme* layer but won't reach the V4+ API).

See memories:
- `recraft_v4_1_upgrade` — model strings, schema diffs, supported sizes
- `midnight_magnates_style_locked_v2` — current MM style addendum
- `recraft_pricing_rule` — cost ceiling (80 = $0.08 vector, banned 250+)
- `recraft_direct_api_rule` — direct API only, fal.ai banned
"""
from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env")

API_KEY = os.environ.get("RECRAFT_API_KEY")
API_BASE = "https://external.api.recraft.ai/v1"
MIN_BYTES = 3000

# Cost ceiling. V4.1 raster = 40 credits = $0.04. Vector V4.1 = 80 credits = $0.08.
# Pro V4.1 = 250–300 credits ($0.25–$0.30) — BANNED.
MAX_CREDITS_PER_IMAGE = 80

# V4+ model prefixes — these accept a DIFFERENT payload schema than V2/V3.
V4_PLUS_PREFIXES = ("recraftv4", "recraftv4_1")

# Default sizes per model family. V4.1 max 16:9 is smaller than V3 (1344×768 vs 1820×1024).
DEFAULT_SIZE_V4 = "1344x768"   # V4+ max 16:9
DEFAULT_SIZE_V3 = "1820x1024"  # V3 max 16:9


def _is_v4_plus(model: str) -> bool:
    return any(model.startswith(p) for p in V4_PLUS_PREFIXES)


def _is_vector_model(model: str) -> bool:
    return model.endswith("_vector")


def gen(
    prompt: str,
    out_path: Path,
    *,
    theme: dict,                          # REQUIRED — palette + style addendum + negative_prompt
    model: str = "recraftv4_1",           # V4.1 raster default (May 2026 lock)
    size: Optional[str] = None,           # auto-picked by model family if None
    # V2/V3-only legacy params (silently ignored on V4+):
    style: str = "digital_illustration",
    substyle: Optional[str] = "noir",
    style_id: Optional[str] = None,
    overwrite: bool = False,
) -> dict:
    """Generate one Recraft image using the provided theme's palette + style addendum.

    Default model is `recraftv4_1` (raster). For vector backgrounds, pass
    `model="recraftv4_1_vector"`. The wrapper automatically routes between
    V4+ and V2/V3 schemas — V4+ drops `style`, `substyle`, `style_id`,
    `negative_prompt` from the payload (these are not accepted by V4+).

    Returns dict with: out_path, credits, cost_usd, skipped, image_url,
    size_bytes, model, schema.

    Idempotent: skips if out_path already exists with > MIN_BYTES.
    """
    out_path = Path(out_path)
    if not overwrite and out_path.exists() and out_path.stat().st_size > MIN_BYTES:
        return {"out_path": str(out_path), "credits": 0, "cost_usd": 0.0, "skipped": True}

    if not API_KEY:
        raise RuntimeError("RECRAFT_API_KEY not set in .env")
    if "style_addendum" not in theme or "palette_rgb" not in theme:
        raise ValueError(
            "theme dict must include 'style_addendum' and 'palette_rgb' — "
            "see tools/animation/catalog/themes/midnight_magnates.py for shape"
        )

    is_v4 = _is_v4_plus(model)
    if size is None:
        size = DEFAULT_SIZE_V4 if is_v4 else DEFAULT_SIZE_V3

    # Compose the full prompt. Theme's style_addendum is auto-prepended.
    full_prompt = f"{theme['style_addendum']}. {prompt}"

    payload: dict = {
        "prompt": full_prompt,
        "model": model,
        "size": size,
        "n": 1,
        "response_format": "url",
    }

    if is_v4:
        # V4+ schema — no style / substyle / style_id / negative_prompt accepted.
        # Theme palette can still be passed via `controls.colors`.
        if theme.get("palette_rgb"):
            payload["controls"] = {"colors": [{"rgb": rgb} for rgb in theme["palette_rgb"]]}
        schema = "V4+"
    else:
        # V2/V3 schema — full payload with style + substyle + negative_prompt + palette.
        payload["negative_prompt"] = theme.get("negative_prompt", "")
        if style_id:
            payload["style_id"] = style_id
        else:
            payload["style"] = style
            if substyle:
                payload["substyle"] = substyle
        if theme.get("palette_rgb"):
            payload["controls"] = {"colors": [{"rgb": rgb} for rgb in theme["palette_rgb"]]}
        schema = "V2/V3"

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    t0 = time.time()
    r = requests.post(f"{API_BASE}/images/generations", headers=headers, json=payload, timeout=180)
    if r.status_code != 200:
        raise RuntimeError(f"Recraft API {r.status_code} [{model} / {schema}]: {r.text[:600]}")

    data = r.json()
    image_url = data["data"][0]["url"]
    # Default credits guess: 40 for raster, 80 for vector
    default_credits = 80 if _is_vector_model(model) else 40
    credits = data.get("credits", default_credits)
    if credits > MAX_CREDITS_PER_IMAGE:
        raise RuntimeError(
            f"Credits {credits} exceeds ceiling {MAX_CREDITS_PER_IMAGE} — "
            f"likely hit Pro pricing tier (BANNED per recraft_pricing_rule). Aborting."
        )

    img_r = requests.get(image_url, timeout=120)
    img_r.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(img_r.content)
    cost = credits / 1000.0  # 40 credits = $0.04, 80 = $0.08
    return {
        "out_path": str(out_path),
        "credits": credits,
        "cost_usd": round(cost, 4),
        "duration_s": round(time.time() - t0, 2),
        "skipped": False,
        "image_url": image_url,
        "size_bytes": len(img_r.content),
        "model": model,
        "schema": schema,
    }
