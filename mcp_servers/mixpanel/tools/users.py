import logging
import json
import base64
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from .base import (
    MixpanelIngestionClient,
    MixpanelQueryClient,
    MixpanelExportClient
)

logger = logging.getLogger(__name__)

async def set_user_profile(
    project_id: str,
    distinct_id: str,
    properties: Optional[Dict[str, Any]] = None,
    operation: str = "$set"
) -> Dict[str, Any]:
    """Set user profile properties in Mixpanel People.
    
    Args:
        project_id: The Mixpanel project ID
        distinct_id: The distinct ID of the user
        properties: The properties to set on the user profile
        operation: The operation type (e.g., "$set", "$set_once", "$add", etc.)
        
    Returns:
        Dict with the operation result
    """
    if not project_id:
        raise ValueError("project_id is required")
    
    if not distinct_id:
        raise ValueError("distinct_id is required")
    
    # Build the profile update data
    profile_data = {
        "$distinct_id": distinct_id,
        operation: properties or {}
    }
    
    # For /engage, we need to encode the data
    encoded_data = base64.b64encode(json.dumps(profile_data).encode()).decode()
    
    params = {"data": encoded_data}
    
    # Use the ingestion client with project_id
    return await MixpanelIngestionClient.make_request(
        "POST", 
        "/engage", 
        params=params,
        project_id=project_id
    )

async def get_user_profile(
    distinct_id: str
) -> Dict[str, Any]:
    """Retrieve user profile data from Mixpanel People."""
    try:
        params = {
            "distinct_id": distinct_id,
            "format": "json"
        }
        
        result = await MixpanelQueryClient.make_request("GET", "/2.0/engage", params=params)
        
        if isinstance(result, dict):
            # Check if we have profile data
            if "results" in result:
                results = result.get("results", [])
                if results and len(results) > 0:
                    profile = results[0]
                    return {
                        "success": True,
                        "profile": profile,
                        "distinct_id": profile.get("$distinct_id", distinct_id),
                        "properties": profile.get("$properties", {}),
                        "message": f"Profile found for user: {distinct_id}"
                    }
                else:
                    return {
                        "success": False,
                        "profile": None,
                        "distinct_id": distinct_id,
                        "message": f"No profile found for user: {distinct_id}"
                    }
            else:
                return {
                    "success": False,
                    "profile": None,
                    "error": "Unexpected response format",
                    "raw_response": result
                }
        else:
            return {
                "success": False,
                "profile": None,
                "error": f"Unexpected response type: {type(result)}"
            }
    except Exception as e:
        logger.exception(f"Error getting user profile: {e}")
        return {
            "success": False,
            "profile": None,
            "error": f"Failed to get user profile: {str(e)}"
        }

async def get_profile_event_activity(
    distinct_id: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """Get event activity feed for a specific user."""
    try:
        # Set default date range if not provided
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "where": f'properties["$distinct_id"] == "{distinct_id}"',
            "limit": limit
        }
        
        # Use Export API to get raw event data
        result = await MixpanelExportClient.make_request("GET", "", params=params)
        
        if isinstance(result, dict) and "events" in result:
            events = result.get("events", [])
            
            # Process events to extract key information
            processed_events = []
            for event in events:
                if isinstance(event, dict):
                    properties = event.get("properties", {})
                    processed_events.append({
                        "event": event.get("event", "Unknown"),
                        "time": properties.get("time"),
                        "timestamp": datetime.fromtimestamp(properties.get("time", 0)).isoformat() if properties.get("time") else None,
                        "properties": properties
                    })
            
            # Sort events by time (most recent first)
            processed_events.sort(key=lambda x: x.get("time", 0), reverse=True)
            
            return {
                "success": True,
                "distinct_id": distinct_id,
                "events": processed_events,
                "total_events": len(processed_events),
                "date_range": {
                    "from": from_date,
                    "to": to_date
                },
                "message": f"Retrieved {len(processed_events)} events for user: {distinct_id}"
            }
        else:
            return {
                "success": False,
                "distinct_id": distinct_id,
                "events": [],
                "error": "No events found or unexpected response format",
                "raw_response": result
            }
    except Exception as e:
        logger.exception(f"Error getting profile event activity: {e}")
        return {
            "success": False,
            "distinct_id": distinct_id,
            "events": [],
            "error": f"Failed to get profile event activity: {str(e)}"
        }
