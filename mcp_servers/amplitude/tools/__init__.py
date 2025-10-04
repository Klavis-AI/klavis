# mcp_servers/amplitude/tools/__init__.py
import os
from contextvars import ContextVar

amplitude_api_key_ctx: ContextVar[str] = ContextVar("amplitude_api_key", default=os.getenv("AMPLITUDE_API_KEY", ""))
amplitude_api_secret_ctx: ContextVar[str] = ContextVar("amplitude_api_secret", default=os.getenv("AMPLITUDE_API_SECRET", ""))

def get_api_key() -> str:
    return amplitude_api_key_ctx.get()

def get_api_secret() -> str:
    return amplitude_api_secret_ctx.get()