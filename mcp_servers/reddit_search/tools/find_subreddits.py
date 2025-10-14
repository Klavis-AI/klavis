import logging
from typing import List, TypedDict

from .base import reddit_get

logger = logging.getLogger(__name__)

class SubredditInfo(TypedDict):
    """Structured data for a single subreddit."""
    name: str
    subscriber_count: int
    description: str

async def find_relevant_subreddits(query: str) -> List[SubredditInfo]:
    """Find subreddits that are relevant to the query and clean up the data."""
    params = {"q": query, "limit": 10, "type": "sr"}

    logger.info(f"Making API call to Reddit to find subreddits for query: '{query}'")
    data = await reddit_get("/subreddits/search", params=params)
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