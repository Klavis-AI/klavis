import logging
from typing import Any, Dict, List, Optional
from .base import make_figma_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_file_comments(file_key: str, as_md: Optional[bool] = None) -> Dict[str, Any]:
    """Get comments from a file."""
    logger.info(f"Executing tool: get_file_comments with file_key: {file_key}")
    try:
        endpoint = f"/v1/files/{file_key}/comments"
        params = {}
        
        if as_md is not None:
            params["as_md"] = as_md
        
        comments_data = await make_figma_request("GET", endpoint, params=params)
        
        result = {
            "comments": []
        }
        
        for comment in comments_data.get("comments", []):
            comment_info = {
                "id": comment.get("id"),
                "file_key": comment.get("file_key"),
                "parent_id": comment.get("parent_id"),
                "user": comment.get("user", {}),
                "created_at": comment.get("created_at"),
                "resolved_at": comment.get("resolved_at"),
                "message": comment.get("message"),
                "client_meta": comment.get("client_meta", {}),
                "order_id": comment.get("order_id")
            }
            result["comments"].append(comment_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_file_comments: {e}")
        return {
            "error": "Failed to retrieve file comments",
            "file_key": file_key,
            "exception": str(e)
        }

async def post_file_comment(file_key: str, message: str, client_meta: Dict[str, Any], 
                           comment_id: Optional[str] = None) -> Dict[str, Any]:
    """Post a comment to a file."""
    logger.info(f"Executing tool: post_file_comment with file_key: {file_key}")
    try:
        endpoint = f"/v1/files/{file_key}/comments"
        
        payload = {
            "message": message,
            "client_meta": client_meta
        }
        
        if comment_id:
            payload["comment_id"] = comment_id
        
        comment_data = await make_figma_request("POST", endpoint, json_data=payload)
        
        result = {
            "id": comment_data.get("id"),
            "file_key": comment_data.get("file_key"),
            "parent_id": comment_data.get("parent_id"),
            "user": comment_data.get("user", {}),
            "created_at": comment_data.get("created_at"),
            "resolved_at": comment_data.get("resolved_at"),
            "message": comment_data.get("message"),
            "client_meta": comment_data.get("client_meta", {}),
            "order_id": comment_data.get("order_id")
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool post_file_comment: {e}")
        return {
            "error": "Failed to post comment",
            "file_key": file_key,
            "message": message,
            "exception": str(e)
        }

async def delete_comment(comment_id: str) -> Dict[str, Any]:
    """Delete a comment."""
    logger.info(f"Executing tool: delete_comment with comment_id: {comment_id}")
    try:
        endpoint = f"/v1/comments/{comment_id}"
        
        await make_figma_request("DELETE", endpoint, expect_empty_response=True)
        
        result = {
            "status": "success",
            "message": f"Comment {comment_id} has been deleted",
            "comment_id": comment_id
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool delete_comment: {e}")
        return {
            "error": "Failed to delete comment",
            "comment_id": comment_id,
            "exception": str(e)
        }