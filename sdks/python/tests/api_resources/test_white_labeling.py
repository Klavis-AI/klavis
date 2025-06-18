# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from klavis import Klavis, AsyncKlavis
from tests.utils import assert_matches_type
from klavis.types import WhiteLabelingResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestWhiteLabeling:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Klavis) -> None:
        white_labeling = client.white_labeling.create(
            client_id="client_id",
            client_secret="client_secret",
            server_name="Slack",
        )
        assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: Klavis) -> None:
        white_labeling = client.white_labeling.create(
            client_id="client_id",
            client_secret="client_secret",
            server_name="Slack",
            account_id="account_id",
            callback_url="callback_url",
        )
        assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Klavis) -> None:
        response = client.white_labeling.with_raw_response.create(
            client_id="client_id",
            client_secret="client_secret",
            server_name="Slack",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        white_labeling = response.parse()
        assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Klavis) -> None:
        with client.white_labeling.with_streaming_response.create(
            client_id="client_id",
            client_secret="client_secret",
            server_name="Slack",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            white_labeling = response.parse()
            assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve(self, client: Klavis) -> None:
        white_labeling = client.white_labeling.retrieve(
            "client_id",
        )
        assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve(self, client: Klavis) -> None:
        response = client.white_labeling.with_raw_response.retrieve(
            "client_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        white_labeling = response.parse()
        assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve(self, client: Klavis) -> None:
        with client.white_labeling.with_streaming_response.retrieve(
            "client_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            white_labeling = response.parse()
            assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_retrieve(self, client: Klavis) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `client_id` but received ''"):
            client.white_labeling.with_raw_response.retrieve(
                "",
            )


class TestAsyncWhiteLabeling:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncKlavis) -> None:
        white_labeling = await async_client.white_labeling.create(
            client_id="client_id",
            client_secret="client_secret",
            server_name="Slack",
        )
        assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncKlavis) -> None:
        white_labeling = await async_client.white_labeling.create(
            client_id="client_id",
            client_secret="client_secret",
            server_name="Slack",
            account_id="account_id",
            callback_url="callback_url",
        )
        assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncKlavis) -> None:
        response = await async_client.white_labeling.with_raw_response.create(
            client_id="client_id",
            client_secret="client_secret",
            server_name="Slack",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        white_labeling = await response.parse()
        assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncKlavis) -> None:
        async with async_client.white_labeling.with_streaming_response.create(
            client_id="client_id",
            client_secret="client_secret",
            server_name="Slack",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            white_labeling = await response.parse()
            assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncKlavis) -> None:
        white_labeling = await async_client.white_labeling.retrieve(
            "client_id",
        )
        assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncKlavis) -> None:
        response = await async_client.white_labeling.with_raw_response.retrieve(
            "client_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        white_labeling = await response.parse()
        assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncKlavis) -> None:
        async with async_client.white_labeling.with_streaming_response.retrieve(
            "client_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            white_labeling = await response.parse()
            assert_matches_type(WhiteLabelingResponse, white_labeling, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncKlavis) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `client_id` but received ''"):
            await async_client.white_labeling.with_raw_response.retrieve(
                "",
            )
