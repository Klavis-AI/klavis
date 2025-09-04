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
        
        self.api_base = os.getenv("DISCORD_API_BASE", "https://discord.com/api/v10")
    
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
                    # Read text early so we can surface bodies for errors or non-JSON responses
                    raw_text = await response.text()
                    content_type = response.headers.get('Content-Type', '')

                    # Treat HTTP errors explicitly so callers receive helpful messages
                    if response.status >= 400:
                        try:
                            error_body = await response.json() if 'application/json' in content_type else raw_text
                        except Exception:
                            error_body = raw_text

                        logger.error(
                            "Discord API request failed: %s %s for %s %s",
                            response.status,
                            error_body,
                            method,
                            url,
                        )
                        raise RuntimeError(f"Discord API Error ({response.status}): {error_body}")

                    if expect_empty_response:
                        if response.status == 204:
                            return None
                        # unexpected non-empty response, try parsing
                        if 'application/json' in content_type:
                            return await response.json()
                        return {"raw_content": raw_text}

                    # Normal successful response
                    if 'application/json' in content_type:
                        return await response.json()
                    logger.warning(
                        "Received non-JSON response for %s %s: %s",
                        method,
                        endpoint,
                        raw_text[:100],
                    )
                    return {"raw_content": raw_text}

            except aiohttp.ClientError as e:
                logger.error(f"An aiohttp error occurred during Discord API request: {e}")
                raise RuntimeError(f"Network error during API call to {method} {url}: {e}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during Discord API request: {e}")
                raise RuntimeError(f"Unexpected error during API call to {method} {url}: {e}") from e
