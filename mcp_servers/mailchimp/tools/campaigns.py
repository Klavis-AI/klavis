import logging
from typing import Any, Dict, List, Optional
from .base import make_mailchimp_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_all_campaigns(
    count: int = 10, 
    offset: int = 0,
    type: Optional[str] = None,
    status: Optional[str] = None,
    before_send_time: Optional[str] = None,
    since_send_time: Optional[str] = None,
    before_create_time: Optional[str] = None,
    since_create_time: Optional[str] = None,
    list_id: Optional[str] = None,
    folder_id: Optional[str] = None,
    sort_field: Optional[str] = None,
    sort_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Get all campaigns in the account with optional filtering."""
    logger.info(f"Executing tool: get_all_campaigns with count: {count}, offset: {offset}")
    try:
        endpoint = "/campaigns"
        params = {
            "count": count,
            "offset": offset
        }
        
        # Add optional filters
        if type:
            params["type"] = type
        if status:
            params["status"] = status
        if before_send_time:
            params["before_send_time"] = before_send_time
        if since_send_time:
            params["since_send_time"] = since_send_time
        if before_create_time:
            params["before_create_time"] = before_create_time
        if since_create_time:
            params["since_create_time"] = since_create_time
        if list_id:
            params["list_id"] = list_id
        if folder_id:
            params["folder_id"] = folder_id
        if sort_field:
            params["sort_field"] = sort_field
        if sort_dir:
            params["sort_dir"] = sort_dir
        
        campaigns_data = await make_mailchimp_request("GET", endpoint, params=params)
        
        result = {
            "total_items": campaigns_data.get("total_items"),
            "campaigns": []
        }
        
        for campaign in campaigns_data.get("campaigns", []):
            campaign_info = {
                "id": campaign.get("id"),
                "web_id": campaign.get("web_id"),
                "parent_campaign_id": campaign.get("parent_campaign_id"),
                "type": campaign.get("type"),
                "create_time": campaign.get("create_time"),
                "archive_url": campaign.get("archive_url"),
                "long_archive_url": campaign.get("long_archive_url"),
                "status": campaign.get("status"),
                "emails_sent": campaign.get("emails_sent"),
                "send_time": campaign.get("send_time"),
                "content_type": campaign.get("content_type"),
                "needs_block_refresh": campaign.get("needs_block_refresh"),
                "resendable": campaign.get("resendable"),
                "recipients": campaign.get("recipients", {}),
                "settings": campaign.get("settings", {}),
                "tracking": campaign.get("tracking", {}),
                "report_summary": campaign.get("report_summary", {}),
                "delivery_status": campaign.get("delivery_status", {})
            }
            result["campaigns"].append(campaign_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_all_campaigns: {e}")
        return {
            "error": "Failed to retrieve campaigns",
            "exception": str(e)
        }

async def create_campaign(
    type: str,
    list_id: str,
    subject_line: str,
    from_name: str,
    reply_to: str,
    title: Optional[str] = None,
    folder_id: Optional[str] = None,
    authenticate: bool = True,
    auto_footer: bool = True,
    inline_css: bool = True,
    auto_tweet: bool = False,
    fb_comments: bool = True,
    timewarp: bool = False,
    template_id: Optional[int] = None,
    drag_and_drop: bool = True
) -> Dict[str, Any]:
    """Create a new Mailchimp campaign."""
    logger.info(f"Executing tool: create_campaign with type: {type}, list_id: {list_id}, subject: {subject_line}")
    try:
        endpoint = "/campaigns"
        
        payload = {
            "type": type,
            "recipients": {
                "list_id": list_id
            },
            "settings": {
                "subject_line": subject_line,
                "from_name": from_name,
                "reply_to": reply_to,
                "authenticate": authenticate,
                "auto_footer": auto_footer,
                "inline_css": inline_css,
                "auto_tweet": auto_tweet,
                "fb_comments": fb_comments,
                "timewarp": timewarp,
                "drag_and_drop": drag_and_drop
            }
        }
        
        if title:
            payload["settings"]["title"] = title
        if folder_id:
            payload["settings"]["folder_id"] = folder_id
        if template_id:
            payload["settings"]["template_id"] = template_id
        
        campaign_data = await make_mailchimp_request("POST", endpoint, json_data=payload)
        
        result = {
            "id": campaign_data.get("id"),
            "web_id": campaign_data.get("web_id"),
            "type": campaign_data.get("type"),
            "create_time": campaign_data.get("create_time"),
            "archive_url": campaign_data.get("archive_url"),
            "long_archive_url": campaign_data.get("long_archive_url"),
            "status": campaign_data.get("status"),
            "emails_sent": campaign_data.get("emails_sent"),
            "content_type": campaign_data.get("content_type"),
            "recipients": campaign_data.get("recipients", {}),
            "settings": campaign_data.get("settings", {}),
            "tracking": campaign_data.get("tracking", {}),
            "delivery_status": campaign_data.get("delivery_status", {}),
            "list_id": list_id,
            "subject_line": subject_line,
            "from_name": from_name,
            "note": "Campaign created successfully. Use set_campaign_content to add content, then send_campaign to send it."
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool create_campaign: {e}")
        return {
            "error": "Failed to create campaign",
            "type": type,
            "list_id": list_id,
            "subject_line": subject_line,
            "exception": str(e)
        }

async def get_campaign_info(campaign_id: str) -> Dict[str, Any]:
    """Get information about a specific campaign."""
    logger.info(f"Executing tool: get_campaign_info with campaign_id: {campaign_id}")
    try:
        endpoint = f"/campaigns/{campaign_id}"
        
        campaign_data = await make_mailchimp_request("GET", endpoint)
        
        result = {
            "id": campaign_data.get("id"),
            "web_id": campaign_data.get("web_id"),
            "parent_campaign_id": campaign_data.get("parent_campaign_id"),
            "type": campaign_data.get("type"),
            "create_time": campaign_data.get("create_time"),
            "archive_url": campaign_data.get("archive_url"),
            "long_archive_url": campaign_data.get("long_archive_url"),
            "status": campaign_data.get("status"),
            "emails_sent": campaign_data.get("emails_sent"),
            "send_time": campaign_data.get("send_time"),
            "content_type": campaign_data.get("content_type"),
            "needs_block_refresh": campaign_data.get("needs_block_refresh"),
            "resendable": campaign_data.get("resendable"),
            "recipients": campaign_data.get("recipients", {}),
            "settings": campaign_data.get("settings", {}),
            "tracking": campaign_data.get("tracking", {}),
            "report_summary": campaign_data.get("report_summary", {}),
            "delivery_status": campaign_data.get("delivery_status", {}),
            "ab_split_opts": campaign_data.get("ab_split_opts", {}),
            "social_card": campaign_data.get("social_card", {}),
            "rss_opts": campaign_data.get("rss_opts", {}),
            "variate_settings": campaign_data.get("variate_settings", {})
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_campaign_info: {e}")
        return {
            "error": "Failed to retrieve campaign information",
            "campaign_id": campaign_id,
            "exception": str(e)
        }

async def set_campaign_content(
    campaign_id: str,
    html: Optional[str] = None,
    plain_text: Optional[str] = None,
    url: Optional[str] = None,
    template: Optional[Dict[str, Any]] = None,
    archive: Optional[Dict[str, Any]] = None,
    variate_contents: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Set the content for a campaign."""
    logger.info(f"Executing tool: set_campaign_content with campaign_id: {campaign_id}")
    try:
        endpoint = f"/campaigns/{campaign_id}/content"
        
        payload = {}
        
        if html:
            payload["html"] = html
        if plain_text:
            payload["plain_text"] = plain_text
        if url:
            payload["url"] = url
        if template:
            payload["template"] = template
        if archive:
            payload["archive"] = archive
        if variate_contents:
            payload["variate_contents"] = variate_contents
        
        if not payload:
            return {
                "error": "No content provided",
                "campaign_id": campaign_id,
                "note": "At least one content type (html, plain_text, url, template, archive, or variate_contents) must be provided"
            }
        
        content_data = await make_mailchimp_request("PUT", endpoint, json_data=payload)
        
        result = {
            "variate_contents": content_data.get("variate_contents", []),
            "html": content_data.get("html"),
            "plain_text": content_data.get("plain_text"),
            "archive_html": content_data.get("archive_html"),
            "campaign_id": campaign_id,
            "content_set": list(payload.keys()),
            "note": "Campaign content has been set successfully. Campaign is now ready to send."
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool set_campaign_content: {e}")
        return {
            "error": "Failed to set campaign content",
            "campaign_id": campaign_id,
            "exception": str(e)
        }

async def send_campaign(campaign_id: str) -> Dict[str, Any]:
    """Send a Mailchimp campaign immediately."""
    logger.info(f"Executing tool: send_campaign with campaign_id: {campaign_id}")
    try:
        endpoint = f"/campaigns/{campaign_id}/actions/send"
        
        await make_mailchimp_request("POST", endpoint, expect_empty_response=True)
        
        result = {
            "status": "success",
            "message": f"Campaign {campaign_id} has been sent successfully",
            "campaign_id": campaign_id,
            "action": "sent",
            "note": "Campaign is now being delivered to recipients. Check campaign reports for delivery status."
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool send_campaign: {e}")
        return {
            "error": "Failed to send campaign",
            "campaign_id": campaign_id,
            "note": "Ensure campaign has content and passes send checklist requirements",
            "exception": str(e)
        }

async def schedule_campaign(campaign_id: str, schedule_time: str, timewarp: bool = False, batch_delay: Optional[int] = None) -> Dict[str, Any]:
    """Schedule a campaign for delivery at a specific time."""
    logger.info(f"Executing tool: schedule_campaign with campaign_id: {campaign_id}, schedule_time: {schedule_time}")
    try:
        endpoint = f"/campaigns/{campaign_id}/actions/schedule"
        
        payload = {
            "schedule_time": schedule_time,
            "timewarp": timewarp
        }
        
        if batch_delay:
            payload["batch_delay"] = batch_delay
        
        await make_mailchimp_request("POST", endpoint, json_data=payload, expect_empty_response=True)
        
        result = {
            "status": "success",
            "message": f"Campaign {campaign_id} has been scheduled successfully",
            "campaign_id": campaign_id,
            "schedule_time": schedule_time,
            "timewarp": timewarp,
            "batch_delay": batch_delay,
            "action": "scheduled",
            "note": "Campaign is scheduled for delivery. Use unschedule if you need to make changes."
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool schedule_campaign: {e}")
        return {
            "error": "Failed to schedule campaign",
            "campaign_id": campaign_id,
            "schedule_time": schedule_time,
            "note": "Ensure campaign has content and passes send checklist requirements",
            "exception": str(e)
        }

async def delete_campaign(campaign_id: str) -> Dict[str, Any]:
    """Delete a campaign from Mailchimp account."""
    logger.info(f"Executing tool: delete_campaign with campaign_id: {campaign_id}")
    try:
        endpoint = f"/campaigns/{campaign_id}"
        
        await make_mailchimp_request("DELETE", endpoint, expect_empty_response=True)
        
        result = {
            "status": "success",
            "message": f"Campaign {campaign_id} has been deleted successfully",
            "campaign_id": campaign_id,
            "action": "deleted",
            "warning": "This action is permanent. Campaign content and statistics have been removed."
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool delete_campaign: {e}")
        return {
            "error": "Failed to delete campaign",
            "campaign_id": campaign_id,
            "note": "Only draft campaigns can be deleted. Sent campaigns cannot be deleted.",
            "exception": str(e)
        }