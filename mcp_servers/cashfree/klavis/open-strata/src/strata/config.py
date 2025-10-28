"""Configuration for MCP servers similar to VSCode's MCP server list."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from platformdirs import user_config_dir
from watchgod import awatch


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    name: str
    # Transport type
    type: str = "stdio"  # "stdio", "sse", or "http"
    # For stdio/command type
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    # For url type
    url: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    # Common fields
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    # Authentication info could be added here later
    auth: str = ""  # "none", "oauth2", etc.

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.type in ["sse", "http"]:
            if not self.url:
                raise ValueError(f"{self.type.upper()} type requires 'url' field")
        else:  # stdio/command
            if not self.command:
                raise ValueError("Command type requires 'command' field")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "name": self.name,
            "type": self.type,
            "enabled": self.enabled,
        }

        if self.type in ["sse", "http"]:
            result["url"] = self.url
            if self.headers:
                result["headers"] = self.headers
        else:  # stdio/command
            result["command"] = self.command
            result["args"] = self.args

        if self.env:
            result["env"] = self.env
        if self.auth:
            result["auth"] = self.auth

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary representation."""
        type_val = data.get("type", "stdio")

        if type_val in ["sse", "http"]:
            return cls(
                name=data["name"],
                type=type_val,
                url=data.get("url"),
                headers=data.get("headers", {}),
                env=data.get("env", {}),
                enabled=data.get("enabled", True),
                auth=data.get("auth", ""),
            )
        else:  # stdio/command
            return cls(
                name=data["name"],
                type=type_val,
                command=data.get("command"),
                args=data.get("args", []),
                env=data.get("env", {}),
                enabled=data.get("enabled", True),
            )


class MCPServerList:
    """Manage a list of MCP server configurations."""

    def __init__(self, config_path: Optional[Path] = None, use_mcp_format: bool = True):
        """Initialize the MCP server list.

        Args:
            config_path: Path to the configuration file. If None, uses default.
            use_mcp_format: If True, save in MCP format. If False, use legacy format.
        """
        if config_path is None:
            # Use platformdirs for cross-platform config directory
            config_dir = Path(user_config_dir("strata"))
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / "servers.json"
        else:
            self.config_path = Path(config_path)

        self.servers: Dict[str, MCPServerConfig] = {}
        self.use_mcp_format = use_mcp_format
        self.load()

    def load(self) -> None:
        """Load server configurations from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # Check if it's MCP format (has "mcp" key with "servers" inside)
                    if "mcp" in data and "servers" in data["mcp"]:
                        # Parse MCP format
                        for name, config in data["mcp"]["servers"].items():
                            # MCP format doesn't have "name" field, add it
                            config_dict = {
                                "name": name,
                                "type": config.get("type", "stdio"),
                                "env": config.get("env", {}),
                                "enabled": config.get("enabled", True),
                            }

                            # Add type-specific fields
                            if config.get("type") in ["sse", "http"]:
                                config_dict["url"] = config.get("url")
                                config_dict["headers"] = config.get("headers", {})
                                config_dict["auth"] = config.get("auth", "")
                            else:  # stdio/command
                                config_dict["command"] = config.get("command", "")
                                config_dict["args"] = config.get("args", [])

                            self.servers[name] = MCPServerConfig.from_dict(config_dict)
                    # Otherwise check for legacy format
                    elif "servers" in data:
                        # Parse legacy format
                        for name, config in data["servers"].items():
                            self.servers[name] = MCPServerConfig.from_dict(config)
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {e}")

    def save(self) -> None:
        """Save server configurations to file."""
        if self.use_mcp_format:
            # Save in MCP format
            servers_dict = {}
            for name, server in self.servers.items():
                server_config = {}

                # Add type field if not stdio (default)
                if server.type and server.type != "stdio":
                    server_config["type"] = server.type

                # Add type-specific fields
                if server.type in ["sse", "http"]:
                    server_config["url"] = server.url
                    if server.headers:
                        server_config["headers"] = server.headers
                    if server.auth:
                        server_config["auth"] = server.auth
                else:  # stdio/command
                    server_config["command"] = server.command
                    server_config["args"] = server.args

                if server.env:
                    server_config["env"] = server.env
                # Always save enabled field to be explicit
                server_config["enabled"] = server.enabled
                servers_dict[name] = server_config

            data = {"mcp": {"servers": servers_dict}}
        else:
            # Save in legacy format
            data = {
                "servers": {
                    name: server.to_dict() for name, server in self.servers.items()
                }
            }

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add_server(self, server: MCPServerConfig) -> bool:
        """Add or update a server configuration.

        Args:
            server: Server configuration to add or update.
                    If a server with the same name exists, it will be overridden.

        Returns:
            True if server was added/updated, False if configuration is identical
        """
        if server.name in self.servers and self.servers[server.name] == server:
            # Configuration is identical, no need to update
            return False

        # Add or update server
        self.servers[server.name] = server
        self.save()
        return True

    def remove_server(self, name: str) -> bool:
        """Remove a server configuration.

        Args:
            name: Name of the server to remove

        Returns:
            True if server was removed, False if not found
        """
        if name in self.servers:
            del self.servers[name]
            self.save()
            return True
        return False

    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get a server configuration by name.

        Args:
            name: Name of the server

        Returns:
            Server configuration or None if not found
        """
        return self.servers.get(name)

    def list_servers(self, enabled_only: bool = False) -> List[MCPServerConfig]:
        """List all server configurations.

        Args:
            enabled_only: If True, only return enabled servers

        Returns:
            List of server configurations
        """
        servers = list(self.servers.values())
        if enabled_only:
            servers = [s for s in servers if s.enabled]
        return servers

    def enable_server(self, name: str) -> bool:
        """Enable a server.

        Args:
            name: Name of the server to enable

        Returns:
            True if server was enabled, False if not found
        """
        if name in self.servers:
            self.servers[name].enabled = True
            self.save()
            return True
        return False

    def disable_server(self, name: str) -> bool:
        """Disable a server.

        Args:
            name: Name of the server to disable

        Returns:
            True if server was disabled, False if not found
        """
        if name in self.servers:
            self.servers[name].enabled = False
            self.save()
            return True
        return False

    async def watch_config(
        self,
        on_changed: Callable[[Dict[str, MCPServerConfig]], None],
    ):
        """Watch configuration file for changes and trigger callback.

        Args:
            on_changed: Callback when configuration changes, receives new server dict
        """
        async for changes in awatch(str(self.config_path.parent)):
            # Check if our config file was modified
            config_changed = False
            for _, path in changes:
                if Path(path) == self.config_path:
                    config_changed = True
                    break

            if not config_changed:
                continue

            # Reload configuration
            self.servers.clear()
            self.load()

            # Trigger callback with new server list
            on_changed(dict(self.servers))


# Global instance for easy access
mcp_server_list = MCPServerList()
