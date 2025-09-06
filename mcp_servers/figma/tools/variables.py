import logging
from typing import Any, Dict, List, Optional
from .base import make_figma_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_local_variables(file_key: str) -> Dict[str, Any]:
    """Get local variables from a file."""
    logger.info(f"Executing tool: get_local_variables with file_key: {file_key}")
    try:
        endpoint = f"/v1/files/{file_key}/variables/local"
        
        variables_data = await make_figma_request("GET", endpoint)
        
        result = {
            "status": variables_data.get("status"),
            "error": variables_data.get("error"),
            "meta": variables_data.get("meta", {}),
            "variables": variables_data.get("variables", {}),
            "variableCollections": variables_data.get("variableCollections", {})
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_local_variables: {e}")
        return {
            "error": "Failed to retrieve local variables",
            "file_key": file_key,
            "exception": str(e)
        }

async def get_published_variables(file_key: str) -> Dict[str, Any]:
    """Get published variables from a file."""
    logger.info(f"Executing tool: get_published_variables with file_key: {file_key}")
    try:
        endpoint = f"/v1/files/{file_key}/variables/published"
        
        variables_data = await make_figma_request("GET", endpoint)
        
        result = {
            "status": variables_data.get("status"),
            "error": variables_data.get("error"),
            "meta": variables_data.get("meta", {}),
            "variables": variables_data.get("variables", {}),
            "variableCollections": variables_data.get("variableCollections", {})
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_published_variables: {e}")
        return {
            "error": "Failed to retrieve published variables",
            "file_key": file_key,
            "exception": str(e)
        }

async def post_variables(file_key: str, variableCollections: List[Dict[str, Any]], 
                        variables: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create or update variables in a file."""
    logger.info(f"Executing tool: post_variables with file_key: {file_key}")
    try:
        endpoint = f"/v1/files/{file_key}/variables"
        
        payload = {
            "variableCollections": variableCollections,
            "variables": variables
        }
        
        variables_data = await make_figma_request("POST", endpoint, json_data=payload)
        
        result = {
            "status": variables_data.get("status"),
            "error": variables_data.get("error"),
            "meta": variables_data.get("meta", {}),
            "variables": variables_data.get("variables", {}),
            "variableCollections": variables_data.get("variableCollections", {})
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool post_variables: {e}")
        return {
            "error": "Failed to create/update variables",
            "file_key": file_key,
            "exception": str(e)
        }