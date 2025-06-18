# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .server_tool import ServerTool

__all__ = ["UserListInstancesResponse", "Instance"]


class Instance(BaseModel):
    id: str

    name: str

    auth_needed: Optional[bool] = FieldInfo(alias="authNeeded", default=None)

    description: Optional[str] = None

    is_authenticated: Optional[bool] = FieldInfo(alias="isAuthenticated", default=None)

    tools: Optional[List[ServerTool]] = None


class UserListInstancesResponse(BaseModel):
    instances: List[Instance]
