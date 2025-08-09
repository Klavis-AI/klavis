import logging
import json
from typing import Any
from handlers.tavily_client import TavilyClient

logger = logging.getLogger(__name__)
tavily = TavilyClient()

async def tavily_search_handler(arguments: dict[str, Any]) -> str:
    try:
        # Validate required fields
        if "query" not in arguments or not arguments["query"]:
            logger.warning("Missing required field: 'query'")
            raise ValueError("Missing required field: 'query'")

        payload = {
            "query": arguments["query"]
        }

        # Handle optional fields
        optional_params = [
            ("search_depth", arguments.get("search_depth")),
            ("topic", arguments.get("topic", "general")),
            ("days", arguments.get("days", 3)),
            ("time_range", arguments.get("time_range")),
            ("start_date", arguments.get("start_date")),
            ("end_date", arguments.get("end_date")),
            ("max_results", arguments.get("max_results", 10)),
            ("include_images", arguments.get("include_images", False)),
            ("include_image_descriptions", arguments.get("include_image_descriptions", False)),
            ("include_raw_content", arguments.get("include_raw_content", False)),
            ("include_domains", arguments.get("include_domains", [])),
            ("exclude_domains", arguments.get("exclude_domains", [])),
            ("country", arguments.get("country", "")),
            ("include_favicon", arguments.get("include_favicon", False)),
        ]

        for key, value in optional_params:
            if value is not None:
                payload[key] = value

        logger.info(f"Sending Tavily search request with payload: {json.dumps(payload)}")
        data = await tavily.post("/search", payload)
        logger.debug(f"Received response: {json.dumps(data)}")

        results = data.get("results", [])
        if not results:
            logger.info("No search results returned.")
            return "No search results returned."

        logger.info(f"Returning {len(results)} search results")
        return json.dumps(results, indent=2)

    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return f"Invalid input: {str(ve)}"

    except Exception as e:
        logger.exception("Unexpected error during Tavily search")
        return f"Request failed: {str(e)}"
