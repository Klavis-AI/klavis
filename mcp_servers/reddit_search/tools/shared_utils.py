import os 
import logging
import requests
from typing import Dict, List, TypedDict
import time
import random
import re

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# load the reddit api key
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

# base api urls
REDDIT_API_BASE = "https://oauth.reddit.com"
REDDIT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "klavis-mcp/0.1 (+https://klavis.ai)")

# cached access token
_access_token = None
_token_expires_at: float | None = None

def _get_reddit_auth_header() -> dict[str, str]:
    """
    Authenticates with the Reddit API and returns the required authorization header.
    It cleverly caches the access token in memory.
    """
    global _access_token

    # if the access token is already cached, return it
    if _access_token:
        return {"Authorization": f"Bearer {_access_token}", "User-Agent": REDDIT_USER_AGENT}

    # if the client_ID and client_secret are not set, raise an error
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set")
    
    auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {"grant_type": "client_credentials"}
    headers = {"User-Agent": REDDIT_USER_AGENT}

    logger.info("No cached token found. Requesting new Reddit API access token...")

    # make the post request to get the access token
    response = requests.post(REDDIT_TOKEN_URL, auth=auth, data=data, headers=headers)
    response.raise_for_status()

    token_data = response.json()
    _access_token = token_data["access_token"]
    logger.info("Successfully obtained and cached new Reddit API access token.")

    return {"Authorization": f"Bearer {_access_token}", "User-Agent": REDDIT_USER_AGENT}


def reddit_get(path: str, params: Dict | None = None, max_retries: int = 3) -> Dict:
    """HTTP GET helper with UA header and simple retry/backoff including 429.

    path should start with '/'.
    """
    headers = _get_reddit_auth_header()
    params = params.copy() if params else {}
    # Prefer raw_json for more consistent body content
    params.setdefault("raw_json", 1)

    backoff_seconds = 1.0
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{REDDIT_API_BASE}{path}", headers=headers, params=params, timeout=20)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                sleep_s = float(retry_after) if retry_after else backoff_seconds
                logger.warning(f"Reddit API 429 rate limit. Sleeping {sleep_s}s then retrying…")
                time.sleep(sleep_s)
                backoff_seconds = min(backoff_seconds * 2, 8)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            logger.warning(f"Reddit GET {path} failed (attempt {attempt+1}/{max_retries}): {exc}")
            time.sleep(backoff_seconds + random.uniform(0, 0.5))
            backoff_seconds = min(backoff_seconds * 2, 8)

    # If all retries failed, raise last exception
    if last_exc:
        raise last_exc
    raise RuntimeError("Reddit GET failed unexpectedly with no exception recorded")


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


# Define the structure of the returned data
class SubredditInfo(TypedDict):
    """Structured data for a single subreddit."""
    name: str
    subscriber_count: int
    description: str


class PostInfo(TypedDict):
    """Structured data for a Reddit post summary."""
    id: str
    subreddit: str
    title: str
    score: int
    url: str
    comment_count: int


class CommentInfo(TypedDict):
    """Structured data for a single comment."""
    author: str
    text: str
    score: int


class PostDetails(TypedDict):
    """The combined structure for a post and its top comments."""
    title: str
    author: str
    text: str
    score: int
    top_comments: List[CommentInfo]
