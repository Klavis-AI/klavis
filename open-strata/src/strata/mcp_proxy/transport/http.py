"""HTTP and SSE transport implementations for MCP."""

import logging
from contextlib import AsyncExitStack
from typing import Dict, Literal, Optional, Tuple
from urllib.parse import urlparse

from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

from strata.mcp_proxy.auth_provider import create_oauth_provider
from .base import Transport

logger = logging.getLogger(__name__)

class HTTPTransport(Transport):
    """HTTP/SSE transport for MCP communication."""

    def __init__(
        self,
        server_name: str,
        url: str,
        mode: Literal["http", "sse"] = "http",
        headers: Optional[Dict[str, str]] = None,
        auth: str = "",
    ):
        """Initialize HTTP transport.

        Args:
            url: HTTP/HTTPS URL of the MCP server
            mode: Transport mode - "http" for request/response, "sse" for server-sent events
            headers: Optional headers to send with requests
        """
        super().__init__()
        self.server_name = server_name
        self.url = url
        self.mode = mode
        self.headers = headers or {}
        self.auth = auth

        # Validate URL
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

    async def _get_streams(self, exit_stack: AsyncExitStack) -> Tuple:
        """Get HTTP/SSE transport streams.

        Args:
            exit_stack: AsyncExitStack to manage the streams

        Returns:
            Tuple of (read_stream, write_stream)
        """
        if self.mode == "sse":
            # Connect via SSE for server-sent events
            logger.info(f"Connecting to MCP server via SSE: {self.url}")
            if self.auth == "oauth":
                return await exit_stack.enter_async_context(
                    sse_client(
                        self.url, headers=self.headers, auth=create_oauth_provider(self.server_name, self.url))
                )
            return await exit_stack.enter_async_context(
                sse_client(self.url, headers=self.headers)
            )
        elif self.mode == "http":
            # Connect via standard HTTP (request/response)
            logger.info(f"Connecting to MCP server via HTTP: {self.url}")
            if self.auth == "oauth":
                return await exit_stack.enter_async_context(
                    streamablehttp_client(
                        self.url, headers=self.headers, auth=create_oauth_provider(self.server_name, self.url))
                )
            return await exit_stack.enter_async_context(
                streamablehttp_client(self.url, headers=self.headers)
            )
        else:
            raise ValueError(
                f"Invalid transport mode: {self.mode}. Use 'http' or 'sse'."
            )
