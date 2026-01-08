import logging
from typing import Any, Dict
from .base import _async_request

logger = logging.getLogger(__name__)





async def get_profile(email: str) -> dict:
    """
    Retrieve profile(s) by email. Uses Klaviyo Profiles API with filter.
    """
    params = {"filter": f"equals(email,'{email}')"}
    return await _async_request("GET", "/profiles", params=params)


async def create_or_update_profile_single(email: str, attributes: Dict[str, Any] = None) -> dict:
    """
    Create a single Klaviyo profile (server-side).
    Uses Profiles API create endpoint.
    """
    if attributes is None:
        attributes = {}
    attributes['email'] = email
    payload = {"data": {"type": "profile", "attributes": attributes}}
    return await _async_request("POST", "/profiles", json=payload)