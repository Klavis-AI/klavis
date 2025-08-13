import logging
import json
import base64
from typing import Any, Dict, Optional

from .base import get_project_token, MixpanelIngestionClient, MixpanelQueryClient

logger = logging.getLogger(__name__)

async def track_event(
    event: str,
    properties: Optional[Dict[str, Any]] = None,
    distinct_id: Optional[str] = None
) -> Dict[str, Any]:
    """Track an event to Mixpanel."""
    project_token = get_project_token()
    
    event_data = {
        "event": event,
        "properties": {
            "token": project_token,
            **(properties or {})
        }
    }
    
    if distinct_id:
        event_data["properties"]["distinct_id"] = distinct_id
    
    # Encode the event data as base64 (Mixpanel requirement)
    encoded_data = base64.b64encode(json.dumps(event_data).encode()).decode()
    
    params = {"data": encoded_data}
    
    return await MixpanelIngestionClient.make_request("POST", "/track", params=params)

async def track_batch_events(
    events: list[Dict[str, Any]]
) -> Dict[str, Any]:
    """Track multiple events in a single batch request to Mixpanel."""
    try:
        if not events or not isinstance(events, list):
            raise ValueError("Events must be a non-empty list")
        
        project_token = get_project_token()
        
        # Prepare batch event data
        batch_events = []
        for i, event_data in enumerate(events):
            if not isinstance(event_data, dict):
                raise ValueError(f"Event {i} must be a dictionary")
            
            event_name = event_data.get("event")
            if not event_name:
                raise ValueError(f"Event {i} missing required 'event' field")
            
            properties = event_data.get("properties", {})
            distinct_id = event_data.get("distinct_id")
            
            # Build event object
            event_obj = {
                "event": event_name,
                "properties": {
                    "token": project_token,
                    **properties
                }
            }
            
            if distinct_id:
                event_obj["properties"]["distinct_id"] = distinct_id
            
            batch_events.append(event_obj)
        
        # Encode the batch data as base64 (Mixpanel requirement)
        encoded_data = base64.b64encode(json.dumps(batch_events).encode()).decode()
        
        params = {"data": encoded_data}
        
        result = await MixpanelIngestionClient.make_request("POST", "/track", params=params)
        
        # Add batch info to result
        if isinstance(result, dict):
            result["batch_size"] = len(batch_events)
            result["events_processed"] = len(batch_events) if result.get("success") else 0
            
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to track batch events: {str(e)}",
            "batch_size": len(events) if isinstance(events, list) else 0,
            "events_processed": 0
        }

async def query_events(
    from_date: str,
    to_date: str,
    event: Optional[str] = None,
    where: Optional[str] = None,
    limit: Optional[int] = 1000
) -> Dict[str, Any]:
    """Query raw event data from Mixpanel."""
    try:
        params = {
            "from_date": from_date,
            "to_date": to_date
        }
        
        if event:
            params["event"] = f'["{event}"]'
        
        if where:
            params["where"] = where
            
        if limit:
            params["limit"] = str(limit)
        
        result = await MixpanelQueryClient.make_request("GET", "/2.0/export", params=params)
        
        if isinstance(result, dict) and "events" in result:
            return {
                "success": True,
                "events": result["events"],
                "count": len(result["events"]),
                "message": f"Retrieved {len(result['events'])} events from {from_date} to {to_date}"
            }
        else:
            return {
                "success": False,
                "events": [],
                "error": f"Unexpected response format: {result}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "events": [],
            "error": f"Failed to query events: {str(e)}"
        }