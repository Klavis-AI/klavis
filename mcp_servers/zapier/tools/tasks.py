"""
Zapier task tools.
"""

import logging
from typing import Any, Dict, Optional

import aiohttp
from .base import require_auth_token

logger = logging.getLogger(__name__)


async def list_tasks(
    workflow_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """List tasks, optionally filtered by workflow."""
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
        
        if workflow_id:
            params["workflow_id"] = workflow_id
        
        async with session.get(
            "https://api.zapier.com/v1/tasks",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to list tasks: {error_text}")


async def get_task(task_id: str) -> Dict[str, Any]:
    """Get details of a specific task."""
    token = require_auth_token()
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with session.get(
            f"https://api.zapier.com/v1/tasks/{task_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get task: {error_text}") 