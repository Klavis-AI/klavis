"""Tool integration utilities for adding Strata to various IDEs and editors."""

import json
import subprocess
import sys
from pathlib import Path


def update_json_recursively(data: dict, keys: list, value) -> dict:
    """Recursively update a nested dictionary, creating keys as needed.

    Args:
        data: The dictionary to update
        keys: List of keys representing the path to update
        value: The value to set at the path

    Returns:
        The updated dictionary
    """
    if not keys:
        return data

    if len(keys) == 1:
        # Base case: set the value
        key = keys[0]
        if isinstance(data.get(key), dict) and isinstance(value, dict):
            # Merge dictionaries if both are dict type
            data[key] = {**data.get(key, {}), **value}
        else:
            data[key] = value
        return data

    # Recursive case: ensure intermediate keys exist
    key = keys[0]
    if key not in data:
        data[key] = {}
    elif not isinstance(data[key], dict):
        # If the existing value is not a dict, replace it with dict
        data[key] = {}

    data[key] = update_json_recursively(data[key], keys[1:], value)
    return data


def ensure_json_config(config_path: Path) -> dict:
    """Ensure JSON configuration file exists and return its content.

    Args:
        config_path: Path to the configuration file

    Returns:
        The configuration dictionary
    """
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing config or create empty one
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(
                f"Warning: Could not read existing config {config_path}: {e}",
                file=sys.stderr,
            )
            print("Creating new configuration file", file=sys.stderr)

    return {}


def save_json_config(config_path: Path, config: dict) -> None:
    """Save JSON configuration to file.

    Args:
        config_path: Path to save the configuration
        config: Configuration dictionary to save
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def check_cli_available(target: str) -> bool:
    """Check if a CLI tool is available.

    Args:
        target: Name of the CLI tool to check

    Returns:
        True if the CLI tool is available, False otherwise
    """
    try:
        if target == "vscode":
            # Check for VSCode CLI (code command)
            result = subprocess.run(
                ["code", "--version"], capture_output=True, text=True, timeout=5
            )
        else:
            result = subprocess.run(
                [target, "--version"], capture_output=True, text=True, timeout=5
            )

        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def add_strata_to_cursor(scope: str = "user") -> int:
    """Add Strata to Cursor MCP configuration.

    Args:
        scope: Configuration scope (user, project, or local)

    Returns:
        0 on success, 1 on error
    """
    try:
        # Determine config path based on scope
        if scope == "user":
            # User scope: ~/.cursor/mcp.json
            cursor_config_path = Path.home() / ".cursor" / "mcp.json"
        elif scope in ["project", "local"]:
            # Project scope: .cursor/mcp.json in current directory
            cursor_config_path = Path.cwd() / ".cursor" / "mcp.json"
        else:
            print(
                f"Error: Unsupported scope '{scope}' for Cursor. Supported: user, project, local",
                file=sys.stderr,
            )
            return 1

        print(
            f"Adding Strata to Cursor with scope '{scope}' at {cursor_config_path}..."
        )

        # Load or create cursor configuration
        cursor_config = ensure_json_config(cursor_config_path)

        # Create Strata server configuration for Cursor
        strata_server_config = {"command": "strata", "args": []}

        # Update configuration using recursive update
        cursor_config = update_json_recursively(
            cursor_config, ["mcpServers", "strata"], strata_server_config
        )

        # Save updated configuration
        save_json_config(cursor_config_path, cursor_config)
        print("✓ Successfully added Strata to Cursor MCP configuration")
        return 0

    except (IOError, OSError) as e:
        print(f"Error handling Cursor configuration: {e}", file=sys.stderr)
        return 1


def add_strata_to_vscode() -> int:
    """Add Strata to VSCode MCP configuration.

    Returns:
        0 on success, 1 on error
    """
    try:
        # VSCode uses JSON format: code --add-mcp '{"name":"strata","command":"strata"}'
        mcp_config = {"name": "strata", "command": "strata"}
        mcp_json = json.dumps(mcp_config)

        print("Adding Strata to VSCode...")
        cmd = ["code", "--add-mcp", mcp_json]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✓ Successfully added Strata to VSCode MCP configuration")
            if result.stdout.strip():
                print(result.stdout)
            return 0
        else:
            print(
                f"Error adding Strata to VSCode: {result.stderr.strip()}",
                file=sys.stderr,
            )
            return result.returncode

    except subprocess.SubprocessError as e:
        print(f"Error running VSCode command: {e}", file=sys.stderr)
        return 1


def add_strata_to_claude_or_gemini(target: str, scope: str = "user") -> int:
    """Add Strata to Claude or Gemini MCP configuration.

    Args:
        target: Target CLI tool (claude or gemini)
        scope: Configuration scope

    Returns:
        0 on success, 1 on error
    """
    try:
        # Claude and Gemini use the original format
        cmd = [target, "mcp", "add"]
        cmd.extend(["--scope", scope])
        cmd.extend(["strata", "strata"])

        print(f"Adding Strata to {target} with scope '{scope}'...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✓ Successfully added Strata to {target} MCP configuration")
            if result.stdout.strip():
                print(result.stdout)
            return 0
        else:
            print(
                f"Error adding Strata to {target}: {result.stderr.strip()}",
                file=sys.stderr,
            )
            return result.returncode

    except subprocess.SubprocessError as e:
        print(f"Error running {target} command: {e}", file=sys.stderr)
        return 1


def add_strata_to_tool(target: str, scope: str = "user") -> int:
    """Add Strata MCP server to specified tool configuration.

    Args:
        target: Target tool (claude, gemini, vscode, cursor)
        scope: Configuration scope

    Returns:
        0 on success, 1 on error
    """
    target = target.lower()

    # Validate target
    if target not in ["claude", "gemini", "vscode", "cursor"]:
        print(
            f"Error: Unsupported target '{target}'. Supported targets: claude, gemini, vscode, cursor",
            file=sys.stderr,
        )
        return 1

    # VSCode doesn't support scope parameter
    if target == "vscode" and scope != "user":
        print(
            "Warning: VSCode doesn't support scope parameter, using default behavior",
            file=sys.stderr,
        )

    # Check if the target CLI is available (skip for cursor as we handle files directly)
    if target != "cursor":
        if not check_cli_available(target):
            cli_name = "code" if target == "vscode" else target
            print(
                f"Error: {cli_name} CLI not found. Please install {cli_name} CLI first.",
                file=sys.stderr,
            )
            return 1

    # Handle each target
    if target == "cursor":
        return add_strata_to_cursor(scope)
    elif target == "vscode":
        return add_strata_to_vscode()
    else:  # claude or gemini
        return add_strata_to_claude_or_gemini(target, scope)
