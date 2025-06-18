# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, Union, Mapping
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    NOT_GIVEN,
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
)
from ._utils import is_given, get_async_library
from ._version import __version__
from .resources import user, redirect, white_labeling
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import KlavisError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)
from .resources.mcp_server import mcp_server

__all__ = ["Timeout", "Transport", "ProxiesTypes", "RequestOptions", "Klavis", "AsyncKlavis", "Client", "AsyncClient"]


class Klavis(SyncAPIClient):
    mcp_server: mcp_server.McpServerResource
    white_labeling: white_labeling.WhiteLabelingResource
    user: user.UserResource
    redirect: redirect.RedirectResource
    with_raw_response: KlavisWithRawResponse
    with_streaming_response: KlavisWithStreamedResponse

    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous Klavis client instance.

        This automatically infers the `api_key` argument from the `KLAVIS_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("KLAVIS_API_KEY")
        if api_key is None:
            raise KlavisError(
                "The api_key client option must be set either by passing api_key to the client or by setting the KLAVIS_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("KLAVIS_BASE_URL")
        if base_url is None:
            base_url = f"https://api.klavis.ai"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.mcp_server = mcp_server.McpServerResource(self)
        self.white_labeling = white_labeling.WhiteLabelingResource(self)
        self.user = user.UserResource(self)
        self.redirect = redirect.RedirectResource(self)
        self.with_raw_response = KlavisWithRawResponse(self)
        self.with_streaming_response = KlavisWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = NOT_GIVEN,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = NOT_GIVEN,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncKlavis(AsyncAPIClient):
    mcp_server: mcp_server.AsyncMcpServerResource
    white_labeling: white_labeling.AsyncWhiteLabelingResource
    user: user.AsyncUserResource
    redirect: redirect.AsyncRedirectResource
    with_raw_response: AsyncKlavisWithRawResponse
    with_streaming_response: AsyncKlavisWithStreamedResponse

    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncKlavis client instance.

        This automatically infers the `api_key` argument from the `KLAVIS_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("KLAVIS_API_KEY")
        if api_key is None:
            raise KlavisError(
                "The api_key client option must be set either by passing api_key to the client or by setting the KLAVIS_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("KLAVIS_BASE_URL")
        if base_url is None:
            base_url = f"https://api.klavis.ai"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self.mcp_server = mcp_server.AsyncMcpServerResource(self)
        self.white_labeling = white_labeling.AsyncWhiteLabelingResource(self)
        self.user = user.AsyncUserResource(self)
        self.redirect = redirect.AsyncRedirectResource(self)
        self.with_raw_response = AsyncKlavisWithRawResponse(self)
        self.with_streaming_response = AsyncKlavisWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = NOT_GIVEN,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = NOT_GIVEN,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class KlavisWithRawResponse:
    def __init__(self, client: Klavis) -> None:
        self.mcp_server = mcp_server.McpServerResourceWithRawResponse(client.mcp_server)
        self.white_labeling = white_labeling.WhiteLabelingResourceWithRawResponse(client.white_labeling)
        self.user = user.UserResourceWithRawResponse(client.user)
        self.redirect = redirect.RedirectResourceWithRawResponse(client.redirect)


class AsyncKlavisWithRawResponse:
    def __init__(self, client: AsyncKlavis) -> None:
        self.mcp_server = mcp_server.AsyncMcpServerResourceWithRawResponse(client.mcp_server)
        self.white_labeling = white_labeling.AsyncWhiteLabelingResourceWithRawResponse(client.white_labeling)
        self.user = user.AsyncUserResourceWithRawResponse(client.user)
        self.redirect = redirect.AsyncRedirectResourceWithRawResponse(client.redirect)


class KlavisWithStreamedResponse:
    def __init__(self, client: Klavis) -> None:
        self.mcp_server = mcp_server.McpServerResourceWithStreamingResponse(client.mcp_server)
        self.white_labeling = white_labeling.WhiteLabelingResourceWithStreamingResponse(client.white_labeling)
        self.user = user.UserResourceWithStreamingResponse(client.user)
        self.redirect = redirect.RedirectResourceWithStreamingResponse(client.redirect)


class AsyncKlavisWithStreamedResponse:
    def __init__(self, client: AsyncKlavis) -> None:
        self.mcp_server = mcp_server.AsyncMcpServerResourceWithStreamingResponse(client.mcp_server)
        self.white_labeling = white_labeling.AsyncWhiteLabelingResourceWithStreamingResponse(client.white_labeling)
        self.user = user.AsyncUserResourceWithStreamingResponse(client.user)
        self.redirect = redirect.AsyncRedirectResourceWithStreamingResponse(client.redirect)


Client = Klavis

AsyncClient = AsyncKlavis
