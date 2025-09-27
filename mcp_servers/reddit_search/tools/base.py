import os
import logging
import httpx
from typing import Dict, List, TypedDict
import time
import random
import re
import asyncio

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# load the reddit api key
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")


# base api urls
REDDIT_API_BASE = "https://oauth.reddit.com"
REDDIT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "klavis-mcp/0.1 (+https://klavis.ai)")

# cached access token and client
_access_token: str | None = None
_token_expires_at: float | None = None
_user_access_token: str | None = None
_user_token_expires_at: float | None = None
_async_client: httpx.AsyncClient | None = None
_token_lock: asyncio.Lock = asyncio.Lock()
_user_token_lock: asyncio.Lock = asyncio.Lock()


# simple per-process concurrency limiter (env-configurable)
_max_concurrency = int(os.getenv("REDDIT_MAX_CONCURRENCY", "10"))
_request_semaphore = asyncio.Semaphore(_max_concurrency)


async def _ensure_async_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=10.0))
    return _async_client


async def _refresh_token_locked() -> None:
    """Refresh OAuth token under lock. Caller must hold _token_lock."""
    global _access_token, _token_expires_at

    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set")

    logger.info("Requesting new Reddit API access token…")
    client = await _ensure_async_client()
    auth = (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {
        "grant_type": "client_credentials",
        "scope": "identity submit read"  # Required scopes for posting and reading
    }
    headers = {"User-Agent": REDDIT_USER_AGENT}
    resp = await client.post(REDDIT_TOKEN_URL, auth=auth, data=data, headers=headers)
    resp.raise_for_status()
    token_data = resp.json()
    _access_token = token_data.get("access_token")
    expires_in = float(token_data.get("expires_in", 3600))
    # refresh a bit early to avoid expiry races
    _token_expires_at = time.time() + max(60.0, expires_in - 120.0)
    logger.info("Obtained new Reddit API access token.")


async def _get_reddit_auth_header() -> dict[str, str]:
    """Return Authorization header, refreshing the token if needed."""
    global _access_token, _token_expires_at

    # Fast path: token exists and not near expiry
    if _access_token and _token_expires_at and time.time() < _token_expires_at:
        return {"Authorization": f"Bearer {_access_token}", "User-Agent": REDDIT_USER_AGENT}

    # Acquire lock to refresh once across awaiters
    async with _token_lock:
        if _access_token and _token_expires_at and time.time() < _token_expires_at:
            
            return {"Authorization": f"Bearer {_access_token}", "User-Agent": REDDIT_USER_AGENT}
        await _refresh_token_locked()
        return {"Authorization": f"Bearer {_access_token}", "User-Agent": REDDIT_USER_AGENT}


async def _refresh_user_token_locked() -> None:
    """Refresh user OAuth token under lock using password grant. Caller must hold _user_token_lock."""
    global _user_access_token, _user_token_expires_at

    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
        raise ValueError("REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, and REDDIT_PASSWORD must be set for user actions.")

    logger.info("Requesting new user-specific Reddit API access token…")
    client = await _ensure_async_client()
    auth = (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {
        "grant_type": "password",
        "username": REDDIT_USERNAME,
        "password": REDDIT_PASSWORD,
        "scope": "identity submit read vote"
    }
    headers = {"User-Agent": REDDIT_USER_AGENT}
    resp = await client.post(REDDIT_TOKEN_URL, auth=auth, data=data, headers=headers)
    resp.raise_for_status()
    token_data = resp.json()
    _user_access_token = token_data.get("access_token")
    expires_in = float(token_data.get("expires_in", 3600))
    _user_token_expires_at = time.time() + max(60.0, expires_in - 120.0)
    logger.info("Obtained new user-specific Reddit API access token.")


async def _get_reddit_user_auth_header() -> dict[str, str]:
    """Return user Authorization header, refreshing the token if needed."""
    global _user_access_token, _user_token_expires_at

    if _user_access_token and _user_token_expires_at and time.time() < _user_token_expires_at:
        return {"Authorization": f"Bearer {_user_access_token}", "User-Agent": REDDIT_USER_AGENT}

    async with _user_token_lock:
        if _user_access_token and _user_token_expires_at and time.time() < _user_token_expires_at:
            return {"Authorization": f"Bearer {_user_access_token}", "User-Agent": REDDIT_USER_AGENT}
        await _refresh_user_token_locked()
        return {"Authorization": f"Bearer {_user_access_token}", "User-Agent": REDDIT_USER_AGENT}


async def reddit_get(path: str, params: Dict | None = None, max_retries: int = 3) -> Dict:
    """HTTP GET helper with UA header and async retry/backoff including 429.

    path should start with '/'.
    """
    client = await _ensure_async_client()
    headers = await _get_reddit_auth_header()
    params = params.copy() if params else {}
    params.setdefault("raw_json", 1)

    backoff_seconds = 1.0
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        async with _request_semaphore:
            try:
                resp = await client.get(f"{REDDIT_API_BASE}{path}", headers=headers, params=params)
                if resp.status_code == 401:
                    # Token likely expired/invalid; refresh once and retry
                    async with _token_lock:
                        await _refresh_token_locked()
                        headers = await _get_reddit_auth_header()
                    resp = await client.get(f"{REDDIT_API_BASE}{path}", headers=headers, params=params)

                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    sleep_s = float(retry_after) if retry_after else backoff_seconds
                    logger.warning(f"Reddit API 429 rate limit. Sleeping {sleep_s}s then retrying…")
                    await asyncio.sleep(sleep_s + random.uniform(0, 0.25))
                    backoff_seconds = min(backoff_seconds * 2, 8)
                    continue

                resp.raise_for_status()
                return resp.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                logger.warning(f"Reddit GET {path} failed (attempt {attempt+1}/{max_retries}): {exc}")
                await asyncio.sleep(backoff_seconds + random.uniform(0, 0.5))
                backoff_seconds = min(backoff_seconds * 2, 8)

    if last_exc:
        raise last_exc
    raise RuntimeError("Reddit GET failed unexpectedly with no exception recorded")


async def reddit_get_as_user(path: str, params: Dict | None = None, max_retries: int = 3) -> Dict:
    """HTTP GET helper for user actions with retry/backoff logic."""
    client = await _ensure_async_client()
    headers = await _get_reddit_user_auth_header()
    params = params.copy() if params else {}
    params.setdefault("raw_json", 1)

    backoff_seconds = 1.0
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        async with _request_semaphore:
            try:
                resp = await client.get(f"{REDDIT_API_BASE}{path}", headers=headers, params=params)
                if resp.status_code == 401:
                    async with _user_token_lock:
                        await _refresh_user_token_locked()
                        headers = await _get_reddit_user_auth_header()
                    resp = await client.get(f"{REDDIT_API_BASE}{path}", headers=headers, params=params)

                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    sleep_s = float(retry_after) if retry_after else backoff_seconds
                    logger.warning(f"Reddit API 429 rate limit. Sleeping {sleep_s}s then retrying…")
                    await asyncio.sleep(sleep_s + random.uniform(0, 0.25))
                    backoff_seconds = min(backoff_seconds * 2, 8)
                    continue

                resp.raise_for_status()
                return resp.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                logger.warning(f"Reddit GET (as user) {path} failed (attempt {attempt+1}/{max_retries}): {exc}")
                await asyncio.sleep(backoff_seconds + random.uniform(0, 0.5))
                backoff_seconds = min(backoff_seconds * 2, 8)

    if last_exc:
        raise last_exc
    raise RuntimeError("Reddit GET (as user) failed unexpectedly with no exception recorded")



async def reddit_post_as_user(path: str, data: Dict, max_retries: int = 3) -> Dict:
    """HTTP POST helper for user actions with retry/backoff logic."""
    client = await _ensure_async_client()
    headers = await _get_reddit_user_auth_header()

    backoff_seconds = 1.0
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        async with _request_semaphore:
            try:
                resp = await client.post(f"{REDDIT_API_BASE}{path}", headers=headers, data=data)

                if resp.status_code == 401:
                    async with _user_token_lock:
                        await _refresh_user_token_locked()
                        headers = await _get_reddit_user_auth_header()
                    resp = await client.post(f"{REDDIT_API_BASE}{path}", headers=headers, data=data)

                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    sleep_s = float(retry_after) if retry_after else backoff_seconds
                    logger.warning(f"Reddit API 429 rate limit. Sleeping {sleep_s}s then retrying…")
                    await asyncio.sleep(sleep_s + random.uniform(0, 0.25))
                    backoff_seconds = min(backoff_seconds * 2, 8)
                    continue

                resp.raise_for_status()
                return resp.json()

            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                logger.warning(f"Reddit POST {path} failed (attempt {attempt+1}/{max_retries}): {exc}")
                await asyncio.sleep(backoff_seconds + random.uniform(0, 0.5))
                backoff_seconds = min(backoff_seconds * 2, 8)

    if last_exc:
        raise last_exc
    raise RuntimeError("Reddit POST failed unexpectedly with no exception recorded")

    
# Lifecycle helpers to integrate with server startup/shutdown
async def init_http_clients() -> None:
    await _ensure_async_client()


async def close_http_clients() -> None:
    global _async_client
    if _async_client is not None:
        try:
            await _async_client.aclose()
        finally:
            _async_client = None


_STOPWORDS = {
    "the", "a", "an", "and", "or", "vs", "vs.", "to", "for", "of", "on", "in", "with",
    "is", "are", "be", "by", "from", "about", "between",
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", value or "")).strip().lower()


def tokenize(value: str) -> list[str]:
    norm = normalize_text(value)
    tokens = [t for t in norm.split() if t and t not in _STOPWORDS]
    return tokens


def generate_variants(tokens: list[str]) -> list[str]:
    # Create simple variants like joined tokens e.g., ["claude", "code"] -> "claudecode"
    variants: list[str] = []
    if len(tokens) >= 2:
        variants.append("".join(tokens))
        variants.append("-".join(tokens))
    # Add common brand variants heuristically
    joined = " ".join(tokens)
    if "cursor" in joined and "ai" in joined and "cursorai" not in variants:
        variants.append("cursorai")
        variants.append("cursor ai")
    if "claude" in joined and "code" in joined and "claudecode" not in variants:
        variants.append("claudecode")
        variants.append("claude code")
    return [v for v in variants if v]


def build_broad_query(query: str) -> str:
    """Build a broader Reddit search query using OR groups and variants.

    If the query looks like a comparison (contains 'vs'), we split into two
    groups and AND them to emphasize posts mentioning both sides.
    """
    text = normalize_text(query)
    parts = re.split(r"\bvs\.?\b", text)
    groups: list[list[str]] = []
    for part in parts:
        toks = tokenize(part)
        if not toks:
            continue
        variants = generate_variants(toks)
        # Group as OR terms inside parentheses
        or_terms = toks + variants
        # Escape quotes inside each term for Reddit search
        group = [f'"{term}"' if " " in term else term for term in or_terms]
        groups.append(group)

    if not groups:
        return text

    if len(groups) == 1:
        return "(" + " OR ".join(groups[0]) + ")"
    # Multiple groups -> AND them
    return " AND ".join("(" + " OR ".join(g) + ")" for g in groups)


def compute_semantic_score(query: str, title: str, selftext: str) -> float:
    """Score semantic relatedness via token overlap with light heuristics.

    Higher weight to title matches; small bonus if both sides of a 'vs' query appear.
    """
    query_tokens = set(tokenize(query))
    title_tokens = set(tokenize(title))
    body_tokens = set(tokenize(selftext))

    if not query_tokens:
        return 0.0

    title_overlap = len(query_tokens & title_tokens)
    body_overlap = len(query_tokens & body_tokens)

    score = title_overlap * 2.0 + body_overlap * 1.0

    # If it is a comparison query, ensure both sides appear
    parts = re.split(r"\bvs\.?\b", normalize_text(query))
    if len(parts) >= 2:
        side_scores = []
        for p in parts[:2]:
            toks = set(tokenize(p))
            side_scores.append(len(toks & (title_tokens | body_tokens)) > 0)
        if all(side_scores):
            score += 2.0

    return float(score)



