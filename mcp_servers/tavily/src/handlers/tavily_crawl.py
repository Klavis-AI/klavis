import logging
import json
from typing import Any
from handlers.tavily_client import TavilyClient

logger = logging.getLogger(__name__)
tavily = TavilyClient()

async def tavily_crawl_handler(arguments: dict[str, Any]) -> str:
    try:
        # Validate required field
        if "url" not in arguments or not arguments["url"]:
            logger.warning("Missing required field: 'url'")
            raise ValueError("Missing required field: 'url'")

        # Required param
        payload = {
            "url": arguments["url"]
        }

        # Optional params
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
            ("include_images", arguments.get("include_images", False)),
            ("categories", arguments.get("categories", [])),
            ("extract_depth", arguments.get("extract_depth", "basic")),
            ("format", arguments.get("format", "markdown")),
            ("include_favicon", arguments.get("include_favicon", False)),
        ]

        for key, value in optional_params:
            if value is not None:
                payload[key] = value

        logger.info(f"Sending Tavily crawl request with payload: {json.dumps(payload)}")
        data = await tavily.post("/crawl", payload)
        logger.debug(f"Received response: {json.dumps(data)}")

        results = data.get("results", [])
        if not results:
            logger.info("No crawl results returned.")
            return "No crawl results returned."

        logger.info(f"Returning {len(results)} crawl results")
        return json.dumps(results, indent=2)

    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return f"Invalid input: {str(ve)}"

    except Exception as e:
        logger.exception("Unexpected error during Tavily crawl request")
        return f"Request failed: {str(e)}"
