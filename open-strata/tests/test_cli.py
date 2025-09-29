"""Tests for CLI commands."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from strata.cli import create_parser
from strata.config import MCPServerList


class TestCLICommands:
    """Test CLI commands."""

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

    def test_add_sse_server(self, temp_config):
        """Test adding an SSE type server."""
        test_args = [
            "strata",
            "--config-path",
            str(temp_config),
            "add",
            "--type",
            "sse",
            "--env",
            "API_KEY=test123",
            "klavis-ai",
            "http://localhost:8080/mcp/",
        ]

        with patch.object(sys, "argv", test_args):
            parser = create_parser()
            args = parser.parse_args(test_args[1:])  # Skip program name
            result = args.func(args)

        assert result == 0

        # Verify the config was saved
        with open(temp_config, "r") as f:
            config = json.load(f)

        assert "klavis-ai" in config["mcp"]["servers"]
        server = config["mcp"]["servers"]["klavis-ai"]
        assert server["type"] == "sse"
        assert server["url"] == "http://localhost:8080/mcp/"
        assert server["env"]["API_KEY"] == "test123"

    def test_add_http_server_with_headers(self, temp_config):
        """Test adding an HTTP type server with headers."""
        test_args = [
            "strata",
            "--config-path",
            str(temp_config),
            "add",
            "--type",
            "http",
            "--header",
            "Authorization:Bearer token123",
            "--header",
            "X-Custom-Header:value",
            "api-server",
            "https://api.example.com/mcp",
        ]

        with patch.object(sys, "argv", test_args):
            parser = create_parser()
            args = parser.parse_args(test_args[1:])
            result = args.func(args)

        assert result == 0

        # Verify the config was saved
        with open(temp_config, "r") as f:
            config = json.load(f)

        assert "api-server" in config["mcp"]["servers"]
        server = config["mcp"]["servers"]["api-server"]
        assert server["type"] == "http"
        assert server["url"] == "https://api.example.com/mcp"
        assert server["headers"]["Authorization"] == "Bearer token123"
        assert server["headers"]["X-Custom-Header"] == "value"

    def test_add_stdio_server(self, temp_config):
        """Test adding a stdio type server with dash-prefixed arguments."""
        test_args = [
            "strata",
            "--config-path",
            str(temp_config),
            "add",
            "--type",
            "stdio",
            "--env",
            "GITHUB_TOKEN=test_token",
            "github",
            "npx",
            "--",  # Use -- to separate command arguments
            "-y",
            "@modelcontextprotocol/server-github",
        ]

        with patch.object(sys, "argv", test_args):
            parser = create_parser()
            args = parser.parse_args(test_args[1:])
            result = args.func(args)

        assert result == 0

        # Verify the config was saved
        with open(temp_config, "r") as f:
            config = json.load(f)

        assert "github" in config["mcp"]["servers"]
        server = config["mcp"]["servers"]["github"]
        assert server["command"] == "npx"
        assert server["args"] == ["-y", "@modelcontextprotocol/server-github"]
        assert server["env"]["GITHUB_TOKEN"] == "test_token"

    def test_add_command_type_normalized_to_stdio(self, temp_config):
        """Test that 'command' type is normalized to 'stdio'."""
        test_args = [
            "strata",
            "--config-path",
            str(temp_config),
            "add",
            "--type",
            "command",
            "test-server",
            "echo",
            "hello",
        ]

        with patch.object(sys, "argv", test_args):
            parser = create_parser()
            args = parser.parse_args(test_args[1:])
            result = args.func(args)

        assert result == 0

        # Verify the config was saved with 'stdio' type
        with open(temp_config, "r") as f:
            config = json.load(f)

        assert "test-server" in config["mcp"]["servers"]
        # The type should be normalized to 'stdio', not 'command'
        assert (
            "type" not in config["mcp"]["servers"]["test-server"]
            or config["mcp"]["servers"]["test-server"].get("type") == "stdio"
        )

    def test_remove_server(self, temp_config):
        """Test removing a server."""
        # First add a server
        server_list = MCPServerList(temp_config)
        from strata.config import MCPServerConfig

        test_server = MCPServerConfig(
            name="test-server", type="stdio", command="echo", args=["hello"]
        )
        server_list.add_server(test_server)
        server_list.save()

        # Now remove it
        test_args = [
            "strata",
            "--config-path",
            str(temp_config),
            "remove",
            "test-server",
        ]

        with patch.object(sys, "argv", test_args):
            parser = create_parser()
            args = parser.parse_args(test_args[1:])
            result = args.func(args)

        assert result == 0

        # Verify the server was removed
        with open(temp_config, "r") as f:
            config = json.load(f)

        assert "test-server" not in config["mcp"]["servers"]

    def test_remove_nonexistent_server(self, temp_config):
        """Test removing a server that doesn't exist."""
        test_args = [
            "strata",
            "--config-path",
            str(temp_config),
            "remove",
            "nonexistent",
        ]

        with patch.object(sys, "argv", test_args):
            parser = create_parser()
            args = parser.parse_args(test_args[1:])
            result = args.func(args)

        assert result == 1  # Should fail

    def test_list_servers(self, temp_config, capsys):
        """Test listing servers."""
        # Add some servers first
        server_list = MCPServerList(temp_config)
        from strata.config import MCPServerConfig

        server1 = MCPServerConfig(
            name="server1", type="sse", url="http://example.com/mcp", enabled=True
        )
        server2 = MCPServerConfig(
            name="server2", type="stdio", command="echo", args=["hello"], enabled=False
        )
        server_list.add_server(server1)
        server_list.add_server(server2)
        server_list.save()

        # List servers
        test_args = ["strata", "--config-path", str(temp_config), "list"]

        with patch.object(sys, "argv", test_args):
            parser = create_parser()
            args = parser.parse_args(test_args[1:])
            result = args.func(args)

        assert result == 0

        captured = capsys.readouterr()
        assert "server1 (sse, enabled)" in captured.out
        assert "server2 (stdio, disabled)" in captured.out

    def test_enable_server(self, temp_config):
        """Test enabling a server."""
        # Add a disabled server
        server_list = MCPServerList(temp_config)
        from strata.config import MCPServerConfig

        test_server = MCPServerConfig(
            name="test-server",
            type="stdio",
            command="echo",
            args=["hello"],
            enabled=False,
        )
        server_list.add_server(test_server)
        server_list.save()

        # Enable it
        test_args = [
            "strata",
            "--config-path",
            str(temp_config),
            "enable",
            "test-server",
        ]

        with patch.object(sys, "argv", test_args):
            parser = create_parser()
            args = parser.parse_args(test_args[1:])
            result = args.func(args)

        assert result == 0

        # Verify it was enabled
        with open(temp_config, "r") as f:
            config = json.load(f)

        assert config["mcp"]["servers"]["test-server"]["enabled"] is True

    def test_disable_server(self, temp_config):
        """Test disabling a server."""
        # Add an enabled server
        server_list = MCPServerList(temp_config)
        from strata.config import MCPServerConfig

        test_server = MCPServerConfig(
            name="test-server",
            type="stdio",
            command="echo",
            args=["hello"],
            enabled=True,
        )
        server_list.add_server(test_server)
        server_list.save()

        # Disable it
        test_args = [
            "strata",
            "--config-path",
            str(temp_config),
            "disable",
            "test-server",
        ]

        with patch.object(sys, "argv", test_args):
            parser = create_parser()
            args = parser.parse_args(test_args[1:])
            result = args.func(args)

        assert result == 0

        # Verify it was disabled
        with open(temp_config, "r") as f:
            config = json.load(f)

        assert config["mcp"]["servers"]["test-server"]["enabled"] is False

    def test_invalid_env_format(self, temp_config, capsys):
        """Test invalid environment variable format."""
        test_args = [
            "strata",
            "--config-path",
            str(temp_config),
            "add",
            "--type",
            "stdio",
            "--env",
            "INVALID_FORMAT",
            "test-server",
            "echo",
        ]

        with patch.object(sys, "argv", test_args):
            parser = create_parser()
            args = parser.parse_args(test_args[1:])
            result = args.func(args)

        assert result == 1  # Should fail

        captured = capsys.readouterr()
        assert "Invalid environment variable format" in captured.err

    def test_invalid_header_format(self, temp_config, capsys):
        """Test invalid header format."""
        test_args = [
            "strata",
            "--config-path",
            str(temp_config),
            "add",
            "--type",
            "http",
            "--header",
            "INVALID_FORMAT",
            "test-server",
            "http://example.com",
        ]

        with patch.object(sys, "argv", test_args):
            parser = create_parser()
            args = parser.parse_args(test_args[1:])
            result = args.func(args)

        assert result == 1  # Should fail

        captured = capsys.readouterr()
        assert "Invalid header format" in captured.err

    def test_cursor_user_scope(self):
        """Test adding Strata to Cursor with user scope."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock home directory
            with patch("pathlib.Path.home", return_value=Path(temp_dir)):
                test_args = ["strata", "tool", "add", "cursor", "--scope", "user"]

                with patch.object(sys, "argv", test_args):
                    parser = create_parser()
                    args = parser.parse_args(test_args[1:])
                    result = args.func(args)

                assert result == 0

                # Check that the config file was created
                cursor_config_path = Path(temp_dir) / ".cursor" / "mcp.json"
                assert cursor_config_path.exists()

                # Check the content
                with open(cursor_config_path, "r") as f:
                    config = json.load(f)

                assert "mcpServers" in config
                assert "strata" in config["mcpServers"]
                assert config["mcpServers"]["strata"]["command"] == "strata"

    def test_cursor_project_scope(self):
        """Test adding Strata to Cursor with project scope."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory to simulate project directory
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                test_args = ["strata", "tool", "add", "cursor", "--scope", "project"]

                with patch.object(sys, "argv", test_args):
                    parser = create_parser()
                    args = parser.parse_args(test_args[1:])
                    result = args.func(args)

                assert result == 0

                # Check that the config file was created
                cursor_config_path = Path(temp_dir) / ".cursor" / "mcp.json"
                assert cursor_config_path.exists()

                # Check the content
                with open(cursor_config_path, "r") as f:
                    config = json.load(f)

                assert "mcpServers" in config
                assert "strata" in config["mcpServers"]
                assert config["mcpServers"]["strata"]["command"] == "strata"

            finally:
                os.chdir(original_cwd)

    def test_cursor_existing_config(self):
        """Test adding Strata to existing Cursor configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing config
            cursor_config_path = Path(temp_dir) / ".cursor" / "mcp.json"
            cursor_config_path.parent.mkdir(parents=True)

            existing_config = {
                "mcpServers": {
                    "existing-server": {"command": "some-command", "args": ["--flag"]}
                },
                "otherConfig": {"someValue": "test"},
            }

            with open(cursor_config_path, "w") as f:
                json.dump(existing_config, f)

            # Change to temp directory
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                test_args = ["strata", "tool", "add", "cursor", "--scope", "project"]

                with patch.object(sys, "argv", test_args):
                    parser = create_parser()
                    args = parser.parse_args(test_args[1:])
                    result = args.func(args)

                assert result == 0

                # Check that existing config is preserved
                with open(cursor_config_path, "r") as f:
                    config = json.load(f)

                # Existing server should be preserved
                assert "existing-server" in config["mcpServers"]
                assert (
                    config["mcpServers"]["existing-server"]["command"] == "some-command"
                )

                # Other config should be preserved
                assert "otherConfig" in config
                assert config["otherConfig"]["someValue"] == "test"

                # Strata should be added
                assert "strata" in config["mcpServers"]
                assert config["mcpServers"]["strata"]["command"] == "strata"

            finally:
                os.chdir(original_cwd)
