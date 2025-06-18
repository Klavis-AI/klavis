# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

from .connection_type import ConnectionType

__all__ = ["McpServerListToolsParams"]


class McpServerListToolsParams(TypedDict, total=False):
    connection_type: ConnectionType
    """The connection type to use for the MCP server. Default is SSE."""
