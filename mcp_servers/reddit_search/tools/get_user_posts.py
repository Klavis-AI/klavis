import logging
from typing import List

from .base import reddit_get_as_user
from .search_posts import PostInfo

logger = logging.getLogger(__name__)

async def get_user_posts(limit: int = 25) -> List[PostInfo]:
    """
    Fetches the most recent posts submitted by the authenticated user.
    
    Args:
        limit: The maximum number of posts to return (default: 25, max: 100).
    """
    limit = max(1, min(100, limit))
    params = {"limit": limit}
    
    logger.info(f"Making API call to Reddit to get user submitted posts with limit: {limit}")
    data = await reddit_get_as_user("/api/v1/me/submitted", params=params)
    
    posts = data.get("data", {}).get("children", [])
    
    return [
        PostInfo(
            id=post["data"].get("id", ""),
            subreddit=post["data"].get("subreddit", ""),
            title=post["data"].get("title", ""),
            score=int(post["data"].get("score", 0)),
            url=post["data"].get("url", ""),
            comment_count=int(post["data"].get("num_comments", 0)),
        )
        for post in posts
    ]
