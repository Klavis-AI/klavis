# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .server_tool import ServerTool

__all__ = ["McpServerListServersResponse", "Server"]


class Server(BaseModel):
    id: str

    name: str

    auth_needed: Optional[bool] = FieldInfo(alias="authNeeded", default=None)

    description: Optional[str] = None

    tools: Optional[List[ServerTool]] = None


class McpServerListServersResponse(BaseModel):
    servers: List[Server]
