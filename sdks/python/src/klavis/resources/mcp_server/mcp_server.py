# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict

import httpx

from ...types import ServerName, ConnectionType, mcp_server_call_tool_params, mcp_server_list_tools_params
from ..._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from ..._utils import maybe_transform, async_maybe_transform
from .instance import (
    InstanceResource,
    AsyncInstanceResource,
    InstanceResourceWithRawResponse,
    AsyncInstanceResourceWithRawResponse,
    InstanceResourceWithStreamingResponse,
    AsyncInstanceResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.server_name import ServerName
from ...types.connection_type import ConnectionType
from ...types.mcp_server_call_tool_response import McpServerCallToolResponse
from ...types.mcp_server_get_tools_response import McpServerGetToolsResponse
from ...types.mcp_server_list_tools_response import McpServerListToolsResponse
from ...types.mcp_server_list_servers_response import McpServerListServersResponse

__all__ = ["McpServerResource", "AsyncMcpServerResource"]


class McpServerResource(SyncAPIResource):
    @cached_property
    def instance(self) -> InstanceResource:
        return InstanceResource(self._client)

    @cached_property
    def with_raw_response(self) -> McpServerResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#accessing-raw-response-data-eg-headers
        """
        return McpServerResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> McpServerResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#with_streaming_response
        """
        return McpServerResourceWithStreamingResponse(self)

    def call_tool(
        self,
        *,
        server_url: str,
        tool_name: str,
        connection_type: ConnectionType | NotGiven = NOT_GIVEN,
        tool_args: Dict[str, object] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> McpServerCallToolResponse:
        """
        Calls a tool on a specific remote MCP server, used for function calling.
        Eliminates the need for manual MCP code implementation. Under the hood, Klavis
        will instantiates an MCP client and establishes a connection with the remote MCP
        server to call the tool.

        Args:
          server_url: The full URL for connecting to the MCP server

          tool_name: The name of the tool to call

          connection_type: The connection type to use for the MCP server. Default is SSE.

          tool_args: The input parameters for the tool

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/mcp-server/call-tool",
            body=maybe_transform(
                {
                    "server_url": server_url,
                    "tool_name": tool_name,
                    "connection_type": connection_type,
                    "tool_args": tool_args,
                },
                mcp_server_call_tool_params.McpServerCallToolParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=McpServerCallToolResponse,
        )

    def get_tools(
        self,
        server_name: ServerName,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> McpServerGetToolsResponse:
        """Get list of tool names for a specific MCP server.

        Mainly used for querying
        metadata about the MCP server.

        Args:
          server_name: The name of the target MCP server.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not server_name:
            raise ValueError(f"Expected a non-empty value for `server_name` but received {server_name!r}")
        return self._get(
            f"/mcp-server/tools/{server_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=McpServerGetToolsResponse,
        )

    def list_servers(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> McpServerListServersResponse:
        """
        Get all MCP servers with their basic information including id, name,
        description, and tools.
        """
        return self._get(
            "/mcp-server/servers",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=McpServerListServersResponse,
        )

    def list_tools(
        self,
        server_url: str,
        *,
        connection_type: ConnectionType | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> McpServerListToolsResponse:
        """
        Lists all tools available for a specific remote MCP server, used for function
        calling. Eliminates the need for manual MCP code implementation. Under the hood,
        Klavis will instantiates an MCP client and establishes a connection with the
        remote MCP server to retrieve available tools.

        Args:
          server_url: The full URL for connecting to the MCP server

          connection_type: The connection type to use for the MCP server. Default is SSE.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not server_url:
            raise ValueError(f"Expected a non-empty value for `server_url` but received {server_url!r}")
        return self._get(
            f"/mcp-server/list-tools/{server_url}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"connection_type": connection_type}, mcp_server_list_tools_params.McpServerListToolsParams
                ),
            ),
            cast_to=McpServerListToolsResponse,
        )


class AsyncMcpServerResource(AsyncAPIResource):
    @cached_property
    def instance(self) -> AsyncInstanceResource:
        return AsyncInstanceResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncMcpServerResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncMcpServerResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMcpServerResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#with_streaming_response
        """
        return AsyncMcpServerResourceWithStreamingResponse(self)

    async def call_tool(
        self,
        *,
        server_url: str,
        tool_name: str,
        connection_type: ConnectionType | NotGiven = NOT_GIVEN,
        tool_args: Dict[str, object] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> McpServerCallToolResponse:
        """
        Calls a tool on a specific remote MCP server, used for function calling.
        Eliminates the need for manual MCP code implementation. Under the hood, Klavis
        will instantiates an MCP client and establishes a connection with the remote MCP
        server to call the tool.

        Args:
          server_url: The full URL for connecting to the MCP server

          tool_name: The name of the tool to call

          connection_type: The connection type to use for the MCP server. Default is SSE.

          tool_args: The input parameters for the tool

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/mcp-server/call-tool",
            body=await async_maybe_transform(
                {
                    "server_url": server_url,
                    "tool_name": tool_name,
                    "connection_type": connection_type,
                    "tool_args": tool_args,
                },
                mcp_server_call_tool_params.McpServerCallToolParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=McpServerCallToolResponse,
        )

    async def get_tools(
        self,
        server_name: ServerName,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> McpServerGetToolsResponse:
        """Get list of tool names for a specific MCP server.

        Mainly used for querying
        metadata about the MCP server.

        Args:
          server_name: The name of the target MCP server.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not server_name:
            raise ValueError(f"Expected a non-empty value for `server_name` but received {server_name!r}")
        return await self._get(
            f"/mcp-server/tools/{server_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=McpServerGetToolsResponse,
        )

    async def list_servers(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> McpServerListServersResponse:
        """
        Get all MCP servers with their basic information including id, name,
        description, and tools.
        """
        return await self._get(
            "/mcp-server/servers",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=McpServerListServersResponse,
        )

    async def list_tools(
        self,
        server_url: str,
        *,
        connection_type: ConnectionType | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> McpServerListToolsResponse:
        """
        Lists all tools available for a specific remote MCP server, used for function
        calling. Eliminates the need for manual MCP code implementation. Under the hood,
        Klavis will instantiates an MCP client and establishes a connection with the
        remote MCP server to retrieve available tools.

        Args:
          server_url: The full URL for connecting to the MCP server

          connection_type: The connection type to use for the MCP server. Default is SSE.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not server_url:
            raise ValueError(f"Expected a non-empty value for `server_url` but received {server_url!r}")
        return await self._get(
            f"/mcp-server/list-tools/{server_url}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"connection_type": connection_type}, mcp_server_list_tools_params.McpServerListToolsParams
                ),
            ),
            cast_to=McpServerListToolsResponse,
        )


class McpServerResourceWithRawResponse:
    def __init__(self, mcp_server: McpServerResource) -> None:
        self._mcp_server = mcp_server

        self.call_tool = to_raw_response_wrapper(
            mcp_server.call_tool,
        )
        self.get_tools = to_raw_response_wrapper(
            mcp_server.get_tools,
        )
        self.list_servers = to_raw_response_wrapper(
            mcp_server.list_servers,
        )
        self.list_tools = to_raw_response_wrapper(
            mcp_server.list_tools,
        )

    @cached_property
    def instance(self) -> InstanceResourceWithRawResponse:
        return InstanceResourceWithRawResponse(self._mcp_server.instance)


class AsyncMcpServerResourceWithRawResponse:
    def __init__(self, mcp_server: AsyncMcpServerResource) -> None:
        self._mcp_server = mcp_server

        self.call_tool = async_to_raw_response_wrapper(
            mcp_server.call_tool,
        )
        self.get_tools = async_to_raw_response_wrapper(
            mcp_server.get_tools,
        )
        self.list_servers = async_to_raw_response_wrapper(
            mcp_server.list_servers,
        )
        self.list_tools = async_to_raw_response_wrapper(
            mcp_server.list_tools,
        )

    @cached_property
    def instance(self) -> AsyncInstanceResourceWithRawResponse:
        return AsyncInstanceResourceWithRawResponse(self._mcp_server.instance)


class McpServerResourceWithStreamingResponse:
    def __init__(self, mcp_server: McpServerResource) -> None:
        self._mcp_server = mcp_server

        self.call_tool = to_streamed_response_wrapper(
            mcp_server.call_tool,
        )
        self.get_tools = to_streamed_response_wrapper(
            mcp_server.get_tools,
        )
        self.list_servers = to_streamed_response_wrapper(
            mcp_server.list_servers,
        )
        self.list_tools = to_streamed_response_wrapper(
            mcp_server.list_tools,
        )

    @cached_property
    def instance(self) -> InstanceResourceWithStreamingResponse:
        return InstanceResourceWithStreamingResponse(self._mcp_server.instance)


class AsyncMcpServerResourceWithStreamingResponse:
    def __init__(self, mcp_server: AsyncMcpServerResource) -> None:
        self._mcp_server = mcp_server

        self.call_tool = async_to_streamed_response_wrapper(
            mcp_server.call_tool,
        )
        self.get_tools = async_to_streamed_response_wrapper(
            mcp_server.get_tools,
        )
        self.list_servers = async_to_streamed_response_wrapper(
            mcp_server.list_servers,
        )
        self.list_tools = async_to_streamed_response_wrapper(
            mcp_server.list_tools,
        )

    @cached_property
    def instance(self) -> AsyncInstanceResourceWithStreamingResponse:
        return AsyncInstanceResourceWithStreamingResponse(self._mcp_server.instance)
