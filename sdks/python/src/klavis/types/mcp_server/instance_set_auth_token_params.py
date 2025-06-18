# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["InstanceSetAuthTokenParams"]


class InstanceSetAuthTokenParams(TypedDict, total=False):
    auth_token: Required[Annotated[str, PropertyInfo(alias="authToken")]]
    """The authentication token to save"""

    instance_id: Required[Annotated[str, PropertyInfo(alias="instanceId")]]
    """The unique identifier for the connection instance"""
