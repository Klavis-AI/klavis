"""Stdio transport implementation for MCP."""

import logging
from contextlib import AsyncExitStack
from typing import Dict, List, Optional, Tuple

from mcp.client.stdio import StdioServerParameters, stdio_client

from .base import Transport

logger = logging.getLogger(__name__)


class StdioTransport(Transport):
    """Stdio transport for MCP communication."""

    def __init__(
        self,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        """Initialize stdio transport.

        Args:
            command: Command to execute (e.g., "docker")
            args: Command arguments (e.g., ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"])
            env: Environment variables to pass to the command (e.g., {"GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"})

        Example server configuration:
            "servers": {
                "github": {
                    "command": "docker",
                    "args": [
                        "run",
                        "-i",
                        "--rm",
                        "-e",
                        "GITHUB_PERSONAL_ACCESS_TOKEN",
                        "ghcr.io/github/github-mcp-server"
                    ],
                    "env": {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
                    }
                }
            }
        """
        super().__init__()
        self.command = command
        self.args = args or []
        self.env = env or {}

    async def _get_streams(self, exit_stack: AsyncExitStack) -> Tuple:
        """Get stdio transport streams.

        Args:
            exit_stack: AsyncExitStack to manage the streams

        Returns:
            Tuple of (read_stream, write_stream)
        """
        # Create stdio server parameters
        server_params = StdioServerParameters(
            command=self.command, args=self.args, env=self.env
        )

        # Connect via stdio
        logger.info(f"Connecting to MCP server via stdio: {self.command} {self.args}")
        return await exit_stack.enter_async_context(stdio_client(server_params))
