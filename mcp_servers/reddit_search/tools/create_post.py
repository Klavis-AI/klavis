import logging
from typing import Dict, Any

from .base import reddit_post_as_user

logger = logging.getLogger(__name__)

async def create_post(subreddit: str, title: str, text: str, **kwargs) -> Dict[str, Any]:
    """Write a text post to a subreddit using httpx.
    
    Args:
        subreddit: The subreddit to write the post to (without r/ prefix).
        title: The title of the post.
        text: The text content of the post.

    Returns:
        A dictionary containing success status, post ID, URL, and any error messages.
    """
    # Clean and validate inputs
    subreddit = subreddit.strip().strip("'\"")
    subreddit = subreddit.removeprefix("r/") if subreddit.lower().startswith("r/") else subreddit
    title = title.strip()
    text = text.strip()
    
    if not subreddit or not title:
        error_msg = "Subreddit and title are required"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    # Validate title length (Reddit limit: 300 characters)
    if len(title) > 300:
        error_msg = f"Title too long: {len(title)} characters (max 300)"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

    try:
        logger.info(f"Creating post in r/{subreddit} with title: '{title[:50]}...'")
        
        payload = {
            "api_type": "json",
            "kind": "self",
            "sr": subreddit,
            "title": title,
            "text": text,
        }
        
        response = await reddit_post_as_user("/api/submit", data=payload)
        
        # The Reddit API returns a complex object. We check for success.
        if response.get("json", {}).get("errors"):
            errors = response["json"]["errors"]
            error_msg = ", ".join([f"{err[0]}: {err[1]}" for err in errors])
            logger.error(f"Failed to create post in r/{subreddit}: {error_msg}")
            return {"success": False, "error": error_msg}

        # If successful, extract the post info
        data = response.get("json", {}).get("data", {})
        post_id = data.get("id")
        post_url = data.get("url")

        if not post_id or not post_url:
             logger.error(f"Post creation in r/{subreddit} seemed to succeed but no post ID/URL was returned.")
             return {"success": False, "error": "API did not return post ID or URL."}

        logger.info(f"Successfully created post {post_id} in r/{subreddit}")
        return {
            "success": True, 
            "post_id": post_id, 
            "url": post_url
        }
            
    except Exception as e:
        error_msg = f"Failed to create post in r/{subreddit}: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "error": error_msg}