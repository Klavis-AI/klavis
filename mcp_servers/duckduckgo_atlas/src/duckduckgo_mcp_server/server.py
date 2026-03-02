#!/usr/bin/env python
"""
DuckDuckGo MCP Server
A Model Context Protocol (MCP) server for searching via DuckDuckGo.
"""

import base64
import contextlib
import json
import logging
import os
import re
import sys
import traceback
import urllib.parse
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS

logger = logging.getLogger(__name__)


def _get_proxy_url() -> Optional[str]:
    """Build proxy URL from environment variables.

    Env vars:
      PROXY_USERNAME, PROXY_PASSWORD  – required
      PROXY_HOST   – default: p.webshare.io
      PROXY_PORT   – default: 1080
      PROXY_SCHEME – default: socks5
    """
    username = os.environ.get("PROXY_USERNAME")
    password = os.environ.get("PROXY_PASSWORD")
    if not (username and password):
        return None
    host = os.environ.get("PROXY_HOST", "p.webshare.io")
    scheme = os.environ.get("PROXY_SCHEME", "http")
    port = os.environ.get("PROXY_PORT", "1080" if "socks" in scheme else "80")
    return f"{scheme}://{username}:{password}@{host}:{port}"


# DuckDuckGo does not require authentication, but we follow the auth extraction
# pattern for consistency with other MCP servers.

def _get_header(request_or_scope, header_name: bytes) -> Optional[str]:
    """Extract a raw header value from a request object or scope dict."""
    header_bytes = header_name if isinstance(header_name, bytes) else header_name.encode('utf-8')
    header_str = header_bytes.decode('utf-8')

    if hasattr(request_or_scope, 'headers'):
        headers = request_or_scope.headers
    elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
        headers = dict(request_or_scope.get("headers", []))
    else:
        return None

    return headers.get(header_str) or headers.get(header_bytes)


def extract_auth_info(request_or_scope) -> dict:
    """Extract auth info from x-auth-data header (for pattern consistency)."""
    auth_data = os.getenv("AUTH_DATA")

    if not auth_data:
        raw = _get_header(request_or_scope, b'x-auth-data')
        if raw:
            if isinstance(raw, bytes):
                auth_data = base64.b64decode(raw).decode('utf-8')
            else:
                auth_data = base64.b64decode(raw).decode('utf-8')

    if not auth_data:
        return {}

    try:
        return json.loads(auth_data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return {}


@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str
    position: int


class DuckDuckGoSearcher:
    """Uses the duckduckgo-search library (primp browser impersonation)
    to avoid CAPTCHAs that raw httpx requests trigger."""

    def format_results_for_llm(self, results: List[SearchResult]) -> str:
        if not results:
            return "No results were found for your search query. This could be due to DuckDuckGo's bot detection or the query returned no matches. Please try rephrasing your search or try again in a few minutes."

        output = []
        output.append(f"Found {len(results)} search results:\n")

        for result in results:
            output.append(f"{result.position}. {result.title}")
            output.append(f"   URL: {result.link}")
            output.append(f"   Summary: {result.snippet}")
            output.append("")

        return "\n".join(output)

    async def search(
        self, query: str, ctx: Context, max_results: int = 10
    ) -> List[SearchResult]:
        try:
            await ctx.info(f"Searching DuckDuckGo for: {query}")

            proxy = _get_proxy_url()
            ddgs = DDGS(proxy=proxy)
            raw_results = ddgs.text(query, max_results=max_results, backend="duckduckgo")

            results = [
                SearchResult(
                    title=r.get("title", ""),
                    link=r.get("href", ""),
                    snippet=r.get("body", ""),
                    position=i + 1,
                )
                for i, r in enumerate(raw_results)
            ]

            await ctx.info(f"Successfully found {len(results)} results")
            return results

        except Exception as e:
            await ctx.error(f"Search error: {e}")
            traceback.print_exc(file=sys.stderr)
            return []


class WebContentFetcher:
    async def fetch_and_parse(self, url: str, ctx: Context) -> str:
        try:
            await ctx.info(f"Fetching content from: {url}")

            proxy = _get_proxy_url()
            async with httpx.AsyncClient(proxy=proxy) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    follow_redirects=True,
                    timeout=30.0,
                )
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)
            text = re.sub(r"\s+", " ", text).strip()

            if len(text) > 8000:
                text = text[:8000] + "... [content truncated]"

            await ctx.info(
                f"Successfully fetched and parsed content ({len(text)} characters)"
            )
            return text

        except httpx.TimeoutError:
            await ctx.error(f"Request timed out for URL: {url}")
            return "Error: The request timed out while trying to fetch the webpage."
        except httpx.HTTPError as e:
            await ctx.error(f"HTTP error occurred while fetching {url}: {str(e)}")
            return f"Error: Could not access the webpage ({str(e)})"
        except Exception as e:
            await ctx.error(f"Error fetching content from {url}: {str(e)}")
            return f"Error: An unexpected error occurred while fetching the webpage ({str(e)})"


_resolved_host = os.environ.get('HOST') or os.environ.get('FASTMCP_HOST') or "0.0.0.0"
_resolved_port_str = os.environ.get('PORT') or os.environ.get('FASTMCP_PORT') or "5000"
try:
    _resolved_port = int(_resolved_port_str)
except ValueError:
    _resolved_port = 5000

mcp = FastMCP("ddg-search", host=_resolved_host, port=_resolved_port)
searcher = DuckDuckGoSearcher()
fetcher = WebContentFetcher()


@mcp.tool()
async def search(query: str, ctx: Context, max_results: int = 10) -> str:
    """
    Search DuckDuckGo and return formatted results.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 10)
        ctx: MCP context for logging
    """
    try:
        results = await searcher.search(query, ctx, max_results)
        return searcher.format_results_for_llm(results)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return f"An error occurred while searching: {str(e)}"


@mcp.tool()
async def fetch_content(url: str, ctx: Context) -> str:
    """
    Fetch and parse content from a webpage URL.

    Args:
        url: The webpage URL to fetch content from
        ctx: MCP context for logging
    """
    return await fetcher.fetch_and_parse(url, ctx)


def main():
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    transport = "streamable-http"
    for i, arg in enumerate(sys.argv):
        if arg == "--transport" and i + 1 < len(sys.argv):
            transport = sys.argv[i + 1]
            break

    if transport == "stdio":
        mcp.run(transport="stdio")
        return

    session_manager = StreamableHTTPSessionManager(
        app=mcp._mcp_server,
        event_store=None,
        json_response=False,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Application started with StreamableHTTP transport!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    port = _resolved_port
    host = _resolved_host
    logger.info(f"Server starting on {host}:{port}")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    uvicorn.run(starlette_app, host=host, port=port)


if __name__ == "__main__":
    main()
