import logging
from typing import Any, Dict, List, Optional
from .base import make_figma_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_team_webhooks(team_id: str) -> Dict[str, Any]:
    """Get webhooks for a team."""
    logger.info(f"Executing tool: get_team_webhooks with team_id: {team_id}")
    try:
        endpoint = f"/v1/teams/{team_id}/webhooks"
        
        webhooks_data = await make_figma_request("GET", endpoint)
        
        result = {
            "webhooks": []
        }
        
        for webhook in webhooks_data.get("webhooks", []):
            webhook_info = {
                "id": webhook.get("id"),
                "team_id": webhook.get("team_id"),
                "event_type": webhook.get("event_type"),
                "client_id": webhook.get("client_id"),
                "endpoint": webhook.get("endpoint"),
                "passcode": webhook.get("passcode"),
                "status": webhook.get("status"),
                "description": webhook.get("description"),
                "protocol_version": webhook.get("protocol_version")
            }
            result["webhooks"].append(webhook_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_team_webhooks: {e}")
        return {
            "error": "Failed to retrieve team webhooks",
            "team_id": team_id,
            "exception": str(e)
        }

async def post_webhook(team_id: str, event_type: str, endpoint: str, 
                      passcode: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """Create a webhook."""
    logger.info(f"Executing tool: post_webhook for team_id: {team_id}, event_type: {event_type}")
    try:
        webhook_endpoint = "/v1/webhooks"
        
        payload = {
            "team_id": team_id,
            "event_type": event_type,
            "endpoint": endpoint
        }
        
        if passcode:
            payload["passcode"] = passcode
        if description:
            payload["description"] = description
        
        webhook_data = await make_figma_request("POST", webhook_endpoint, json_data=payload)
        
        result = {
            "id": webhook_data.get("id"),
            "team_id": webhook_data.get("team_id"),
            "event_type": webhook_data.get("event_type"),
            "client_id": webhook_data.get("client_id"),
            "endpoint": webhook_data.get("endpoint"),
            "passcode": webhook_data.get("passcode"),
            "status": webhook_data.get("status"),
            "description": webhook_data.get("description"),
            "protocol_version": webhook_data.get("protocol_version")
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool post_webhook: {e}")
        return {
            "error": "Failed to create webhook",
            "team_id": team_id,
            "event_type": event_type,
            "endpoint": endpoint,
            "exception": str(e)
        }

async def put_webhook(webhook_id: str, event_type: Optional[str] = None, 
                     endpoint: Optional[str] = None, passcode: Optional[str] = None,
                     description: Optional[str] = None) -> Dict[str, Any]:
    """Update a webhook."""
    logger.info(f"Executing tool: put_webhook with webhook_id: {webhook_id}")
    try:
        webhook_endpoint = f"/v1/webhooks/{webhook_id}"
        
        payload = {}
        if event_type:
            payload["event_type"] = event_type
        if endpoint:
            payload["endpoint"] = endpoint
        if passcode:
            payload["passcode"] = passcode
        if description:
            payload["description"] = description
        
        if not payload:
            return {
                "error": "No update parameters provided",
                "webhook_id": webhook_id
            }
        
        webhook_data = await make_figma_request("PUT", webhook_endpoint, json_data=payload)
        
        result = {
            "id": webhook_data.get("id"),
            "team_id": webhook_data.get("team_id"),
            "event_type": webhook_data.get("event_type"),
            "client_id": webhook_data.get("client_id"),
            "endpoint": webhook_data.get("endpoint"),
            "passcode": webhook_data.get("passcode"),
            "status": webhook_data.get("status"),
            "description": webhook_data.get("description"),
            "protocol_version": webhook_data.get("protocol_version")
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool put_webhook: {e}")
        return {
            "error": "Failed to update webhook",
            "webhook_id": webhook_id,
            "exception": str(e)
        }

async def delete_webhook(webhook_id: str) -> Dict[str, Any]:
    """Delete a webhook."""
    logger.info(f"Executing tool: delete_webhook with webhook_id: {webhook_id}")
    try:
        endpoint = f"/v1/webhooks/{webhook_id}"
        
        await make_figma_request("DELETE", endpoint, expect_empty_response=True)
        
        result = {
            "status": "success",
            "message": f"Webhook {webhook_id} has been deleted",
            "webhook_id": webhook_id
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool delete_webhook: {e}")
        return {
            "error": "Failed to delete webhook",
            "webhook_id": webhook_id,
            "exception": str(e)
        }