# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["InstanceCreateResponse"]


class InstanceCreateResponse(BaseModel):
    instance_id: str = FieldInfo(alias="instanceId")
    """The unique identifier for this specific server connection instance."""

    server_url: str = FieldInfo(alias="serverUrl")
    """The full URL for connecting to the MCP server, including the instance ID."""
