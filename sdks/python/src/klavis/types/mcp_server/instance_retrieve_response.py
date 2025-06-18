# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["InstanceRetrieveResponse"]


class InstanceRetrieveResponse(BaseModel):
    auth_needed: Optional[bool] = FieldInfo(alias="authNeeded", default=None)
    """Indicates whether authentication is required for this server instance."""

    external_user_id: Optional[str] = FieldInfo(alias="externalUserId", default=None)
    """The user's identifier on the external platform."""

    instance_id: Optional[str] = FieldInfo(alias="instanceId", default=None)
    """The unique identifier of the connection instance."""

    is_authenticated: Optional[bool] = FieldInfo(alias="isAuthenticated", default=None)
    """Indicates whether the instance is authenticated successfully."""

    platform: Optional[str] = None
    """The platform associated with the instance."""

    server_name: Optional[str] = FieldInfo(alias="serverName", default=None)
    """The name of the MCP server associated with the instance."""
