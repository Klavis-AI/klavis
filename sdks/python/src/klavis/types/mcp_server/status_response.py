# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["StatusResponse"]


class StatusResponse(BaseModel):
    success: bool

    message: Optional[str] = None
