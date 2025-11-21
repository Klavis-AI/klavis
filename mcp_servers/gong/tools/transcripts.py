import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, List

from .base import post

logger = logging.getLogger(__name__)

async def get_transcripts_by_user(
    user_email: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """Retrieve call transcripts for calls that involve the given user email.

    The function makes one request to the /v2/calls/extensive endpoint with a filter that
    matches the provided email address in the parties list.  For each call it asks Gong to
    include both the transcript and the parties so that callers can determine which company
    participants belong to.

    Parameters
    ----------
    user_email : str
        Email address of the user whose calls we want to fetch.
    from_date : str, optional
        ISO-8601 date-time string for the start of the time window.  If omitted, defaults
        to 30 days in the past.
    to_date : str, optional
        ISO-8601 date-time string for the end of the time window.  If omitted, defaults
        to now.
    limit : int, optional
        Maximum number of calls to return (Gong caps pagination at 100 per page).
    """

    logger.info(
        "Executing Gong tool get_transcripts_by_user for %s (limit=%s)",
        user_email,
        limit,
    )

    if not from_date:
        from_date = (
            datetime.now(timezone.utc) - timedelta(days=30)
        ).isoformat(timespec="seconds")
    if not to_date:
        to_date = datetime.now(timezone.utc).isoformat(timespec="seconds")

    payload: Dict[str, Any] = {
        "contentSelector": {
            "context": "Extended",
            "exposedFields": {
                "content": {"transcript": True},
                "parties": True,
            },
        },
        "filter": {
            "fromDateTime": from_date,
            "toDateTime": to_date,
            "parties": {
                "emailAddress": {"eq": user_email}
            },
        },
        "limit": limit,
    }

    response = await post("/v2/calls/extensive", payload)

    # The API returns { "calls": [...] }. Return the whole response for maximum flexibility.
    return response

async def get_call_transcripts(
    call_ids: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    workspace_id: Optional[str] = None,
    cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve transcripts for calls that took place during the specified date period.
    
    If call IDs are specified, only transcripts for calls with those IDs that took place 
    during the time period are returned.

    Parameters
    ----------
    call_ids : list[str], optional
        Gong call IDs whose transcripts should be fetched (max 100 per API call).
        If not provided, returns all calls in the specified date range.
    from_date : str, optional
        ISO-8601 date-time string for the start of the time window.  If omitted, defaults
        to 30 days in the past.
    to_date : str, optional
        ISO-8601 date-time string for the end of the time window.  If omitted, defaults
        to now.
    workspace_id : str, optional
        The Gong workspace ID to filter by.
    cursor : str, optional
        When paging is needed, provide the value supplied by the previous API call to 
        bring the following page of records.
    """
    logger.info(
        "Retrieving transcripts for %s calls",
        len(call_ids) if call_ids else "all"
    )

    if not from_date:
        from_date = (
            datetime.now(timezone.utc) - timedelta(days=30)
        ).isoformat(timespec="seconds")
    if not to_date:
        to_date = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Build the filter object (fromDateTime and toDateTime are required)
    filter_obj: Dict[str, Any] = {
        "fromDateTime": from_date,
        "toDateTime": to_date,
    }
    
    if call_ids:
        filter_obj["callIds"] = call_ids
    
    if workspace_id:
        filter_obj["workspaceId"] = workspace_id

    payload: Dict[str, Any] = {
        "filter": filter_obj,
    }
    
    if cursor:
        payload["cursor"] = cursor

    return await post("/v2/calls/transcript", payload) 