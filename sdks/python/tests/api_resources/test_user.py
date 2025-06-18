# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from klavis import Klavis, AsyncKlavis
from tests.utils import assert_matches_type
from klavis.types import UserListInstancesResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestUser:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_instances(self, client: Klavis) -> None:
        user = client.user.list_instances(
            platform_name="platform_name",
            user_id="user_id",
        )
        assert_matches_type(UserListInstancesResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_instances(self, client: Klavis) -> None:
        response = client.user.with_raw_response.list_instances(
            platform_name="platform_name",
            user_id="user_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserListInstancesResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_instances(self, client: Klavis) -> None:
        with client.user.with_streaming_response.list_instances(
            platform_name="platform_name",
            user_id="user_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserListInstancesResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncUser:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_instances(self, async_client: AsyncKlavis) -> None:
        user = await async_client.user.list_instances(
            platform_name="platform_name",
            user_id="user_id",
        )
        assert_matches_type(UserListInstancesResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_instances(self, async_client: AsyncKlavis) -> None:
        response = await async_client.user.with_raw_response.list_instances(
            platform_name="platform_name",
            user_id="user_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserListInstancesResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_instances(self, async_client: AsyncKlavis) -> None:
        async with async_client.user.with_streaming_response.list_instances(
            platform_name="platform_name",
            user_id="user_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserListInstancesResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True
