# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from klavis import Klavis, AsyncKlavis
from tests.utils import assert_matches_type
from klavis.types import (
    McpServerCallToolResponse,
    McpServerGetToolsResponse,
    McpServerListToolsResponse,
    McpServerListServersResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMcpServer:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_call_tool(self, client: Klavis) -> None:
        mcp_server = client.mcp_server.call_tool(
            server_url="serverUrl",
            tool_name="toolName",
        )
        assert_matches_type(McpServerCallToolResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_call_tool_with_all_params(self, client: Klavis) -> None:
        mcp_server = client.mcp_server.call_tool(
            server_url="serverUrl",
            tool_name="toolName",
            connection_type="SSE",
            tool_args={"foo": "bar"},
        )
        assert_matches_type(McpServerCallToolResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_call_tool(self, client: Klavis) -> None:
        response = client.mcp_server.with_raw_response.call_tool(
            server_url="serverUrl",
            tool_name="toolName",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mcp_server = response.parse()
        assert_matches_type(McpServerCallToolResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_call_tool(self, client: Klavis) -> None:
        with client.mcp_server.with_streaming_response.call_tool(
            server_url="serverUrl",
            tool_name="toolName",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mcp_server = response.parse()
            assert_matches_type(McpServerCallToolResponse, mcp_server, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_get_tools(self, client: Klavis) -> None:
        mcp_server = client.mcp_server.get_tools(
            "Markdown2doc",
        )
        assert_matches_type(McpServerGetToolsResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_get_tools(self, client: Klavis) -> None:
        response = client.mcp_server.with_raw_response.get_tools(
            "Markdown2doc",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mcp_server = response.parse()
        assert_matches_type(McpServerGetToolsResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_get_tools(self, client: Klavis) -> None:
        with client.mcp_server.with_streaming_response.get_tools(
            "Markdown2doc",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mcp_server = response.parse()
            assert_matches_type(McpServerGetToolsResponse, mcp_server, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list_servers(self, client: Klavis) -> None:
        mcp_server = client.mcp_server.list_servers()
        assert_matches_type(McpServerListServersResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_servers(self, client: Klavis) -> None:
        response = client.mcp_server.with_raw_response.list_servers()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mcp_server = response.parse()
        assert_matches_type(McpServerListServersResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_servers(self, client: Klavis) -> None:
        with client.mcp_server.with_streaming_response.list_servers() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mcp_server = response.parse()
            assert_matches_type(McpServerListServersResponse, mcp_server, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list_tools(self, client: Klavis) -> None:
        mcp_server = client.mcp_server.list_tools(
            server_url="server_url",
        )
        assert_matches_type(McpServerListToolsResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_tools_with_all_params(self, client: Klavis) -> None:
        mcp_server = client.mcp_server.list_tools(
            server_url="server_url",
            connection_type="SSE",
        )
        assert_matches_type(McpServerListToolsResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_tools(self, client: Klavis) -> None:
        response = client.mcp_server.with_raw_response.list_tools(
            server_url="server_url",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mcp_server = response.parse()
        assert_matches_type(McpServerListToolsResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_tools(self, client: Klavis) -> None:
        with client.mcp_server.with_streaming_response.list_tools(
            server_url="server_url",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mcp_server = response.parse()
            assert_matches_type(McpServerListToolsResponse, mcp_server, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_list_tools(self, client: Klavis) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `server_url` but received ''"):
            client.mcp_server.with_raw_response.list_tools(
                server_url="",
            )


class TestAsyncMcpServer:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_call_tool(self, async_client: AsyncKlavis) -> None:
        mcp_server = await async_client.mcp_server.call_tool(
            server_url="serverUrl",
            tool_name="toolName",
        )
        assert_matches_type(McpServerCallToolResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_call_tool_with_all_params(self, async_client: AsyncKlavis) -> None:
        mcp_server = await async_client.mcp_server.call_tool(
            server_url="serverUrl",
            tool_name="toolName",
            connection_type="SSE",
            tool_args={"foo": "bar"},
        )
        assert_matches_type(McpServerCallToolResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_call_tool(self, async_client: AsyncKlavis) -> None:
        response = await async_client.mcp_server.with_raw_response.call_tool(
            server_url="serverUrl",
            tool_name="toolName",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mcp_server = await response.parse()
        assert_matches_type(McpServerCallToolResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_call_tool(self, async_client: AsyncKlavis) -> None:
        async with async_client.mcp_server.with_streaming_response.call_tool(
            server_url="serverUrl",
            tool_name="toolName",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mcp_server = await response.parse()
            assert_matches_type(McpServerCallToolResponse, mcp_server, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_get_tools(self, async_client: AsyncKlavis) -> None:
        mcp_server = await async_client.mcp_server.get_tools(
            "Markdown2doc",
        )
        assert_matches_type(McpServerGetToolsResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_get_tools(self, async_client: AsyncKlavis) -> None:
        response = await async_client.mcp_server.with_raw_response.get_tools(
            "Markdown2doc",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mcp_server = await response.parse()
        assert_matches_type(McpServerGetToolsResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_get_tools(self, async_client: AsyncKlavis) -> None:
        async with async_client.mcp_server.with_streaming_response.get_tools(
            "Markdown2doc",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mcp_server = await response.parse()
            assert_matches_type(McpServerGetToolsResponse, mcp_server, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_servers(self, async_client: AsyncKlavis) -> None:
        mcp_server = await async_client.mcp_server.list_servers()
        assert_matches_type(McpServerListServersResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_servers(self, async_client: AsyncKlavis) -> None:
        response = await async_client.mcp_server.with_raw_response.list_servers()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mcp_server = await response.parse()
        assert_matches_type(McpServerListServersResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_servers(self, async_client: AsyncKlavis) -> None:
        async with async_client.mcp_server.with_streaming_response.list_servers() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mcp_server = await response.parse()
            assert_matches_type(McpServerListServersResponse, mcp_server, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_tools(self, async_client: AsyncKlavis) -> None:
        mcp_server = await async_client.mcp_server.list_tools(
            server_url="server_url",
        )
        assert_matches_type(McpServerListToolsResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_tools_with_all_params(self, async_client: AsyncKlavis) -> None:
        mcp_server = await async_client.mcp_server.list_tools(
            server_url="server_url",
            connection_type="SSE",
        )
        assert_matches_type(McpServerListToolsResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_tools(self, async_client: AsyncKlavis) -> None:
        response = await async_client.mcp_server.with_raw_response.list_tools(
            server_url="server_url",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mcp_server = await response.parse()
        assert_matches_type(McpServerListToolsResponse, mcp_server, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_tools(self, async_client: AsyncKlavis) -> None:
        async with async_client.mcp_server.with_streaming_response.list_tools(
            server_url="server_url",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mcp_server = await response.parse()
            assert_matches_type(McpServerListToolsResponse, mcp_server, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_list_tools(self, async_client: AsyncKlavis) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `server_url` but received ''"):
            await async_client.mcp_server.with_raw_response.list_tools(
                server_url="",
            )
