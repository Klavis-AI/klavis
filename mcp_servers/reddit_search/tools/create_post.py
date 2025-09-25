import logging
from typing import Dict, Any
from .base import reddit_post

logger = logging.getLogger(__name__)


class PostCreationResult:
    """Structured result for post creation."""
    def __init__(self, success: bool, post_id: str = "", url: str = "", error: str = ""):
        self.success = success
        self.post_id = post_id
        self.url = url
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "post_id": self.post_id,
            "url": self.url,
            "error": self.error
        }


async def create_post(subreddit: str, title: str, text: str) -> Dict[str, Any]:
    """Write a text post to a subreddit.
    
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
        return PostCreationResult(success=False, error=error_msg).to_dict()
    
    # Prepare the data payload for Reddit API
    data = {
        "sr": subreddit,
        "title": title,
        "kind": "self",  # Required: specifies this is a text post
        "text": text,
        "api_type": "json"  # Required: tells Reddit to return JSON response
    }
    
    try:
        logger.info(f"Creating post in r/{subreddit} with title: '{title[:50]}...'")
        response = await reddit_post("/api/submit", data)
        
        # Check for Reddit API errors
        if response and response.get("json", {}).get("errors"):
            errors = response["json"]["errors"]
            error_msg = f"Reddit API errors: {errors}"
            logger.error(f"Reddit API returned errors for r/{subreddit}: {errors}")
            return PostCreationResult(success=False, error=error_msg).to_dict()
        
        # Extract post information from successful response
        json_data = response.get("json", {})
        if json_data.get("data"):
            post_data = json_data["data"]
            post_id = post_data.get("id", "")
            post_url = post_data.get("url", "")
            
            logger.info(f"Successfully created post {post_id} in r/{subreddit}")
            return PostCreationResult(
                success=True, 
                post_id=post_id, 
                url=post_url
            ).to_dict()
        else:
            error_msg = "Unexpected response format from Reddit API"
            logger.error(f"{error_msg}: {response}")
            return PostCreationResult(success=False, error=error_msg).to_dict()
            
    except Exception as e:
        error_msg = f"Failed to create post in r/{subreddit}: {str(e)}"
        logger.error(error_msg)
        return PostCreationResult(success=False, error=error_msg).to_dict()

