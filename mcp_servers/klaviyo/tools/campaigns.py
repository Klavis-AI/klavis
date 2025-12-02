from typing import Any, Dict
from .base import _async_request, _async_paginate_get



async def get_campaigns(channel: str) -> dict:
    """
    Retrieve campaigns from Klaviyo filtered by channel.

    You must provide one of these channels:
    - 'email' → For email campaigns
    - 'sms' → For SMS campaigns
    - 'mobile_push' → For mobile push campaigns
    """
    valid_channels = ["email", "sms", "mobile_push"]
    if channel not in valid_channels:
        raise ValueError(f"Invalid channel '{channel}'. Must be one of {valid_channels}")

    params = {"filter": f"equals(messages.channel,'{channel}')"}
    campaigns = await _async_paginate_get("/campaigns", params=params)
    return {"campaigns": campaigns}



async def create_campaign(campaign_data: Dict[str, Any]) -> dict:
    """
    Create a new campaign in Klaviyo.

    Args:
        campaign_data: A dictionary following Klaviyo's campaign creation schema.
                       See: https://developers.klaviyo.com/en/reference/create_campaign
    """
    payload = {"data": {"type": "campaign", "attributes": campaign_data}}
    return await _async_request("POST", "/campaigns", json=payload)



async def get_campaign(campaign_id: str) -> dict:
    """
    Retrieve a specific campaign by ID from Klaviyo.

    Args:
        campaign_id: The ID of the campaign to retrieve.
    """
    return await _async_request("GET", f"/campaigns/{campaign_id}")
