"""Test MCP Client with different transport methods using pytest."""

import json
import os
import shutil

import pytest
import pytest_asyncio

from strata.mcp_proxy import MCPClient
from strata.mcp_proxy.transport import HTTPTransport, StdioTransport

# GitHub PAT from environment variable
GITHUB_PAT = os.getenv("GITHUB_PAT") or ""
if not GITHUB_PAT:
    raise ValueError(
        "GITHUB_PAT environment variable is required. "
        "Set it with: export GITHUB_PAT='your_github_personal_access_token'"
    )


def __get_container_runtime():
    """Detect available container runtime."""
    if shutil.which("podman"):
        return "podman"
    elif shutil.which("docker"):
        return "docker"
    else:
        raise RuntimeError("Neither podman nor docker found in PATH")


# Detect container runtime (podman or docker)
CONTAINER_RUNTIME = __get_container_runtime()
print(f"Using container runtime: {CONTAINER_RUNTIME}")


@pytest_asyncio.fixture
async def http_client():
    """Create HTTP client fixture."""
    transport = HTTPTransport(
        url="https://api.githubcopilot.com/mcp/",
        mode="http",
        headers={"Authorization": f"Bearer {GITHUB_PAT}"},
    )
    client = MCPClient(transport)
    await client.connect()
    try:
        yield client
    finally:
        if client.is_connected():
            await client.disconnect()


@pytest_asyncio.fixture
async def stdio_client():
    """Create stdio client fixture using available container runtime."""
    transport = StdioTransport(
        command=CONTAINER_RUNTIME,
        args=[
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server",
        ],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_PAT},
    )
    client = MCPClient(transport)
    await client.connect()
    try:
        yield client
    finally:
        if client.is_connected():
            await client.disconnect()


class TestHTTPTransport:
    """Test HTTP transport functionality."""

    @pytest.mark.asyncio
    async def test_connection(self, http_client):
        """Test HTTP connection to GitHub MCP server."""
        assert http_client.is_connected()
        print("✓ Connected via HTTP")

    @pytest.mark.asyncio
    async def test_list_tools(self, http_client):
        """Test listing tools via HTTP."""
        tools = await http_client.list_tools()
        assert len(tools) > 0
        print(f"✓ Found {len(tools)} tools via HTTP")

        # Print sample tools
        for i, tool in enumerate(tools[:3]):
            print(f"  Tool {i+1}: {tool['name']}")

    @pytest.mark.asyncio
    async def test_tool_call_search_code(self, http_client):
        """Test calling search_code tool via HTTP."""
        # Search for a simple query in the github/docs repo
        result = await http_client.call_tool(
            "search_code", {"query": "README repo:github/docs", "perPage": 3}
        )

        assert result is not None

        # Parse result
        if hasattr(result, "content") and result.content:
            content = result.content[0]
            if hasattr(content, "text"):
                data = json.loads(content.text)
                assert "items" in data or "total_count" in data
                print(f"✓ Search returned {data.get('total_count', 0)} results")
                if "items" in data and data["items"]:
                    print(f"  First result: {data['items'][0].get('path', 'N/A')}")

    @pytest.mark.asyncio
    async def test_tool_call_get_me(self, http_client):
        """Test calling get_me tool via HTTP."""
        result = await http_client.call_tool("get_me", {})

        assert result is not None

        # Parse result
        if hasattr(result, "content") and result.content:
            content = result.content[0]
            if hasattr(content, "text"):
                data = json.loads(content.text)
                assert "login" in data or "id" in data
                print(f"✓ Got user: {data.get('login', data.get('id'))}")
                print(f"  Name: {data.get('name', 'N/A')}")
                print(f"  Public repos: {data.get('public_repos', 'N/A')}")


class TestStdioTransport:
    """Test stdio transport functionality."""

    @pytest.mark.asyncio
    async def test_connection(self, stdio_client):
        """Test stdio connection via container runtime."""
        assert stdio_client.is_connected()
        print(f"✓ Connected via stdio/{CONTAINER_RUNTIME}")

    @pytest.mark.asyncio
    async def test_list_tools(self, stdio_client):
        """Test listing tools via stdio."""
        tools = await stdio_client.list_tools()
        assert len(tools) > 0
        print(f"✓ Found {len(tools)} tools via stdio")

        # Print sample tools
        for i, tool in enumerate(tools[:3]):
            print(f"  Tool {i+1}: {tool['name']}")

    @pytest.mark.asyncio
    async def test_tool_call_search_code(self, stdio_client):
        """Test calling search_code tool via stdio."""
        # Search for a simple query
        result = await stdio_client.call_tool(
            "search_code", {"query": "README repo:github/docs", "perPage": 3}
        )

        assert result is not None

        # Parse result
        if hasattr(result, "content") and result.content:
            content = result.content[0]
            if hasattr(content, "text"):
                data = json.loads(content.text)
                assert "items" in data or "total_count" in data
                print(f"✓ Search returned {data.get('total_count', 0)} results")
                if "items" in data and data["items"]:
                    print(f"  First result: {data['items'][0].get('path', 'N/A')}")

    @pytest.mark.asyncio
    async def test_tool_call_get_me(self, stdio_client):
        """Test calling get_me tool via stdio."""
        result = await stdio_client.call_tool("get_me", {})

        assert result is not None

        # Parse result
        if hasattr(result, "content") and result.content:
            content = result.content[0]
            if hasattr(content, "text"):
                data = json.loads(content.text)
                assert "login" in data or "id" in data
                print(f"✓ Got user: {data.get('login', data.get('id'))}")
                print(f"  Name: {data.get('name', 'N/A')}")
                print(f"  Public repos: {data.get('public_repos', 'N/A')}")


class TestContextManager:
    """Test context manager functionality."""

    @pytest.mark.asyncio
    async def test_http_context_manager(self):
        """Test HTTP client as context manager."""
        transport = HTTPTransport(
            url="https://api.githubcopilot.com/mcp/",
            mode="http",
            headers={"Authorization": f"Bearer {GITHUB_PAT}"},
        )

        async with MCPClient(transport) as client:
            assert client.is_connected()
            tools = await client.list_tools()
            assert len(tools) > 0
            print(f"✓ Context manager: Found {len(tools)} tools")

        # Should be disconnected after exiting context
        assert not client.is_connected()
        print("✓ Context manager: Auto-disconnected")

    @pytest.mark.asyncio
    async def test_stdio_context_manager(self):
        """Test stdio client as context manager."""
        transport = StdioTransport(
            command=CONTAINER_RUNTIME,
            args=[
                "run",
                "-i",
                "--rm",
                "-e",
                "GITHUB_PERSONAL_ACCESS_TOKEN",
                "ghcr.io/github/github-mcp-server",
            ],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_PAT},
        )

        async with MCPClient(transport) as client:
            assert client.is_connected()
            tools = await client.list_tools()
            assert len(tools) > 0
            print(f"✓ Context manager: Found {len(tools)} tools")

        # Should be disconnected after exiting context
        assert not client.is_connected()
        print("✓ Context manager: Auto-disconnected")


class TestToolCaching:
    """Test tool caching functionality."""

    @pytest.mark.asyncio
    async def test_tool_cache(self, http_client):
        """Test that tools are cached after first retrieval."""
        # First call - should fetch from server
        tools1 = await http_client.list_tools(use_cache=False)
        assert len(tools1) > 0

        # Second call with cache - should return same tools
        tools2 = await http_client.list_tools(use_cache=True)
        assert tools1 == tools2
        print("✓ Tool caching works correctly")

        # Force refresh without cache
        tools3 = await http_client.list_tools(use_cache=False)
        assert len(tools3) == len(tools1)
        print("✓ Cache bypass works correctly")


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_invalid_tool_call(self, http_client):
        """Test handling of invalid tool calls."""
        with pytest.raises(Exception) as exc_info:
            await http_client.call_tool("non_existent_tool", {"param": "value"})

        assert (
            "not found" in str(exc_info.value).lower()
            or "error" in str(exc_info.value).lower()
        )
        print("✓ Invalid tool call handled correctly")

    @pytest.mark.asyncio
    @staticmethod
    async def test_disconnected_client():
        """Test operations on disconnected client."""
        transport = HTTPTransport(
            url="https://api.githubcopilot.com/mcp/",
            mode="http",
            headers={"Authorization": f"Bearer {GITHUB_PAT}"},
        )
        client = MCPClient(transport)

        # Should not be connected initially
        assert not client.is_connected()

        # Operations should fail
        with pytest.raises(RuntimeError) as exc_info:
            await client.list_tools()

        assert "not connected" in str(exc_info.value).lower()
        print("✓ Disconnected client errors handled correctly")
