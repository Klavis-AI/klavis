import logging
import base64
from typing import Any, Dict, Optional
from .base import AffinityV1Client

# Configure logging
logger = logging.getLogger(__name__)

async def get_all_entity_files(
    person_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Get all Entity Files in Affinity.
    
    Args:
        person_id: Filter by person ID
        organization_id: Filter by organization ID
        opportunity_id: Filter by opportunity ID
        page_size: Number of items per page
        page_token: Token for pagination
    """
    logger.info("Executing tool: get_all_entity_files")
    try:
        params = {}
        if person_id:
            params["person_id"] = person_id
        if organization_id:
            params["organization_id"] = organization_id
        if opportunity_id:
            params["opportunity_id"] = opportunity_id
        if page_size:
            params["page_size"] = page_size
        if page_token:
            params["page_token"] = page_token
            
        return await AffinityV1Client.make_request("GET", "/entity-files", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_all_entity_files: {e}")
        raise e

async def get_entity_file(file_id: int) -> Dict[str, Any]:
    """Get a specific Entity File by ID.
    
    Args:
        file_id: Entity File ID
    """
    logger.info(f"Executing tool: get_entity_file with file_id: {file_id}")
    try:
        return await AffinityV1Client.make_request("GET", f"/entity-files/{file_id}")
    except Exception as e:
        logger.exception(f"Error executing tool get_entity_file: {e}")
        raise e

async def download_entity_file(file_id: int) -> Dict[str, Any]:
    """Download the content of a specific Entity File.
    
    Args:
        file_id: Entity File ID
    """
    logger.info(f"Executing tool: download_entity_file with file_id: {file_id}")
    try:
        # Use the dedicated download_file method that handles binary content and redirects
        response = await AffinityV1Client.download_file(f"/entity-files/download/{file_id}")
        
        # Add file_id to the response for reference
        response["file_id"] = file_id
        
        return response
    except Exception as e:
        logger.exception(f"Error executing tool download_entity_file: {e}")
        raise e

async def search_entity_files_by_name(
    filename_pattern: str,
    person_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    opportunity_id: Optional[int] = None
) -> Dict[str, Any]:
    """Search for Entity Files by filename pattern.
    
    Args:
        filename_pattern: Pattern to search for in filenames (case-insensitive)
        person_id: Filter by person ID
        organization_id: Filter by organization ID
        opportunity_id: Filter by opportunity ID
    """
    logger.info(f"Executing tool: search_entity_files_by_name with pattern: {filename_pattern}")
    try:
        # First get all files with the specified filters
        all_files = await get_all_entity_files(
            person_id=person_id,
            organization_id=organization_id,
            opportunity_id=opportunity_id
        )
        
        # Filter files by filename pattern
        if isinstance(all_files, list):
            files_list = all_files
        else:
            files_list = all_files.get('files', [])
        
        matching_files = []
        pattern_lower = filename_pattern.lower()
        
        for file_item in files_list:
            filename = file_item.get('name', '').lower()
            if pattern_lower in filename:
                matching_files.append(file_item)
        
        return {
            "matching_files": matching_files,
            "total_matches": len(matching_files),
            "search_pattern": filename_pattern
        }
        
    except Exception as e:
        logger.exception(f"Error executing tool search_entity_files_by_name: {e}")
        raise e
