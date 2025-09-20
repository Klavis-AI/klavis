"""Abstract base class for MCP transport implementations."""

import logging
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Optional, Tuple

from mcp.client.session import ClientSession

logger = logging.getLogger(__name__)


class Transport(ABC):
    """Abstract base class for MCP transport implementations."""

    def __init__(self):
        """Initialize the transport."""
        self._session: Optional[ClientSession] = None
        self._exit_stack: Optional[AsyncExitStack] = None
        self._connected: bool = False

    @abstractmethod
    async def _get_streams(self, exit_stack: AsyncExitStack) -> Tuple:
        """Get the transport-specific streams.

        Args:
            exit_stack: AsyncExitStack to manage the streams

        Returns:
            Tuple of (read_stream, write_stream)
        """
    async def initialize(self) -> None:
        if not self._exit_stack:
            self._exit_stack = AsyncExitStack()
        
        try:
            # Get transport-specific streams
            streams = await self._get_streams(self._exit_stack)

            # Create client session (common for all transports)
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(streams[0], streams[1])
            )
            logger.info("Client session created successfully")
            # Initialize the session
            await self._session.initialize()

            self._connected = True
            logger.info(f"Successfully connected via {self.__class__.__name__}")

        except Exception as e:
            logger.error(f"Failed to connect via {self.__class__.__name__}: {e}")
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None
            raise

    async def connect(self) -> None:
        """Connect to the MCP server using the specific transport."""
        if self._connected:
            return

        await self.initialize()

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._connected:
            return

        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
            except RuntimeError as e:
                # Handle cross-task cleanup errors from anyio's CancelScope
                if "cancel scope" in str(e).lower():
                    logger.warning(
                        "Cross-task cleanup detected and handled. "
                        "This typically happens with pytest fixtures."
                    )
                else:
                    raise

        self._session = None
        self._exit_stack = None
        self._connected = False

    def is_connected(self) -> bool:
        """Check if connected to an MCP server."""
        return self._connected

    def get_session(self) -> ClientSession:
        """Get the current client session."""
        if not self._connected or not self._session:
            raise RuntimeError("Not connected to an MCP server.")
        return self._session

    async def __aenter__(self):
        """Enter async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.disconnect()
