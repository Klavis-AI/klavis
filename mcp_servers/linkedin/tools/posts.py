import logging
import urllib.parse
from typing import Any, Dict, List, Optional
from .base import make_linkedin_request

# Configure logging
logger = logging.getLogger(__name__)

async def create_text_post(text: str, visibility: str = "PUBLIC") -> Dict[str, Any]:
    """Create a text post on LinkedIn."""
    logger.info(f"Executing tool: create_text_post")
    try:
        # Check if we have w_member_social scope by trying to post
        profile = await make_linkedin_request("GET", "/userinfo")
        person_id = profile.get('sub')
        
        endpoint = "/ugcPosts"
        payload = {
            "author": f"urn:li:person:{person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        post_data = await make_linkedin_request("POST", endpoint, json_data=payload)
        return {
            "id": post_data.get("id"),
            "created": post_data.get("created"),
            "lastModified": post_data.get("lastModified"),
            "lifecycleState": post_data.get("lifecycleState")
        }
    except Exception as e:
        logger.exception(f"Error executing tool create_text_post: {e}")
        return {
            "error": "Post creation failed - likely due to insufficient permissions",
            "text": text,
            "note": "Requires 'w_member_social' scope in LinkedIn app settings",
            "exception": str(e)
        }

async def create_article_post(title: str, text: str, visibility: str = "PUBLIC") -> Dict[str, Any]:
    """Create an article post on LinkedIn."""
    logger.info(f"Executing tool: create_article_post")
    try:
        # Get current user info
        profile = await make_linkedin_request("GET", "/userinfo")
        person_id = profile.get('sub')
        
        # Use the same format as text posts but with longer content
        endpoint = "/ugcPosts"
        payload = {
            "author": f"urn:li:person:{person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": f"{title}\n\n{text}"
                    },
                    "shareMediaCategory": "NONE"  # Changed from "ARTICLE" to "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        post_data = await make_linkedin_request("POST", endpoint, json_data=payload)
        return {
            "id": post_data.get("id"),
            "created": post_data.get("created"),
            "lastModified": post_data.get("lastModified"),
            "lifecycleState": post_data.get("lifecycleState"),
            "title": title,
            "note": "Created as text post with article format (title + content)"
        }
    except Exception as e:
        logger.exception(f"Error executing tool create_article_post: {e}")
        return {
            "error": "Article creation failed - trying alternative approach",
            "title": title,
            "text": text,
            "note": "Will attempt to create as formatted text post",
            "exception": str(e)
        }

async def get_user_posts(person_id: Optional[str] = None, count: int = 10) -> List[Dict[str, Any]]:
    """Get recent posts from a user's profile."""
    logger.info(f"Executing tool: get_user_posts with person_id: {person_id}, count: {count}")
    try:
        if person_id:
            author_urn = f"urn:li:person:{person_id}"
        else:
            # Get current user's info
            profile = await make_linkedin_request("GET", "/userinfo")
            author_urn = f"urn:li:person:{profile.get('sub')}"
        
        count = max(1, min(count, 50))  # Clamp between 1 and 50
        
        # Try the ugcPosts endpoint first
        endpoint = f"/ugcPosts?q=authors&authors={urllib.parse.quote(author_urn)}&count={count}"
        
        try:
            posts_data = await make_linkedin_request("GET", endpoint)
            
            if not isinstance(posts_data.get("elements"), list):
                # If ugcPosts doesn't work, try shares endpoint
                endpoint = f"/shares?q=owners&owners={urllib.parse.quote(author_urn)}&count={count}"
                posts_data = await make_linkedin_request("GET", endpoint)
            
            if not isinstance(posts_data.get("elements"), list):
                return [{
                    "error": "No posts found or API format changed",
                    "note": "The LinkedIn API may have changed or no posts are available",
                    "requested_person_id": person_id,
                    "requested_count": count,
                    "attempted_endpoints": ["/ugcPosts", "/shares"]
                }]
            
            posts_list = []
            for post in posts_data.get("elements", []):
                # Handle both ugcPosts and shares format
                if "specificContent" in post:  # ugcPosts format
                    specific_content = post.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {})
                    commentary = specific_content.get("shareCommentary", {})
                    text = commentary.get("text", "")
                else:  # shares format
                    text_content = post.get("text", {})
                    text = text_content.get("text", "") if isinstance(text_content, dict) else ""
                
                posts_list.append({
                    "id": post.get("id"),
                    "text": text,
                    "created": post.get("created", {}).get("time") if isinstance(post.get("created"), dict) else post.get("created"),
                    "lastModified": post.get("lastModified", {}).get("time") if isinstance(post.get("lastModified"), dict) else post.get("lastModified"),
                    "lifecycleState": post.get("lifecycleState"),
                    "activity": post.get("activity")
                })
            
            return posts_list if posts_list else [{
                "info": "No posts found for this user",
                "note": "User may not have any posts or posts may not be publicly accessible"
            }]
            
        except Exception as api_error:
            return [{
                "error": "Getting user posts failed with current permissions",
                "note": "This feature may require elevated LinkedIn API access",
                "requested_person_id": person_id,
                "requested_count": count,
                "api_error": str(api_error)
            }]
            
    except Exception as e:
        logger.exception(f"Error executing tool get_user_posts: {e}")
        return [{
            "error": "Function execution failed",
            "exception": str(e),
            "requested_person_id": person_id,
            "requested_count": count
        }]