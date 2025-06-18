# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from klavis import Klavis, AsyncKlavis
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRedirect:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_to_jira_callback(self, client: Klavis) -> None:
        redirect = client.redirect.to_jira_callback()
        assert_matches_type(object, redirect, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_to_jira_callback(self, client: Klavis) -> None:
        response = client.redirect.with_raw_response.to_jira_callback()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        redirect = response.parse()
        assert_matches_type(object, redirect, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_to_jira_callback(self, client: Klavis) -> None:
        with client.redirect.with_streaming_response.to_jira_callback() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            redirect = response.parse()
            assert_matches_type(object, redirect, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncRedirect:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_to_jira_callback(self, async_client: AsyncKlavis) -> None:
        redirect = await async_client.redirect.to_jira_callback()
        assert_matches_type(object, redirect, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_to_jira_callback(self, async_client: AsyncKlavis) -> None:
        response = await async_client.redirect.with_raw_response.to_jira_callback()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        redirect = await response.parse()
        assert_matches_type(object, redirect, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_to_jira_callback(self, async_client: AsyncKlavis) -> None:
        async with async_client.redirect.with_streaming_response.to_jira_callback() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            redirect = await response.parse()
            assert_matches_type(object, redirect, path=["response"])

        assert cast(Any, response.is_closed) is True
