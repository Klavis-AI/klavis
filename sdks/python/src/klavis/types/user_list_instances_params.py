# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["UserListInstancesParams"]


class UserListInstancesParams(TypedDict, total=False):
    platform_name: Required[str]
    """The platform name"""

    user_id: Required[str]
    """The external user ID"""
