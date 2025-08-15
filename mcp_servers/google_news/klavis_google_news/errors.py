# klavis_google_news/errors.py
from pydantic import BaseModel
from typing import Any


class ToolExecutionError(Exception):
    def __init__(self, message: str, status_code: int = 400, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details
