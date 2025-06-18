# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .connection_type import ConnectionType

__all__ = ["McpServerCallToolParams"]


class McpServerCallToolParams(TypedDict, total=False):
    server_url: Required[Annotated[str, PropertyInfo(alias="serverUrl")]]
    """The full URL for connecting to the MCP server"""

    tool_name: Required[Annotated[str, PropertyInfo(alias="toolName")]]
    """The name of the tool to call"""

    connection_type: Annotated[ConnectionType, PropertyInfo(alias="connectionType")]
    """The connection type to use for the MCP server. Default is SSE."""

    tool_args: Annotated[Dict[str, object], PropertyInfo(alias="toolArgs")]
    """The input parameters for the tool"""
