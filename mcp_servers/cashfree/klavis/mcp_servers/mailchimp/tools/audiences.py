import logging
from typing import Any, Dict, List, Optional
from .base import make_mailchimp_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_all_audiences(count: int = 10, offset: int = 0) -> Dict[str, Any]:
    """Get information about all audiences (lists) in the account."""
    logger.info(f"Executing tool: get_all_audiences with count: {count}, offset: {offset}")
    try:
        endpoint = "/lists"
        params = {
            "count": count,
            "offset": offset
        }
        
        audiences_data = await make_mailchimp_request("GET", endpoint, params=params)
        
        result = {
            "total_items": audiences_data.get("total_items"),
            "audiences": []
        }
        
        for audience in audiences_data.get("lists", []):
            audience_info = {
                "id": audience.get("id"),
                "name": audience.get("name"),
                "date_created": audience.get("date_created"),
                "list_rating": audience.get("list_rating"),
                "stats": {
                    "member_count": audience.get("stats", {}).get("member_count"),
                    "unsubscribe_count": audience.get("stats", {}).get("unsubscribe_count"),
                    "cleaned_count": audience.get("stats", {}).get("cleaned_count"),
                    "member_count_since_send": audience.get("stats", {}).get("member_count_since_send"),
                    "unsubscribe_count_since_send": audience.get("stats", {}).get("unsubscribe_count_since_send"),
                    "cleaned_count_since_send": audience.get("stats", {}).get("cleaned_count_since_send"),
                    "campaign_count": audience.get("stats", {}).get("campaign_count"),
                    "campaign_last_sent": audience.get("stats", {}).get("campaign_last_sent"),
                    "merge_field_count": audience.get("stats", {}).get("merge_field_count"),
                    "avg_sub_rate": audience.get("stats", {}).get("avg_sub_rate"),
                    "avg_unsub_rate": audience.get("stats", {}).get("avg_unsub_rate"),
                    "target_sub_rate": audience.get("stats", {}).get("target_sub_rate"),
                    "open_rate": audience.get("stats", {}).get("open_rate"),
                    "click_rate": audience.get("stats", {}).get("click_rate"),
                    "last_sub_date": audience.get("stats", {}).get("last_sub_date"),
                    "last_unsub_date": audience.get("stats", {}).get("last_unsub_date")
                },
                "subscribe_url_short": audience.get("subscribe_url_short"),
                "subscribe_url_long": audience.get("subscribe_url_long"),
                "beamer_address": audience.get("beamer_address"),
                "visibility": audience.get("visibility"),
                "double_optin": audience.get("double_optin"),
                "has_welcome": audience.get("has_welcome"),
                "marketing_permissions": audience.get("marketing_permissions")
            }
            result["audiences"].append(audience_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_all_audiences: {e}")
        return {
            "error": "Failed to retrieve audiences",
            "exception": str(e)
        }

async def create_audience(
    name: str,
    contact: Dict[str, str],
    permission_reminder: str,
    from_name: str,
    from_email: str,
    subject: str,
    language: str = "EN_US",
    email_type_option: bool = False,
    double_optin: bool = False,
    has_welcome: bool = False
) -> Dict[str, Any]:
    """Create a new audience (list) in Mailchimp."""
    logger.info(f"Executing tool: create_audience with name: {name}")
    try:
        endpoint = "/lists"
        
        payload = {
            "name": name,
            "contact": contact,
            "permission_reminder": permission_reminder,
            "campaign_defaults": {
                "from_name": from_name,
                "from_email": from_email,
                "subject": subject,
                "language": language
            },
            "email_type_option": email_type_option,
            "double_optin": double_optin,
            "has_welcome": has_welcome
        }
        
        audience_data = await make_mailchimp_request("POST", endpoint, json_data=payload)
        
        result = {
            "id": audience_data.get("id"),
            "name": audience_data.get("name"),
            "date_created": audience_data.get("date_created"),
            "list_rating": audience_data.get("list_rating"),
            "subscribe_url_short": audience_data.get("subscribe_url_short"),
            "subscribe_url_long": audience_data.get("subscribe_url_long"),
            "beamer_address": audience_data.get("beamer_address"),
            "visibility": audience_data.get("visibility"),
            "double_optin": audience_data.get("double_optin"),
            "has_welcome": audience_data.get("has_welcome"),
            "permission_reminder": audience_data.get("permission_reminder"),
            "from_name": from_name,
            "from_email": from_email,
            "contact": contact
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool create_audience: {e}")
        return {
            "error": "Failed to create audience",
            "name": name,
            "exception": str(e)
        }

async def get_audience_info(list_id: str) -> Dict[str, Any]:
    """Get information about a specific audience (list)."""
    logger.info(f"Executing tool: get_audience_info with list_id: {list_id}")
    try:
        endpoint = f"/lists/{list_id}"
        
        audience_data = await make_mailchimp_request("GET", endpoint)
        
        result = {
            "id": audience_data.get("id"),
            "name": audience_data.get("name"),
            "date_created": audience_data.get("date_created"),
            "list_rating": audience_data.get("list_rating"),
            "stats": audience_data.get("stats", {}),
            "subscribe_url_short": audience_data.get("subscribe_url_short"),
            "subscribe_url_long": audience_data.get("subscribe_url_long"),
            "beamer_address": audience_data.get("beamer_address"),
            "visibility": audience_data.get("visibility"),
            "double_optin": audience_data.get("double_optin"),
            "has_welcome": audience_data.get("has_welcome"),
            "permission_reminder": audience_data.get("permission_reminder"),
            "use_archive_bar": audience_data.get("use_archive_bar"),
            "notify_on_subscribe": audience_data.get("notify_on_subscribe"),
            "notify_on_unsubscribe": audience_data.get("notify_on_unsubscribe"),
            "marketing_permissions": audience_data.get("marketing_permissions"),
            "contact": audience_data.get("contact", {}),
            "campaign_defaults": audience_data.get("campaign_defaults", {})
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_audience_info: {e}")
        return {
            "error": "Failed to retrieve audience information",
            "list_id": list_id,
            "exception": str(e)
        }

async def update_audience(
    list_id: str,
    name: Optional[str] = None,
    contact: Optional[Dict[str, str]] = None,
    permission_reminder: Optional[str] = None,
    from_name: Optional[str] = None,
    from_email: Optional[str] = None,
    subject: Optional[str] = None,
    language: Optional[str] = None,
    email_type_option: Optional[bool] = None,
    double_optin: Optional[bool] = None,
    has_welcome: Optional[bool] = None
) -> Dict[str, Any]:
    """Update settings for a specific audience (list)."""
    logger.info(f"Executing tool: update_audience with list_id: {list_id}")
    try:
        endpoint = f"/lists/{list_id}"
        
        # Build payload with only provided fields
        payload = {}
        
        if name is not None:
            payload["name"] = name
        if contact is not None:
            payload["contact"] = contact
        if permission_reminder is not None:
            payload["permission_reminder"] = permission_reminder
        if email_type_option is not None:
            payload["email_type_option"] = email_type_option
        if double_optin is not None:
            payload["double_optin"] = double_optin
        if has_welcome is not None:
            payload["has_welcome"] = has_welcome
            
        # Handle campaign_defaults separately
        campaign_defaults = {}
        if from_name is not None:
            campaign_defaults["from_name"] = from_name
        if from_email is not None:
            campaign_defaults["from_email"] = from_email
        if subject is not None:
            campaign_defaults["subject"] = subject
        if language is not None:
            campaign_defaults["language"] = language
            
        if campaign_defaults:
            payload["campaign_defaults"] = campaign_defaults
        
        if not payload:
            return {
                "error": "No update parameters provided",
                "list_id": list_id
            }
        
        audience_data = await make_mailchimp_request("PATCH", endpoint, json_data=payload)
        
        result = {
            "id": audience_data.get("id"),
            "name": audience_data.get("name"),
            "date_created": audience_data.get("date_created"),
            "updated_fields": list(payload.keys()),
            "stats": audience_data.get("stats", {}),
            "contact": audience_data.get("contact", {}),
            "campaign_defaults": audience_data.get("campaign_defaults", {}),
            "permission_reminder": audience_data.get("permission_reminder"),
            "double_optin": audience_data.get("double_optin"),
            "has_welcome": audience_data.get("has_welcome")
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool update_audience: {e}")
        return {
            "error": "Failed to update audience",
            "list_id": list_id,
            "exception": str(e)
        }

async def delete_audience(list_id: str) -> Dict[str, Any]:
    """Delete an audience (list) from Mailchimp account."""
    logger.info(f"Executing tool: delete_audience with list_id: {list_id}")
    try:
        endpoint = f"/lists/{list_id}"
        
        await make_mailchimp_request("DELETE", endpoint, expect_empty_response=True)
        
        result = {
            "status": "success",
            "message": f"Audience {list_id} has been deleted",
            "list_id": list_id,
            "warning": "This action is permanent. List history including subscriber activity, unsubscribes, complaints, and bounces have been lost."
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool delete_audience: {e}")
        return {
            "error": "Failed to delete audience",
            "list_id": list_id,
            "exception": str(e)
        }