import logging
from typing import Any, Dict, List, Optional
from .base import make_calendly_request

# Configure logging
logger = logging.getLogger(__name__)

async def list_events(
    status: Optional[str] = None,
    count: int = 20
) -> Dict[str, Any]:
    """List scheduled events for the current user."""
    logger.info(f"Executing tool: list_events with status: {status}, count: {count}")
    try:
        # First get current user to get their URI
        user_data = await make_calendly_request("GET", "/users/me")
        user_uri = user_data.get("resource", {}).get("uri")
        
        if not user_uri:
            raise RuntimeError("Unable to get current user URI")
        
        # Build query parameters
        params = {
            "user": user_uri,
            "count": min(count, 100)  # Calendly API limit
        }
        
        if status:
            params["status"] = status
        
        # Get events
        endpoint = "/scheduled_events"
        events_data = await make_calendly_request("GET", endpoint, params=params)
        
        return events_data
    except Exception as e:
        logger.exception(f"Error executing tool list_events: {e}")
        raise e

async def get_event_details(event_uuid: str) -> Dict[str, Any]:
    """Get detailed information about a specific event."""
    logger.info(f"Executing tool: get_event_details with event_uuid: {event_uuid}")
    try:
        # Get event details
        endpoint = f"/scheduled_events/{event_uuid}"
        event_data = await make_calendly_request("GET", endpoint)
        
        # Also get invitees for this event
        try:
            invitees_endpoint = f"/scheduled_events/{event_uuid}/invitees"
            invitees_data = await make_calendly_request("GET", invitees_endpoint)
            event_data["invitees"] = invitees_data
        except Exception as e:
            logger.warning(f"Could not get invitees for event {event_uuid}: {e}")
            event_data["invitees"] = {"error": str(e)}
        
        return event_data
    except Exception as e:
        logger.exception(f"Error executing tool get_event_details: {e}")
        raise e

async def list_event_types(
    active: bool = True,
    count: int = 20
) -> Dict[str, Any]:
    """List available event types for the current user."""
    logger.info(f"Executing tool: list_event_types with active: {active}, count: {count}")
    try:
        # First get current user to get their URI
        user_data = await make_calendly_request("GET", "/users/me")
        user_uri = user_data.get("resource", {}).get("uri")
        
        if not user_uri:
            raise RuntimeError("Unable to get current user URI")
        
        # Build query parameters
        params = {
            "user": user_uri,
            "count": min(count, 100)  # Calendly API limit
        }
        
        if active is not None:
            params["active"] = "true" if active else "false"
        
        # Get event types
        endpoint = "/event_types"
        event_types_data = await make_calendly_request("GET", endpoint, params=params)
        
        return event_types_data
    except Exception as e:
        logger.exception(f"Error executing tool list_event_types: {e}")
        raise e

async def list_availability_schedules(
    user_uri: Optional[str] = None,
    count: int = 20
) -> Dict[str, Any]:
    """List the availability schedules of the given user."""
    logger.info(f"Executing tool: list_availability_schedules with user_uri: {user_uri}, count: {count}")
    try:
        # If no user_uri provided, get current user's URI
        if not user_uri:
            user_data = await make_calendly_request("GET", "/users/me")
            user_uri = user_data.get("resource", {}).get("uri")
            
            if not user_uri:
                raise RuntimeError("Unable to get current user URI")
        
        # Build query parameters
        params = {
            "user": user_uri,
            "count": min(count, 100)  # Calendly API limit
        }
        
        # Get user availability schedules
        endpoint = "/user_availability_schedules"
        schedules_data = await make_calendly_request("GET", endpoint, params=params)
        
        return schedules_data
    except Exception as e:
        logger.exception(f"Error executing tool list_availability_schedules: {e}")
        raise e

async def list_event_invitees(
    event_uuid: str,
    count: int = 20,
    email: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """List invitees for a specific scheduled event."""
    logger.info(f"Executing tool: list_event_invitees with event_uuid: {event_uuid}, count: {count}, email: {email}, status: {status}")
    try:
        # Build query parameters
        params = {
            "count": min(count, 100)  # Calendly API limit
        }
        
        if email:
            params["email"] = email
        
        if status:
            params["status"] = status
        
        # Get event invitees
        endpoint = f"/scheduled_events/{event_uuid}/invitees"
        invitees_data = await make_calendly_request("GET", endpoint, params=params)
        
        return invitees_data
    except Exception as e:
        logger.exception(f"Error executing tool list_event_invitees: {e}")
        raise e