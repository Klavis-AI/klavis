import logging
from typing import Any, Dict, Optional

from .base import MixpanelQueryClient

logger = logging.getLogger(__name__)


async def run_segmentation_query(
    project_id: str,
    event: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    unit: Optional[str] = "day",
    type: Optional[str] = "general",
    where: Optional[str] = None,
    on: Optional[str] = None,
    numerical_aggregation: Optional[str] = None,
) -> Dict[str, Any]:
    """Run Mixpanel Segmentation query via Query API.

    Args:
        project_id: Mixpanel project id.
        event: Event name to analyze.
        from_date: Start date (YYYY-MM-DD). Defaults to None (defer to server defaults).
        to_date: End date (YYYY-MM-DD). Defaults to None (defer to server defaults).
        unit: One of {hour, day, month}. Time bucketing for results.
        type: One of {general, unique}. general = raw counts, unique = distinct users.
        where: Optional boolean expression filter.
        on: Optional segmentation property or computed key.
        numerical_aggregation: Optional numeric aggregation when grouping by numeric field.

    Returns:
        Dict[str, Any] response as returned by Mixpanel Query API.
    """
    if not project_id:
        raise ValueError("project_id is required")
    if not event:
        raise ValueError("event is required")

    # Dates are optional; if omitted, allow API/server defaults to apply

    # Normalize enums
    allowed_units = {"hour", "day", "month"}
    allowed_types = {"general", "unique"}
    allowed_num_aggs = {"sum", "average", "buckets"}

    if unit not in allowed_units:
        raise ValueError(f"unit must be one of {sorted(allowed_units)}")
    if type not in allowed_types:
        raise ValueError(f"type must be one of {sorted(allowed_types)}")
    if numerical_aggregation is not None and numerical_aggregation not in allowed_num_aggs:
        raise ValueError(f"numerical_aggregation must be one of {sorted(allowed_num_aggs)}")

    # Build params for Query API. Use the stable 2.0 segmentation path.
    params: Dict[str, Any] = {
        "event": event,
        "project_id": str(project_id),
        "from_date": from_date,
        "to_date": to_date,
        "unit": unit,
        "type": type,
    }

    if where:
        params["where"] = where
    if on:
        params["on"] = on
    if numerical_aggregation:
        params["numerical_aggregation"] = numerical_aggregation

    # Remove any Nones from params
    params = {k: v for k, v in params.items() if v is not None}
        
    try:
        # Use Query API segmentation endpoint under https://mixpanel.com/api
        endpoint = "/query/segmentation"
        result = await MixpanelQueryClient.make_request("GET", endpoint, params=params)
        return result
    except Exception as e:
        logger.exception("Error running segmentation query: %s", e)
        return {
            "success": False,
            "error": f"Failed to run segmentation query: {str(e)}",
            "params": params,
        }


