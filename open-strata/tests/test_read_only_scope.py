"""Tests for Strata read-only action scoping."""

import json
from types import SimpleNamespace

import pytest

from strata.mcp_proxy.client import MCPClient
from strata.tools import (
    ACTION_SCOPE_READ_ONLY,
    TOOL_DISCOVER_SERVER_ACTIONS,
    TOOL_EXECUTE_ACTION,
    TOOL_GET_ACTION_DETAILS,
    execute_tool,
    filter_tools_by_scope,
    is_read_only_tool,
)


READ_TOOL = {
    "name": "gmail_search",
    "description": "Search messages",
    "inputSchema": {"type": "object"},
    "annotations": {"readOnlyHint": True},
}

WRITE_TOOL = {
    "name": "gmail_send",
    "description": "Send a message",
    "inputSchema": {"type": "object"},
    "annotations": {"readOnlyHint": False},
}


class FakeClient:
    def __init__(self):
        self.called_tools = []

    async def list_tools(self):
        return [READ_TOOL, WRITE_TOOL]

    async def call_tool(self, action_name, action_params):
        self.called_tools.append((action_name, action_params))
        return []


class FakeManager:
    def __init__(self, client):
        self.active_clients = {"gmail": client}
        self.client = client

    def get_client(self, server_name):
        if server_name != "gmail":
            raise KeyError(server_name)
        return self.client


def parse_text_result(result):
    return json.loads(result[0].text)


def test_read_only_detection_uses_mcp_annotations():
    assert is_read_only_tool(READ_TOOL)
    assert not is_read_only_tool(WRITE_TOOL)
    assert filter_tools_by_scope([READ_TOOL, WRITE_TOOL], ACTION_SCOPE_READ_ONLY) == [
        READ_TOOL
    ]


@pytest.mark.asyncio
async def test_discover_server_actions_can_return_only_read_only_tools():
    client = FakeClient()
    result = await execute_tool(
        TOOL_DISCOVER_SERVER_ACTIONS,
        {"server_names": ["gmail"], "scope": ACTION_SCOPE_READ_ONLY},
        FakeManager(client),
    )

    payload = parse_text_result(result)
    assert payload["servers"]["gmail"] == {
        "action_count": 1,
        "actions": ["gmail_search"],
    }


@pytest.mark.asyncio
async def test_get_action_details_hides_write_actions_in_read_only_scope():
    client = FakeClient()
    result = await execute_tool(
        TOOL_GET_ACTION_DETAILS,
        {
            "server_name": "gmail",
            "action_name": "gmail_send",
            "scope": ACTION_SCOPE_READ_ONLY,
        },
        FakeManager(client),
    )

    payload = parse_text_result(result)
    assert payload == {"error": "Action 'gmail_send' not found in server 'gmail'"}


@pytest.mark.asyncio
async def test_execute_action_rejects_write_actions_in_read_only_scope():
    client = FakeClient()
    result = await execute_tool(
        TOOL_EXECUTE_ACTION,
        {
            "server_name": "gmail",
            "action_name": "gmail_send",
            "scope": ACTION_SCOPE_READ_ONLY,
        },
        FakeManager(client),
    )

    payload = parse_text_result(result)
    assert payload == {
        "error": (
            "Action 'gmail_send' is not available in scope 'read_only' "
            "for server 'gmail'"
        )
    }
    assert client.called_tools == []


class DumpableAnnotations:
    def model_dump(self, exclude_none=False):
        assert exclude_none is True
        return {"readOnlyHint": True}


class FakeTransport:
    def is_connected(self):
        return True

    def get_session(self):
        return self

    async def list_tools(self):
        return SimpleNamespace(
            tools=[
                SimpleNamespace(
                    name="read",
                    description="Read records",
                    inputSchema={"type": "object"},
                    annotations=DumpableAnnotations(),
                )
            ]
        )


@pytest.mark.asyncio
async def test_mcp_client_preserves_tool_annotations_for_router_scoping():
    client = MCPClient(FakeTransport())

    tools = await client.list_tools(use_cache=False)

    assert tools == [
        {
            "name": "read",
            "description": "Read records",
            "inputSchema": {"type": "object"},
            "annotations": {"readOnlyHint": True},
        }
    ]
