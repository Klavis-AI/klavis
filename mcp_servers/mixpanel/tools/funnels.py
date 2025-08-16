import logging
import json
from typing import Any, Dict, List, Optional
import httpx

from .base import MixpanelQueryClient

logger = logging.getLogger(__name__)

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