"""Tests for config watching functionality."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from strata.config import MCPServerList


class TestConfigWatch:
    """Test config file watching functionality."""

    @pytest.fixture
    def temp_config(self):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config = {"mcp": {"servers": {}}}
            json.dump(config, f)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        temp_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_watch_config_add_server(self, temp_config):
        """Test that adding a server triggers the callback."""
        server_list = MCPServerList(temp_config)

        # Track callback calls
        callback_calls = []

        def on_changed(servers):
            callback_calls.append(servers.copy())

        # Start watching in background
        watch_task = asyncio.create_task(server_list.watch_config(on_changed))

        try:
            # Give watcher time to start
            await asyncio.sleep(0.1)

            # Add a server by modifying the file directly
            new_config = {
                "mcp": {
                    "servers": {
                        "test-server": {
                            "command": "echo",
                            "args": ["hello"],
                            "enabled": True,
                        }
                    }
                }
            }

            with open(temp_config, "w") as f:
                json.dump(new_config, f)

            # Wait for change to be detected
            await asyncio.sleep(0.5)

            # Check callback was called
            assert len(callback_calls) == 1
            assert "test-server" in callback_calls[0]
            assert callback_calls[0]["test-server"].name == "test-server"
            assert callback_calls[0]["test-server"].command == "echo"

        finally:
            watch_task.cancel()
            try:
                await watch_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_watch_config_remove_server(self, temp_config):
        """Test that removing a server triggers the callback."""
        # Start with a server
        initial_config = {
            "mcp": {
                "servers": {
                    "test-server": {
                        "command": "echo",
                        "args": ["hello"],
                        "enabled": True,
                    }
                }
            }
        }
        with open(temp_config, "w") as f:
            json.dump(initial_config, f)

        server_list = MCPServerList(temp_config)

        # Track callback calls
        callback_calls = []

        def on_changed(servers):
            callback_calls.append(servers.copy())

        # Start watching in background
        watch_task = asyncio.create_task(server_list.watch_config(on_changed))

        try:
            # Give watcher time to start
            await asyncio.sleep(0.1)

            # Remove the server
            new_config = {"mcp": {"servers": {}}}

            with open(temp_config, "w") as f:
                json.dump(new_config, f)

            # Wait for change to be detected
            await asyncio.sleep(0.5)

            # Check callback was called with empty servers
            assert len(callback_calls) == 1
            assert len(callback_calls[0]) == 0

        finally:
            watch_task.cancel()
            try:
                await watch_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_watch_config_enable_disable(self, temp_config):
        """Test that enabling/disabling a server triggers the callback."""
        # Start with a disabled server
        initial_config = {
            "mcp": {
                "servers": {
                    "test-server": {
                        "command": "echo",
                        "args": ["hello"],
                        "enabled": False,
                    }
                }
            }
        }
        with open(temp_config, "w") as f:
            json.dump(initial_config, f)

        server_list = MCPServerList(temp_config)

        # Track callback calls
        callback_calls = []

        def on_changed(servers):
            callback_calls.append(servers.copy())

        # Start watching in background
        watch_task = asyncio.create_task(server_list.watch_config(on_changed))

        try:
            # Give watcher time to start
            await asyncio.sleep(0.1)

            # Enable the server
            new_config = {
                "mcp": {
                    "servers": {
                        "test-server": {
                            "command": "echo",
                            "args": ["hello"],
                            "enabled": True,
                        }
                    }
                }
            }

            with open(temp_config, "w") as f:
                json.dump(new_config, f)

            # Wait for change to be detected
            await asyncio.sleep(0.5)

            # Check callback was called with enabled server
            assert len(callback_calls) == 1
            assert callback_calls[0]["test-server"].enabled is True

            # Now disable it
            new_config["mcp"]["servers"]["test-server"]["enabled"] = False

            with open(temp_config, "w") as f:
                json.dump(new_config, f)

            # Wait for change to be detected
            await asyncio.sleep(0.5)

            # Check callback was called again with disabled server
            assert len(callback_calls) == 2
            assert callback_calls[1]["test-server"].enabled is False

        finally:
            watch_task.cancel()
            try:
                await watch_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_watch_config_multiple_changes(self, temp_config):
        """Test that multiple rapid changes all trigger callbacks."""
        server_list = MCPServerList(temp_config)

        # Track callback calls
        callback_calls = []

        def on_changed(servers):
            callback_calls.append(servers.copy())

        # Start watching in background
        watch_task = asyncio.create_task(server_list.watch_config(on_changed))

        try:
            # Give watcher time to start
            await asyncio.sleep(0.1)

            # Make multiple changes
            for i in range(3):
                new_config = {
                    "mcp": {
                        "servers": {
                            f"server-{i}": {
                                "command": "echo",
                                "args": [f"hello-{i}"],
                                "enabled": True,
                            }
                        }
                    }
                }

                with open(temp_config, "w") as f:
                    json.dump(new_config, f)

                # Small delay between changes
                await asyncio.sleep(0.3)

            # Wait a bit more for all changes to be processed
            await asyncio.sleep(0.5)

            # Check at least some changes were detected (watchgod may batch changes)
            assert len(callback_calls) >= 1

            # Check the last state has server-2 (the final state)
            last_servers = callback_calls[-1]
            assert "server-2" in last_servers
            assert last_servers["server-2"].args == ["hello-2"]

        finally:
            watch_task.cancel()
            try:
                await watch_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_watch_config_ignores_other_files(self, temp_config):
        """Test that changes to other files in the directory are ignored."""
        server_list = MCPServerList(temp_config)

        # Track callback calls
        callback_calls = []

        def on_changed(servers):
            callback_calls.append(servers.copy())

        # Start watching in background
        watch_task = asyncio.create_task(server_list.watch_config(on_changed))

        try:
            # Give watcher time to start
            await asyncio.sleep(0.1)

            # Create another file in the same directory
            other_file = temp_config.parent / "other.txt"
            other_file.write_text("some content")

            # Wait to see if it triggers a callback
            await asyncio.sleep(0.5)

            # Should not have triggered any callbacks
            assert len(callback_calls) == 0

            # Clean up the other file
            other_file.unlink()

        finally:
            watch_task.cancel()
            try:
                await watch_task
            except asyncio.CancelledError:
                pass
