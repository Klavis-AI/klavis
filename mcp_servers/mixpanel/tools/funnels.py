import logging
from typing import Any, Dict
import httpx

from .base import get_api_secret, get_service_account_username, get_service_account_secret

logger = logging.getLogger(__name__)

async def list_saved_funnels() -> Dict[str, Any]:
    """List all saved funnels from Mixpanel with their names and funnel IDs."""
    try:
        # Use the correct base URL for funnels API
        base_url = "https://mixpanel.com/api/query/funnels/list"
        
        # Get authentication
        auth = None
        try:
            api_secret = get_api_secret()
            if api_secret:
                auth = httpx.BasicAuth(api_secret, "")
                logger.info("Using API secret authentication for funnels")
        except RuntimeError:
            # Fall back to service account
            try:
                username = get_service_account_username()
                secret = get_service_account_secret()
                if username and secret:
                    auth = httpx.BasicAuth(username, secret)
                    logger.info("Using service account authentication for funnels")
            except RuntimeError:
                pass
        
        if not auth:
            raise RuntimeError("No authentication provided. Please set either service account credentials or API secret.")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, auth=auth, headers=headers)
            
            # Handle specific status codes
            if response.status_code == 402:
                error_data = response.json() if response.text else {}
                return {
                    "success": False,
                    "funnels": [],
                    "error": "API access requires a paid Mixpanel plan",
                    "details": error_data.get("error", "Your plan does not allow API calls. Upgrade at mixpanel.com/pricing"),
                    "status_code": 402,
                    "upgrade_url": "https://mixpanel.com/pricing"
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "funnels": [],
                    "error": "Authentication failed",
                    "details": "Please check your API secret or service account credentials",
                    "status_code": 401
                }
            
            response.raise_for_status()
            
            # Handle successful response
            result = response.json() if response.text else {}
        
        if isinstance(result, dict):
            # Check if we have funnel data
            if "funnels" in result or isinstance(result, list):
                # Handle both possible response formats
                funnels_data = result.get("funnels", result) if isinstance(result, dict) else result
                
                # Process funnel data to extract key information
                processed_funnels = []
                if isinstance(funnels_data, list):
                    for funnel in funnels_data:
                        if isinstance(funnel, dict):
                            processed_funnels.append({
                                "funnel_id": funnel.get("funnel_id", "N/A"),
                                "name": funnel.get("name", "Unnamed Funnel"),
                                "description": funnel.get("description", ""),
                                "created_date": funnel.get("created", ""),
                                "updated_date": funnel.get("updated", ""),
                                "creator": funnel.get("creator", ""),
                                "steps": funnel.get("steps", []),
                                "step_count": len(funnel.get("steps", [])),
                            })
                
                return {
                    "success": True,
                    "funnels": processed_funnels,
                    "total_funnels": len(processed_funnels),
                    "message": f"Retrieved {len(processed_funnels)} saved funnels"
                }
            else:
                return {
                    "success": True,
                    "funnels": [],
                    "total_funnels": 0,
                    "message": "No saved funnels found",
                    "raw_response": result
                }
        else:
            return {
                "success": False,
                "funnels": [],
                "error": f"Unexpected response format: {result}"
            }
            
    except Exception as e:
        logger.exception(f"Error listing saved funnels: {e}")
        return {
            "success": False,
            "funnels": [],
            "error": f"Failed to list saved funnels: {str(e)}"
        }