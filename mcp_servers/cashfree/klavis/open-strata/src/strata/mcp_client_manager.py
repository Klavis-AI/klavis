"""MCP Client Manager for managing multiple MCP server connections."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

from strata.config import MCPServerConfig, MCPServerList
from strata.mcp_proxy.client import MCPClient
from strata.mcp_proxy.transport.http import HTTPTransport
from strata.mcp_proxy.transport.stdio import StdioTransport

logger = logging.getLogger(__name__)


class MCPClientManager:
    """Manages multiple MCP client connections based on configuration."""

    def __init__(self, config_path: Optional[Path] = None, server_names: Optional[List[str]] = None):
        """Initialize the MCP client manager.

        Args:
            config_path: Optional path to configuration file.
                        If None, uses default from MCPServerList.
            server_names: Optional list of specific server names to initialize.
                         If None, all enabled servers will be initialized.
        """
        self.server_list = MCPServerList(config_path)
        self.server_names = server_names  # Specific servers to manage
        self.active_clients: Dict[str, MCPClient] = {}
        self.active_transports: Dict[str, HTTPTransport | StdioTransport] = {}
        # Cache of current server configs for comparison during sync
        self.cached_configs: List[MCPServerConfig] = []
        # Mutex to prevent concurrent sync operations
        self._sync_lock = asyncio.Lock()

    async def initialize_from_config(self) -> Dict[str, bool]:
        """Initialize MCP clients from configuration.

        Only initializes servers that are enabled in the configuration.
        If server_names was specified in __init__, only those servers will be initialized.

        Returns:
            Dict mapping server names to success status (True if connected)
        """
        results = {}
        enabled_servers = self.server_list.list_servers(enabled_only=True)
        
        # Filter servers if specific names were provided
        if self.server_names:
            enabled_servers = [s for s in enabled_servers if s.name in self.server_names]

        for server in enabled_servers:
            try:
                await self._connect_server(server)
                results[server.name] = True
                logger.info(f"Successfully connected to MCP server: {server.name}")
            except Exception as e:
                results[server.name] = False
                logger.error(f"Failed to connect to MCP server {server.name}: {e}")

        # Cache all server configs (both enabled and disabled) for future comparisons
        self.cached_configs = self.server_list.list_servers()

        return results
    
    async def authenticate_server(self, server_name: str) -> None:
        """Authenticate a single MCP server.

        Args:
            server_name: Name of the server to authenticate
        """
        if server_name in self.active_clients:
            client = self.active_clients[server_name]
            try:
                await client.initialize()
                await client.disconnect()
                logger.info(f"Initialized MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error initializing {server_name}: {e}")

    async def _connect_server(self, server: MCPServerConfig) -> None:
        """Connect to a single MCP server.

        Args:
            server: Server configuration

        Raises:
            Exception: If connection fails
        """
        # Create transport based on type
        if server.type in ["sse", "http"]:
            if not server.url:
                raise ValueError(f"Server {server.name} has no URL configured")

            transport = HTTPTransport(
                server_name=server.name,
                url=server.url,
                mode=server.type,  # "http" or "sse" # type: ignore
                headers=server.headers,
                auth=server.auth
            )
        else:  # stdio/command
            if not server.command:
                raise ValueError(f"Server {server.name} has no command configured")
            transport = StdioTransport(
                command=server.command, args=server.args, env=server.env
            )

        # Create client
        client = MCPClient(transport)

        # Connect
        await client.connect()

        # Store active client and transport
        self.active_clients[server.name] = client
        self.active_transports[server.name] = transport

    async def _disconnect_server(self, server_name: str) -> None:
        """Disconnect from a single MCP server.

        Args:
            server_name: Name of the server to disconnect
        """
        if server_name in self.active_clients:
            client = self.active_clients[server_name]
            try:
                await client.disconnect()
                logger.info(f"Disconnected from MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {server_name}: {e}")
            finally:
                # Remove from active clients
                del self.active_clients[server_name]
                if server_name in self.active_transports:
                    del self.active_transports[server_name]

    async def sync_with_config(self, new_servers: Dict[str, MCPServerConfig]) -> None:
        """Sync the manager state with new configuration.

        This method handles all changes: add, remove, enable, disable, and config updates.
        Uses a mutex lock to prevent concurrent sync operations.

        Args:
            new_servers: New server configurations from config file
        """
        async with self._sync_lock:
            # Create lookup for current cached configs by name
            cached_by_name = {config.name: config for config in self.cached_configs}

            # Find servers to remove (in active clients but not in new config)
            servers_to_remove = set(self.active_clients.keys()) - set(
                new_servers.keys()
            )
            for server_name in servers_to_remove:
                await self._disconnect_server(server_name)
                logger.info(f"Removed MCP server: {server_name}")

            # Process each server in new config
            for server_name, new_config in new_servers.items():
                try:
                    is_active = server_name in self.active_clients
                    cached_config = cached_by_name.get(server_name)
                    config_changed = cached_config != new_config

                    if new_config.enabled:
                        if not is_active:
                            # Server is enabled but not connected, connect it
                            await self._connect_server(new_config)
                            logger.info(f"Connected to MCP server: {server_name}")
                        elif config_changed:
                            # Server is active but config changed, reconnect
                            await self._disconnect_server(server_name)
                            await self._connect_server(new_config)
                            logger.info(
                                f"Reconnected MCP server with new config: {server_name}"
                            )
                        # If server is active and config unchanged, do nothing
                    else:
                        if is_active:
                            # Server is disabled but still connected, disconnect it
                            await self._disconnect_server(server_name)
                            logger.info(f"Disabled MCP server: {server_name}")
                except Exception as e:
                    logger.error(f"Failed to sync server {server_name}: {e}")

            # Update cached configs with new config
            self.cached_configs = list(new_servers.values())

    def get_client(self, server_name: str) -> MCPClient:
        """Get an active MCP client by server name.

        Args:
            server_name: Name of the server

        Returns:
            MCPClient instance if active, None otherwise
        """
        return self.active_clients[server_name]

    def list_active_servers(self) -> list[str]:
        """List names of all active (connected) servers.

        Returns:
            List of active server names
        """
        return list(self.active_clients.keys())

    def is_connected(self, server_name: str) -> bool:
        """Check if a server is currently connected.

        Args:
            server_name: Name of the server

        Returns:
            True if connected, False otherwise
        """
        client = self.active_clients.get(server_name)
        return client is not None and client.is_connected()

    async def disconnect_all(self) -> None:
        """Disconnect from all active MCP servers."""
        server_names = list(self.active_clients.keys())
        for server_name in server_names:
            await self._disconnect_server(server_name)
        logger.info("Disconnected from all MCP servers")

    async def reconnect_server(self, server_name: str) -> bool:
        """Reconnect to a server (disconnect if connected, then connect).

        Args:
            server_name: Name of the server to reconnect

        Returns:
            True if successfully reconnected, False otherwise
        """
        server = self.server_list.get_server(server_name)
        if server is None:
            logger.error(f"Server not found: {server_name}")
            return False

        if not server.enabled:
            logger.error(f"Cannot reconnect disabled server: {server_name}")
            return False

        try:
            # Disconnect if active
            if server_name in self.active_clients:
                await self._disconnect_server(server_name)

            # Reconnect
            await self._connect_server(server)
            logger.info(f"Reconnected to MCP server: {server_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to reconnect to server {server_name}: {e}")
            return False

    async def __aenter__(self):
        """Enter async context manager."""
        await self.initialize_from_config()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.disconnect_all()
