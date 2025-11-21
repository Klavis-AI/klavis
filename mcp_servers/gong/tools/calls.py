import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, List
import httpx

from .base import get, post

logger = logging.getLogger(__name__)

async def list_calls(
    from_date: str,
    to_date: str,
    limit: int = 50,
    cursor: Optional[str] = None,
    workspace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """List calls in Gong between two datetimes.

    Returns calls that started on or after from_date and up to but excluding to_date.
    
    Parameters
    ----------
    from_date : str
        ISO-8601 formatted datetime from which to list calls (required).
    to_date : str
        ISO-8601 formatted datetime until which to list calls (required).
    limit : int, optional
        Maximum number of calls to return (default 50).
    cursor : str, optional
        Pagination cursor from previous API call.
    workspace_id : str, optional
        Filter calls by workspace identifier.
    """
    if not from_date or not to_date:
        raise ValueError("from_date and to_date are required parameters")

    params = {
        "fromDateTime": from_date,
        "toDateTime": to_date,
        "limit": limit,
    }
    
    if cursor:
        params["cursor"] = cursor
    if workspace_id:
        params["workspaceId"] = workspace_id
        
    logger.info("Listing calls from %s to %s (limit=%s, workspace_id=%s)", 
                from_date, to_date, limit, workspace_id)
    
    try:
        return await get("/v2/calls", params=params)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # 404 means no calls found for the specified period, not an error
            logger.info("No calls found for the specified period from %s to %s", from_date, to_date)
            return {
                "calls": [],
                "records": {"totalRecords": 0, "currentPageSize": 0, "currentPageNumber": 1},
                "message": "No calls found for the specified period"
            }
        elif e.response.status_code == 429:
            # 429 means API request limit exceeded
            logger.warning("Gong API request limit exceeded")
            raise RuntimeError("Gong API request limit exceeded. Please try again later.") from e
        else:
            # Re-raise other HTTP errors
            raise

async def add_new_call(call_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new call record to Gong.

    Creates a new call record in Gong. Either provide a downloadMediaUrl or use 
    the returned callId to upload media in a follow-up request to /v2/calls/{id}/media.

    Parameters
    ----------
    call_data : Dict[str, Any]
        Call metadata including:
        
        Required fields:
        - clientUniqueId (str): Unique identifier in PBX/recording system (0-2048 chars)
        - actualStart (str): ISO-8601 datetime when call started
        - parties (list): List of call participants (must include primaryUser)
        - direction (str): "Inbound", "Outbound", "Conference", or "Unknown"
        - primaryUser (str): Gong internal user ID of the call host
        
        Optional fields:
        - title (str): Call title for indexing/search
        - purpose (str): Call purpose (0-255 chars)
        - scheduledStart (str): ISO-8601 scheduled start datetime
        - scheduledEnd (str): ISO-8601 scheduled end datetime
        - duration (float): Actual call duration in seconds
        - disposition (str): Call disposition (0-255 chars)
        - context (list): References to external systems (CRM, etc.)
        - customData (str): Optional metadata for troubleshooting
        - speakersTimeline (dict): Speech segments (who spoke when)
        - meetingUrl (str): Conference call URL
        - callProviderCode (str): Provider code (zoom, ringcentral, etc.)
        - downloadMediaUrl (str): URL to download media file (max 1.5GB)
        - workspaceId (str): Optional workspace identifier
        - languageCode (str): Language code for transcription (e.g., en-US)
        - flowContext (dict): Task ID association

    Returns
    -------
    Dict[str, Any]
        Response containing the created call's details, including callId
    """
    if not call_data:
        raise ValueError("call_data cannot be empty")

    # Validate required fields
    required_fields = ["clientUniqueId", "actualStart", "parties", "direction", "primaryUser"]
    missing_fields = [field for field in required_fields if field not in call_data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    logger.info("Adding new call to Gong with clientUniqueId: %s", call_data.get("clientUniqueId"))
    return await post("/v2/calls", call_data)

async def get_call_by_id(call_id: str) -> Dict[str, Any]:
    """Retrieve data for a specific call by ID.

    Retrieves detailed information for a single call using Gong's unique call identifier.
    
    Parameters
    ----------
    call_id : str
        Gong's unique numeric identifier for the call (up to 20 digits).

    Returns
    -------
    Dict[str, Any]
        Response containing the call's details
    """
    if not call_id:
        raise ValueError("call_id is required")

    logger.info("Retrieving call with ID: %s", call_id)
    return await get(f"/v2/calls/{call_id}") 