from .base import _async_request, _async_paginate_get


async def get_flows() -> dict:
    """
    Retrieve all flows (paginated).

    Example natural language triggers:
    - "Show me all flows in Klaviyo"
    - "List automation flows"
    """
    flows = await _async_paginate_get("/flows")
    return {"flows": flows}
