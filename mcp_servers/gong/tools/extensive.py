import logging
from typing import Any, Dict, List, Optional

from .base import post

logger = logging.getLogger(__name__)

async def get_extensive_data(
    call_ids: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    user_ids: Optional[List[str]] = None,
    workspace_id: Optional[str] = None,
    cursor: Optional[str] = None,
    context: str = "Extended",
    context_timing: Optional[List[str]] = None,
    exposed_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Retrieve extensive call data by various filters.

    Parameters
    ----------
    call_ids : list[str], optional
        List of Gong call IDs to fetch.
    from_date : str, optional
        ISO-8601 formatted datetime to filter calls from (e.g., '2018-02-18T02:30:00-07:00').
    to_date : str, optional
        ISO-8601 formatted datetime to filter calls until (e.g., '2018-02-18T08:00:00Z').
    user_ids : list[str], optional
        List of user IDs to filter calls hosted by these users.
    workspace_id : str, optional
        Workspace identifier to filter calls.
    cursor : str, optional
        Pagination cursor returned by a previous request.
    context : str, optional
        Context level: "None", "Extended", etc. (default "Extended").
    context_timing : list[str], optional
        Context timing values (e.g., ["Now"]).
    exposed_fields : dict, optional
        Custom exposedFields structure. If not provided, uses default with parties and basic content.
    """

    # Build filter object based on provided parameters
    filter_obj: Dict[str, Any] = {}
    
    if call_ids:
        filter_obj["callIds"] = call_ids
    
    if from_date and to_date:
        filter_obj["fromDateTime"] = from_date
        filter_obj["toDateTime"] = to_date
    
    if user_ids:
        filter_obj["primaryUserIds"] = user_ids
    
    if workspace_id:
        filter_obj["workspaceId"] = workspace_id

    # At least one filter criterion must be provided
    if not filter_obj:
        raise ValueError("At least one filter parameter must be provided (call_ids, date range, or user_ids)")

    logger.info("Executing get_extensive_data with filters: %s", filter_obj)

    # Build contentSelector
    content_selector: Dict[str, Any] = {
        "context": context,
    }
    
    if context_timing:
        content_selector["contextTiming"] = context_timing
    
    # Use custom exposedFields if provided, otherwise use defaults
    if exposed_fields:
        content_selector["exposedFields"] = exposed_fields
    else:
        # Default: include parties and basic content
        content_selector["exposedFields"] = {
            "parties": True,
            "content": {
                "brief": True,
                "outline": True,
                "highlights": True,
            }
        }

    # Build the request payload according to API spec
    payload: Dict[str, Any] = {
        "filter": filter_obj,
        "contentSelector": content_selector,
    }
    
    if cursor:
        payload["cursor"] = cursor

    return await post("/v2/calls/extensive", payload) 