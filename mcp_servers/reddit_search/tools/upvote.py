import logging
from typing import Dict, Any

from .base import reddit_post_as_user

logger = logging.getLogger(__name__)

async def upvote(post_id: str) -> Dict[str, Any]:
    """
    Upvotes a post.

    Args:
        post_id: The ID of the post to upvote (without the 't3_' prefix).
    """
    post_id = post_id.strip()
    if not post_id:
        return {"success": False, "error": "post_id is required"}

    try:
        logger.info(f"Upvoting post {post_id}")

        payload = {
            "id": f"t3_{post_id}",
            "dir": 1, # 1 for upvote
            "api_type": "json",
        }

        # The vote API returns an empty JSON {} on success
        await reddit_post_as_user("/api/vote", data=payload)
        
        logger.info(f"Successfully upvoted post {post_id}")
        return {"success": True, "post_id": post_id}

    except Exception as e:
        # The API might return errors in a non-200 response, which httpx will raise
        error_msg = f"Failed to upvote post {post_id}: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "error": error_msg}
