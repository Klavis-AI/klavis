# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...types import ServerName, ConnectionType
from ..._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.mcp_server import instance_create_params, instance_set_auth_token_params
from ...types.server_name import ServerName
from ...types.connection_type import ConnectionType
from ...types.mcp_server.status_response import StatusResponse
from ...types.mcp_server.instance_create_response import InstanceCreateResponse
from ...types.mcp_server.instance_retrieve_response import InstanceRetrieveResponse

__all__ = ["InstanceResource", "AsyncInstanceResource"]


class InstanceResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> InstanceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#accessing-raw-response-data-eg-headers
        """
        return InstanceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> InstanceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#with_streaming_response
        """
        return InstanceResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        platform_name: str,
        server_name: ServerName,
        user_id: str,
        connection_type: ConnectionType | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> InstanceCreateResponse:
        """
        Creates a URL for a specified MCP server, validating the request with an API key
        and user details. Returns the existing server URL if it already exists for the
        user.

        Args:
          platform_name: The name of the platform associated with the user.

          server_name: The name of the target MCP server.

          user_id: The identifier for the user requesting the server URL.

          connection_type: The connection type to use for the MCP server. Default is SSE.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/mcp-server/instance/create",
            body=maybe_transform(
                {
                    "platform_name": platform_name,
                    "server_name": server_name,
                    "user_id": user_id,
                    "connection_type": connection_type,
                },
                instance_create_params.InstanceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InstanceCreateResponse,
        )

    def retrieve(
        self,
        instance_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> InstanceRetrieveResponse:
        """
        Checks the details of a specific server connection instance using its unique ID
        and API key, returning server details like authentication status and associated
        server/platform info.

        Args:
          instance_id: The ID of the connection instance whose status is being checked. This is
              returned by the Create API.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not instance_id:
            raise ValueError(f"Expected a non-empty value for `instance_id` but received {instance_id!r}")
        return self._get(
            f"/mcp-server/instance/get/{instance_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InstanceRetrieveResponse,
        )

    def delete(
        self,
        instance_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StatusResponse:
        """
        Completely removes a server connection instance using its unique ID, deleting
        all associated data from the system.

        Args:
          instance_id: The ID of the connection instance to delete.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not instance_id:
            raise ValueError(f"Expected a non-empty value for `instance_id` but received {instance_id!r}")
        return self._delete(
            f"/mcp-server/instance/delete/{instance_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatusResponse,
        )

    def delete_auth(
        self,
        instance_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StatusResponse:
        """
        Deletes authentication metadata for a specific server connection instance.

        Args:
          instance_id: The ID of the connection instance to delete auth for.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not instance_id:
            raise ValueError(f"Expected a non-empty value for `instance_id` but received {instance_id!r}")
        return self._delete(
            f"/mcp-server/instance/delete-auth/{instance_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatusResponse,
        )

    def set_auth_token(
        self,
        *,
        auth_token: str,
        instance_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StatusResponse:
        """Sets an authentication token for a specific instance.

        This updates the
        auth_metadata for the specified instance.

        Args:
          auth_token: The authentication token to save

          instance_id: The unique identifier for the connection instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/mcp-server/instance/set-auth-token",
            body=maybe_transform(
                {
                    "auth_token": auth_token,
                    "instance_id": instance_id,
                },
                instance_set_auth_token_params.InstanceSetAuthTokenParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatusResponse,
        )


class AsyncInstanceResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncInstanceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncInstanceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncInstanceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#with_streaming_response
        """
        return AsyncInstanceResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        platform_name: str,
        server_name: ServerName,
        user_id: str,
        connection_type: ConnectionType | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> InstanceCreateResponse:
        """
        Creates a URL for a specified MCP server, validating the request with an API key
        and user details. Returns the existing server URL if it already exists for the
        user.

        Args:
          platform_name: The name of the platform associated with the user.

          server_name: The name of the target MCP server.

          user_id: The identifier for the user requesting the server URL.

          connection_type: The connection type to use for the MCP server. Default is SSE.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/mcp-server/instance/create",
            body=await async_maybe_transform(
                {
                    "platform_name": platform_name,
                    "server_name": server_name,
                    "user_id": user_id,
                    "connection_type": connection_type,
                },
                instance_create_params.InstanceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InstanceCreateResponse,
        )

    async def retrieve(
        self,
        instance_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> InstanceRetrieveResponse:
        """
        Checks the details of a specific server connection instance using its unique ID
        and API key, returning server details like authentication status and associated
        server/platform info.

        Args:
          instance_id: The ID of the connection instance whose status is being checked. This is
              returned by the Create API.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not instance_id:
            raise ValueError(f"Expected a non-empty value for `instance_id` but received {instance_id!r}")
        return await self._get(
            f"/mcp-server/instance/get/{instance_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InstanceRetrieveResponse,
        )

    async def delete(
        self,
        instance_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StatusResponse:
        """
        Completely removes a server connection instance using its unique ID, deleting
        all associated data from the system.

        Args:
          instance_id: The ID of the connection instance to delete.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not instance_id:
            raise ValueError(f"Expected a non-empty value for `instance_id` but received {instance_id!r}")
        return await self._delete(
            f"/mcp-server/instance/delete/{instance_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatusResponse,
        )

    async def delete_auth(
        self,
        instance_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StatusResponse:
        """
        Deletes authentication metadata for a specific server connection instance.

        Args:
          instance_id: The ID of the connection instance to delete auth for.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not instance_id:
            raise ValueError(f"Expected a non-empty value for `instance_id` but received {instance_id!r}")
        return await self._delete(
            f"/mcp-server/instance/delete-auth/{instance_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatusResponse,
        )

    async def set_auth_token(
        self,
        *,
        auth_token: str,
        instance_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StatusResponse:
        """Sets an authentication token for a specific instance.

        This updates the
        auth_metadata for the specified instance.

        Args:
          auth_token: The authentication token to save

          instance_id: The unique identifier for the connection instance

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/mcp-server/instance/set-auth-token",
            body=await async_maybe_transform(
                {
                    "auth_token": auth_token,
                    "instance_id": instance_id,
                },
                instance_set_auth_token_params.InstanceSetAuthTokenParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatusResponse,
        )


class InstanceResourceWithRawResponse:
    def __init__(self, instance: InstanceResource) -> None:
        self._instance = instance

        self.create = to_raw_response_wrapper(
            instance.create,
        )
        self.retrieve = to_raw_response_wrapper(
            instance.retrieve,
        )
        self.delete = to_raw_response_wrapper(
            instance.delete,
        )
        self.delete_auth = to_raw_response_wrapper(
            instance.delete_auth,
        )
        self.set_auth_token = to_raw_response_wrapper(
            instance.set_auth_token,
        )


class AsyncInstanceResourceWithRawResponse:
    def __init__(self, instance: AsyncInstanceResource) -> None:
        self._instance = instance

        self.create = async_to_raw_response_wrapper(
            instance.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            instance.retrieve,
        )
        self.delete = async_to_raw_response_wrapper(
            instance.delete,
        )
        self.delete_auth = async_to_raw_response_wrapper(
            instance.delete_auth,
        )
        self.set_auth_token = async_to_raw_response_wrapper(
            instance.set_auth_token,
        )


class InstanceResourceWithStreamingResponse:
    def __init__(self, instance: InstanceResource) -> None:
        self._instance = instance

        self.create = to_streamed_response_wrapper(
            instance.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            instance.retrieve,
        )
        self.delete = to_streamed_response_wrapper(
            instance.delete,
        )
        self.delete_auth = to_streamed_response_wrapper(
            instance.delete_auth,
        )
        self.set_auth_token = to_streamed_response_wrapper(
            instance.set_auth_token,
        )


class AsyncInstanceResourceWithStreamingResponse:
    def __init__(self, instance: AsyncInstanceResource) -> None:
        self._instance = instance

        self.create = async_to_streamed_response_wrapper(
            instance.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            instance.retrieve,
        )
        self.delete = async_to_streamed_response_wrapper(
            instance.delete,
        )
        self.delete_auth = async_to_streamed_response_wrapper(
            instance.delete_auth,
        )
        self.set_auth_token = async_to_streamed_response_wrapper(
            instance.set_auth_token,
        )
