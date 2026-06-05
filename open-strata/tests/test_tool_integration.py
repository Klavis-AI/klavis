"""Tests for tool integration utilities."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from strata.utils.tool_integration import (
    add_strata_to_cursor,
    backup_json_config,
    ensure_json_config,
    save_json_config,
    update_json_recursively,
)


class TestToolIntegration:
    """Test tool integration utilities."""

    def test_update_json_recursively_simple(self):
        """Test updating a simple nested dictionary."""
        data = {}
        result = update_json_recursively(data, ["key"], "value")
        assert result["key"] == "value"

    def test_update_json_recursively_nested(self):
        """Test updating a deeply nested dictionary."""
        data = {}
        result = update_json_recursively(data, ["level1", "level2", "key"], "value")
        assert result["level1"]["level2"]["key"] == "value"

    def test_update_json_recursively_merge_dict(self):
        """Test merging dictionaries."""
        data = {"existing": {"keep": "this"}}
        new_value = {"new": "data"}
        result = update_json_recursively(data, ["existing"], new_value)

        assert result["existing"]["keep"] == "this"
        assert result["existing"]["new"] == "data"

    def test_update_json_recursively_overwrite_existing(self):
        """Test overwriting existing keys."""
        data = {"existing": {"old": "value"}}
        result = update_json_recursively(data, ["existing", "old"], "new_value")
        assert result["existing"]["old"] == "new_value"

    def test_ensure_json_config_new_file(self):
        """Test creating new config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.json"
            config = ensure_json_config(config_path)

            assert isinstance(config, dict)
            assert len(config) == 0

    def test_ensure_json_config_existing_file(self):
        """Test reading existing config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.json"

            # Create existing config
            existing_data = {"existing": "data"}
            with open(config_path, "w") as f:
                json.dump(existing_data, f)

            config = ensure_json_config(config_path)
            assert config["existing"] == "data"

    def test_save_json_config(self):
        """Test saving JSON config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.json"
            data = {"test": "data"}

            save_json_config(config_path, data)

            assert config_path.exists()
            with open(config_path, "r") as f:
                saved_data = json.load(f)

            assert saved_data["test"] == "data"

    def test_backup_json_config_existing_file(self):
        """Test backing up an existing JSON config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.json"
            original_data = {"existing": "data"}

            with open(config_path, "w") as f:
                json.dump(original_data, f)

            backup_path = backup_json_config(config_path)

            assert backup_path is not None
            assert backup_path.exists()
            assert backup_path.name.startswith("test.json.")
            assert backup_path.name.endswith(".bak")

            with open(backup_path, "r") as f:
                backup_data = json.load(f)

            assert backup_data == original_data

    def test_backup_json_config_missing_file(self):
        """Test backup is skipped when the config does not exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "missing.json"
            assert backup_json_config(config_path) is None

    def test_add_strata_to_cursor_user_scope(self):
        """Test adding Strata to Cursor user scope."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pathlib.Path.home", return_value=Path(temp_dir)):
                result = add_strata_to_cursor("user")

                assert result == 0

                # Check config was created
                config_path = Path(temp_dir) / ".cursor" / "mcp.json"
                assert config_path.exists()

                with open(config_path, "r") as f:
                    config = json.load(f)

                assert "mcpServers" in config
                assert "strata" in config["mcpServers"]
                assert config["mcpServers"]["strata"]["command"] == "strata"

    def test_add_strata_to_cursor_project_scope(self):
        """Test adding Strata to Cursor project scope."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                result = add_strata_to_cursor("project")

                assert result == 0

                # Check config was created
                config_path = Path(temp_dir) / ".cursor" / "mcp.json"
                assert config_path.exists()

                with open(config_path, "r") as f:
                    config = json.load(f)

                assert "mcpServers" in config
                assert "strata" in config["mcpServers"]
                assert config["mcpServers"]["strata"]["command"] == "strata"

            finally:
                os.chdir(original_cwd)

    def test_add_strata_to_cursor_backs_up_existing_config(self):
        """Test adding Strata to Cursor backs up an existing changed config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / ".cursor" / "mcp.json"
            config_path.parent.mkdir(parents=True)
            existing_config = {
                "mcpServers": {
                    "existing-server": {"command": "existing", "args": []}
                }
            }

            with open(config_path, "w") as f:
                json.dump(existing_config, f)

            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                result = add_strata_to_cursor("project")

                assert result == 0
                backups = list(config_path.parent.glob("mcp.json.*.bak"))
                assert len(backups) == 1

                with open(backups[0], "r") as f:
                    backup_data = json.load(f)
                assert backup_data == existing_config

                with open(config_path, "r") as f:
                    updated_config = json.load(f)
                assert "strata" in updated_config["mcpServers"]
                assert "existing-server" in updated_config["mcpServers"]

            finally:
                os.chdir(original_cwd)

    def test_add_strata_to_cursor_skips_backup_when_unchanged(self):
        """Test backup is skipped if Strata is already configured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / ".cursor" / "mcp.json"
            config_path.parent.mkdir(parents=True)
            existing_config = {
                "mcpServers": {"strata": {"command": "strata", "args": []}}
            }

            with open(config_path, "w") as f:
                json.dump(existing_config, f)

            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                result = add_strata_to_cursor("project")

                assert result == 0
                assert list(config_path.parent.glob("mcp.json.*.bak")) == []

            finally:
                os.chdir(original_cwd)

    def test_add_strata_to_cursor_invalid_scope(self):
        """Test adding Strata to Cursor with invalid scope."""
        result = add_strata_to_cursor("invalid")
        assert result == 1
