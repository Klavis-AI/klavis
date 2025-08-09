import logging
import json
from typing import Any
from handlers.tavily_client import TavilyClient

logger = logging.getLogger(__name__)
tavily = TavilyClient()

async def tavily_map_handler(arguments: dict[str, Any]) -> str:
    try:
        # Validate required field
        if "url" not in arguments or not arguments["url"]:
            logger.warning("Missing required field: 'url'")
            raise ValueError("Missing required field: 'url'")

        payload = {
            "url": arguments["url"]
        }

        # Optional parameters with defaults
        optional_params = [
            ("instructions", arguments.get("instructions")),
            ("max_depth", arguments.get("max_depth")),
            ("max_breadth", arguments.get("max_breadth")),
            ("limit", arguments.get("limit")),
            ("select_paths", arguments.get("select_paths", [])),
            ("exclude_paths", arguments.get("exclude_paths", [])),
            ("select_domains", arguments.get("select_domains", [])),
            ("exclude_domains", arguments.get("exclude_domains", [])),
            ("allow_external", arguments.get("allow_external", True)),
            ("categories", arguments.get("categories", [])),
        ]

        for key, value in optional_params:
            if value is not None:
                payload[key] = value

        logger.info(f"Sending Tavily map request with payload: {json.dumps(payload)}")
        data = await tavily.post("/map", payload)
        logger.debug(f"Received response: {json.dumps(data)}")

        results = data.get("results", [])
        if not results:
            logger.info("No map results returned.")
            return "No map results returned."

        logger.info(f"Returning {len(results)} map results")
        return json.dumps(results, indent=2)

    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return f"Invalid input: {str(ve)}"

    except Exception as e:
        logger.exception("Unexpected error during Tavily map request")
        return f"Request failed: {str(e)}"
