"""Shared Replicate helpers — currently retry-with-backoff for 429 / 5xx."""

from __future__ import annotations

import time
from typing import Any

import requests


def replicate_post_with_retry(
    url: str,
    headers: dict[str, str],
    json_payload: dict[str, Any],
    *,
    max_retries: int = 6,
    base_backoff: float = 2.0,
    max_backoff: float = 60.0,
    timeout: float = 90.0,
) -> requests.Response:
    """POST to Replicate's prediction endpoint with exponential backoff on
    429 (rate-limited) and 5xx (server) responses.

    Replicate enforces a per-second burst limit on POST /v1/predictions that
    routinely triggers when a batch of predictions is submitted in quick
    succession (even at modest concurrency). Without retry, a sweep loses
    multiple jobs and the wall clock fills with re-run cycles.

    Backoff sequence: 2s, 4s, 8s, 16s, 32s, 60s (capped). Total worst-case
    wait before giving up: ~2 minutes across 6 retries.
    """
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        resp: requests.Response | None = None
        try:
            resp = requests.post(url, headers=headers, json=json_payload, timeout=timeout)
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                if attempt < max_retries:
                    delay = min(base_backoff * (2 ** attempt), max_backoff)
                    time.sleep(delay)
                    continue
                # Out of retries — surface the response as an error.
                resp.raise_for_status()
            resp.raise_for_status()
            return resp
        except requests.HTTPError as e:
            last_exc = e
            if (
                attempt < max_retries
                and resp is not None
                and (resp.status_code == 429 or 500 <= resp.status_code < 600)
            ):
                delay = min(base_backoff * (2 ** attempt), max_backoff)
                time.sleep(delay)
                continue
            raise
        except requests.RequestException as e:
            # Connection error, timeout, etc. — retry too.
            last_exc = e
            if attempt < max_retries:
                delay = min(base_backoff * (2 ** attempt), max_backoff)
                time.sleep(delay)
                continue
            raise

    if last_exc:
        raise last_exc
    raise RuntimeError("replicate_post_with_retry: exhausted retries without an exception (unreachable)")
