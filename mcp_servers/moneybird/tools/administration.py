import logging
from typing import Any, Dict
from .base import get_auth_token, MONEYBIRD_API_ENDPOINT
import httpx

# Configure logging
logger = logging.getLogger(__name__)

async def moneybird_list_administrations() -> Dict[str, Any]:
    """List all administrations that the authenticated user has access to."""
    logger.info("Executing tool: moneybird_list_administrations")
    
    api_key = get_auth_token()
    
    if not api_key:
        raise RuntimeError("No API key provided. Please set the x-auth-token header.")
    
    # Administrations endpoint is at the root level, no administration_id needed
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # The administrations endpoint doesn't require an administration_id
    url = f"{MONEYBIRD_API_ENDPOINT}/administrations"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            try:
                json_response = response.json()
                if json_response is None:
                    return {"data": None, "message": "API returned null response"}
                return json_response
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response.content}")
                return {"error": "Invalid JSON response", "content": response.text}
                
    except Exception as e:
        logger.exception(f"Error executing tool moneybird_list_administrations: {e}")
        raise e