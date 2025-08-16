"""
Discord Authentication Module

Handles Discord API authentication and request management.
"""

import os
import logging
from typing import Any, Dict, Optional

import aiohttp
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("discord-mcp-server")


class DiscordAuth:
    """Handles Discord API authentication and HTTP requests."""
    
    def __init__(self):
        """Initialize Discord authentication."""
        self.token = os.getenv("DISCORD_TOKEN")
        if not self.token:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        
        self.api_base = "https://discord.com/api/v10"
    
    def get_headers(self) -> Dict[str, str]:
        """Get standard headers for Discord API calls."""
        return {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }
    
    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict] = None, 
        expect_empty_response: bool = False
    ) -> Any:
        """
        Make an HTTP request to the Discord API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path (e.g., "/guilds/{guild_id}")
            json_data: JSON data to send in request body
            expect_empty_response: Whether to expect empty response (204)
            
        Returns:
            Response data as dict or None
            
        Raises:
            RuntimeError: If API request fails
        """
        url = f"{self.api_base}{endpoint}"
        headers = self.get_headers()
        
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.request(method, url, json=json_data) as response:
                    response.raise_for_status()
                    
                    if expect_empty_response:
                        if response.status == 204:
                            return None
                        else:
                            logger.warning(f"Expected empty response for {method} {endpoint}, but got status {response.status}")
                            try:
                                return await response.json()
                            except aiohttp.ContentTypeError:
                                return await response.text()
                    else:
                        # Check if response is JSON
                        if 'application/json' in response.headers.get('Content-Type', ''):
                            return await response.json()
                        else:
                            text_content = await response.text()
                            logger.warning(f"Received non-JSON response for {method} {endpoint}: {text_content[:100]}...")
                            return {"raw_content": text_content}
                            
            except aiohttp.ClientResponseError as e:
                logger.error(f"Discord API request failed: {e.status} {e.message} for {method} {url}")
                error_details = e.message
                try:
                    error_body = await e.response.json()
                    error_details = f"{e.message} - {error_body}"
                except Exception:
                    pass
                raise RuntimeError(f"Discord API Error ({e.status}): {error_details}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during Discord API request: {e}")
                raise RuntimeError(f"Unexpected error during API call to {method} {url}") from e
