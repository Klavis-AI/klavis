"""
Zapier webhook tools.
"""

import logging
from typing import Any, Dict, List, Optional

import aiohttp
from .base import require_auth_token

logger = logging.getLogger(__name__)


async def list_webhooks(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """List all webhooks in the Zapier account."""
    token = require_auth_token()
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        params = {
            "limit": limit,
            "offset": offset,
        }
        
        async with session.get(
            "https://api.zapier.com/v1/webhooks",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to list webhooks: {error_text}")


async def create_webhook(
    name: str,
    url: str,
    events: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a new webhook."""
    token = require_auth_token()
    
    data = {
        "name": name,
        "url": url,
    }
    
    if events:
        data["events"] = events
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with session.post(
            "https://api.zapier.com/v1/webhooks",
            headers=headers,
            json=data
        ) as response:
            if response.status == 201:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to create webhook: {error_text}")


async def get_webhook(webhook_id: str) -> Dict[str, Any]:
    """Get details of a specific webhook."""
    token = require_auth_token()
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with session.get(
            f"https://api.zapier.com/v1/webhooks/{webhook_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get webhook: {error_text}") 