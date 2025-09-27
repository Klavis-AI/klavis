"""
Zapier app tools.
"""

import logging
from typing import Any, Dict, Optional

import aiohttp
from .base import require_auth_token

logger = logging.getLogger(__name__)


async def list_apps(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """List available apps in Zapier."""
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
            "https://api.zapier.com/v1/apps",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to list apps: {error_text}")


async def get_app(app_id: str) -> Dict[str, Any]:
    """Get details of a specific app."""
    token = require_auth_token()
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with session.get(
            f"https://api.zapier.com/v1/apps/{app_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get app: {error_text}")


async def connect_app(
    app_id: str,
    auth_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Connect an app to your Zapier account."""
    token = require_auth_token()
    
    data = {}
    if auth_data:
        data["auth_data"] = auth_data
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with session.post(
            f"https://api.zapier.com/v1/apps/{app_id}/connect",
            headers=headers,
            json=data
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to connect app: {error_text}") 