# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from .._models import BaseModel

__all__ = ["WhiteLabelingResponse"]


class WhiteLabelingResponse(BaseModel):
    success: bool
    """Whether the operation was successful"""

    data: Optional[Dict[str, object]] = None
    """The white labeling data if successful"""

    message: Optional[str] = None
    """Error message if unsuccessful"""
