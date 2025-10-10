import logging
from typing import List, TypedDict

from .base import reddit_get, build_broad_query, compute_semantic_score

logger = logging.getLogger(__name__)

class PostInfo(TypedDict):
    """Structured data for a Reddit post summary."""
    id: str
    subreddit: str
    title: str
    score: int
    url: str
    comment_count: int

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
    broad_q = build_broad_query(query)

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
        data = await reddit_get("/search", params={**params, "sr_detail": False, "subreddit": subreddit})
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
            sem_score = compute_semantic_score(query, pi["title"], pd.get("selftext", ""))
            scored.append((sem_score, pi))
    except Exception as exc:
        logger.warning(f"Subreddit search failed, will try listing-based fallback. Error: {exc}")

    # 2) Fallback to listing endpoints and local filtering if needed
    if len(scored) < 10:
        try:
            hot = (await reddit_get(f"/r/{subreddit}/hot", params={"limit": 25})).get("data", {}).get("children", [])
            top = (await reddit_get(f"/r/{subreddit}/top", params={"limit": 25, "t": "month"})).get("data", {}).get("children", [])
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
                sem_score = compute_semantic_score(query, pi["title"], pd.get("selftext", ""))
                if sem_score > 0:
                    scored.append((sem_score, pi))
        except Exception as exc:
            logger.warning(f"Listing fallback failed: {exc}")

    # 3) Rank: semantic score first, then Reddit score
    # Deduplicate by id
    seen: set[str] = set()
    for s, pi in sorted(scored, key=lambda x: (x[0], x[1]["score"]),
                          reverse=True):
        if not pi["id"] or pi["id"] in seen:
            continue
        seen.add(pi["id"])
        matching_posts.append(pi)
        if len(matching_posts) >= 10:
            break

    return matching_posts