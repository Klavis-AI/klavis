"""
Asset management tools for HeyGen API (voices, avatars, avatar groups).
"""

from typing import Dict, Any, Optional
from .base import make_request

async def heygen_get_voices(limit: Optional[int] = 20) -> Dict[str, Any]:
    """
    Retrieve a list of available voices from the HeyGen API.
    
    Args:
        limit: Maximum number of voices to return (default: 20)
    
    Returns:
        Dict containing list of available voices
    """
    response = await make_request("GET", "/v2/voices")
    
    # Limit the response to prevent context overflow
    if "data" in response and "voices" in response["data"] and limit is not None:
        original_count = len(response["data"]["voices"])
        if original_count > limit:
            response["data"]["voices"] = response["data"]["voices"][:limit]
            response["data"]["note"] = f"Showing first {limit} of {original_count} voices. Increase limit parameter to see more."
    
    return response

async def heygen_get_voice_locales(limit: Optional[int] = 20) -> Dict[str, Any]:
    """
    Retrieve a list of available voice locales (languages) from the HeyGen API.
    
    Args:
        limit: Maximum number of voice locales to return (default: 20)
    
    Returns:
        Dict containing list of available voice locales
    """
    response = await make_request("GET", "/v2/voices/locales")
    
    # Limit the response to prevent context overflow
    if "data" in response and "locales" in response["data"] and limit is not None:
        original_count = len(response["data"]["locales"])
        if original_count > limit:
            response["data"]["locales"] = response["data"]["locales"][:limit]
            response["data"]["note"] = f"Showing first {limit} of {original_count} voice locales. Increase limit parameter to see more."
    
    return response

async def heygen_get_avatar_groups() -> Dict[str, Any]:
    """
    Retrieve a list of HeyGen avatar groups.
    
    Returns:
        Dict containing list of avatar groups
    """
    return await make_request("GET", "/v2/avatar_group.list")

async def heygen_get_avatars_in_avatar_group(group_id: str) -> Dict[str, Any]:
    """
    Retrieve a list of avatars in a specific HeyGen avatar group.
    
    Args:
        group_id: The ID of the avatar group
        
    Returns:
        Dict containing list of avatars in the specified group
    """
    return await make_request("GET", f"/v2/avatar_groups/{group_id}/avatars")

async def heygen_list_avatars(limit: Optional[int] = 20) -> Dict[str, Any]:
    """
    Retrieve a list of all available avatars from the HeyGen API.
    This includes your instant avatars and public avatars.
    
    Args:
        limit: Maximum number of avatars to return (default: 20)
    
    Returns:
        Dict containing list of available avatars
    """
    response = await make_request("GET", "/v2/avatars")
    
    # Remove talking_photos array to reduce response size (always remove regardless of limit)
    if "data" in response and "talking_photos" in response["data"]:
        del response["data"]["talking_photos"]
    
    # Limit the response to prevent context overflow
    if "data" in response and "avatars" in response["data"] and limit is not None:
        original_count = len(response["data"]["avatars"])
        if original_count > limit:
            response["data"]["avatars"] = response["data"]["avatars"][:limit]
            response["data"]["note"] = f"Showing first {limit} of {original_count} avatars. Increase limit parameter to see more."
    
    return response