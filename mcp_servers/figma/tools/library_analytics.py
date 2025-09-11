import logging
from typing import Any, Dict, List, Optional
from .base import make_figma_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_library_analytics(file_key: str) -> Dict[str, Any]:
    """Get analytics data for a published library."""
    logger.info(f"Executing tool: get_library_analytics with file_key: {file_key}")
    try:
        endpoint = f"/v1/files/{file_key}/library_analytics"
        
        analytics_data = await make_figma_request("GET", endpoint)
        
        result = {
            "meta": analytics_data.get("meta", {}),
            "components": [],
            "component_sets": [],
            "styles": []
        }
        
        # Process components analytics
        for component in analytics_data.get("components", []):
            component_info = {
                "node_id": component.get("node_id"),
                "name": component.get("name"),
                "created_at": component.get("created_at"),
                "updated_at": component.get("updated_at"),
                "usage_count": component.get("usage_count", 0),
                "consuming_teams_count": component.get("consuming_teams_count", 0)
            }
            result["components"].append(component_info)
        
        # Process component sets analytics
        for component_set in analytics_data.get("component_sets", []):
            component_set_info = {
                "node_id": component_set.get("node_id"),
                "name": component_set.get("name"),
                "created_at": component_set.get("created_at"),
                "updated_at": component_set.get("updated_at"),
                "usage_count": component_set.get("usage_count", 0),
                "consuming_teams_count": component_set.get("consuming_teams_count", 0)
            }
            result["component_sets"].append(component_set_info)
        
        # Process styles analytics
        for style in analytics_data.get("styles", []):
            style_info = {
                "node_id": style.get("node_id"),
                "name": style.get("name"),
                "style_type": style.get("style_type"),
                "created_at": style.get("created_at"),
                "updated_at": style.get("updated_at"),
                "usage_count": style.get("usage_count", 0),
                "consuming_teams_count": style.get("consuming_teams_count", 0)
            }
            result["styles"].append(style_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_library_analytics: {e}")
        return {
            "error": "Failed to retrieve library analytics",
            "file_key": file_key,
            "note": "Make sure this is a published library file and you have access to analytics",
            "exception": str(e)
        }