"""Tests for tool integration utilities."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from strata.utils.tool_integration import (
    add_strata_to_cursor,
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

    def test_add_strata_to_cursor_invalid_scope(self):
        """Test adding Strata to Cursor with invalid scope."""
        result = add_strata_to_cursor("invalid")
        assert result == 1

    def test_ensure_json_config_invalid_json_aborts(self):
        """Test that invalid JSON in existing config aborts instead of silently replacing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.json"
            config_path.write_text("{invalid json", encoding="utf-8")

            with pytest.raises(SystemExit):
                ensure_json_config(config_path)

    def test_save_json_config_atomic_write(self):
        """Test that save uses atomic write and doesn't corrupt on failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.json"

            # Write initial data
            initial_data = {"existing": "servers"}
            save_json_config(config_path, initial_data)

            # Overwrite with new data
            new_data = {"existing": "servers", "mcpServers": {"strata": {}}}
            save_json_config(config_path, new_data)

            with open(config_path, "r") as f:
                saved = json.load(f)
            assert saved == new_data

            # No leftover temp files
            tmp_files = list(Path(temp_dir).glob(".mcp_*.tmp"))
            assert len(tmp_files) == 0

    def test_add_strata_to_cursor_creates_backup(self):
        """Test that existing config is backed up before modification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pathlib.Path.home", return_value=Path(temp_dir)):
                # Create existing config
                cursor_dir = Path(temp_dir) / ".cursor"
                cursor_dir.mkdir()
                config_path = cursor_dir / "mcp.json"
                original = {"mcpServers": {"other": {"command": "other"}}}
                with open(config_path, "w") as f:
                    json.dump(original, f)

                result = add_strata_to_cursor("user", yes=True)
                assert result == 0

                # Backup should exist with original content
                backup_path = config_path.with_suffix(".json.bak")
                assert backup_path.exists()
                with open(backup_path, "r") as f:
                    backup_data = json.load(f)
                assert backup_data == original

    def test_add_strata_to_cursor_confirmation_denied(self):
        """Test that user can abort when confirmation is denied."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pathlib.Path.home", return_value=Path(temp_dir)):
                # Create existing config so confirmation triggers
                cursor_dir = Path(temp_dir) / ".cursor"
                cursor_dir.mkdir()
                config_path = cursor_dir / "mcp.json"
                original = {"mcpServers": {}}
                with open(config_path, "w") as f:
                    json.dump(original, f)

                with patch("builtins.input", return_value="n"):
                    result = add_strata_to_cursor("user")
                    assert result == 1

                # Config should be unchanged
                with open(config_path, "r") as f:
                    data = json.load(f)
                assert data == original

    def test_add_strata_to_cursor_yes_skips_confirmation(self):
        """Test that yes=True skips the confirmation prompt."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pathlib.Path.home", return_value=Path(temp_dir)):
                cursor_dir = Path(temp_dir) / ".cursor"
                cursor_dir.mkdir()
                config_path = cursor_dir / "mcp.json"
                with open(config_path, "w") as f:
                    json.dump({"mcpServers": {}}, f)

                # Should succeed without prompting
                result = add_strata_to_cursor("user", yes=True)
                assert result == 0

                with open(config_path, "r") as f:
                    config = json.load(f)
                assert "strata" in config["mcpServers"]
