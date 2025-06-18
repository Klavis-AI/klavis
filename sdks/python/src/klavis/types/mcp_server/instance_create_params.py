# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo
from ..server_name import ServerName
from ..connection_type import ConnectionType

__all__ = ["InstanceCreateParams"]


class InstanceCreateParams(TypedDict, total=False):
    platform_name: Required[Annotated[str, PropertyInfo(alias="platformName")]]
    """The name of the platform associated with the user."""

    server_name: Required[Annotated[ServerName, PropertyInfo(alias="serverName")]]
    """The name of the target MCP server."""

    user_id: Required[Annotated[str, PropertyInfo(alias="userId")]]
    """The identifier for the user requesting the server URL."""

    connection_type: Annotated[ConnectionType, PropertyInfo(alias="connectionType")]
    """The connection type to use for the MCP server. Default is SSE."""
