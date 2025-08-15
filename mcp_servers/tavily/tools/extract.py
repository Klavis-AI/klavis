# tools/extract.py
import os
import time
import json
import asyncio
import logging
from typing import List, Dict, Any, Union, Optional

import httpx
from app import mcp
from .client import BASE, auth_headers
from .errors import normalize
from .types import ExtractResponse

# Logging safeguard: configure only if no handlers exist
log = logging.getLogger("tavily")
if not log.handlers:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

REQUEST_TIMEOUT_S = float(os.getenv("TAVILY_TIMEOUT_S", "20"))
CONNECT_TIMEOUT_S = float(os.getenv("TAVILY_CONNECT_TIMEOUT_S", "5"))
MAX_RETRIES = int(os.getenv("TAVILY_MAX_RETRIES", "3"))
SEMAPHORE_MAX = int(os.getenv("TAVILY_CONCURRENCY", "8"))
CACHE_TTL_S = int(os.getenv("TAVILY_CACHE_TTL_S", "120"))

_SEM = asyncio.Semaphore(SEMAPHORE_MAX)
_CACHE: Dict[str, Dict[str, Any]] = {}

def _validate_params(urls: List[str]):
    if not isinstance(urls, list) or not urls:
        raise RuntimeError("urls must be a non-empty list of strings")
    bad = [u for u in urls if not isinstance(u, str) or not u.strip()]
    if bad:
        raise RuntimeError("every item in urls must be a non-empty string")

def _cache_key(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)

def _cache_get(k: str):
    ent = _CACHE.get(k)
    if not ent:
        return None
    if time.time() > ent["exp"]:
        _CACHE.pop(k, None)
        return None
    return ent["data"]

def _cache_set(k: str, data: Dict[str, Any]):
    _CACHE[k] = {"data": data, "exp": time.time() + CACHE_TTL_S}

async def _post_with_retry(path: str, payload: dict) -> httpx.Response:
    retry_statuses = {429, 502, 503, 504}
    attempt = 0
    last_exc = None
    r: Optional[httpx.Response] = None  # prevent UnboundLocalError on rare paths
    timeouts = httpx.Timeout(REQUEST_TIMEOUT_S, connect=CONNECT_TIMEOUT_S)
    async with httpx.AsyncClient(timeout=timeouts, headers=auth_headers()) as http:
        while attempt <= MAX_RETRIES:
            try:
                r = await http.post(f"{BASE}{path}", json=payload)
                if r.status_code in retry_statuses:
                    ra = r.headers.get("Retry-After")
                    try:
                        sleep_s = float(ra) if ra else 2 ** attempt
                    except ValueError:
                        sleep_s = 2 ** attempt
                    await asyncio.sleep(min(sleep_s, 8))
                    attempt += 1
                    continue
                return r
            except httpx.RequestError as e:
                last_exc = e
                await asyncio.sleep(min(2 ** attempt, 8))
                attempt += 1
        if last_exc:
            raise RuntimeError(f"Network error after retries: {last_exc}")
        if r is None:
            raise RuntimeError("Network error after retries: no response object")
        return r

def _shape_extract_payload(urls: List[str], include_images: bool) -> Dict[str, Any]:
    return {"urls": urls, "include_images": bool(include_images)}

def _shape_extract_response(data: Dict[str, Any]) -> Dict[str, Any]:
    # Normalize different upstream field names into content and images
    items = []
    for item in data.get("results", []) or data.get("data", []) or []:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        title = item.get("title")
        # content can appear under various keys
        content = (
            item.get("content")
            or item.get("raw_content")
            or item.get("text")
            or item.get("article")
            or item.get("markdown")
        )
        # images array may appear under different keys, keep as list if present
        images = item.get("images") or item.get("image_urls") or None
        if isinstance(images, str):
            images = [images]
        items.append({"url": url, "title": title, "content": content, "images": images})
    return {"results": items}

@mcp.tool(
    name="tavily_extract",
    description=(
        "Extract the primary content from one or more URLs. "
        "Use when you already know the URL(s) and need cleaned text and optional images."
    ),
)
async def tavily_extract(urls: Union[str, List[str]], include_images: bool = False) -> ExtractResponse:
    """
    Fetch and extract the main content from one or more URLs.

    Inputs:
      - urls: string or list of strings
      - include_images: bool

    Returns:
      ExtractResponse:
        results: [{url, title?, content?, images?}]
      Fields may be missing if the source page does not provide them.

    Errors:
      ERR_UNAUTHORIZED, ERR_RATE_LIMIT, or ERR_UPSTREAM_<status> with a short hint.
    Side effects: none.
    """
    # normalize to list BEFORE validation
    if isinstance(urls, str):
        urls = [urls]
    elif not isinstance(urls, list) or not all(isinstance(u, str) and u.strip() for u in urls):
        raise RuntimeError("urls must be a string or a non-empty list of non-empty strings")

    _validate_params(urls)

    payload = _shape_extract_payload(urls, include_images)
    ck = _cache_key(payload)
    cached = _cache_get(ck)
    if cached:
        return ExtractResponse.model_validate(cached)

    start = time.time()
    async with _SEM:
        r = await _post_with_retry("/extract", payload)
    try:
        normalize(r)
    except Exception as e:
        log.warning("tavily_extract fail n_urls=%s err=%s", len(urls), e)
        raise

    try:
        raw = r.json()
    except ValueError as e:
        # Defensive: valid HTTP but invalid JSON body
        raise RuntimeError(f"ERR_UPSTREAM_BODY: invalid JSON in response: {e}") from e

    data = _shape_extract_response(raw)

    elapsed_ms = (time.time() - start) * 1000.0
    log.info("tavily_extract ok n_urls=%s ms=%.1f", len(urls), elapsed_ms)

    _cache_set(ck, data)
    return ExtractResponse.model_validate(data)
