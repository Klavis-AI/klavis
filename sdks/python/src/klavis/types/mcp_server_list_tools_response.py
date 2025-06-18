# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel

__all__ = ["McpServerListToolsResponse"]


class McpServerListToolsResponse(BaseModel):
    success: bool
    """Whether the list tools request was successful"""

    error: Optional[str] = None
    """Error message, if the request failed"""

    tools: Optional[List[object]] = None
    """List of tools available for the MCP server"""
