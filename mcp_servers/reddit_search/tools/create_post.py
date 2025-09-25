import logging
import os
import praw
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

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


def _get_reddit_instance():
    """Get a configured PRAW Reddit instance."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "klavis-mcp/0.1 (+https://klavis.ai)")
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")
    
    if not all([client_id, client_secret, username, password]):
        raise ValueError(
            "Missing required Reddit credentials. Please set:\n"
            "- REDDIT_CLIENT_ID\n"
            "- REDDIT_CLIENT_SECRET\n"
            "- REDDIT_USERNAME\n"
            "- REDDIT_PASSWORD\n"
            "in your .env file"
        )
    
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        username=username,
        password=password
    )


async def create_post(subreddit: str, title: str, text: str) -> Dict[str, Any]:
    """Write a text post to a subreddit using PRAW.
    
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
    
    # Validate title length (Reddit limit: 300 characters)
    if len(title) > 300:
        error_msg = f"Title too long: {len(title)} characters (max 300)"
        logger.error(error_msg)
        return PostCreationResult(success=False, error=error_msg).to_dict()
    
    try:
        logger.info(f"Creating post in r/{subreddit} with title: '{title[:50]}...'")
        
        # Get Reddit instance
        reddit = _get_reddit_instance()
        
        # Get the subreddit
        subreddit_obj = reddit.subreddit(subreddit)
        
        # Submit the post
        submission = subreddit_obj.submit(title=title, selftext=text)
        
        # Extract post information
        post_id = submission.id
        post_url = f"https://reddit.com{submission.permalink}"
        
        logger.info(f"Successfully created post {post_id} in r/{subreddit}")
        return PostCreationResult(
            success=True, 
            post_id=post_id, 
            url=post_url
        ).to_dict()
            
    except Exception as e:
        error_msg = f"Failed to create post in r/{subreddit}: {str(e)}"
        logger.error(error_msg)
        return PostCreationResult(success=False, error=error_msg).to_dict()

