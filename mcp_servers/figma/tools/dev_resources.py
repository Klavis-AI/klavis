import logging
from typing import Any, Dict, List, Optional
from .base import make_figma_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_dev_resources(file_key: str, node_id: Optional[str] = None) -> Dict[str, Any]:
    """Get dev resources from a file."""
    logger.info(f"Executing tool: get_dev_resources with file_key: {file_key}")
    try:
        endpoint = f"/v1/files/{file_key}/dev_resources"
        params = {}
        
        if node_id:
            params["node_id"] = node_id
        
        dev_resources_data = await make_figma_request("GET", endpoint, params=params)
        
        result = {
            "dev_resources": []
        }
        
        for resource in dev_resources_data.get("dev_resources", []):
            resource_info = {
                "id": resource.get("id"),
                "name": resource.get("name"),
                "url": resource.get("url"),
                "node_id": resource.get("node_id"),
                "file_key": resource.get("file_key"),
                "created_at": resource.get("created_at"),
                "updated_at": resource.get("updated_at")
            }
            result["dev_resources"].append(resource_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_dev_resources: {e}")
        return {
            "error": "Failed to retrieve dev resources",
            "file_key": file_key,
            "exception": str(e)
        }

async def post_dev_resources(file_key: str, dev_resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create dev resources for a file."""
    logger.info(f"Executing tool: post_dev_resources with file_key: {file_key}")
    try:
        endpoint = f"/v1/files/{file_key}/dev_resources"
        
        payload = {
            "dev_resources": dev_resources
        }
        
        dev_resources_data = await make_figma_request("POST", endpoint, json_data=payload)
        
        result = {
            "dev_resources": []
        }
        
        for resource in dev_resources_data.get("dev_resources", []):
            resource_info = {
                "id": resource.get("id"),
                "name": resource.get("name"),
                "url": resource.get("url"),
                "node_id": resource.get("node_id"),
                "file_key": resource.get("file_key"),
                "created_at": resource.get("created_at"),
                "updated_at": resource.get("updated_at")
            }
            result["dev_resources"].append(resource_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool post_dev_resources: {e}")
        return {
            "error": "Failed to create dev resources",
            "file_key": file_key,
            "exception": str(e)
        }

async def put_dev_resource(dev_resource_id: str, name: Optional[str] = None, 
                          url: Optional[str] = None) -> Dict[str, Any]:
    """Update a dev resource."""
    logger.info(f"Executing tool: put_dev_resource with dev_resource_id: {dev_resource_id}")
    try:
        endpoint = f"/v1/dev_resources/{dev_resource_id}"
        
        payload = {}
        if name:
            payload["name"] = name
        if url:
            payload["url"] = url
        
        if not payload:
            return {
                "error": "No update parameters provided",
                "dev_resource_id": dev_resource_id
            }
        
        dev_resource_data = await make_figma_request("PUT", endpoint, json_data=payload)
        
        result = {
            "id": dev_resource_data.get("id"),
            "name": dev_resource_data.get("name"),
            "url": dev_resource_data.get("url"),
            "node_id": dev_resource_data.get("node_id"),
            "file_key": dev_resource_data.get("file_key"),
            "created_at": dev_resource_data.get("created_at"),
            "updated_at": dev_resource_data.get("updated_at")
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool put_dev_resource: {e}")
        return {
            "error": "Failed to update dev resource",
            "dev_resource_id": dev_resource_id,
            "exception": str(e)
        }

async def delete_dev_resource(dev_resource_id: str) -> Dict[str, Any]:
    """Delete a dev resource."""
    logger.info(f"Executing tool: delete_dev_resource with dev_resource_id: {dev_resource_id}")
    try:
        endpoint = f"/v1/dev_resources/{dev_resource_id}"
        
        await make_figma_request("DELETE", endpoint, expect_empty_response=True)
        
        result = {
            "status": "success",
            "message": f"Dev resource {dev_resource_id} has been deleted",
            "dev_resource_id": dev_resource_id
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool delete_dev_resource: {e}")
        return {
            "error": "Failed to delete dev resource",
            "dev_resource_id": dev_resource_id,
            "exception": str(e)
        }