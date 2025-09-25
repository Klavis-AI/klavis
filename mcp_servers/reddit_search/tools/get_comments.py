import logging
from typing import List, TypedDict

from .base import reddit_get

logger = logging.getLogger(__name__)

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

async def get_post_and_top_comments(post_id: str, subreddit: str) -> PostDetails:
    """Gets post and comment details via the Reddit API and cleans the data."""
    params = {"limit": 3, "sort": "top", "raw_json": 1}

    logger.info(f"Making API call to Reddit for comments on post '{post_id}' in subreddit '{subreddit}'")
    # Use the comments endpoint directly - this is the correct Reddit API pattern
    data = await reddit_get(f"/comments/{post_id}", params=params)
    
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