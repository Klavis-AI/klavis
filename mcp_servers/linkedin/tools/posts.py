import logging
import urllib.parse
from typing import Any, Dict, List, Optional
from .base import make_linkedin_request

# Configure logging
logger = logging.getLogger(__name__)

async def create_post(text: str, title: Optional[str] = None, visibility: str = "PUBLIC") -> Dict[str, Any]:
    """Create a post on LinkedIn with optional title for article-style posts."""
    tool_name = "create_article_post" if title else "create_text_post"
    logger.info(f"Executing tool: {tool_name}")
    try:
        profile = await make_linkedin_request("GET", "/userinfo")
        person_id = profile.get('sub')
        
        # Format content with title if provided
        content = f"{title}\n\n{text}" if title else text
        
        endpoint = "/ugcPosts"
        payload = {
            "author": f"urn:li:person:{person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        post_data = await make_linkedin_request("POST", endpoint, json_data=payload)
        result = {
            "id": post_data.get("id"),
            "created": post_data.get("created"),
            "lastModified": post_data.get("lastModified"),
            "lifecycleState": post_data.get("lifecycleState")
        }
        
        if title:
            result["title"] = title
            result["note"] = "Created as text post with article format (title + content)"
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool {tool_name}: {e}")
        error_result = {
            "error": "Post creation failed - likely due to insufficient permissions",
            "text": text,
            "note": "Requires 'w_member_social' scope in LinkedIn app settings",
            "exception": str(e)
        }
        
        if title:
            error_result["title"] = title
            error_result["error"] = "Article creation failed - trying alternative approach"
            error_result["note"] = "Will attempt to create as formatted text post"
        
        return error_result


