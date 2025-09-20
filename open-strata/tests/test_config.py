"""Test cases for MCPServerList configuration parsing."""

import json
import tempfile
from pathlib import Path

from strata.config import MCPServerConfig, MCPServerList


class TestMCPServerList:
    """Test MCPServerList functionality."""

    def test_parse_mcp_config_format(self):
        """Test parsing MCP config format with servers section."""
        # Create a sample MCP config
        mcp_config = {
            "mcp": {
                "servers": {
                    "github": {
                        "command": "docker",
                        "args": [
                            "run",
                            "-i",
                            "--rm",
                            "-e",
                            "GITHUB_PERSONAL_ACCESS_TOKEN",
                            "ghcr.io/github/github-mcp-server",
                        ],
                        "env": {
                            "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
                        },
                    },
                    "filesystem": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                    },
                }
            }
        }

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(mcp_config, f)
            config_path = Path(f.name)

        try:
            # Create MCPServerList instance
            server_list = MCPServerList(config_path)

            # Verify servers were loaded correctly
            assert len(server_list.servers) == 2

            # Check GitHub server
            github_server = server_list.get_server("github")
            assert github_server is not None
            assert github_server.name == "github"
            assert github_server.command == "docker"
            assert github_server.args == [
                "run",
                "-i",
                "--rm",
                "-e",
                "GITHUB_PERSONAL_ACCESS_TOKEN",
                "ghcr.io/github/github-mcp-server",
            ]
            assert github_server.env == {
                "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
            }

            # Check filesystem server
            fs_server = server_list.get_server("filesystem")
            assert fs_server is not None
            assert fs_server.name == "filesystem"
            assert fs_server.command == "npx"
            assert fs_server.args == ["-y", "@modelcontextprotocol/server-filesystem"]
            # Description field was removed from MCPServerConfig

        finally:
            # Clean up
            config_path.unlink()

    def test_parse_legacy_format(self):
        """Test parsing legacy servers format (current implementation)."""
        legacy_config = {
            "servers": {
                "test-server": {
                    "name": "test-server",
                    "command": "python",
                    "args": ["-m", "test"],
                    "env": {"TEST_VAR": "value"},
                    "enabled": True,
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(legacy_config, f)
            config_path = Path(f.name)

        try:
            server_list = MCPServerList(config_path)

            assert len(server_list.servers) == 1
            server = server_list.get_server("test-server")
            assert server is not None
            assert server.name == "test-server"
            assert server.command == "python"
            assert server.args == ["-m", "test"]
            assert server.env == {"TEST_VAR": "value"}
            assert server.enabled is True

        finally:
            config_path.unlink()

    def test_add_server_override(self):
        """Test that adding a server with existing name overrides it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            server_list = MCPServerList(config_path)

            # Add initial server
            server1 = MCPServerConfig(
                name="test",
                command="python",
                args=["-m", "test1"],
            )
            result1 = server_list.add_server(server1)

            # Verify it was added
            assert result1 is True
            assert len(server_list.servers) == 1
            assert server_list.get_server("test").command == "python"

            # Add server with same name (should override)
            server2 = MCPServerConfig(
                name="test",
                command="node",
                args=["test2.js"],
            )
            result2 = server_list.add_server(server2)

            # Verify it was overridden
            assert result2 is True
            assert len(server_list.servers) == 1
            assert server_list.get_server("test").command == "node"
            assert server_list.get_server("test").args == ["test2.js"]

    def test_add_server_returns_false_for_identical(self):
        """Test that add_server returns False when configuration is identical."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            server_list = MCPServerList(config_path)

            # Create a server configuration
            server = MCPServerConfig(
                name="test-server",
                command="python",
                args=["-m", "test"],
                env={"KEY": "value"},
                enabled=True,
            )

            # First add should return True
            result1 = server_list.add_server(server)
            assert result1 is True
            assert "test-server" in server_list.servers

            # Adding identical server should return False
            identical_server = MCPServerConfig(
                name="test-server",
                command="python",
                args=["-m", "test"],
                env={"KEY": "value"},
                enabled=True,
            )
            result2 = server_list.add_server(identical_server)
            assert result2 is False

    def test_add_server_returns_true_for_different_config(self):
        """Test that add_server returns True when configuration is different."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            server_list = MCPServerList(config_path)

            # Create initial server
            server1 = MCPServerConfig(
                name="test-server",
                command="python",
                args=["-m", "test"],
                env={"KEY": "value"},
                enabled=True,
            )

            # First add
            result1 = server_list.add_server(server1)
            assert result1 is True

            # Modified server with same name but different config
            server2 = MCPServerConfig(
                name="test-server",
                command="node",  # Different command
                args=["-m", "test"],
                env={"KEY": "value"},
                enabled=True,
            )
            result2 = server_list.add_server(server2)
            assert result2 is True
            assert server_list.get_server("test-server").command == "node"

    def test_add_server_detects_small_differences(self):
        """Test that add_server detects small differences in configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            server_list = MCPServerList(config_path)

            base_server = MCPServerConfig(
                name="test",
                command="python",
                args=["arg1", "arg2"],
                env={"KEY1": "value1"},
                enabled=True,
            )

            # Add initial server
            assert server_list.add_server(base_server) is True

            # Test different args
            server_diff_args = MCPServerConfig(
                name="test",
                command="python",
                args=["arg1", "arg3"],  # Different arg
                env={"KEY1": "value1"},
                enabled=True,
            )
            assert server_list.add_server(server_diff_args) is True

            # Test different env
            server_diff_env = MCPServerConfig(
                name="test",
                command="python",
                args=["arg1", "arg3"],
                env={"KEY1": "value2"},  # Different value
                enabled=True,
            )
            assert server_list.add_server(server_diff_env) is True

            # Test different enabled status
            server_diff_enabled = MCPServerConfig(
                name="test",
                command="python",
                args=["arg1", "arg3"],
                env={"KEY1": "value2"},
                enabled=False,  # Different enabled status
            )
            assert server_list.add_server(server_diff_enabled) is True

            # Test identical to last one
            server_identical = MCPServerConfig(
                name="test",
                command="python",
                args=["arg1", "arg3"],
                env={"KEY1": "value2"},
                enabled=False,
            )
            assert server_list.add_server(server_identical) is False

    def test_add_new_server_always_returns_true(self):
        """Test that adding a new server always returns True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            server_list = MCPServerList(config_path)

            server1 = MCPServerConfig(name="server1", command="cmd1")
            server2 = MCPServerConfig(name="server2", command="cmd2")

            assert server_list.add_server(server1) is True
            assert server_list.add_server(server2) is True
            assert len(server_list.servers) == 2

    def test_empty_config_file(self):
        """Test handling of empty config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            config_path = Path(f.name)

        try:
            server_list = MCPServerList(config_path)
            assert len(server_list.servers) == 0
        finally:
            config_path.unlink()

    def test_nonexistent_config_file(self):
        """Test handling when config file doesn't exist."""
        config_path = Path("/tmp/nonexistent_config_12345.json")
        server_list = MCPServerList(config_path)

        # Should start with empty servers (no defaults)
        assert len(server_list.servers) == 0

    def test_save_mcp_format(self):
        """Test saving servers in MCP format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"

            # Create and save servers in MCP format
            server_list = MCPServerList(config_path, use_mcp_format=True)
            server = MCPServerConfig(
                name="test",
                command="python",
                args=["-m", "test"],
                env={"KEY": "value"},
            )
            server_list.add_server(server)

            # Load the saved file and verify format
            with open(config_path, "r") as f:
                saved_data = json.load(f)

            # Should save in MCP format
            assert "mcp" in saved_data
            assert "servers" in saved_data["mcp"]
            assert "test" in saved_data["mcp"]["servers"]

            # Verify the saved data structure
            test_server = saved_data["mcp"]["servers"]["test"]
            assert test_server["command"] == "python"
            assert test_server["args"] == ["-m", "test"]
            assert test_server["env"] == {"KEY": "value"}
            assert test_server["enabled"] is True

    def test_save_legacy_format(self):
        """Test saving servers in legacy format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"

            # Create and save servers in legacy format
            server_list = MCPServerList(config_path, use_mcp_format=False)
            server = MCPServerConfig(
                name="test",
                command="python",
                args=["-m", "test"],
                env={"KEY": "value"},
            )
            server_list.add_server(server)

            # Load the saved file and verify format
            with open(config_path, "r") as f:
                saved_data = json.load(f)

            # Should save in legacy format
            assert "servers" in saved_data
            assert "test" in saved_data["servers"]
            assert saved_data["servers"]["test"]["name"] == "test"

    def test_mixed_env_variables(self):
        """Test handling of environment variables with template syntax."""
        config = {
            "mcp": {
                "servers": {
                    "mixed-env": {
                        "command": "test",
                        "args": [],
                        "env": {
                            "NORMAL_VAR": "plain_value",
                            "TEMPLATE_VAR": "${input:some_token}",
                            "MIXED_VAR": "prefix_${input:token}_suffix",
                        },
                    }
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            config_path = Path(f.name)

        try:
            server_list = MCPServerList(config_path)
            server = server_list.get_server("mixed-env")

            assert server is not None
            assert server.env["NORMAL_VAR"] == "plain_value"
            assert server.env["TEMPLATE_VAR"] == "${input:some_token}"
            assert server.env["MIXED_VAR"] == "prefix_${input:token}_suffix"

        finally:
            config_path.unlink()

    def test_mcp_format_round_trip(self):
        """Test saving and loading servers in MCP format preserves data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"

            # Create servers with various configurations
            server_list1 = MCPServerList(config_path, use_mcp_format=True)

            server1 = MCPServerConfig(
                name="github",
                command="docker",
                args=["run", "-i", "--rm", "ghcr.io/github/github-mcp-server"],
                env={"GITHUB_TOKEN": "${input:github_token}"},
            )
            server_list1.add_server(server1)

            server2 = MCPServerConfig(
                name="filesystem",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"],
            )
            server_list1.add_server(server2)

            server3 = MCPServerConfig(
                name="disabled-server",
                command="test",
                args=["arg1", "arg2"],
                enabled=False,
            )
            server_list1.add_server(server3)

            # Load from the same file
            server_list2 = MCPServerList(config_path)

            # Verify all servers were loaded correctly
            assert len(server_list2.servers) == 3

            # Check GitHub server
            github = server_list2.get_server("github")
            assert github.command == "docker"
            assert github.args == [
                "run",
                "-i",
                "--rm",
                "ghcr.io/github/github-mcp-server",
            ]
            assert github.env == {"GITHUB_TOKEN": "${input:github_token}"}
            assert github.name == "github"
            assert github.enabled is True

            # Check filesystem server
            fs = server_list2.get_server("filesystem")
            assert fs.command == "npx"
            assert fs.args == ["-y", "@modelcontextprotocol/server-filesystem"]
            assert fs.name == "filesystem"
            assert fs.env == {}
            assert fs.enabled is True

            # Check disabled server
            disabled = server_list2.get_server("disabled-server")
            assert disabled.command == "test"
            assert disabled.args == ["arg1", "arg2"]
            assert disabled.enabled is False
            assert disabled.enabled is False
