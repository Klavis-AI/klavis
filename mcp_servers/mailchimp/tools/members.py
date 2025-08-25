import logging
import hashlib
from typing import Any, Dict, List, Optional
from .base import make_mailchimp_request

# Configure logging
logger = logging.getLogger(__name__)

def _get_subscriber_hash(email: str) -> str:
    """Generate MD5 hash of lowercase email for Mailchimp subscriber_hash."""
    return hashlib.md5(email.lower().encode()).hexdigest()

async def get_audience_members(
    list_id: str, 
    count: int = 10, 
    offset: int = 0,
    status: Optional[str] = None,
    since_timestamp_opt: Optional[str] = None
) -> Dict[str, Any]:
    """Get members from a specific audience (list)."""
    logger.info(f"Executing tool: get_audience_members with list_id: {list_id}, count: {count}, offset: {offset}")
    try:
        endpoint = f"/lists/{list_id}/members"
        params = {
            "count": count,
            "offset": offset
        }
        
        if status:
            params["status"] = status
        if since_timestamp_opt:
            params["since_timestamp_opt"] = since_timestamp_opt
        
        members_data = await make_mailchimp_request("GET", endpoint, params=params)
        
        result = {
            "list_id": list_id,
            "total_items": members_data.get("total_items"),
            "members": []
        }
        
        for member in members_data.get("members", []):
            member_info = {
                "id": member.get("id"),
                "email_address": member.get("email_address"),
                "unique_email_id": member.get("unique_email_id"),
                "contact_id": member.get("contact_id"),
                "full_name": member.get("full_name"),
                "web_id": member.get("web_id"),
                "email_type": member.get("email_type"),
                "status": member.get("status"),
                "unsubscribe_reason": member.get("unsubscribe_reason"),
                "consents_to_one_to_one_messaging": member.get("consents_to_one_to_one_messaging"),
                "merge_fields": member.get("merge_fields", {}),
                "interests": member.get("interests", {}),
                "stats": member.get("stats", {}),
                "ip_signup": member.get("ip_signup"),
                "timestamp_signup": member.get("timestamp_signup"),
                "ip_opt": member.get("ip_opt"),
                "timestamp_opt": member.get("timestamp_opt"),
                "member_rating": member.get("member_rating"),
                "last_changed": member.get("last_changed"),
                "language": member.get("language"),
                "vip": member.get("vip"),
                "email_client": member.get("email_client"),
                "location": member.get("location", {}),
                "marketing_permissions": member.get("marketing_permissions", []),
                "last_note": member.get("last_note", {}),
                "source": member.get("source"),
                "tags_count": member.get("tags_count"),
                "tags": member.get("tags", [])
            }
            result["members"].append(member_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_audience_members: {e}")
        return {
            "error": "Failed to retrieve audience members",
            "list_id": list_id,
            "exception": str(e)
        }

async def add_member_to_audience(
    list_id: str,
    email_address: str,
    status: str = "subscribed",
    merge_fields: Optional[Dict[str, str]] = None,
    interests: Optional[Dict[str, bool]] = None,
    language: Optional[str] = None,
    vip: Optional[bool] = None,
    tags: Optional[List[str]] = None,
    ip_signup: Optional[str] = None,
    timestamp_signup: Optional[str] = None,
    ip_opt: Optional[str] = None,
    timestamp_opt: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new member to an audience or update existing member."""
    logger.info(f"Executing tool: add_member_to_audience with list_id: {list_id}, email: {email_address}")
    try:
        endpoint = f"/lists/{list_id}/members"
        
        payload = {
            "email_address": email_address,
            "status": status
        }
        
        if merge_fields:
            payload["merge_fields"] = merge_fields
        if interests:
            payload["interests"] = interests
        if language:
            payload["language"] = language
        if vip is not None:
            payload["vip"] = vip
        if tags:
            payload["tags"] = tags
        if ip_signup:
            payload["ip_signup"] = ip_signup
        if timestamp_signup:
            payload["timestamp_signup"] = timestamp_signup
        if ip_opt:
            payload["ip_opt"] = ip_opt
        if timestamp_opt:
            payload["timestamp_opt"] = timestamp_opt
        
        member_data = await make_mailchimp_request("POST", endpoint, json_data=payload)
        
        result = {
            "id": member_data.get("id"),
            "email_address": member_data.get("email_address"),
            "unique_email_id": member_data.get("unique_email_id"),
            "contact_id": member_data.get("contact_id"),
            "full_name": member_data.get("full_name"),
            "web_id": member_data.get("web_id"),
            "email_type": member_data.get("email_type"),
            "status": member_data.get("status"),
            "merge_fields": member_data.get("merge_fields", {}),
            "interests": member_data.get("interests", {}),
            "stats": member_data.get("stats", {}),
            "ip_signup": member_data.get("ip_signup"),
            "timestamp_signup": member_data.get("timestamp_signup"),
            "ip_opt": member_data.get("ip_opt"),
            "timestamp_opt": member_data.get("timestamp_opt"),
            "member_rating": member_data.get("member_rating"),
            "last_changed": member_data.get("last_changed"),
            "language": member_data.get("language"),
            "vip": member_data.get("vip"),
            "email_client": member_data.get("email_client"),
            "location": member_data.get("location", {}),
            "source": member_data.get("source"),
            "tags_count": member_data.get("tags_count"),
            "tags": member_data.get("tags", []),
            "list_id": list_id
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool add_member_to_audience: {e}")
        return {
            "error": "Failed to add member to audience",
            "list_id": list_id,
            "email_address": email_address,
            "note": "Try using update_member if member already exists",
            "exception": str(e)
        }

async def get_member_info(list_id: str, email_address: str) -> Dict[str, Any]:
    """Get information about a specific audience member."""
    logger.info(f"Executing tool: get_member_info with list_id: {list_id}, email: {email_address}")
    try:
        subscriber_hash = _get_subscriber_hash(email_address)
        endpoint = f"/lists/{list_id}/members/{subscriber_hash}"
        
        member_data = await make_mailchimp_request("GET", endpoint)
        
        result = {
            "id": member_data.get("id"),
            "email_address": member_data.get("email_address"),
            "unique_email_id": member_data.get("unique_email_id"),
            "contact_id": member_data.get("contact_id"),
            "full_name": member_data.get("full_name"),
            "web_id": member_data.get("web_id"),
            "email_type": member_data.get("email_type"),
            "status": member_data.get("status"),
            "unsubscribe_reason": member_data.get("unsubscribe_reason"),
            "consents_to_one_to_one_messaging": member_data.get("consents_to_one_to_one_messaging"),
            "merge_fields": member_data.get("merge_fields", {}),
            "interests": member_data.get("interests", {}),
            "stats": member_data.get("stats", {}),
            "ip_signup": member_data.get("ip_signup"),
            "timestamp_signup": member_data.get("timestamp_signup"),
            "ip_opt": member_data.get("ip_opt"),
            "timestamp_opt": member_data.get("timestamp_opt"),
            "member_rating": member_data.get("member_rating"),
            "last_changed": member_data.get("last_changed"),
            "language": member_data.get("language"),
            "vip": member_data.get("vip"),
            "email_client": member_data.get("email_client"),
            "location": member_data.get("location", {}),
            "marketing_permissions": member_data.get("marketing_permissions", []),
            "last_note": member_data.get("last_note", {}),
            "source": member_data.get("source"),
            "tags_count": member_data.get("tags_count"),
            "tags": member_data.get("tags", []),
            "list_id": list_id,
            "subscriber_hash": subscriber_hash
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_member_info: {e}")
        return {
            "error": "Failed to retrieve member information",
            "list_id": list_id,
            "email_address": email_address,
            "exception": str(e)
        }

async def update_member(
    list_id: str,
    email_address: str,
    status: Optional[str] = None,
    merge_fields: Optional[Dict[str, str]] = None,
    interests: Optional[Dict[str, bool]] = None,
    language: Optional[str] = None,
    vip: Optional[bool] = None,
    ip_opt: Optional[str] = None,
    timestamp_opt: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing audience member or add if not exists."""
    logger.info(f"Executing tool: update_member with list_id: {list_id}, email: {email_address}")
    try:
        subscriber_hash = _get_subscriber_hash(email_address)
        endpoint = f"/lists/{list_id}/members/{subscriber_hash}"
        
        payload = {
            "email_address": email_address
        }
        
        if status:
            payload["status"] = status
        if merge_fields:
            payload["merge_fields"] = merge_fields
        if interests:
            payload["interests"] = interests
        if language:
            payload["language"] = language
        if vip is not None:
            payload["vip"] = vip
        if ip_opt:
            payload["ip_opt"] = ip_opt
        if timestamp_opt:
            payload["timestamp_opt"] = timestamp_opt
        
        member_data = await make_mailchimp_request("PATCH", endpoint, json_data=payload)
        
        result = {
            "id": member_data.get("id"),
            "email_address": member_data.get("email_address"),
            "status": member_data.get("status"),
            "merge_fields": member_data.get("merge_fields", {}),
            "interests": member_data.get("interests", {}),
            "stats": member_data.get("stats", {}),
            "member_rating": member_data.get("member_rating"),
            "last_changed": member_data.get("last_changed"),
            "language": member_data.get("language"),
            "vip": member_data.get("vip"),
            "location": member_data.get("location", {}),
            "tags_count": member_data.get("tags_count"),
            "tags": member_data.get("tags", []),
            "list_id": list_id,
            "updated_fields": [k for k in payload.keys() if k != "email_address"]
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool update_member: {e}")
        return {
            "error": "Failed to update member",
            "list_id": list_id,
            "email_address": email_address,
            "exception": str(e)
        }

async def delete_member(list_id: str, email_address: str) -> Dict[str, Any]:
    """Delete/permanently remove a member from an audience."""
    logger.info(f"Executing tool: delete_member with list_id: {list_id}, email: {email_address}")
    try:
        subscriber_hash = _get_subscriber_hash(email_address)
        endpoint = f"/lists/{list_id}/members/{subscriber_hash}"
        
        await make_mailchimp_request("DELETE", endpoint, expect_empty_response=True)
        
        result = {
            "status": "success",
            "message": f"Member {email_address} has been permanently deleted from audience {list_id}",
            "list_id": list_id,
            "email_address": email_address,
            "subscriber_hash": subscriber_hash,
            "warning": "This action is permanent. Consider using update_member with status 'unsubscribed' instead."
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool delete_member: {e}")
        return {
            "error": "Failed to delete member",
            "list_id": list_id,
            "email_address": email_address,
            "exception": str(e)
        }

async def add_member_tags(list_id: str, email_address: str, tags: List[str]) -> Dict[str, Any]:
    """Add tags to a specific audience member."""
    logger.info(f"Executing tool: add_member_tags with list_id: {list_id}, email: {email_address}, tags: {tags}")
    try:
        subscriber_hash = _get_subscriber_hash(email_address)
        endpoint = f"/lists/{list_id}/members/{subscriber_hash}/tags"
        
        payload = {
            "tags": [{"name": tag, "status": "active"} for tag in tags]
        }
        
        await make_mailchimp_request("POST", endpoint, json_data=payload, expect_empty_response=True)
        
        result = {
            "status": "success",
            "message": f"Tags added to member {email_address}",
            "list_id": list_id,
            "email_address": email_address,
            "tags_added": tags,
            "tags_count": len(tags)
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool add_member_tags: {e}")
        return {
            "error": "Failed to add tags to member",
            "list_id": list_id,
            "email_address": email_address,
            "tags": tags,
            "exception": str(e)
        }

async def remove_member_tags(list_id: str, email_address: str, tags: List[str]) -> Dict[str, Any]:
    """Remove tags from a specific audience member."""
    logger.info(f"Executing tool: remove_member_tags with list_id: {list_id}, email: {email_address}, tags: {tags}")
    try:
        subscriber_hash = _get_subscriber_hash(email_address)
        endpoint = f"/lists/{list_id}/members/{subscriber_hash}/tags"
        
        payload = {
            "tags": [{"name": tag, "status": "inactive"} for tag in tags]
        }
        
        await make_mailchimp_request("POST", endpoint, json_data=payload, expect_empty_response=True)
        
        result = {
            "status": "success",
            "message": f"Tags removed from member {email_address}",
            "list_id": list_id,
            "email_address": email_address,
            "tags_removed": tags,
            "tags_count": len(tags)
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool remove_member_tags: {e}")
        return {
            "error": "Failed to remove tags from member",
            "list_id": list_id,
            "email_address": email_address,
            "tags": tags,
            "exception": str(e)
        }

async def get_member_activity(list_id: str, email_address: str, count: int = 10) -> Dict[str, Any]:
    """Get the last 50 events of a member's activity on a specific list."""
    logger.info(f"Executing tool: get_member_activity with list_id: {list_id}, email: {email_address}")
    try:
        subscriber_hash = _get_subscriber_hash(email_address)
        endpoint = f"/lists/{list_id}/members/{subscriber_hash}/activity"
        
        params = {"count": count}
        
        activity_data = await make_mailchimp_request("GET", endpoint, params=params)
        
        result = {
            "email_id": activity_data.get("email_id"),
            "list_id": activity_data.get("list_id"),
            "list_is_active": activity_data.get("list_is_active"),
            "contact_status": activity_data.get("contact_status"),
            "email_address": email_address,
            "total_items": activity_data.get("total_items"),
            "activity": []
        }
        
        for activity in activity_data.get("activity", []):
            activity_info = {
                "action": activity.get("action"),
                "timestamp": activity.get("timestamp"),
                "url": activity.get("url"),
                "type": activity.get("type"),
                "campaign_id": activity.get("campaign_id"),
                "title": activity.get("title"),
                "parent_campaign": activity.get("parent_campaign")
            }
            result["activity"].append(activity_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_member_activity: {e}")
        return {
            "error": "Failed to retrieve member activity",
            "list_id": list_id,
            "email_address": email_address,
            "exception": str(e)
        }