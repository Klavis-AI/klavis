from __future__ import annotations
import asyncio
import os
import pytest

# A very light smoke test that ensures the module imports and tools are registered

def test_import_and_tools_registered():
    from klavis_tavily_mcp.server import mcp  # noqa: F401

    # Ensure tool names are what we expect
    tool_names = {t.name for t in mcp._tools}  # FastMCP keeps a registry
    assert "tavily_search" in tool_names
    assert "tavily_extract" in tool_names


@pytest.mark.asyncio
async def test_auth_missing_returns_error(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    from klavis_tavily_mcp import server

    result = await server.tavily_search("hello world")
    assert result["ok"] is False
    assert result.get("error") == "auth"