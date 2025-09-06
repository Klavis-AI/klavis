import logging
from typing import Any, Dict, List, Optional
from .base import make_figma_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_file(file_key: str, version: Optional[str] = None, ids: Optional[str] = None, 
                   depth: Optional[int] = None, geometry: Optional[str] = None, 
                   plugin_data: Optional[str] = None, branch_data: Optional[bool] = None) -> Dict[str, Any]:
    """Get file content by file key."""
    logger.info(f"Executing tool: get_file with file_key: {file_key}")
    try:
        endpoint = f"/v1/files/{file_key}"
        params = {}
        
        if version:
            params["version"] = version
        if ids:
            params["ids"] = ids
        if depth is not None:
            params["depth"] = depth
        if geometry:
            params["geometry"] = geometry
        if plugin_data:
            params["plugin_data"] = plugin_data
        if branch_data is not None:
            params["branch_data"] = branch_data
        
        file_data = await make_figma_request("GET", endpoint, params=params)
        
        result = {
            "name": file_data.get("name"),
            "role": file_data.get("role"),
            "lastModified": file_data.get("lastModified"),
            "editorType": file_data.get("editorType"),
            "thumbnailUrl": file_data.get("thumbnailUrl"),
            "version": file_data.get("version"),
            "document": file_data.get("document", {}),
            "components": file_data.get("components", {}),
            "componentSets": file_data.get("componentSets", {}),
            "schemaVersion": file_data.get("schemaVersion"),
            "styles": file_data.get("styles", {}),
            "mainFileKey": file_data.get("mainFileKey"),
            "branches": file_data.get("branches", [])
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_file: {e}")
        return {
            "error": "Failed to retrieve file",
            "file_key": file_key,
            "exception": str(e)
        }

async def get_file_nodes(file_key: str, ids: str, version: Optional[str] = None, 
                        depth: Optional[int] = None, geometry: Optional[str] = None, 
                        plugin_data: Optional[str] = None) -> Dict[str, Any]:
    """Get specific nodes from a file."""
    logger.info(f"Executing tool: get_file_nodes with file_key: {file_key}, ids: {ids}")
    try:
        endpoint = f"/v1/files/{file_key}/nodes"
        params = {"ids": ids}
        
        if version:
            params["version"] = version
        if depth is not None:
            params["depth"] = depth
        if geometry:
            params["geometry"] = geometry
        if plugin_data:
            params["plugin_data"] = plugin_data
        
        nodes_data = await make_figma_request("GET", endpoint, params=params)
        
        result = {
            "name": nodes_data.get("name"),
            "role": nodes_data.get("role"),
            "lastModified": nodes_data.get("lastModified"),
            "editorType": nodes_data.get("editorType"),
            "thumbnailUrl": nodes_data.get("thumbnailUrl"),
            "version": nodes_data.get("version"),
            "nodes": nodes_data.get("nodes", {}),
            "err": nodes_data.get("err")
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_file_nodes: {e}")
        return {
            "error": "Failed to retrieve file nodes",
            "file_key": file_key,
            "node_ids": ids,
            "exception": str(e)
        }

async def get_file_images(file_key: str, ids: str, scale: Optional[float] = None, 
                         format: Optional[str] = None, svg_include_id: Optional[bool] = None,
                         svg_simplify_stroke: Optional[bool] = None, use_absolute_bounds: Optional[bool] = None,
                         version: Optional[str] = None) -> Dict[str, Any]:
    """Get images from specific nodes in a file."""
    logger.info(f"Executing tool: get_file_images with file_key: {file_key}, ids: {ids}")
    try:
        endpoint = f"/v1/images/{file_key}"
        params = {"ids": ids}
        
        if scale is not None:
            params["scale"] = scale
        if format:
            params["format"] = format
        if svg_include_id is not None:
            params["svg_include_id"] = svg_include_id
        if svg_simplify_stroke is not None:
            params["svg_simplify_stroke"] = svg_simplify_stroke
        if use_absolute_bounds is not None:
            params["use_absolute_bounds"] = use_absolute_bounds
        if version:
            params["version"] = version
        
        images_data = await make_figma_request("GET", endpoint, params=params)
        
        result = {
            "err": images_data.get("err"),
            "images": images_data.get("images", {}),
            "status": images_data.get("status")
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_file_images: {e}")
        return {
            "error": "Failed to retrieve file images",
            "file_key": file_key,
            "node_ids": ids,
            "exception": str(e)
        }

async def get_file_versions(file_key: str) -> Dict[str, Any]:
    """Get version history for a file."""
    logger.info(f"Executing tool: get_file_versions with file_key: {file_key}")
    try:
        endpoint = f"/v1/files/{file_key}/versions"
        
        versions_data = await make_figma_request("GET", endpoint)
        
        result = {
            "versions": []
        }
        
        for version in versions_data.get("versions", []):
            version_info = {
                "id": version.get("id"),
                "created_at": version.get("created_at"),
                "label": version.get("label"),
                "description": version.get("description"),
                "user": version.get("user", {}),
                "thumbnail_url": version.get("thumbnail_url")
            }
            result["versions"].append(version_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_file_versions: {e}")
        return {
            "error": "Failed to retrieve file versions",
            "file_key": file_key,
            "exception": str(e)
        }