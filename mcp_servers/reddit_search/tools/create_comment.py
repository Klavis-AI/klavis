import logging
from typing import Dict, Any

from .base import reddit_post_as_user

logger = logging.getLogger(__name__)

async def create_comment(post_id: str, text: str) -> Dict[str, Any]:
    """
    Creates a new comment on a given Reddit post.

    Args:
        post_id: The ID of the post to comment on (without the 't3_' prefix).
        text: The Markdown content of the comment.
    """
    post_id = post_id.strip()
    text = text.strip()

    if not post_id or not text:
        error_msg = "post_id and text are required"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

    try:
        logger.info(f"Creating comment on post {post_id}")

        payload = {
            "api_type": "json",
            "thing_id": f"t3_{post_id}",
            "text": text,
        }

        response = await reddit_post_as_user("/api/comment", data=payload)

        if response.get("json", {}).get("errors"):
            errors = response["json"]["errors"]
            error_msg = ", ".join([f"{err[0]}: {err[1]}" for err in errors])
            logger.error(f"Failed to create comment on post {post_id}: {error_msg}")
            return {"success": False, "error": error_msg}

        # A successful comment creation returns a data structure with the new comment
        data = response.get("json", {}).get("data", {})
        if data and data.get("things"):
            comment_id = data["things"][0]["data"]["id"]
            logger.info(f"Successfully created comment {comment_id} on post {post_id}")
            return {"success": True, "comment_id": comment_id}
        
        logger.error(f"Comment creation on {post_id} seemed to succeed but API response was unexpected.")
        return {"success": False, "error": "API did not return expected comment data."}

    except Exception as e:
        error_msg = f"Failed to create comment on post {post_id}: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "error": error_msg}
