from .base import _async_request


async def get_metrics() -> dict:
    """List all standard metrics available in the Klaviyo account."""
    return await _async_request("GET", "/metrics")


async def get_custom_metrics() -> dict:
    """List all custom metrics available in the Klaviyo account."""
    return await _async_request("GET", "/custom-metrics")
