import logging
from typing import List

from .base import reddit_get, build_broad_query, compute_semantic_score
from .search_posts import PostInfo

logger = logging.getLogger(__name__)


async def find_similar_posts_reddit(post_id: str, limit: int = 10) -> List[PostInfo]:
    """Find posts similar to the given post using its title as the query.

    The search combines subreddit-restricted results and site-wide results,
    ranks by semantic similarity and Reddit score, and returns up to `limit`.
    """
    # 1) Resolve the post to get its title and subreddit quickly
    info = await reddit_get("/api/info", params={"id": f"t3_{post_id}"})
    children = info.get("data", {}).get("children", [])
    if not children:
        raise ValueError(f"Post with ID '{post_id}' not found")
    post_data = children[0].get("data", {})
    title = post_data.get("title", "")
    subreddit = post_data.get("subreddit", "")

    if not title:
        raise ValueError("Unable to resolve title for the given post")

    broad_q = build_broad_query(title)

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
            data_sr = await reddit_get("/search", params=params_sr)
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
                sem = compute_semantic_score(title, pi["title"], pd.get("selftext", ""))
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
        data_all = await reddit_get("/search", params=params_all)
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
            sem = compute_semantic_score(title, pi["title"], pd.get("selftext", ""))
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