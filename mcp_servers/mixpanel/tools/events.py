import logging
import json
from typing import Any, Dict, Optional, List
import time
import uuid

from .base import (
    MixpanelIngestionClient,
    MixpanelExportClient,
    MixpanelQueryClient
)

logger = logging.getLogger(__name__)

async def send_events(
    project_id: str,
    events: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Send events to Mixpanel using the /import endpoint with Service Account authentication.
    Use this API to send batches of events from your servers to Mixpanel.
    
    Args:
        project_id: The Mixpanel project ID to import events to
        events: List of event objects to import
        
    Returns:
        Dict with import results
    """
    try:
        if not events or not isinstance(events, list):
            raise ValueError("Events must be a non-empty list")
        
        if not project_id:
            raise ValueError("project_id is required")
        
        # Prepare batch event data for /import endpoint
        batch_events = []
        for i, event_data in enumerate(events):
            if not isinstance(event_data, dict):
                raise ValueError(f"Event {i} must be a dictionary")
            
            event_name = event_data.get("event")
            if not event_name:
                raise ValueError(f"Event {i} missing required 'event' field")
            
            properties = event_data.get("properties", {})
            distinct_id = event_data.get("distinct_id", "")
            
            # Ensure required fields for /import endpoint
            if "time" not in properties:
                # Use current time in milliseconds if not specified
                properties["time"] = int(time.time() * 1000)
            
            if "$insert_id" not in properties:
                # Generate a unique insert_id for deduplication
                properties["$insert_id"] = str(uuid.uuid4())
            
            # Ensure distinct_id is in properties
            properties["distinct_id"] = distinct_id or ""
            
            # Build event object for /import endpoint
            event_obj = {
                "event": event_name,
                "properties": properties
            }
            
            batch_events.append(event_obj)
        
        # Use Service Account auth with /import endpoint
        result = await MixpanelIngestionClient.make_request(
            "POST", 
            "/import",
            data=batch_events,
            project_id=project_id
        )
        
        # Add batch info to result
        if isinstance(result, dict):
            result["batch_size"] = len(batch_events)
            result["events_processed"] = len(batch_events) if result.get("success", True) else 0
            result["project_id"] = project_id
            
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to send events: {str(e)}",
            "batch_size": len(events) if isinstance(events, list) else 0,
            "events_processed": 0,
            "project_id": project_id
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
        
        # The export endpoint is already included in MIXPANEL_EXPORT_ENDPOINT
        result = await MixpanelExportClient.make_request("GET", "", params=params)
        
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
        # The export endpoint is already included in MIXPANEL_EXPORT_ENDPOINT
        result = await MixpanelExportClient.make_request("GET", "", params=params)
        
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
        # The export endpoint is already included in MIXPANEL_EXPORT_ENDPOINT
        result = await MixpanelExportClient.make_request("GET", "", params=params)
        
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

async def get_events(
    project_id: str
) -> List[str]:
    """Get event names for the given Mixpanel project.
    
    This tool retrieves all event names that have been tracked in the specified project.
    Useful for discovering what events are available for analysis.
    
    Args:
        project_id: The Mixpanel project ID to get event names for
        
    Returns:
        List of event names (strings) for the project
    """
    try:
        if not project_id:
            raise ValueError("project_id is required")
        
        # Use the Query API endpoint to get event names
        params = {
            "project_id": project_id,
            "type": "general"  # Default type for event names
        }
        
        result = await MixpanelQueryClient.make_request(
            "GET",
            "/query/events/names",
            params=params
        )
        
        # The API returns a list of event names directly
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "data" in result:
            # Sometimes the response might be wrapped
            data = result["data"]
            if isinstance(data, list):
                return data
            else:
                logger.warning(f"Unexpected data format: {data}")
                return []
        else:
            logger.warning(f"Unexpected response format: {result}")
            return []
            
    except Exception as e:
        logger.exception(f"Error getting event names: {e}")
        raise

async def get_event_properties(
    project_id: str,
    event: str
) -> List[str]:
    """Get available properties for a specific event in a Mixpanel project.

    This returns the list of event property keys that can be used for filtering
    or aggregation in queries for the provided event name and project.

    Args:
        project_id: Mixpanel project ID
        event: Event name (e.g., "AI Prompt Sent")

    Returns:
        List of property names (strings)
    """
    try:
        if not project_id:
            raise ValueError("project_id is required")
        if not event:
            raise ValueError("event is required")

        params = {
            "project_id": project_id,
            "event": event,
        }

        # Query API endpoint for event properties, mirroring naming used for events/names
        result = await MixpanelQueryClient.make_request(
            "GET",
            "/query/events/properties",
            params=params,
        )

        # The API commonly returns a bare list; handle wrapped responses too
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            # Some responses may be wrapped like { "data": [...] }
            data = result.get("data")
            if isinstance(data, list):
                return data
            # Or keyed by the event name
            by_event = result.get(event)
            if isinstance(by_event, list):
                return by_event
            logger.warning(f"Unexpected event properties response format: {result}")
            return []

        logger.warning(f"Unexpected response type for event properties: {type(result)}")
        return []

    except Exception as e:
        logger.exception(f"Error getting event properties: {e}")
        raise

async def get_event_property_values(
    project_id: str,
    event: str,
    property_name: str
) -> List[str]:
    """Get distinct values for a specific event property in a Mixpanel project.

    This returns the list of unique values that have been seen for the given
    event's property, useful for building filters and understanding taxonomy.

    Args:
        project_id: Mixpanel project ID
        event: Event name (e.g., "AI Prompt Sent")
        property_name: Property name (e.g., "utm_source")

    Returns:
        List of property values (strings)
    """
    try:
        if not project_id:
            raise ValueError("project_id is required")
        if not event:
            raise ValueError("event is required")
        if not property_name:
            raise ValueError("property is required")

        params = {
            "project_id": project_id,
            "event": event,
            # Mixpanel expects the property key under the `name` query param
            "name": property_name,
        }

        # Query API endpoint for property values of an event
        result = await MixpanelQueryClient.make_request(
            "GET",
            "/query/events/properties/values",
            params=params,
        )

        # API typically returns a list of strings; handle wrapped responses too
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            data = result.get("data")
            if isinstance(data, list):
                return data
            logger.warning(f"Unexpected event property values response format: {result}")
            return []

        logger.warning(f"Unexpected response type for event property values: {type(result)}")
        return []

    except Exception as e:
        logger.exception(f"Error getting event property values: {e}")
        raise