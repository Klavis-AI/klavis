# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel
from .server_tool import ServerTool

__all__ = ["McpServerGetToolsResponse"]


class McpServerGetToolsResponse(BaseModel):
    tools: Optional[List[ServerTool]] = None
    """List of available tools with their descriptions"""
