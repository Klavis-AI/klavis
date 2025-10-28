import logging
import urllib.parse
from typing import Any, Dict, List, Optional
from .base import make_linkedin_request

# Configure logging
logger = logging.getLogger(__name__)

def _format_hashtags(hashtags: List[str]) -> str:
    """Format hashtags for LinkedIn posts"""
    formatted = []
    for tag in hashtags:
        # Remove # if already present and add it back
        clean_tag = tag.strip().lstrip('#')
        if clean_tag:  # Only add non-empty tags
            formatted.append(f"#{clean_tag}")
    return " ".join(formatted)

def format_rich_post(
    text: str,
    bold_text: Optional[List[str]] = None,
    italic_text: Optional[List[str]] = None,
    bullet_points: Optional[List[str]] = None,
    numbered_list: Optional[List[str]] = None,
    hashtags: Optional[List[str]] = None,
    mentions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Format rich text for LinkedIn posts with various formatting options.
    This is a utility function that doesn't make API calls.
    """
    logger.info("Executing tool: format_rich_post")
    try:
        formatted_text = text
        
        # Apply bold formatting (LinkedIn uses **text** for bold)
        if bold_text:
            for bold in bold_text:
                if bold in formatted_text:
                    formatted_text = formatted_text.replace(bold, f"**{bold}**")
        
        # Apply italic formatting (LinkedIn uses *text* for italic)
        if italic_text:
            for italic in italic_text:
                if italic in formatted_text:
                    formatted_text = formatted_text.replace(italic, f"*{italic}*")
        
        # Add bullet points
        if bullet_points:
            bullet_section = "\n\n" + "\n".join([f"• {point}" for point in bullet_points])
            formatted_text += bullet_section
        
        # Add numbered list
        if numbered_list:
            numbered_section = "\n\n" + "\n".join([f"{i+1}. {item}" for i, item in enumerate(numbered_list)])
            formatted_text += numbered_section
        
        # Add mentions (LinkedIn uses @mention format)
        if mentions:
            mention_section = "\n\n" + " ".join([f"@{mention}" for mention in mentions])
            formatted_text += mention_section
        
        # Add hashtags
        if hashtags:
            hashtag_section = "\n\n" + _format_hashtags(hashtags)
            formatted_text += hashtag_section
        
        result = {
            "original_text": text,
            "formatted_text": formatted_text,
            "formatting_applied": {
                "bold_count": len(bold_text) if bold_text else 0,
                "italic_count": len(italic_text) if italic_text else 0,
                "bullet_points": len(bullet_points) if bullet_points else 0,
                "numbered_items": len(numbered_list) if numbered_list else 0,
                "hashtags": len(hashtags) if hashtags else 0,
                "mentions": len(mentions) if mentions else 0
            },
            "character_count": len(formatted_text),
            "note": "This is formatted text ready for posting. Use linkedin_create_post to publish."
        }
        
        return result
        
    except Exception as e:
        logger.exception(f"Error executing tool format_rich_post: {e}")
        return {
            "error": "Rich text formatting failed",
            "original_text": text,
            "exception": str(e)
        }

async def create_post(text: str, title: Optional[str] = None, visibility: str = "PUBLIC", hashtags: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a post on LinkedIn with optional title for article-style posts and hashtags."""
    tool_name = "create_article_post" if title else "create_text_post"
    if hashtags:
        tool_name += "_with_hashtags"
    logger.info(f"Executing tool: {tool_name}")
    try:
        profile = await make_linkedin_request("GET", "/userinfo")
        person_id = profile.get('sub')
        
        # Format hashtags if provided
        hashtag_text = ""
        if hashtags:
            formatted_hashtags = _format_hashtags(hashtags)
            if formatted_hashtags:
                hashtag_text = f"\n\n{formatted_hashtags}"
        
        # Format content with title and hashtags if provided
        content = text
        if title:
            content = f"{title}\n\n{text}"
        content += hashtag_text
        
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
        
        if hashtags:
            formatted_hashtags = _format_hashtags(hashtags)
            result["hashtags_used"] = formatted_hashtags
            result["hashtag_count"] = len([h for h in hashtags if h.strip()])
        
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

async def create_url_share(url: str, text: str, title: Optional[str] = None, description: Optional[str] = None, visibility: str = "PUBLIC") -> Dict[str, Any]:
    """Create a LinkedIn post that shares a URL with metadata preview"""
    logger.info(f"Executing tool: create_url_share with URL: {url}")
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
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {
                                "text": description or "Shared link"
                            },
                            "originalUrl": url,
                            "title": {
                                "text": title or "Shared Content"
                            }
                        }
                    ]
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
            "lifecycleState": post_data.get("lifecycleState"),
            "shared_url": url,
            "url_title": title or "Shared Content",
            "url_description": description or "Shared link"
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool create_url_share: {e}")
        error_result = {
            "error": "URL share creation failed - likely due to insufficient permissions or invalid URL",
            "text": text,
            "url": url,
            "note": "Requires 'w_member_social' scope and valid URL format",
            "exception": str(e)
        }
        
        if title:
            error_result["title"] = title
        if description:
            error_result["description"] = description
            
        return error_result
