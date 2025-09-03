"""
Zapier workflow tools.
"""

import logging
from typing import Any, Dict, List, Optional

import aiohttp
from .base import require_auth_token

logger = logging.getLogger(__name__)


async def list_workflows(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """List all workflows in the Zapier account."""
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
            "https://api.zapier.com/v1/workflows",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to list workflows: {error_text}")


async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """Get details of a specific workflow."""
    token = require_auth_token()
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with session.get(
            f"https://api.zapier.com/v1/workflows/{workflow_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get workflow: {error_text}")


async def create_workflow(
    name: str,
    description: str,
    steps: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Create a new workflow."""
    token = require_auth_token()
    
    data = {
        "name": name,
        "description": description,
    }
    
    if steps:
        data["steps"] = steps
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with session.post(
            "https://api.zapier.com/v1/workflows",
            headers=headers,
            json=data
        ) as response:
            if response.status == 201:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to create workflow: {error_text}")


async def update_workflow(
    workflow_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    steps: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Update an existing workflow."""
    token = require_auth_token()
    
    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if steps is not None:
        data["steps"] = steps
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with session.put(
            f"https://api.zapier.com/v1/workflows/{workflow_id}",
            headers=headers,
            json=data
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to update workflow: {error_text}")


async def delete_workflow(workflow_id: str) -> Dict[str, Any]:
    """Delete a workflow."""
    token = require_auth_token()
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with session.delete(
            f"https://api.zapier.com/v1/workflows/{workflow_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to delete workflow: {error_text}")


async def trigger_workflow(
    workflow_id: str,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Trigger a workflow manually."""
    token = require_auth_token()
    
    payload = {}
    if data:
        payload["data"] = data
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with session.post(
            f"https://api.zapier.com/v1/workflows/{workflow_id}/trigger",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to trigger workflow: {error_text}") 