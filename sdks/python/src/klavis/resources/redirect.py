# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["RedirectResource", "AsyncRedirectResource"]


class RedirectResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RedirectResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#accessing-raw-response-data-eg-headers
        """
        return RedirectResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RedirectResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#with_streaming_response
        """
        return RedirectResourceWithStreamingResponse(self)

    def to_jira_callback(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Simple redirect endpoint that forwards to the Jira OAuth callback URL while
        preserving all original query parameters
        """
        return self._get(
            "/redirect",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncRedirectResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRedirectResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncRedirectResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRedirectResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Klavis-AI/python-sdk#with_streaming_response
        """
        return AsyncRedirectResourceWithStreamingResponse(self)

    async def to_jira_callback(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Simple redirect endpoint that forwards to the Jira OAuth callback URL while
        preserving all original query parameters
        """
        return await self._get(
            "/redirect",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class RedirectResourceWithRawResponse:
    def __init__(self, redirect: RedirectResource) -> None:
        self._redirect = redirect

        self.to_jira_callback = to_raw_response_wrapper(
            redirect.to_jira_callback,
        )


class AsyncRedirectResourceWithRawResponse:
    def __init__(self, redirect: AsyncRedirectResource) -> None:
        self._redirect = redirect

        self.to_jira_callback = async_to_raw_response_wrapper(
            redirect.to_jira_callback,
        )


class RedirectResourceWithStreamingResponse:
    def __init__(self, redirect: RedirectResource) -> None:
        self._redirect = redirect

        self.to_jira_callback = to_streamed_response_wrapper(
            redirect.to_jira_callback,
        )


class AsyncRedirectResourceWithStreamingResponse:
    def __init__(self, redirect: AsyncRedirectResource) -> None:
        self._redirect = redirect

        self.to_jira_callback = async_to_streamed_response_wrapper(
            redirect.to_jira_callback,
        )
