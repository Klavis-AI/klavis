"""
Account management tools for HeyGen API.
"""

from typing import Dict, Any
from .base import make_request

async def heygen_get_remaining_credits() -> Dict[str, Any]:
    """
    Retrieve the remaining credits in your HeyGen account.
    
    Returns:
        Dict containing remaining credits information
    """
    response = await make_request("GET", "/v2/user/remaining_quota")
    
    # Convert quota to credits (quota ÷ 60 = credits)
    if "data" in response and "quota" in response["data"]:
        quota = response["data"]["quota"]
        credits = quota / 60
        response["data"]["credits"] = round(credits, 2)
    
    return response