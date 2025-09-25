import logging
from typing import Dict
from .base import reddit_post

logger = logging.getLogger(__name__)

async def create_post(subreddit: str, title: str, text: str) -> Dict[str, str]:
    """Write a post to a subreddit.
    
    Args:
        subreddit: The subreddit to write the post to.
        title: The title of the post.
        text: The text of the post.

    Returns:
        A dictionary containing information about the newly created post, such as its ID and URL.
    """
    # The data payload is passed directly to the 'data' argument
    data = {
        "sr": subreddit,
        "title": title,
        "text": text
    }
    try:
    # Make the POST request to the Reddit API
        logger.info(f"Writing post to {subreddit} with title {title} and content {text}")
        response = await reddit_post("/api/submit", data)
    except Exception as e:
        logger.error(f"Error writing post to {subreddit} with title {title} and content {text}: {e}")
        raise e
    
    # process the response
    if response and response.get("json", {}).get("errors"):
        logger.error(f"Reddit API returned errors for r/{subreddit}: {response['json']['errors']}")
        return {"error": "Reddit API returned errors", "details": response['json']['errors']}

    post_data = response.get("json", {}).get("data", {}).get("url", "")

    return post_data

