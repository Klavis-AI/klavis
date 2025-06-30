import logging
import os
from typing import Optional

import aiohttp
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

AIRTABLE_PERSONAL_ACCESS_TOKEN = os.getenv("AIRTABLE_PERSONAL_ACCESS_TOKEN")
if not AIRTABLE_PERSONAL_ACCESS_TOKEN:
    raise ValueError("AIRTABLE_PERSONAL_ACCESS_TOKEN environment variable is required")

AIRTABLE_API_BASE = "https://api.airtable.com/v0"


def _get_airtable_headers() -> dict:
    """Get the standard headers for Airtable API requests."""
    return {
        "Authorization": f"Bearer {AIRTABLE_PERSONAL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


async def make_airtable_request(
    method: str,
    endpoint: str,
    json_data: Optional[dict] = None,
    expect_empty_response: bool = False,
) -> dict | None:
    """Make a request to the Airtable API."""
    url = f"{AIRTABLE_API_BASE}/{endpoint}"
    headers = _get_airtable_headers()
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.request(method, url, json=json_data) as response:
                response.raise_for_status()  # Raise exception for non-2xx status codes
                if expect_empty_response:
                    # For requests like DELETE or PUT roles/reactions where success is 204 No Content
                    if response.status == 204:
                        return None
                    else:
                        # If we expected empty but got something else (and it wasn't an error raised above)
                        logger.warning(
                            f"Expected empty response for {method} {endpoint}, but got status {response.status}"
                        )
                        # Try to parse JSON anyway, might be useful error info
                        try:
                            return await response.json()
                        except aiohttp.ContentTypeError:
                            return await response.text()  # Return text if not json
                else:
                    # Check if response is JSON before parsing
                    if "application/json" in response.headers.get("Content-Type", ""):
                        return await response.json()
                    else:
                        # Handle non-JSON responses if necessary, e.g., log or return text
                        text_content = await response.text()
                        logger.warning(
                            f"Received non-JSON response for {method} {endpoint}: {text_content[:100]}..."
                        )
                        return {"raw_content": text_content}
        except aiohttp.ClientResponseError as e:
            logger.error(
                f"Airtable API request failed: {e.status} {e.message} for {method} {url}"
            )
            error_details = e.message
            try:
                # Airtable often returns JSON errors
                error_body = await e.response.json()
                error_details = f"{e.message} - {error_body}"
            except Exception:
                # If response body isn't JSON or can't be read
                pass
            raise RuntimeError(
                f"Airtable API Error ({e.status}): {error_details}"
            ) from e
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during Airtable API request: {e}"
            )
            raise RuntimeError(
                f"Unexpected error during API call to {method} {url}"
            ) from e
