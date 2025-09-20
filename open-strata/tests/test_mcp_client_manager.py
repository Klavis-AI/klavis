"""Test cases for MCP Client Manager."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from strata.mcp_client_manager import MCPClientManager


def get_container_runtime():
    """Detect available container runtime."""
    if shutil.which("podman"):
        return "podman"
    elif shutil.which("docker"):
        return "docker"
    else:
        pytest.skip("Neither podman nor docker found in PATH")


@pytest_asyncio.fixture
async def temp_config():
    """Create a temporary config file with test servers."""
    config = {
        "mcp": {
            "servers": {
                "test-server-1": {
                    "command": "python",
                    "args": ["-m", "test_server"],
                    "env": {"TEST_VAR": "value1"},
                    "enabled": True,
                },
                "test-server-2": {
                    "command": "node",
                    "args": ["server.js"],
                    "env": {"NODE_ENV": "test"},
                    "enabled": False,
                },
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        config_path = Path(f.name)

    yield config_path

    # Cleanup
    config_path.unlink()


@pytest_asyncio.fixture
async def manager_with_config(temp_config):
    """Create a manager with test configuration."""
    manager = MCPClientManager(temp_config)
    yield manager
    # Cleanup - disconnect all
    await manager.disconnect_all()


@pytest_asyncio.fixture
async def manager_with_github_server():
    """Create a manager with real GitHub MCP server configuration."""
    # Get GitHub PAT from environment
    github_pat = os.getenv("GITHUB_PAT", "")
    if not github_pat:
        pytest.skip("GITHUB_PAT environment variable not set")

    container_runtime = get_container_runtime()

    # Create temporary config with real GitHub MCP server
    config = {
        "mcp": {
            "servers": {
                "github": {
                    "command": container_runtime,
                    "args": [
                        "run",
                        "-i",
                        "--rm",
                        "-e",
                        "GITHUB_PERSONAL_ACCESS_TOKEN",
                        "ghcr.io/github/github-mcp-server",
                    ],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": github_pat},
                    "enabled": True,
                },
                "disabled-server": {
                    "command": "echo",
                    "args": ["test"],
                    "enabled": False,
                },
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        config_path = Path(f.name)

    manager = MCPClientManager(config_path)

    yield manager

    # Cleanup
    await manager.disconnect_all()
    config_path.unlink()


class TestMCPClientManager:
    """Test cases for MCPClientManager."""

    @pytest.mark.asyncio
    async def test_initialization(self, temp_config):
        """Test manager initialization."""
        manager = MCPClientManager(temp_config)

        # Check that servers are loaded
        assert len(manager.server_list.servers) == 2
        assert "test-server-1" in manager.server_list.servers
        assert "test-server-2" in manager.server_list.servers

        # No active clients initially
        assert len(manager.active_clients) == 0

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_initialize_from_config(
        self, mock_transport, mock_client, manager_with_config
    ):
        """Test initializing clients from configuration."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Initialize from config (only enabled servers)
        results = await manager_with_config.initialize_from_config()

        # Only test-server-1 should be initialized (it's enabled)
        assert results == {"test-server-1": True}
        assert len(manager_with_config.active_clients) == 1
        assert "test-server-1" in manager_with_config.active_clients

        # Verify transport was created with correct params
        mock_transport.assert_called_once_with(
            command="python", args=["-m", "test_server"], env={"TEST_VAR": "value1"}
        )

        # Verify client was connected
        mock_client_instance.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_disconnect_all(
        self, mock_transport, mock_client, manager_with_config
    ):
        """Test disconnecting from all servers."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Initialize first
        await manager_with_config.initialize_from_config()
        assert len(manager_with_config.active_clients) == 1

        # Disconnect all
        await manager_with_config.disconnect_all()

        assert len(manager_with_config.active_clients) == 0
        # Verify disconnect was called
        mock_client_instance.disconnect.assert_called_once()

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_list_active_servers(
        self, mock_transport, mock_client, manager_with_config
    ):
        """Test listing active servers."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Initially no active servers
        assert manager_with_config.list_active_servers() == []

        # Initialize from config
        await manager_with_config.initialize_from_config()

        # Should have one active server (test-server-1)
        active_servers = manager_with_config.list_active_servers()
        assert len(active_servers) == 1
        assert "test-server-1" in active_servers

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_is_connected(self, mock_transport, mock_client, manager_with_config):
        """Test checking if a server is connected."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client_instance.is_connected = MagicMock(return_value=True)
        mock_client.return_value = mock_client_instance

        # Initially not connected
        assert not manager_with_config.is_connected("test-server-1")

        # Initialize from config
        await manager_with_config.initialize_from_config()

        # Now should be connected
        assert manager_with_config.is_connected("test-server-1")
        assert not manager_with_config.is_connected("test-server-2")  # Disabled
        assert not manager_with_config.is_connected("nonexistent")  # Doesn't exist

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_get_client(self, mock_transport, mock_client, manager_with_config):
        """Test getting a client by server name."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Initialize from config
        await manager_with_config.initialize_from_config()

        # Get client
        client = manager_with_config.get_client("test-server-1")
        assert client == mock_client_instance

        # Try to get non-existent client
        with pytest.raises(KeyError):
            manager_with_config.get_client("nonexistent")

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_reconnect_server(
        self, mock_transport, mock_client, manager_with_config
    ):
        """Test reconnecting to a server."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Initialize from config
        await manager_with_config.initialize_from_config()
        assert mock_client_instance.connect.call_count == 1

        # Reconnect
        success = await manager_with_config.reconnect_server("test-server-1")
        assert success is True

        # Should have disconnected and connected again
        assert mock_client_instance.disconnect.call_count == 1
        assert mock_client_instance.connect.call_count == 2

        # Try to reconnect non-existent server
        success = await manager_with_config.reconnect_server("nonexistent")
        assert success is False

        # Try to reconnect disabled server
        success = await manager_with_config.reconnect_server("test-server-2")
        assert success is False

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_context_manager(self, mock_transport, mock_client, temp_config):
        """Test using manager as async context manager."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance

        async with MCPClientManager(temp_config) as manager:
            # Should auto-initialize
            assert len(manager.active_clients) == 1
            assert mock_client_instance.connect.call_count == 1

        # Should auto-disconnect
        assert mock_client_instance.disconnect.call_count == 1


@pytest.mark.integration
class TestMCPClientManagerIntegration:
    """Integration tests for MCPClientManager with real MCP servers."""

    @pytest.mark.asyncio
    async def test_initialize_and_connect_real_server(self, manager_with_github_server):
        """Test initializing and connecting to real GitHub MCP server."""
        # Initialize
        results = await manager_with_github_server.initialize_from_config()

        # Should connect to github server (enabled) but not disabled-server
        assert "github" in results
        assert results["github"] is True
        assert "disabled-server" not in results

        # Verify it's actually connected
        assert manager_with_github_server.is_connected("github")
        assert "github" in manager_with_github_server.list_active_servers()

        # Get the client and test it
        client = manager_with_github_server.get_client("github")
        assert client is not None

        # Test that we can call a real method
        tools = await client.list_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        print(f"✓ Connected to GitHub MCP server, found {len(tools)} tools")

    @pytest.mark.asyncio
    async def test_reconnect_real_server(self, manager_with_github_server):
        """Test reconnecting to a real server."""
        # Initialize
        await manager_with_github_server.initialize_from_config()
        assert manager_with_github_server.is_connected("github")

        # Get initial tools
        client1 = manager_with_github_server.get_client("github")
        tools1 = await client1.list_tools()

        # Reconnect
        success = await manager_with_github_server.reconnect_server("github")
        assert success is True
        assert manager_with_github_server.is_connected("github")

        # Get tools after reconnect
        client2 = manager_with_github_server.get_client("github")
        tools2 = await client2.list_tools()

        # Should have same tools
        assert len(tools2) == len(tools1)
        print(f"✓ Reconnected successfully, tools still available: {len(tools2)}")

    @pytest.mark.asyncio
    async def test_use_real_tool(self, manager_with_github_server):
        """Test using a real tool from the GitHub MCP server."""
        # Initialize
        await manager_with_github_server.initialize_from_config()

        # Get client
        client = manager_with_github_server.get_client("github")

        # List tools to find one we can test
        tools = await client.list_tools()

        # Find a simple tool like get_user
        user_tool = next(
            (t for t in tools if "user" in t.get("name", "").lower()), None
        )

        if user_tool:
            # Try to call the tool
            try:
                result = await client.call_tool(
                    user_tool["name"], {"username": "octocat"}
                )
                print(f"✓ Successfully called tool {user_tool['name']}")
                if result:
                    data = result[0].text if hasattr(result[0], "text") else str(result)
                    print(f"  Got result: {data[:100]}...")
            except Exception as e:
                print(f"  Tool call failed (expected for some tools): {e}")
        else:
            print("  No user tool found to test")
