"""MCP Client for connecting to and interacting with MCP servers."""

import logging
from typing import Any, Dict, List, Optional

from mcp import types

from .transport import Transport

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for connecting to MCP servers using various transports.

    Usage:
        # With stdio transport
        transport = StdioTransport("docker", ["run", "-i", "my-server"])
        client = MCPClient(transport)
        await client.connect()

        # With HTTP/SSE transport
        transport = HTTPTransport("http://localhost:8080", mode="sse")
        client = MCPClient(transport)
        await client.connect()
    """

    def __init__(self, transport: Transport):
        """Initialize the MCP client with a transport.

        Args:
            transport: Transport instance (StdioTransport or HTTPTransport)
        """
        self.transport = transport
        self._tools_cache: Optional[List[Dict[str, Any]]] = None

    async def initialize(self) -> None:
        """Initialize the MCP client by connecting the transport."""
        await self.transport.initialize()

    async def connect(self) -> None:
        """Connect to the MCP server."""
        await self.transport.connect()
        logger.info(
            f"Connected to MCP server using {self.transport.__class__.__name__}"
        )

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        await self.transport.disconnect()
        self._tools_cache = None
        logger.info("Disconnected from MCP server")

    def is_connected(self) -> bool:
        """Check if connected to an MCP server."""
        return self.transport.is_connected()

    async def list_tools(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """List available tools from the MCP server.

        Args:
            use_cache: Whether to use cached tools if available

        Returns:
            List of tool definitions with name, description, and inputSchema
        """
        if not self.transport.is_connected():
            raise RuntimeError("Not connected to any MCP server")

        if use_cache and self._tools_cache is not None:
            return self._tools_cache

        # Get tools from server
        session = self.transport.get_session()
        response = await session.list_tools()

        # Convert to dict format
        tools = []
        for tool in response.tools:
            tool_dict = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            # Add optional fields only if they have values
            if hasattr(tool, "title") and tool.title:
                tool_dict["title"] = tool.title
            if hasattr(tool, "outputSchema") and tool.outputSchema:
                tool_dict["outputSchema"] = tool.outputSchema
            tools.append(tool_dict)

        self._tools_cache = tools
        logger.info(f"Retrieved {len(tools)} tools from MCP server")

        return tools

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> List[types.ContentBlock]:
        """Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result from MCP server
        """
        if not self.transport.is_connected():
            raise RuntimeError("Not connected to any MCP server")

        logger.info(f"Calling tool '{tool_name}' with arguments: {arguments}")

        # Call the tool and return result directly
        session = self.transport.get_session()
        result = await session.call_tool(tool_name, arguments)
        if result.isError:
            logger.error(
                f"Tool '{tool_name}' returned error: {result.structuredContent}"
            )
            raise RuntimeError(f"Tool '{tool_name}' error: {result.structuredContent}")
        return result.content

    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the schema for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool schema or None if not found
        """
        tools = await self.list_tools()

        for tool in tools:
            if tool["name"] == tool_name:
                return tool

        return None

    async def __aenter__(self):
        """Enter async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.disconnect()
