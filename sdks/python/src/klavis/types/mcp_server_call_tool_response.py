# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["McpServerCallToolResponse", "Result"]


class Result(BaseModel):
    content: List[object]
    """The content of the tool call"""

    is_error: Optional[bool] = FieldInfo(alias="isError", default=None)
    """Whether the tool call was successful"""


class McpServerCallToolResponse(BaseModel):
    success: bool
    """Whether the API call was successful"""

    error: Optional[str] = None
    """Error message, if the tool call failed"""

    result: Optional[Result] = None
    """The server's response to a tool call."""
