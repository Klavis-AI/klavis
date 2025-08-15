import logging
import json
from typing import Any, Dict, List, Optional
import httpx

from .base import get_service_account_credentials, MixpanelQueryClient

logger = logging.getLogger(__name__)

async def list_saved_funnels() -> Dict[str, Any]:
    """List all saved funnels from Mixpanel with their names and funnel IDs."""
    try:
        # Use the correct base URL for funnels API
        base_url = "https://mixpanel.com/api/query/funnels/list"
        
        # Get service account credentials
        username, secret = get_service_account_credentials()
        
        # Use Basic Auth with service account credentials
        auth = httpx.BasicAuth(username, secret)
        
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

async def run_funnels_query(
    project_id: str,
    events: List[Dict[str, Any]] | str,
    from_date: str,
    to_date: str,
    count_type: Optional[str] = "unique",
) -> Dict[str, Any]:
    """Run a funnel query via Mixpanel Query API.

    Measures conversion through a sequence of steps.

    Args:
        project_id: Mixpanel project id.
        events: Ordered list of funnel steps (each item typically has at least an 'event' and optional 'step_label'),
                or a pre-serialized JSON string for the same.
        from_date: Start date YYYY-MM-DD.
        to_date: End date YYYY-MM-DD.
        count_type: One of {unique, general}. Defaults to unique (distinct users).

    Returns:
        Dict[str, Any] response as returned by Mixpanel.
    """
    if not project_id:
        raise ValueError("project_id is required")
    if not events:
        raise ValueError("events is required and must define at least one step")
    if not from_date or not to_date:
        raise ValueError("from_date and to_date are required in YYYY-MM-DD format")

    allowed_count_types = {"unique", "general"}
    if count_type and count_type not in allowed_count_types:
        raise ValueError(f"count_type must be one of {sorted(allowed_count_types)}")

    # Mixpanel funnels API expects the 'events' parameter as a JSON-encoded array string
    if isinstance(events, str):
        events_param = events
    else:
        try:
            events_param = json.dumps(events)
        except Exception as e:
            raise ValueError(f"events must be serializable to JSON array of step objects: {e}")

    params: Dict[str, Any] = {
        "project_id": str(project_id),
        "events": events_param,
        "from_date": from_date,
        "to_date": to_date,
        "count_type": count_type or "unique",
    }

    # Remove any Nones
    params = {k: v for k, v in params.items() if v is not None}

    try:
        # Historical Mixpanel endpoint for funnels
        endpoint = "/2.0/funnels"
        result = await MixpanelQueryClient.make_request("GET", endpoint, params=params)
        return result
    except Exception as e:
        logger.exception("Error running funnels query: %s", e)
        return {
            "success": False,
            "error": f"Failed to run funnels query: {str(e)}",
            "params": params,
        }