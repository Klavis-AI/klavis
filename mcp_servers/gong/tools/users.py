import logging
from typing import Any, Dict, Optional
import httpx

from .base import get, post

logger = logging.getLogger(__name__)

async def list_all_users(
    cursor: Optional[str] = None,
    include_avatars: bool = False,
) -> Dict[str, Any]:
    """List all of the company's users.
    
    When accessed through a Bearer token authorization method, this endpoint 
    requires the scope 'api:users:read'.
    
    Parameters
    ----------
    cursor : str, optional
        When paging is needed, provide the value supplied by the previous API call 
        to bring the following page of records.
    include_avatars : bool, optional
        Avatars are synthetic users representing Gong employees (CSMs and support 
        providers) when they access your instance. References to avatars' IDs may be 
        found in the outputs of other API endpoints. This parameter is optional, if 
        not provided avatars will not be included in the results.
    
    Returns
    -------
    Dict[str, Any]
        Response containing the list of users
    """
    params: Dict[str, Any] = {}
    
    if cursor:
        params["cursor"] = cursor
    if include_avatars:
        params["includeAvatars"] = include_avatars
        
    logger.info("Listing all users (include_avatars=%s)", include_avatars)
    
    return await get("/v2/users", params=params if params else None)


async def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """Retrieve a specific user.
    
    When accessed through a Bearer token authorization method, this endpoint 
    requires the scope 'api:users:read'.
    
    Parameters
    ----------
    user_id : str
        Gong's unique numeric identifier for the user (up to 20 digits).
    
    Returns
    -------
    Dict[str, Any]
        Response containing the user's details
    """
    if not user_id:
        raise ValueError("user_id is required")
    
    logger.info("Retrieving user with ID: %s", user_id)
    
    try:
        return await get(f"/v2/users/{user_id}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # 404 means user not found
            logger.info("User not found with ID: %s", user_id)
            return {
                "user": None,
                "message": "User not found"
            }
        else:
            # Re-raise other HTTP errors
            raise


async def get_user_settings_history(user_id: str) -> Dict[str, Any]:
    """Retrieve a specific user's settings history.
    
    When accessed through a Bearer token authorization method, this endpoint 
    requires the scope 'api:users:read'.
    
    Parameters
    ----------
    user_id : str
        Gong's unique numeric identifier for the user (up to 20 digits).
    
    Returns
    -------
    Dict[str, Any]
        Response containing the user's settings history
    """
    if not user_id:
        raise ValueError("user_id is required")
    
    logger.info("Retrieving settings history for user with ID: %s", user_id)
    
    try:
        return await get(f"/v2/users/{user_id}/settings-history")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # 404 means user not found
            logger.info("User not found with ID: %s", user_id)
            return {
                "settingsHistory": None,
                "message": "User not found"
            }
        else:
            # Re-raise other HTTP errors
            raise


async def list_users_by_filter(
    filter_data: Dict[str, Any],
    cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """List multiple Users by filter criteria.
    
    When accessed through a Bearer token authorization method, this endpoint 
    requires the scope 'api:users:read'.
    
    Parameters
    ----------
    filter_data : Dict[str, Any]
        Filter parameters to apply when listing users.
    cursor : str, optional
        When paging is needed, provide the value supplied by the previous API call 
        to bring the following page of records.
    
    Returns
    -------
    Dict[str, Any]
        Response containing the filtered list of users
    """
    if not filter_data:
        raise ValueError("filter_data is required")
    
    body: Dict[str, Any] = {
        "filter": filter_data
    }
    
    if cursor:
        body["cursor"] = cursor
        
    logger.info("Listing users by filter")
    
    try:
        return await post("/v2/users/extensive", body)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # 404 means no users found for the specified filter
            logger.info("No users found for the specified filter")
            return {
                "users": [],
                "records": {"totalRecords": 0, "currentPageSize": 0, "currentPageNumber": 1},
                "message": "No users found for the specified filter"
            }
        elif e.response.status_code == 429:
            # 429 means API request limit exceeded
            logger.warning("Gong API request limit exceeded")
            raise RuntimeError("Gong API request limit exceeded. Please try again later.") from e
        else:
            # Re-raise other HTTP errors
            raise

