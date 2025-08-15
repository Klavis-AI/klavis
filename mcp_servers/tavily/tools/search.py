# tools/search.py
import os
import time
import uuid
import json
import asyncio
import logging
from typing import Optional, Literal, Dict, Any

import httpx
from app import mcp
from .client import BASE, auth_headers
from .errors import normalize
from .types import SearchResponse

# ---------- Config ----------
MAX_RESULTS_CAP = int(os.getenv("TAVILY_MAX_RESULTS_CAP", "10"))
REQUEST_TIMEOUT_S = float(os.getenv("TAVILY_TIMEOUT_S", "20"))
CONNECT_TIMEOUT_S = float(os.getenv("TAVILY_CONNECT_TIMEOUT_S", "5"))
MAX_RETRIES = int(os.getenv("TAVILY_MAX_RETRIES", "2"))
CACHE_TTL_S = int(os.getenv("TAVILY_CACHE_TTL_S", "120"))
SEMAPHORE_MAX = int(os.getenv("TAVILY_CONCURRENCY", "8"))

ALLOWED_DEPTH = {"basic", "advanced"}

# ---------- Infra ----------
log = logging.getLogger("tavily")
if not log.handlers:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

_SEM = asyncio.Semaphore(SEMAPHORE_MAX)
_CACHE: Dict[str, Dict[str, Any]] = {}

def _clean_query(q: str, max_len: int = 500) -> str:
    q = "".join(ch for ch in q if ch.isprintable())
    q = q.strip()
    return q[:max_len]

def _validate_params(
    query: str,
    search_depth: str,
    max_results: int,
    days: Optional[int],
) -> None:
    if not isinstance(query, str) or not query.strip():
        raise RuntimeError("query must be a non-empty string")
    if search_depth not in ALLOWED_DEPTH:
        raise RuntimeError("search_depth must be 'basic' or 'advanced'")
    if not isinstance(max_results, int) or not 1 <= max_results <= MAX_RESULTS_CAP:
        raise RuntimeError(f"max_results must be 1..{MAX_RESULTS_CAP}")
    if days is not None and not (0 <= days <= 365):
        raise RuntimeError("days must be between 0 and 365")

def _cache_key(payload: Dict[str, Any]) -> str:
    # Deterministic key from payload
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)

def _cache_get(key: str):
    ent = _CACHE.get(key)
    if not ent:
        return None
    if time.time() > ent["exp"]:
        _CACHE.pop(key, None)
        return None
    return ent["data"]

def _cache_set(key: str, data: Dict[str, Any]):
    _CACHE[key] = {"data": data, "exp": time.time() + CACHE_TTL_S}

async def _post_with_retry(path: str, payload: dict) -> httpx.Response:
    retry_statuses = {429, 502, 503, 504}
    attempt = 0
    last_exc = None
    r: Optional[httpx.Response] = None  # initialize to avoid UnboundLocalError
    timeouts = httpx.Timeout(REQUEST_TIMEOUT_S, connect=CONNECT_TIMEOUT_S)
    async with httpx.AsyncClient(timeout=timeouts, headers={
        **auth_headers(),
        "User-Agent": "KlavisMCP-Tavily/0.1",
        "X-Request-Id": str(uuid.uuid4()),
    }) as http:
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
        return r  # fallback

@mcp.tool(
    name="tavily_search",
    description=(
        "Search the web for a query and return summarized results. "
        "Use when you need current information or reputable sources. "
        "Returns an optional synthesized answer plus result items."
    ),
)
async def tavily_search(
    query: str,
    search_depth: Literal["basic", "advanced"] = "basic",
    max_results: int = 5,
    include_answer: bool = True,
    include_raw_content: bool = False,
    days: Optional[int] = None,
    topic: Optional[str] = None,
) -> SearchResponse:
    """
    Execute a Tavily web search and return structured results.

    Inputs:
      - query: non-empty search text
      - search_depth: 'basic' for faster shallow search, 'advanced' for deeper search
      - max_results: 1..10
      - include_answer: include a synthesized final answer when available
      - include_raw_content: include raw_content snippets per result when available
      - days: optional freshness filter 0..365
      - topic: optional topical focus string

    Returns:
      SearchResponse with answer, results [{url, title, content, score, favicon?}],
      response_time (string), and auto_parameters.

    Errors:
      ERR_UNAUTHORIZED, ERR_RATE_LIMIT, or ERR_UPSTREAM_<status> with a brief hint.
    Side effects: none.
    """
    # Validate and sanitize
    _validate_params(query, search_depth, max_results, days)
    query = _clean_query(query)

    payload = {
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_answer": include_answer,
        "include_raw_content": include_raw_content,
    }
    if days is not None:
        payload["days"] = days
    if topic is not None:
        payload["topic"] = topic

    # Simple cache for basic small searches
    ck = None
    if search_depth == "basic" and max_results <= 5 and not include_raw_content:
        ck = _cache_key(payload)
        cached = _cache_get(ck)
        if cached:
            # Coerce response_time to string for schema consistency
            rt = cached.get("response_time")
            if isinstance(rt, (int, float)):
                cached["response_time"] = str(rt)
            return SearchResponse.model_validate(cached)

    start = time.time()
    async with _SEM:
        r = await _post_with_retry("/search", payload)
    try:
        normalize(r)
    except Exception as e:
        log.warning("tavily_search fail depth=%s max=%s err=%s", search_depth, max_results, e)
        raise

    elapsed_ms = (time.time() - start) * 1000.0
    data = r.json()

    # Response shaping
    # Coerce response_time to string to satisfy clients expecting string|null
    rt = data.get("response_time")
    if isinstance(rt, (int, float)):
        data["response_time"] = str(rt)

    # Deduplicate by URL
    seen = set()
    deduped = []
    for it in data.get("results", []):
        u = it.get("url")
        if u and u not in seen:
            deduped.append(it)
            seen.add(u)
    data["results"] = deduped

    log.info(
        "tavily_search ok depth=%s max=%s ms=%.1f results=%s",
        search_depth,
        max_results,
        elapsed_ms,
        len(data.get("results", [])),
    )

    # Cache only safe responses
    if ck:
        try:
            _cache_set(ck, data)
        except Exception:
            pass

    return SearchResponse.model_validate(data)
