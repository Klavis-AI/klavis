import logging
import json
from typing import Any
from handlers.tavily_client import TavilyClient

logger = logging.getLogger(__name__)
tavily = TavilyClient()

async def tavily_extract_handler(arguments: dict[str, Any]) -> str:
    try:
        # Validate required field
        if "urls" not in arguments or not arguments["urls"]:
            logger.warning("Missing required field: 'urls'")
            raise ValueError("Missing required field: 'urls'")

        payload = {
            "urls": arguments["urls"]
        }

        optional_params = [
            ("include_images", arguments.get("include_images")),
            ("include_favicon", arguments.get("include_favicon")),
            ("extract_depth", arguments.get("extract_depth", "basic")),
            ("format", arguments.get("format", "markdown")),
        ]

        for key, value in optional_params:
            if value is not None:
                payload[key] = value

        logger.info(f"Sending Tavily extract request with payload: {json.dumps(payload)}")
        data = await tavily.post("/extract", payload)
        logger.debug(f"Received response: {json.dumps(data)}")

        results = data.get("results", [])
        if not results:
            logger.info("No extract results returned.")
            return "No extract results returned."

        logger.info(f"Returning {len(results)} extract results")
        return json.dumps(results, indent=2)

    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return f"Invalid input: {str(ve)}"

    except Exception as e:
        logger.exception("Unexpected error during Tavily extract request")
        return f"Request failed: {str(e)}"
