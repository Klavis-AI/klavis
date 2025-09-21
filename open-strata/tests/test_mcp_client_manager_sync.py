"""Tests for MCPClientManager sync_with_config functionality."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from strata.config import MCPServerConfig
from strata.mcp_client_manager import MCPClientManager


@pytest_asyncio.fixture
async def manager_with_mocks():
    """Create a manager with mocked clients for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {"mcp": {"servers": {}}}
        json.dump(config, f)
        config_path = Path(f.name)

    manager = MCPClientManager(config_path)

    yield manager

    await manager.disconnect_all()
    config_path.unlink()


class TestSyncWithConfig:
    """Test sync_with_config method."""

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_sync_add_new_server(
        self, mock_transport, mock_client, manager_with_mocks
    ):
        """Test syncing when a new server is added."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.disconnect = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Create new server config
        new_servers = {
            "test-server": MCPServerConfig(
                name="test-server", command="echo", args=["hello"], enabled=True
            )
        }

        # Sync with new config
        await manager_with_mocks.sync_with_config(new_servers)

        # Verify server was connected
        assert "test-server" in manager_with_mocks.active_clients
        mock_client_instance.connect.assert_called_once()
        mock_client_instance.disconnect.assert_not_called()

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_sync_remove_server(
        self, mock_transport, mock_client, manager_with_mocks
    ):
        """Test syncing when a server is removed."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.disconnect = AsyncMock()
        mock_client.return_value = mock_client_instance

        # First add a server
        manager_with_mocks.active_clients["test-server"] = mock_client_instance

        # Sync with empty config (removes the server)
        await manager_with_mocks.sync_with_config({})

        # Verify server was disconnected
        assert "test-server" not in manager_with_mocks.active_clients
        mock_client_instance.disconnect.assert_called_once()

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_sync_disable_server(
        self, mock_transport, mock_client, manager_with_mocks
    ):
        """Test syncing when a server is disabled."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.disconnect = AsyncMock()
        mock_client.return_value = mock_client_instance

        # First add an active server
        manager_with_mocks.active_clients["test-server"] = mock_client_instance

        # Sync with disabled server
        new_servers = {
            "test-server": MCPServerConfig(
                name="test-server",
                command="echo",
                args=["hello"],
                enabled=False,  # Disabled
            )
        }

        await manager_with_mocks.sync_with_config(new_servers)

        # Verify server was disconnected
        assert "test-server" not in manager_with_mocks.active_clients
        mock_client_instance.disconnect.assert_called_once()

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_sync_enable_server(
        self, mock_transport, mock_client, manager_with_mocks
    ):
        """Test syncing when a server is enabled."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.disconnect = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Start with no active servers
        assert len(manager_with_mocks.active_clients) == 0

        # Sync with enabled server
        new_servers = {
            "test-server": MCPServerConfig(
                name="test-server", command="echo", args=["hello"], enabled=True
            )
        }

        await manager_with_mocks.sync_with_config(new_servers)

        # Verify server was connected
        assert "test-server" in manager_with_mocks.active_clients
        mock_client_instance.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_sync_config_change_reconnects(
        self, mock_transport, mock_client, manager_with_mocks
    ):
        """Test syncing when server config changes (should reconnect)."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.disconnect = AsyncMock()
        mock_client.return_value = mock_client_instance

        # First add a server
        manager_with_mocks.active_clients["test-server"] = mock_client_instance

        # Sync with modified config
        new_servers = {
            "test-server": MCPServerConfig(
                name="test-server",
                command="node",  # Changed from echo
                args=["server.js"],  # Changed args
                enabled=True,
            )
        }

        await manager_with_mocks.sync_with_config(new_servers)

        # Verify server was reconnected (disconnect + connect)
        assert "test-server" in manager_with_mocks.active_clients
        mock_client_instance.disconnect.assert_called_once()
        mock_client_instance.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_sync_multiple_changes(
        self, mock_transport, mock_client, manager_with_mocks
    ):
        """Test syncing with multiple changes at once."""
        # Setup mocks
        mock_client_instance1 = AsyncMock()
        mock_client_instance1.connect = AsyncMock()
        mock_client_instance1.disconnect = AsyncMock()

        mock_client_instance2 = AsyncMock()
        mock_client_instance2.connect = AsyncMock()
        mock_client_instance2.disconnect = AsyncMock()

        # Return different instances for different calls
        mock_client.side_effect = [mock_client_instance1, mock_client_instance2]

        # Start with one active server
        manager_with_mocks.active_clients["old-server"] = mock_client_instance1

        # Sync with new config: remove old, add two new
        new_servers = {
            "new-server-1": MCPServerConfig(
                name="new-server-1", command="python", args=["server1.py"], enabled=True
            ),
            "new-server-2": MCPServerConfig(
                name="new-server-2", command="node", args=["server2.js"], enabled=True
            ),
        }

        await manager_with_mocks.sync_with_config(new_servers)

        # Verify old server was removed
        assert "old-server" not in manager_with_mocks.active_clients
        mock_client_instance1.disconnect.assert_called_once()

        # Verify new servers were added
        assert "new-server-1" in manager_with_mocks.active_clients
        assert "new-server-2" in manager_with_mocks.active_clients
        mock_client_instance1.connect.assert_called_once()
        mock_client_instance2.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_sync_with_http_server(
        self, mock_transport, mock_client, manager_with_mocks
    ):
        """Test syncing with HTTP/SSE servers."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client.return_value = mock_client_instance

        with patch("strata.mcp_client_manager.HTTPTransport") as mock_http_transport:
            mock_http_transport_instance = MagicMock()
            mock_http_transport.return_value = mock_http_transport_instance

            # Sync with HTTP server
            new_servers = {
                "api-server": MCPServerConfig(
                    name="api-server",
                    type="http",
                    url="https://api.example.com/mcp",
                    headers={"Authorization": "Bearer token"},
                    enabled=True,
                )
            }

            await manager_with_mocks.sync_with_config(new_servers)

            # Verify HTTP transport was created with correct params
            mock_http_transport.assert_called_once_with(
                url="https://api.example.com/mcp",
                mode="http",
                headers={"Authorization": "Bearer token"},
            )

            # Verify server was connected
            assert "api-server" in manager_with_mocks.active_clients
            mock_client_instance.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_sync_error_handling(
        self, mock_transport, mock_client, manager_with_mocks
    ):
        """Test that sync continues even if one server fails."""
        # Setup mocks - first server fails, second succeeds
        mock_client_instance1 = AsyncMock()
        mock_client_instance1.connect = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        mock_client_instance2 = AsyncMock()
        mock_client_instance2.connect = AsyncMock()

        mock_client.side_effect = [mock_client_instance1, mock_client_instance2]

        # Sync with two servers
        new_servers = {
            "failing-server": MCPServerConfig(
                name="failing-server", command="bad-command", args=[], enabled=True
            ),
            "working-server": MCPServerConfig(
                name="working-server", command="echo", args=["hello"], enabled=True
            ),
        }

        await manager_with_mocks.sync_with_config(new_servers)

        # First server should fail and not be in active clients
        assert "failing-server" not in manager_with_mocks.active_clients

        # Second server should succeed
        assert "working-server" in manager_with_mocks.active_clients
        mock_client_instance2.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_sync_mutex_prevents_concurrent_operations(
        self, mock_transport, mock_client, manager_with_mocks
    ):
        """Test that mutex prevents concurrent sync operations."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.disconnect = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Track the order of operations
        operations = []

        # Create a slow connect operation
        async def slow_connect():
            operations.append("connect_start")
            await asyncio.sleep(0.1)  # Simulate slow connection
            operations.append("connect_end")

        mock_client_instance.connect = slow_connect

        # Create two different server configs
        servers1 = {
            "server1": MCPServerConfig(
                name="server1", command="echo", args=["1"], enabled=True
            )
        }

        servers2 = {
            "server2": MCPServerConfig(
                name="server2", command="echo", args=["2"], enabled=True
            )
        }

        # Start two sync operations concurrently
        task1 = asyncio.create_task(manager_with_mocks.sync_with_config(servers1))
        task2 = asyncio.create_task(manager_with_mocks.sync_with_config(servers2))

        # Wait for both to complete
        await asyncio.gather(task1, task2)

        # Verify operations were serialized (not interleaved)
        # Should see connect_start, connect_end, connect_start, connect_end
        assert len(operations) == 4
        assert operations[0] == "connect_start"
        assert operations[1] == "connect_end"
        assert operations[2] == "connect_start"
        assert operations[3] == "connect_end"

        # Only one server should remain active (the last one)
        assert len(manager_with_mocks.active_clients) == 1
        assert "server2" in manager_with_mocks.active_clients
