# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal

import httpx

from ..types import white_labeling_create_params
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.white_labeling_response import WhiteLabelingResponse

__all__ = ["WhiteLabelingResource", "AsyncWhiteLabelingResource"]


class WhiteLabelingResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> WhiteLabelingResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#accessing-raw-response-data-eg-headers
        """
        return WhiteLabelingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WhiteLabelingResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#with_streaming_response
        """
        return WhiteLabelingResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        client_id: str,
        client_secret: str,
        server_name: Literal[
            "Slack",
            "Supabase",
            "Notion",
            "GitHub",
            "Jira",
            "Confluence",
            "WordPress",
            "Gmail",
            "Google Drive",
            "Google Calendar",
            "Google Sheets",
            "Google Docs",
            "Attio",
            "Salesforce",
            "Linear",
            "Asana",
            "Close",
            "ClickUp",
        ],
        account_id: Optional[str] | NotGiven = NOT_GIVEN,
        callback_url: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> WhiteLabelingResponse:
        """
        Saves OAuth white labeling information, or updates existing information if the
        `client_id` matches.

        Args:
          client_id: OAuth client ID

          client_secret: OAuth client secret

          server_name: Optional. The name of the server

          account_id: Optional. The UUID of the account

          callback_url: Optional. OAuth callback URL

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/white-labeling/create",
            body=maybe_transform(
                {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "server_name": server_name,
                    "account_id": account_id,
                    "callback_url": callback_url,
                },
                white_labeling_create_params.WhiteLabelingCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WhiteLabelingResponse,
        )

    def retrieve(
        self,
        client_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> WhiteLabelingResponse:
        """
        Retrieves white labeling information for a specific OAuth client ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not client_id:
            raise ValueError(f"Expected a non-empty value for `client_id` but received {client_id!r}")
        return self._get(
            f"/white-labeling/get/{client_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WhiteLabelingResponse,
        )


class AsyncWhiteLabelingResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncWhiteLabelingResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncWhiteLabelingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWhiteLabelingResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#with_streaming_response
        """
        return AsyncWhiteLabelingResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        client_id: str,
        client_secret: str,
        server_name: Literal[
            "Slack",
            "Supabase",
            "Notion",
            "GitHub",
            "Jira",
            "Confluence",
            "WordPress",
            "Gmail",
            "Google Drive",
            "Google Calendar",
            "Google Sheets",
            "Google Docs",
            "Attio",
            "Salesforce",
            "Linear",
            "Asana",
            "Close",
            "ClickUp",
        ],
        account_id: Optional[str] | NotGiven = NOT_GIVEN,
        callback_url: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> WhiteLabelingResponse:
        """
        Saves OAuth white labeling information, or updates existing information if the
        `client_id` matches.

        Args:
          client_id: OAuth client ID

          client_secret: OAuth client secret

          server_name: Optional. The name of the server

          account_id: Optional. The UUID of the account

          callback_url: Optional. OAuth callback URL

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/white-labeling/create",
            body=await async_maybe_transform(
                {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "server_name": server_name,
                    "account_id": account_id,
                    "callback_url": callback_url,
                },
                white_labeling_create_params.WhiteLabelingCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WhiteLabelingResponse,
        )

    async def retrieve(
        self,
        client_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> WhiteLabelingResponse:
        """
        Retrieves white labeling information for a specific OAuth client ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not client_id:
            raise ValueError(f"Expected a non-empty value for `client_id` but received {client_id!r}")
        return await self._get(
            f"/white-labeling/get/{client_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WhiteLabelingResponse,
        )


class WhiteLabelingResourceWithRawResponse:
    def __init__(self, white_labeling: WhiteLabelingResource) -> None:
        self._white_labeling = white_labeling

        self.create = to_raw_response_wrapper(
            white_labeling.create,
        )
        self.retrieve = to_raw_response_wrapper(
            white_labeling.retrieve,
        )


class AsyncWhiteLabelingResourceWithRawResponse:
    def __init__(self, white_labeling: AsyncWhiteLabelingResource) -> None:
        self._white_labeling = white_labeling

        self.create = async_to_raw_response_wrapper(
            white_labeling.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            white_labeling.retrieve,
        )


class WhiteLabelingResourceWithStreamingResponse:
    def __init__(self, white_labeling: WhiteLabelingResource) -> None:
        self._white_labeling = white_labeling

        self.create = to_streamed_response_wrapper(
            white_labeling.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            white_labeling.retrieve,
        )


class AsyncWhiteLabelingResourceWithStreamingResponse:
    def __init__(self, white_labeling: AsyncWhiteLabelingResource) -> None:
        self._white_labeling = white_labeling

        self.create = async_to_streamed_response_wrapper(
            white_labeling.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            white_labeling.retrieve,
        )
