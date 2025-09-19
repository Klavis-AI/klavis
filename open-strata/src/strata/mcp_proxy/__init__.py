"""MCP Proxy module for connecting to and interacting with MCP servers."""

from .client import MCPClient
from .transport import HTTPTransport, StdioTransport, Transport
from .auth_provider import create_oauth_provider

__all__ = ["MCPClient", "StdioTransport", "HTTPTransport", "Transport", "create_oauth_provider"]
