from __future__ import annotations
import json
import os
import sys
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, HttpUrl, ValidationError

# Load .env locally if present (safe for dev; CI can inject env vars)
load_dotenv()

mcp = FastMCP("klavis-tavily")

TAVILY_API_BASE = "https://api.tavily.com"
API_KEY = os.getenv("TAVILY_API_KEY", "")

if not API_KEY:
    # Log to stderr only (never stdout in stdio servers)
    print(
        "[klavis-tavily] Warning: TAVILY_API_KEY not set; tools will return auth errors.",
        file=sys.stderr,
    )


class _SearchArgs(BaseModel):
    query: str = Field(..., description="Natural language search query.")
    max_results: int = Field(5, ge=1, le=20, description="Max number of results to return (1-20).")
    search_depth: str = Field(
        "advanced",
        pattern=r"^(basic|advanced)$",
        description="Depth of search: 'basic' or 'advanced'.",
    )
    include_answer: bool = Field(True, description="If true, include Tavily's synthesized answer.")
    include_raw_content: bool = Field(
        False, description="If true, include raw content snippets when available."
    )


class _ExtractArgs(BaseModel):
    urls: List[HttpUrl] = Field(..., description="One or more absolute URLs to extract.")
    extract_depth: str = Field(
        "basic",
        pattern=r"^(basic|advanced)$",
        description="Extraction depth: 'basic' or 'advanced'.",
    )
    format: str = Field(
        "markdown",
        pattern=r"^(markdown|text)$",
        description="Return format: 'markdown' or 'text'.",
    )
    include_images: bool = Field(False, description="If true, include image URLs in results.")
    include_favicon: bool = Field(False, description="If true, include site favicon URL in results.")


async def _tavily_request(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Helper for POSTing to Tavily with auth and basic error handling."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{TAVILY_API_BASE}{endpoint}", headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Return structured error the LLM can reason about
            return {
                "ok": False,
                "status_code": resp.status_code,
                "endpoint": endpoint,
                "error": str(e),
                "body": resp.text,
            }
        data = resp.json()
        return {"ok": True, "data": data}


@mcp.tool(
    description=(
        "Perform a Tavily web search and return structured results. "
        "Use for general web queries; supports answer synthesis and content snippets."
    )
)
async def tavily_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "advanced",
    include_answer: bool = True,
    include_raw_content: bool = False,
) -> Dict[str, Any]:
    """
    Perform a Tavily web search and return structured results.

    Args:
        query: Natural language search query.
        max_results: Max number of results (1-20).
        search_depth: 'basic' or 'advanced'.
        include_answer: If true, include Tavily's synthesized answer.
        include_raw_content: If true, return raw content snippets when available.
    """
    try:
        args = _SearchArgs(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
        )
    except ValidationError as ve:
        return {"ok": False, "error": "invalid_arguments", "details": json.loads(ve.json())}

    if not API_KEY:
        return {"ok": False, "error": "auth", "message": "TAVILY_API_KEY is not set."}

    # Use JSON mode so any future JSON-encodable types are converted safely
    payload = args.model_dump(mode="json")

    result = await _tavily_request("/search", payload)
    if not result.get("ok"):
        return result

    data = result["data"]
    # Normalize expected shape for the LLM
    normalized: Dict[str, Any] = {
        "query": args.query,
        "answer": data.get("answer"),
        "results": [],
    }
    for item in data.get("results", [])[: args.max_results]:
        normalized["results"].append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "score": item.get("score"),
                "content": item.get("content"),
            }
        )
    return {"ok": True, "data": normalized}


@mcp.tool(
    description=(
        "Extract main content from one or more URLs using Tavily Extract. "
        "Use after a search if you need full-page content (markdown or text)."
    )
)
async def tavily_extract(
    urls: List[str],
    extract_depth: str = "basic",
    format: str = "markdown",
    include_images: bool = False,
    include_favicon: bool = False,
) -> Dict[str, Any]:
    """
    Extract the main content from one or more URLs.

    Args:
        urls: Absolute URLs to extract.
        extract_depth: 'basic' or 'advanced'.
        format: 'markdown' or 'text'.
        include_images: Whether to include image URLs.
        include_favicon: Whether to include site favicon URLs.
    """
    try:
        args = _ExtractArgs(
            urls=urls,
            extract_depth=extract_depth,
            format=format,
            include_images=include_images,
            include_favicon=include_favicon,
        )
    except ValidationError as ve:
        return {"ok": False, "error": "invalid_arguments", "details": json.loads(ve.json())}

    if not API_KEY:
        return {"ok": False, "error": "auth", "message": "TAVILY_API_KEY is not set."}

    # Convert Pydantic types (e.g., HttpUrl) into JSON-safe values
    payload = args.model_dump(mode="json")
    # Defensive: ensure URLs are plain strings
    if "urls" in payload:
        payload["urls"] = [str(u) for u in payload["urls"]]

    result = await _tavily_request("/extract", payload)
    if not result.get("ok"):
        return result

    return {"ok": True, "data": result["data"]}


def main() -> None:
    # Run as stdio server (most common for local tools)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
