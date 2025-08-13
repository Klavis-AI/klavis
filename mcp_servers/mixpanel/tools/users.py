import logging
import json
import base64
from typing import Any, Dict, Optional

from .base import get_project_token, MixpanelIngestionClient, MixpanelQueryClient

logger = logging.getLogger(__name__)

async def set_user_profile(
    distinct_id: str,
    properties: Optional[Dict[str, Any]] = None,
    operation: str = "$set"
) -> Dict[str, Any]:
    """Set user profile properties in Mixpanel People."""
    project_token = get_project_token()
    
    profile_data = {
        "$token": project_token,
        "$distinct_id": distinct_id,
        operation: properties or {}
    }
    
    # Encode the profile data as base64 (Mixpanel requirement)
    encoded_data = base64.b64encode(json.dumps(profile_data).encode()).decode()
    
    params = {"data": encoded_data}
    
    return await MixpanelIngestionClient.make_request("POST", "/engage", params=params)

async def get_user_profile(
    distinct_id: str
) -> Dict[str, Any]:
    """Get user profile from Mixpanel People."""
    try:
        # Use the Query API to get user profile
        params = {
            "where": json.dumps({"$distinct_id": distinct_id}),
            "limit": 1
        }
        
        result = await MixpanelQueryClient.make_request("GET", "/2.0/engage", params=params)
        
        if isinstance(result, dict) and "results" in result:
            results = result["results"]
            if results and len(results) > 0:
                return {
                    "success": True,
                    "profile": results[0],
                    "message": f"Profile found for user {distinct_id}"
                }
            else:
                return {
                    "success": False,
                    "profile": None,
                    "error": f"No profile found for user {distinct_id}"
                }
        else:
            return {
                "success": False,
                "profile": None,
                "error": f"Unexpected response format: {result}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "profile": None,
            "error": f"Failed to retrieve user profile: {str(e)}"
        }