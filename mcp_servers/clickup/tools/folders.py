import logging
from typing import Any, Dict, Optional
from .base import make_clickup_request
from .normalize import normalize_folders, normalize_folder

# Configure logging
logger = logging.getLogger(__name__)

async def get_folders(space_id: str) -> Dict[str, Any]:
    """Get all folders in a space."""
    logger.info(f"Executing tool: get_folders with space_id: {space_id}")
    try:
        result = await make_clickup_request(f"space/{space_id}/folder")
        return normalize_folders(result)
    except Exception as e:
        logger.exception(f"Error executing tool get_folders: {e}")
        raise e

async def create_folder(space_id: str, name: str) -> Dict[str, Any]:
    """Create a new folder in a space."""
    logger.info(f"Executing tool: create_folder with name: {name}")
    try:
        data = {"name": name}
        result = await make_clickup_request(f"space/{space_id}/folder", "POST", data)
        return normalize_folder(result)
    except Exception as e:
        logger.exception(f"Error executing tool create_folder: {e}")
        raise e

async def update_folder(folder_id: str, name: str) -> Dict[str, Any]:
    """Update an existing folder."""
    logger.info(f"Executing tool: update_folder with folder_id: {folder_id}")
    try:
        data = {"name": name}
        result = await make_clickup_request(f"folder/{folder_id}", "PUT", data)
        return normalize_folder(result)
    except Exception as e:
        logger.exception(f"Error executing tool update_folder: {e}")
        raise e 