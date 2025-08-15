import logging
from typing import Any, Dict, Optional
from datetime import date, timedelta

from .base import MixpanelQueryClient

logger = logging.getLogger(__name__)


async def run_retention_query(
    project_id: str,
    event: str,
    born_event: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    unit: Optional[str] = "day",
    retention_type: Optional[str] = "birth",
    interval_count: Optional[int] = None,
    metric: Optional[str] = "unique",
    where: Optional[str] = None,
    on: Optional[str] = None,
) -> Dict[str, Any]:
    """Run Mixpanel Retention query via Query API.

    Args:
        project_id: Mixpanel project id.
        event: Retention event to analyze.
        born_event: Cohort/born event. If not provided, defaults to the same as `event`.
        from_date: Start date (YYYY-MM-DD). Defaults to 30 days ago.
        to_date: End date (YYYY-MM-DD). Defaults to today.
        unit: One of {day, week, month}. Granularity for cohorts.
        retention_type: One of {birth, compounded}.
        interval_count: Number of intervals to include. Optional; API may infer from range.
        metric: One of {general, unique}. general = raw counts, unique = distinct users.
        where: Optional boolean expression filter.
        on: Optional segmentation property or computed key.

    Returns:
        Dict[str, Any] response as returned by Mixpanel Query API.
    """
    if not project_id:
        raise ValueError("project_id is required")
    if not event:
        raise ValueError("event is required")

    # Default dates: last 30 days
    if not to_date:
        to_date = date.today().strftime("%Y-%m-%d")
    if not from_date:
        from_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Normalize enums
    allowed_units = {"day", "week", "month"}
    allowed_metrics = {"general", "unique"}
    allowed_retention_types = {"birth", "compounded"}

    if unit not in allowed_units:
        raise ValueError(f"unit must be one of {sorted(allowed_units)}")
    if metric not in allowed_metrics:
        raise ValueError(f"metric must be one of {sorted(allowed_metrics)}")
    if retention_type not in allowed_retention_types:
        raise ValueError(f"retention_type must be one of {sorted(allowed_retention_types)}")

    params: Dict[str, Any] = {
        "project_id": str(project_id),
        "from_date": from_date,
        "to_date": to_date,
        "unit": unit,
        "metric": metric,
        "retention_type": retention_type,
    }

    # Mixpanel Query API commonly expects event names as JSON-encoded arrays in query params.
    params["event"] = f'[{event!r}]'
    params["born_event"] = f'[{(born_event or event)!r}]'

    if interval_count is not None:
        params["interval_count"] = int(interval_count)
    if where:
        params["where"] = where
    if on:
        params["on"] = on

    # Remove any Nones from params
    params = {k: v for k, v in params.items() if v is not None}

    try:
        endpoint = "/query/retention"
        result = await MixpanelQueryClient.make_request("GET", endpoint, params=params)
        return result
    except Exception as e:
        logger.exception("Error running retention query: %s", e)
        return {
            "success": False,
            "error": f"Failed to run retention query: {str(e)}",
            "params": params,
        }


