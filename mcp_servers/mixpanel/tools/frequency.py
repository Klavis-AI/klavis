import logging
from typing import Any, Dict, Optional
from datetime import date, timedelta

from .base import MixpanelQueryClient

logger = logging.getLogger(__name__)


async def run_frequency_query(
    project_id: str,
    event: str,
    born_event: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    unit: Optional[str] = "day",
    addiction_unit: Optional[str] = "hour",
    metric: Optional[str] = "unique",
    where: Optional[str] = None,
    on: Optional[str] = None,
) -> Dict[str, Any]:
    """Run Mixpanel Frequency (Addiction) query via Query API.

    Args:
        project_id: Mixpanel project id.
        event: Retention event to analyze.
        born_event: Cohort/born event. If not provided, defaults to the same as `event`.
        from_date: Start date (YYYY-MM-DD). Defaults to 30 days ago.
        to_date: End date (YYYY-MM-DD). Defaults to today.
        unit: One of {day, week, month}. Granularity of cohorts/time buckets.
        addiction_unit: One of {hour, day, week}. Sub-interval used for frequency bins.
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
    allowed_addiction_units = {"hour", "day", "week"}
    allowed_metrics = {"general", "unique"}

    if unit not in allowed_units:
        raise ValueError(f"unit must be one of {sorted(allowed_units)}")
    if addiction_unit not in allowed_addiction_units:
        raise ValueError(f"addiction_unit must be one of {sorted(allowed_addiction_units)}")
    if metric not in allowed_metrics:
        raise ValueError(f"metric must be one of {sorted(allowed_metrics)}")

    # Build params for Query API. Endpoint path aligns with other /query/* calls in this project.
    params: Dict[str, Any] = {
        "project_id": project_id,
        "from_date": from_date,
        "to_date": to_date,
        "unit": unit,
        "addiction_unit": addiction_unit,
        "metric": metric,
    }

    # Mixpanel Query API commonly expects event names as JSON-encoded arrays in query params.
    # Provide both single-string fallback and encoded-array form for broader compatibility.
    params["event"] = f'[{event!r}]' if event else None
    if born_event:
        params["born_event"] = f'[{born_event!r}]'
    else:
        params["born_event"] = f'[{event!r}]'

    if where:
        params["where"] = where
    if on:
        params["on"] = on

    # Remove any Nones from params
    params = {k: v for k, v in params.items() if v is not None}

    # Execute request
    try:
        # Endpoint chosen to match Query API naming used elsewhere (e.g., /query/events/names)
        endpoint = "/query/retention/frequency"
        result = await MixpanelQueryClient.make_request("GET", endpoint, params=params)
        return result
    except Exception as e:
        logger.exception("Error running frequency query: %s", e)
        return {
            "success": False,
            "error": f"Failed to run frequency query: {str(e)}",
            "params": params,
        }


