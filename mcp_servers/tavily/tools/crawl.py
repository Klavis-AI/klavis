# tools/crawl.py
import os
import re
import time
import json
import asyncio
import logging
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any, Set, Deque, Tuple, Optional, Literal
from collections import deque

import httpx
from app import mcp
from .client import BASE, auth_headers
from .errors import normalize
from .types import CrawlResponse
from .extract import _shape_extract_response  # reuse normalizer

# Logging safeguard
log = logging.getLogger("tavily")
if not log.handlers:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

REQUEST_TIMEOUT_S = float(os.getenv("TAVILY_TIMEOUT_S", "20"))
CONNECT_TIMEOUT_S = float(os.getenv("TAVILY_CONNECT_TIMEOUT_S", "5"))
MAX_RETRIES = int(os.getenv("TAVILY_MAX_RETRIES", "2"))
SEMAPHORE_MAX = int(os.getenv("TAVILY_CONCURRENCY", "8"))
CACHE_TTL_S = int(os.getenv("TAVILY_CACHE_TTL_S", "120"))

MAX_PAGES_DEFAULT = int(os.getenv("TAVILY_CRAWL_MAX_PAGES", "50"))
HTML_FETCH_TIMEOUT_S = float(os.getenv("TAVILY_HTML_FETCH_TIMEOUT_S", "8"))

_SEM = asyncio.Semaphore(SEMAPHORE_MAX)
_CACHE: Dict[str, Dict[str, Any]] = {}

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

def _validate_params_single(url: str, max_depth: int, max_breadth: int, limit: int):
    if not isinstance(url, str) or not url.strip():
        raise RuntimeError("url must be a non-empty string")
    if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 3:
        # API requires x >= 1; keep a modest upper bound for safety
        raise RuntimeError("max_depth must be an integer between 1 and 3")
    if not isinstance(max_breadth, int) or max_breadth < 1:
        raise RuntimeError("max_breadth must be >= 1")
    if not isinstance(limit, int) or limit < 1 or limit > 500:
        raise RuntimeError("limit must be between 1 and 500")

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

def _same_domain(a: str, b: str) -> bool:
    try:
        return urlparse(a).netloc == urlparse(b).netloc
    except Exception:
        return False

_LINK_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)

def _extract_links_from_html(html: str, base_url: str) -> List[str]:
    if not html:
        return []
    links = []
    for m in _LINK_RE.finditer(html):
        href = m.group(1)
        full = urljoin(base_url, href)
        links.append(full)
    out, seen = [], set()
    for u in links:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out

async def _fetch_html_for_links(url: str) -> str:
    """Lightweight HTML fetch ONLY to discover <a href> links when Tavily returns plain text."""
    try:
        async with httpx.AsyncClient(timeout=HTML_FETCH_TIMEOUT_S, follow_redirects=True) as http:
            r = await http.get(url, headers={"User-Agent": "KlavisMCP-Tavily/0.1"})
            if r.status_code >= 400:
                return ""
            ct = r.headers.get("Content-Type", "")
            if "text/html" not in ct:
                return ""
            return r.text or ""
    except Exception:
        return ""

async def _tavily_extract_batch(urls: List[str], include_images: bool = False) -> List[Dict[str, Any]]:
    payload = {"urls": urls, "include_images": bool(include_images)}
    r = await _post_with_retry("/extract", payload)
    normalize(r)
    try:
        shaped = _shape_extract_response(r.json())  # {"results":[...]}
    except ValueError as e:
        raise RuntimeError(f"ERR_UPSTREAM_BODY: invalid JSON in response: {e}") from e
    return shaped.get("results", [])

def _shape_crawl_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Tavily /crawl response (results with raw_content, favicon, etc.)
    into our CrawlResponse schema: {"pages":[{url, title?, content?, images?, depth?, parent?, favicon?}]}
    """
    pages = []
    for item in data.get("results", []) or []:
        if not isinstance(item, dict):
            continue
        pages.append({
            "url": item.get("url"),
            "title": item.get("title"),
            "content": item.get("raw_content") or item.get("content") or item.get("text"),
            "images": item.get("images") or item.get("image_urls"),
            "favicon": item.get("favicon"),
            # depth/parent may not be present in /crawl beta; allow extras
            "depth": item.get("depth"),
            "parent": item.get("parent"),
        })
    return {"pages": pages}

@mcp.tool(
    name="tavily_crawl",
    description=(
        "Crawl from a single start URL up to max_depth/max_breadth/limit, returning extracted pages. "
        "Use for site exploration and content collection when you need multiple pages, not just one."
    ),
)
async def tavily_crawl(
    url: str,
    max_depth: int = 1,
    max_breadth: int = 20,
    limit: int = MAX_PAGES_DEFAULT,
    instructions: Optional[str] = None,
    select_paths: Optional[List[str]] = None,
    select_domains: Optional[List[str]] = None,
    exclude_paths: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    allow_external: bool = True,
    include_images: bool = False,
    categories: Optional[List[str]] = None,
    extract_depth: Literal["basic", "advanced"] = "basic",
    format: Literal["markdown", "text"] = "markdown",
    include_favicon: bool = False,
) -> CrawlResponse:
    """
    Tavily Crawl: graph-based traversal with built-in extraction & discovery (single start URL).

    Inputs:
      - url (required): root URL to begin the crawl (scheme or bare domain both accepted)
      - instructions (optional): natural language guidance for crawler (increases cost)
      - max_depth (>=1), max_breadth (>=1), limit (>=1)
      - select_paths, select_domains, exclude_paths, exclude_domains: regex filters
      - allow_external: include external domains in results
      - include_images: include images in results
      - categories: list of predefined categories (e.g., "Documentation", "Blog", "API")
      - extract_depth: "basic" | "advanced"
      - format: "markdown" | "text"
      - include_favicon: include favicon URL per result

    Returns:
      CrawlResponse: { pages: [{url, title?, content?, images?, favicon?, depth?, parent?}, ...] }
    """
    # Validate core params
    _validate_params_single(url, max_depth, max_breadth, limit)

    # Build payload per Tavily /crawl
    payload: Dict[str, Any] = {
        "url": url.strip(),
        "max_depth": max_depth,
        "max_breadth": max_breadth,
        "limit": limit,
        "allow_external": allow_external,
        "include_images": include_images,
        "extract_depth": extract_depth,
        "format": format,
        "include_favicon": include_favicon,
    }
    # Optional fields only if provided
    if instructions: payload["instructions"] = instructions
    if select_paths: payload["select_paths"] = select_paths
    if select_domains: payload["select_domains"] = select_domains
    if exclude_paths: payload["exclude_paths"] = exclude_paths
    if exclude_domains: payload["exclude_domains"] = exclude_domains
    if categories: payload["categories"] = categories

    # Cache
    ck = _cache_key(payload)
    cached = _cache_get(ck)
    if cached:
        return CrawlResponse.model_validate(cached)

    start_ts = time.time()

    # Try native /crawl first
    try:
        async with _SEM:
            r = await _post_with_retry("/crawl", payload)
        normalize(r)
        try:
            shaped = _shape_crawl_response(r.json())
        except ValueError as e:
            raise RuntimeError(f"ERR_UPSTREAM_BODY: invalid JSON in response: {e}") from e
        elapsed_ms = (time.time() - start_ts) * 1000.0
        log.info("tavily_crawl native ok depth=%s breadth=%s limit=%s pages=%s ms=%.1f",
                 max_depth, max_breadth, limit, len(shaped.get("pages", [])), elapsed_ms)
        _cache_set(ck, shaped)
        return CrawlResponse.model_validate(shaped)
    except Exception as e:
        # Fallback: lightweight BFS via /extract (+ minimal HTML link discovery)
        log.info("tavily_crawl: native /crawl failed or unavailable, fallback BFS. reason=%s", str(e))

    # ---------- Fallback BFS ----------
    pages: List[Dict[str, Any]] = []
    visited: Set[str] = set()
    q: Deque[Tuple[str, int, Optional[str]]] = deque([(url.strip(), 0, None)])

    async with _SEM:
        while q and len(pages) < limit:
            current_url, depth, parent = q.popleft()
            if current_url in visited:
                continue
            visited.add(current_url)

            # Extract current page
            try:
                batch = await _tavily_extract_batch([current_url], include_images=include_images)
            except Exception as ex:
                log.warning("extract failed url=%s err=%s", current_url, ex)
                pages.append({
                    "url": current_url,
                    "title": None,
                    "content": None,
                    "images": None,
                    "favicon": None,
                    "depth": depth,
                    "parent": parent,
                })
                continue

            if not batch:
                pages.append({
                    "url": current_url,
                    "title": None,
                    "content": None,
                    "images": None,
                    "favicon": None,
                    "depth": depth,
                    "parent": parent,
                })
            else:
                item = batch[0]
                pages.append({
                    "url": item.get("url") or current_url,
                    "title": item.get("title"),
                    "content": item.get("content"),
                    "images": item.get("images"),
                    "favicon": None,  # /extract doesn't return favicon
                    "depth": depth,
                    "parent": parent,
                })

            # Discover next links if we can go deeper
            if depth < max_depth and len(pages) < limit:
                html = await _fetch_html_for_links(current_url)
                discovered = _extract_links_from_html(html, current_url)

                # Apply simple domain restriction to mimic allow_external=False
                if not allow_external:
                    discovered = [u for u in discovered if _same_domain(u, url)]

                # Apply simple regex-based filters when provided
                def _match_any(patterns: Optional[List[str]], value: str) -> bool:
                    if not patterns:
                        return True
                    return any(re.search(p, value) for p in patterns)

                filtered = []
                for link in discovered:
                    if not _match_any(select_domains, urlparse(link).netloc):
                        continue
                    if not _match_any(select_paths, urlparse(link).path):
                        continue
                    if exclude_domains and any(re.search(p, urlparse(link).netloc) for p in exclude_domains):
                        continue
                    if exclude_paths and any(re.search(p, urlparse(link).path) for p in exclude_paths):
                        continue
                    filtered.append(link)

                # Enqueue up to max_breadth for the next depth
                next_links = []
                for link in filtered:
                    if link not in visited:
                        next_links.append(link)
                        if len(next_links) >= max_breadth:
                            break

                for link in next_links:
                    q.append((link, depth + 1, current_url))
    # -----------------------------------

    elapsed_ms = (time.time() - start_ts) * 1000.0
    shaped_fallback = {"pages": pages}
    log.info("tavily_crawl fallback ok depth=%s breadth=%s limit=%s pages=%s ms=%.1f",
             max_depth, max_breadth, limit, len(pages), elapsed_ms)

    _cache_set(ck, shaped_fallback)
    return CrawlResponse.model_validate(shaped_fallback)
