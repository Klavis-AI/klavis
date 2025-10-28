"""Integration test for config watching and client manager syncing."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from strata.mcp_client_manager import MCPClientManager


class TestConfigSyncIntegration:
    """Integration tests for config watching + client manager sync."""

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_config_change_triggers_sync(self, mock_transport, mock_client):
        """Test that config file changes trigger client manager sync."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.disconnect = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Create temporary config with initial server
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            initial_config = {
                "mcp": {
                    "servers": {
                        "initial-server": {
                            "command": "echo",
                            "args": ["initial"],
                            "enabled": True,
                        }
                    }
                }
            }
            json.dump(initial_config, f)
            config_path = Path(f.name)

        try:
            # Create manager and initialize
            manager = MCPClientManager(config_path)
            await manager.initialize_from_config()

            # Verify initial server is connected
            assert "initial-server" in manager.active_clients
            assert mock_client_instance.connect.call_count == 1

            # Track sync calls
            sync_calls = []
            original_sync = manager.sync_with_config

            async def track_sync(new_servers):
                sync_calls.append(dict(new_servers))
                return await original_sync(new_servers)

            manager.sync_with_config = track_sync

            # Start config watching
            watch_task = asyncio.create_task(
                manager.server_list.watch_config(
                    lambda servers: asyncio.create_task(
                        manager.sync_with_config(servers)
                    )
                )
            )

            # Give watcher time to start
            await asyncio.sleep(0.1)

            # Update config file to add new server and remove old one
            new_config = {
                "mcp": {
                    "servers": {
                        "new-server": {
                            "command": "node",
                            "args": ["server.js"],
                            "enabled": True,
                        }
                    }
                }
            }

            with open(config_path, "w") as f:
                json.dump(new_config, f)

            # Wait for config change to be detected and processed
            await asyncio.sleep(0.6)

            # Verify sync was called
            assert len(sync_calls) >= 1

            # Check that the new config has the correct server
            last_sync = sync_calls[-1]
            assert "new-server" in last_sync
            assert "initial-server" not in last_sync

            # Verify client manager state reflects the change
            assert "new-server" in manager.active_clients
            assert "initial-server" not in manager.active_clients

            # Should have disconnected old and connected new
            assert mock_client_instance.disconnect.call_count >= 1
            assert mock_client_instance.connect.call_count >= 2

            watch_task.cancel()

        finally:
            # Cleanup
            config_path.unlink(missing_ok=True)
            await manager.disconnect_all()

    @pytest.mark.asyncio
    @patch("strata.mcp_client_manager.MCPClient")
    @patch("strata.mcp_client_manager.StdioTransport")
    async def test_config_enable_disable_triggers_sync(
        self, mock_transport, mock_client
    ):
        """Test that enabling/disabling servers triggers appropriate sync actions."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.disconnect = AsyncMock()
        mock_client.return_value = mock_client_instance

        # Create temporary config with disabled server
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            initial_config = {
                "mcp": {
                    "servers": {
                        "test-server": {
                            "command": "echo",
                            "args": ["test"],
                            "enabled": False,  # Disabled initially
                        }
                    }
                }
            }
            json.dump(initial_config, f)
            config_path = Path(f.name)

        try:
            # Create manager and initialize
            manager = MCPClientManager(config_path)
            await manager.initialize_from_config()

            # Verify no servers are connected (server is disabled)
            assert len(manager.active_clients) == 0
            assert mock_client_instance.connect.call_count == 0

            # Start config watching
            watch_task = asyncio.create_task(
                manager.server_list.watch_config(
                    lambda servers: asyncio.create_task(
                        manager.sync_with_config(servers)
                    )
                )
            )

            # Give watcher time to start
            await asyncio.sleep(0.1)

            # Update config to enable the server
            enabled_config = {
                "mcp": {
                    "servers": {
                        "test-server": {
                            "command": "echo",
                            "args": ["test"],
                            "enabled": True,  # Now enabled
                        }
                    }
                }
            }

            with open(config_path, "w") as f:
                json.dump(enabled_config, f)

            # Wait for config change to be detected and processed
            await asyncio.sleep(0.6)

            # Verify server is now connected
            assert "test-server" in manager.active_clients
            assert mock_client_instance.connect.call_count == 1

            # Now disable the server again
            disabled_config = {
                "mcp": {
                    "servers": {
                        "test-server": {
                            "command": "echo",
                            "args": ["test"],
                            "enabled": False,  # Disabled again
                        }
                    }
                }
            }

            with open(config_path, "w") as f:
                json.dump(disabled_config, f)

            # Wait for config change to be detected and processed
            await asyncio.sleep(0.6)

            # Verify server is now disconnected
            assert "test-server" not in manager.active_clients
            assert mock_client_instance.disconnect.call_count == 1

            watch_task.cancel()

        finally:
            # Cleanup
            config_path.unlink(missing_ok=True)
            await manager.disconnect_all()
