import logging
from typing import Any, Dict
from .base import make_mailchimp_request

# Configure logging
logger = logging.getLogger(__name__)

async def ping_mailchimp() -> Dict[str, Any]:
    """Test the connection to Mailchimp API and verify authentication."""
    logger.info("Executing tool: ping_mailchimp")
    try:
        endpoint = "/ping"
        
        ping_data = await make_mailchimp_request("GET", endpoint)
        
        result = {
            "status": "success",
            "health_status": ping_data.get("health_status"),
            "message": "Mailchimp API connection successful"
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool ping_mailchimp: {e}")
        return {
            "status": "error",
            "message": "Failed to connect to Mailchimp API",
            "error": str(e)
        }

async def get_account_info() -> Dict[str, Any]:
    """Get information about the Mailchimp account."""
    logger.info("Executing tool: get_account_info")
    try:
        endpoint = "/"
        
        account_data = await make_mailchimp_request("GET", endpoint)
        
        account_info = {
            "account_id": account_data.get("account_id"),
            "account_name": account_data.get("account_name"),
            "username": account_data.get("username"),
            "email": account_data.get("email"),
            "first_name": account_data.get("first_name"),
            "last_name": account_data.get("last_name"),
            "avatar_url": account_data.get("avatar_url"),
            "role": account_data.get("role"),
            "member_since": account_data.get("member_since"),
            "pricing_plan_type": account_data.get("pricing_plan_type"),
            "industry": account_data.get("industry"),
            "timezone": account_data.get("timezone"),
            "total_subscribers": account_data.get("total_subscribers"),
            "contact": account_data.get("contact", {}),
            "pro_enabled": account_data.get("pro_enabled"),
            "last_login": account_data.get("last_login")
        }
        
        return account_info
    except Exception as e:
        logger.exception(f"Error executing tool get_account_info: {e}")
        return {
            "error": "Failed to retrieve account information",
            "exception": str(e)
        }