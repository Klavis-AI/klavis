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

async def get_call_transcripts(call_ids: List[str]) -> Dict[str, Any]:
    """Retrieve transcripts for specific call IDs.

    Parameters
    ----------
    call_ids : list[str]
        Gong call IDs whose transcripts should be fetched (max 100 per API call).
    """
    if not call_ids:
        raise ValueError("call_ids list cannot be empty")

    payload = {
        "callIds": call_ids,
    }

    logger.info("Retrieving transcripts for %s calls", len(call_ids))
    return await post("/v2/calls/transcript", payload) 