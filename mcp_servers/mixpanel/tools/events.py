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

async def get_event_count(
    from_date: str,
    to_date: str,
    event: Optional[str] = None
) -> Dict[str, Any]:
    """Get total event count for a date range from Mixpanel."""
    try:
        params = {
            "from_date": from_date,
            "to_date": to_date
        }
        
        # If specific event is provided, filter by it
        if event:
            params["event"] = f'["{event}"]'
        
        # Query events and count them
        result = await MixpanelQueryClient.make_request("GET", "/2.0/export", params=params)
        
        if isinstance(result, dict) and "events" in result:
            event_count = len(result["events"])
            
            # Calculate additional stats
            unique_users = set()
            event_types = {}
            
            for event_data in result["events"]:
                # Count unique users
                if "properties" in event_data and "distinct_id" in event_data["properties"]:
                    unique_users.add(event_data["properties"]["distinct_id"])
                
                # Count event types
                event_name = event_data.get("event", "Unknown")
                event_types[event_name] = event_types.get(event_name, 0) + 1
            
            return {
                "success": True,
                "total_events": event_count,
                "unique_users": len(unique_users),
                "date_range": {
                    "from": from_date,
                    "to": to_date
                },
                "event_breakdown": event_types,
                "filtered_event": event if event else "All events",
                "message": f"Found {event_count} events from {from_date} to {to_date}"
            }
        else:
            return {
                "success": False,
                "total_events": 0,
                "error": f"Unexpected response format: {result}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "total_events": 0,
            "error": f"Failed to get event count: {str(e)}"
        }

async def get_top_events(
    from_date: str,
    to_date: str,
    limit: Optional[int] = 10
) -> Dict[str, Any]:
    """Get the most common events over a time period from Mixpanel."""
    try:
        params = {
            "from_date": from_date,
            "to_date": to_date
        }
        
        # Query all events for the time period
        result = await MixpanelQueryClient.make_request("GET", "/2.0/export", params=params)
        
        if isinstance(result, dict) and "events" in result:
            events = result["events"]
            
            # Count events by type
            event_counts = {}
            total_events = len(events)
            unique_users = set()
            
            for event_data in events:
                # Count events by name
                event_name = event_data.get("event", "Unknown")
                event_counts[event_name] = event_counts.get(event_name, 0) + 1
                
                # Track unique users
                if "properties" in event_data and "distinct_id" in event_data["properties"]:
                    unique_users.add(event_data["properties"]["distinct_id"])
            
            # Sort events by count (descending) and get top N
            sorted_events = sorted(event_counts.items(), key=lambda x: x[1], reverse=True)
            top_events = sorted_events[:limit] if limit else sorted_events
            
            # Calculate percentages
            top_events_with_stats = []
            for event_name, count in top_events:
                percentage = (count / total_events * 100) if total_events > 0 else 0
                top_events_with_stats.append({
                    "event_name": event_name,
                    "count": count,
                    "percentage": round(percentage, 2)
                })
            
            return {
                "success": True,
                "top_events": top_events_with_stats,
                "total_events_analyzed": total_events,
                "unique_users": len(unique_users),
                "date_range": {
                    "from": from_date,
                    "to": to_date
                },
                "limit_requested": limit,
                "events_returned": len(top_events_with_stats),
                "message": f"Found top {len(top_events_with_stats)} events from {from_date} to {to_date}"
            }
        else:
            return {
                "success": False,
                "top_events": [],
                "error": f"Unexpected response format: {result}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "top_events": [],
            "error": f"Failed to get top events: {str(e)}"
        }

async def get_todays_top_events(
    limit: Optional[int] = 10
) -> Dict[str, Any]:
    """Get the most common events from today from Mixpanel analytics."""
    try:
        from datetime import datetime, date
        
        # Get today's date in YYYY-MM-DD format
        today = date.today().strftime('%Y-%m-%d')
        
        print(f"Querying today's events for date: {today}")
        
        # Use the existing get_top_events function with today's date
        result = await get_top_events(today, today, limit)
        
        if isinstance(result, dict) and result.get("success"):
            # Enhance the result with today-specific information
            enhanced_result = {
                **result,
                "date": today,
                "date_description": f"Today ({today})",
                "is_today": True,
                "message": f"Found top {len(result.get('top_events', []))} events for today ({today})"
            }
            
            # Add some additional context
            if result.get("total_events_analyzed", 0) == 0:
                enhanced_result.update({
                    "message": f"No events found for today ({today}). This might be because it's early in the day or no events have been tracked yet.",
                    "suggestion": "Try tracking some test events or check events from yesterday."
                })
            
            return enhanced_result
        else:
            # Handle case where get_top_events failed
            return {
                "success": False,
                "top_events": [],
                "date": today,
                "date_description": f"Today ({today})",
                "is_today": True,
                "error": result.get("error", "Failed to get today's top events"),
                "message": f"Could not retrieve events for today ({today})"
            }
            
    except Exception as e:
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        return {
            "success": False,
            "top_events": [],
            "date": today,
            "date_description": f"Today ({today})",
            "is_today": True,
            "error": f"Failed to get today's top events: {str(e)}"
        }