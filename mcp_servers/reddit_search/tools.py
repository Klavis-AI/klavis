import os 
import logging
import requests
from typing import Dict,List, TypedDict
import time
import random
import re
from urllib.parse import urlencode

from dotenv import load_dotenv

load_dotenv()

logger =  logging.getLogger(__name__)

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


def _reddit_get(path: str, params: Dict | None = None, max_retries: int = 3) -> Dict:
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


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", value or "")).strip().lower()


def _tokenize(value: str) -> list[str]:
    norm = _normalize_text(value)
    tokens = [t for t in norm.split() if t and t not in _STOPWORDS]
    return tokens


def _generate_variants(tokens: list[str]) -> list[str]:
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


def _build_broad_query(query: str) -> str:
    """Build a broader Reddit search query using OR groups and variants.

    If the query looks like a comparison (contains 'vs'), we split into two
    groups and AND them to emphasize posts mentioning both sides.
    """
    text = _normalize_text(query)
    parts = re.split(r"\bvs\.?\b", text)
    groups: list[list[str]] = []
    for part in parts:
        toks = _tokenize(part)
        if not toks:
            continue
        variants = _generate_variants(toks)
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


def _compute_semantic_score(query: str, title: str, selftext: str) -> float:
    """Score semantic relatedness via token overlap with light heuristics.

    Higher weight to title matches; small bonus if both sides of a 'vs' query appear.
    """
    query_tokens = set(_tokenize(query))
    title_tokens = set(_tokenize(title))
    body_tokens = set(_tokenize(selftext))

    if not query_tokens:
        return 0.0

    title_overlap = len(query_tokens & title_tokens)
    body_overlap = len(query_tokens & body_tokens)

    score = title_overlap * 2.0 + body_overlap * 1.0

    # If it is a comparison query, ensure both sides appear
    parts = re.split(r"\bvs\.?\b", _normalize_text(query))
    if len(parts) >= 2:
        side_scores = []
        for p in parts[:2]:
            toks = set(_tokenize(p))
            side_scores.append(len(toks & (title_tokens | body_tokens)) > 0)
        if all(side_scores):
            score += 2.0

    return float(score)

# define the structure of the returned data
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

# implement the functions utilised by the tools
async def find_relevant_subreddits(query: str) -> List[SubredditInfo]:
    """ find subreddits that are relevant to the query and clean up the data """
    headers = _get_reddit_auth_header()
    params = {"q": query, "limit": 10, "type": "sr"}

    logger.info(f"Making API call to Reddit to find subreddits for query: '{query}'")
    data = _reddit_get("/subreddits/search", params=params)
    # Reddit API returns data in listing format: {"data": {"children": [...]}}
    subreddits = data["data"]["children"]
    
    # We loop through the raw results and build a clean list of our SubredditInfo objects.
    return [
        SubredditInfo(
            name=sub["data"]["display_name"],
            subscriber_count=sub["data"]["subscribers"],
            description=sub["data"].get("public_description", "No description provided."),
        )
        for sub in subreddits
    ]
async def search_subreddit_posts(subreddit: str, query: str) -> List[PostInfo]:
    """Search for posts in a subreddit with semantic-style matching.

    Strategy:
    - Build a broad Reddit search query (boolean OR groups, detect comparisons)
    - Use Reddit's /search with restrict_sr=1 for recall
    - Rank locally with token-overlap semantic score + Reddit score fallback
    - Fall back to listing endpoints if search yields too few results
    """
    # Clean inputs
    subreddit = subreddit.strip().strip("'\"")
    subreddit = subreddit.removeprefix("r/") if subreddit.lower().startswith("r/") else subreddit
    query = query.strip().strip("'\"")

    # Build a broad query string
    broad_q = _build_broad_query(query)

    matching_posts: list[PostInfo] = []
    scored: list[tuple[float, PostInfo]] = []

    # 1) Try Reddit's search API scoped to subreddit
    try:
        params = {
            "q": broad_q,
            "limit": 50,
            "type": "link",
            "sort": "relevance",
            "restrict_sr": 1,
        }
        data = _reddit_get("/search", params={**params, "sr_detail": False, "subreddit": subreddit})
        posts = data.get("data", {}).get("children", [])
        for post in posts:
            pd = post.get("data", {})
            pi: PostInfo = PostInfo(
                id=pd.get("id", ""),
                subreddit=pd.get("subreddit", subreddit),
                title=pd.get("title", ""),
                score=int(pd.get("score", 0)),
                url=pd.get("url", ""),
                comment_count=int(pd.get("num_comments", 0)),
            )
            sem_score = _compute_semantic_score(query, pi["title"], pd.get("selftext", ""))
            scored.append((sem_score, pi))
    except Exception as exc:
        logger.warning(f"Subreddit search failed, will try listing-based fallback. Error: {exc}")

    # 2) Fallback to listing endpoints and local filtering if needed
    if len(scored) < 10:
        try:
            hot = _reddit_get(f"/r/{subreddit}/hot", params={"limit": 25}).get("data", {}).get("children", [])
            top = _reddit_get(f"/r/{subreddit}/top", params={"limit": 25, "t": "month"}).get("data", {}).get("children", [])
            for post in hot + top:
                pd = post.get("data", {})
                pi: PostInfo = PostInfo(
                    id=pd.get("id", ""),
                    subreddit=pd.get("subreddit", subreddit),
                    title=pd.get("title", ""),
                    score=int(pd.get("score", 0)),
                    url=pd.get("url", ""),
                    comment_count=int(pd.get("num_comments", 0)),
                )
                sem_score = _compute_semantic_score(query, pi["title"], pd.get("selftext", ""))
                if sem_score > 0:
                    scored.append((sem_score, pi))
        except Exception as exc:
            logger.warning(f"Listing fallback failed: {exc}")

    # 3) Rank: semantic score first, then Reddit score
    # Deduplicate by id
    seen: set[str] = set()
    for s, pi in sorted(scored, key=lambda x: (x[0], x[1]["score"]), reverse=True):
        if not pi["id"] or pi["id"] in seen:
            continue
        seen.add(pi["id"])
        matching_posts.append(pi)
        if len(matching_posts) >= 10:
            break

    return matching_posts
async def get_post_and_top_comments(post_id: str, subreddit: str) -> PostDetails:
    """Gets post and comment details via the Reddit API and cleans the data."""
    headers = _get_reddit_auth_header()
    params = {"limit": 3, "sort": "top", "raw_json": 1}

    logger.info(f"Making API call to Reddit for comments on post '{post_id}' in subreddit '{subreddit}'")
    # Use the comments endpoint directly - this is the correct Reddit API pattern
    data = _reddit_get(f"/comments/{post_id}", params=params)
    
    # Reddit returns an array: [post_listing, comments_listing]
    # First element contains the post data, second contains comments
    if len(data) < 2:
        raise ValueError("Invalid response structure from Reddit API")
    
    post_listing = data[0]["data"]["children"]
    comments_listing = data[1]["data"]["children"]
    
    if not post_listing:
        raise ValueError(f"Post with ID '{post_id}' not found")
    
    post_data = post_listing[0]["data"]

    # Here we assemble our final, nested PostDetails object from the raw API data.
    return PostDetails(
        title=post_data["title"],
        author=post_data["author"],
        text=post_data.get("selftext", "[This post has no text content]"),
        score=post_data["score"],
        top_comments=[
            CommentInfo(
                author=comment["data"].get("author", "[deleted]"),
                text=comment["data"].get("body", ""),
                score=comment["data"].get("score", 0),
            )
            # We add a small check to filter out any empty or deleted comments.
            for comment in comments_listing 
            if comment.get("data", {}).get("body") and comment["data"].get("author") != "[deleted]"
        ],
    )
async def find_similar_posts_reddit(post_id: str, limit: int = 10) -> List[PostInfo]:
    """Find posts similar to the given post using its title as the query.

    The search combines subreddit-restricted results and site-wide results,
    ranks by semantic similarity and Reddit score, and returns up to `limit`.
    """
    # 1) Resolve the post to get its title and subreddit quickly
    info = _reddit_get("/api/info", params={"id": f"t3_{post_id}"})
    children = info.get("data", {}).get("children", [])
    if not children:
        raise ValueError(f"Post with ID '{post_id}' not found")
    post_data = children[0].get("data", {})
    title = post_data.get("title", "")
    subreddit = post_data.get("subreddit", "")

    if not title:
        raise ValueError("Unable to resolve title for the given post")

    broad_q = _build_broad_query(title)

    scored: list[tuple[float, PostInfo]] = []

    # 2) Search in the same subreddit first (if available)
    try:
        if subreddit:
            params_sr = {
                "q": broad_q,
                "limit": min(max(limit, 5), 50),
                "type": "link",
                "sort": "relevance",
                "restrict_sr": 1,
                "subreddit": subreddit,
            }
            data_sr = _reddit_get("/search", params=params_sr)
            for child in data_sr.get("data", {}).get("children", []):
                pd = child.get("data", {})
                if pd.get("id") == post_id:
                    continue  # skip the same post
                pi: PostInfo = PostInfo(
                    id=pd.get("id", ""),
                    subreddit=pd.get("subreddit", subreddit),
                    title=pd.get("title", ""),
                    score=int(pd.get("score", 0)),
                    url=pd.get("url", ""),
                    comment_count=int(pd.get("num_comments", 0)),
                )
                sem = _compute_semantic_score(title, pi["title"], pd.get("selftext", ""))
                if sem > 0:
                    scored.append((sem, pi))
    except Exception as exc:
        logger.warning(f"Subreddit-scope similar search failed: {exc}")

    # 3) Site-wide search for broader recall
    try:
        params_all = {
            "q": broad_q,
            "limit": min(50, max(limit, 10)),
            "type": "link",
            "sort": "relevance",
        }
        data_all = _reddit_get("/search", params=params_all)
        for child in data_all.get("data", {}).get("children", []):
            pd = child.get("data", {})
            if pd.get("id") == post_id:
                continue
            pi: PostInfo = PostInfo(
                id=pd.get("id", ""),
                subreddit=pd.get("subreddit", subreddit or pd.get("subreddit", "")),
                title=pd.get("title", ""),
                score=int(pd.get("score", 0)),
                url=pd.get("url", ""),
                comment_count=int(pd.get("num_comments", 0)),
            )
            sem = _compute_semantic_score(title, pi["title"], pd.get("selftext", ""))
            if sem > 0:
                scored.append((sem, pi))
    except Exception as exc:
        logger.warning(f"Site-wide similar search failed: {exc}")

    # 4) Rank by semantic score then Reddit score; dedupe by id
    seen: set[str] = set()
    results: list[PostInfo] = []
    for s, pi in sorted(scored, key=lambda x: (x[0], x[1]["score"]), reverse=True):
        if not pi["id"] or pi["id"] in seen:
            continue
        seen.add(pi["id"])
        results.append(pi)
        if len(results) >= limit:
            break

    return results