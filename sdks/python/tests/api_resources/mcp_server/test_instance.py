# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from klavis import Klavis, AsyncKlavis
from tests.utils import assert_matches_type
from klavis.types.mcp_server import (
    StatusResponse,
    InstanceCreateResponse,
    InstanceRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestInstance:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Klavis) -> None:
        instance = client.mcp_server.instance.create(
            platform_name="x",
            server_name="Markdown2doc",
            user_id="x",
        )
        assert_matches_type(InstanceCreateResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: Klavis) -> None:
        instance = client.mcp_server.instance.create(
            platform_name="x",
            server_name="Markdown2doc",
            user_id="x",
            connection_type="SSE",
        )
        assert_matches_type(InstanceCreateResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Klavis) -> None:
        response = client.mcp_server.instance.with_raw_response.create(
            platform_name="x",
            server_name="Markdown2doc",
            user_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        instance = response.parse()
        assert_matches_type(InstanceCreateResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Klavis) -> None:
        with client.mcp_server.instance.with_streaming_response.create(
            platform_name="x",
            server_name="Markdown2doc",
            user_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            instance = response.parse()
            assert_matches_type(InstanceCreateResponse, instance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve(self, client: Klavis) -> None:
        instance = client.mcp_server.instance.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(InstanceRetrieveResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve(self, client: Klavis) -> None:
        response = client.mcp_server.instance.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        instance = response.parse()
        assert_matches_type(InstanceRetrieveResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve(self, client: Klavis) -> None:
        with client.mcp_server.instance.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            instance = response.parse()
            assert_matches_type(InstanceRetrieveResponse, instance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_retrieve(self, client: Klavis) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `instance_id` but received ''"):
            client.mcp_server.instance.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_delete(self, client: Klavis) -> None:
        instance = client.mcp_server.instance.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete(self, client: Klavis) -> None:
        response = client.mcp_server.instance.with_raw_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        instance = response.parse()
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete(self, client: Klavis) -> None:
        with client.mcp_server.instance.with_streaming_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            instance = response.parse()
            assert_matches_type(StatusResponse, instance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_delete(self, client: Klavis) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `instance_id` but received ''"):
            client.mcp_server.instance.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_delete_auth(self, client: Klavis) -> None:
        instance = client.mcp_server.instance.delete_auth(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete_auth(self, client: Klavis) -> None:
        response = client.mcp_server.instance.with_raw_response.delete_auth(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        instance = response.parse()
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete_auth(self, client: Klavis) -> None:
        with client.mcp_server.instance.with_streaming_response.delete_auth(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            instance = response.parse()
            assert_matches_type(StatusResponse, instance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_delete_auth(self, client: Klavis) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `instance_id` but received ''"):
            client.mcp_server.instance.with_raw_response.delete_auth(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_set_auth_token(self, client: Klavis) -> None:
        instance = client.mcp_server.instance.set_auth_token(
            auth_token="authToken",
            instance_id="instanceId",
        )
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_set_auth_token(self, client: Klavis) -> None:
        response = client.mcp_server.instance.with_raw_response.set_auth_token(
            auth_token="authToken",
            instance_id="instanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        instance = response.parse()
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_set_auth_token(self, client: Klavis) -> None:
        with client.mcp_server.instance.with_streaming_response.set_auth_token(
            auth_token="authToken",
            instance_id="instanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            instance = response.parse()
            assert_matches_type(StatusResponse, instance, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncInstance:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncKlavis) -> None:
        instance = await async_client.mcp_server.instance.create(
            platform_name="x",
            server_name="Markdown2doc",
            user_id="x",
        )
        assert_matches_type(InstanceCreateResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncKlavis) -> None:
        instance = await async_client.mcp_server.instance.create(
            platform_name="x",
            server_name="Markdown2doc",
            user_id="x",
            connection_type="SSE",
        )
        assert_matches_type(InstanceCreateResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncKlavis) -> None:
        response = await async_client.mcp_server.instance.with_raw_response.create(
            platform_name="x",
            server_name="Markdown2doc",
            user_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        instance = await response.parse()
        assert_matches_type(InstanceCreateResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncKlavis) -> None:
        async with async_client.mcp_server.instance.with_streaming_response.create(
            platform_name="x",
            server_name="Markdown2doc",
            user_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            instance = await response.parse()
            assert_matches_type(InstanceCreateResponse, instance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncKlavis) -> None:
        instance = await async_client.mcp_server.instance.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(InstanceRetrieveResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncKlavis) -> None:
        response = await async_client.mcp_server.instance.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        instance = await response.parse()
        assert_matches_type(InstanceRetrieveResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncKlavis) -> None:
        async with async_client.mcp_server.instance.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            instance = await response.parse()
            assert_matches_type(InstanceRetrieveResponse, instance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncKlavis) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `instance_id` but received ''"):
            await async_client.mcp_server.instance.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete(self, async_client: AsyncKlavis) -> None:
        instance = await async_client.mcp_server.instance.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncKlavis) -> None:
        response = await async_client.mcp_server.instance.with_raw_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        instance = await response.parse()
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncKlavis) -> None:
        async with async_client.mcp_server.instance.with_streaming_response.delete(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            instance = await response.parse()
            assert_matches_type(StatusResponse, instance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncKlavis) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `instance_id` but received ''"):
            await async_client.mcp_server.instance.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete_auth(self, async_client: AsyncKlavis) -> None:
        instance = await async_client.mcp_server.instance.delete_auth(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete_auth(self, async_client: AsyncKlavis) -> None:
        response = await async_client.mcp_server.instance.with_raw_response.delete_auth(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        instance = await response.parse()
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete_auth(self, async_client: AsyncKlavis) -> None:
        async with async_client.mcp_server.instance.with_streaming_response.delete_auth(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            instance = await response.parse()
            assert_matches_type(StatusResponse, instance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_delete_auth(self, async_client: AsyncKlavis) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `instance_id` but received ''"):
            await async_client.mcp_server.instance.with_raw_response.delete_auth(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_set_auth_token(self, async_client: AsyncKlavis) -> None:
        instance = await async_client.mcp_server.instance.set_auth_token(
            auth_token="authToken",
            instance_id="instanceId",
        )
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_set_auth_token(self, async_client: AsyncKlavis) -> None:
        response = await async_client.mcp_server.instance.with_raw_response.set_auth_token(
            auth_token="authToken",
            instance_id="instanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        instance = await response.parse()
        assert_matches_type(StatusResponse, instance, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_set_auth_token(self, async_client: AsyncKlavis) -> None:
        async with async_client.mcp_server.instance.with_streaming_response.set_auth_token(
            auth_token="authToken",
            instance_id="instanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            instance = await response.parse()
            assert_matches_type(StatusResponse, instance, path=["response"])

        assert cast(Any, response.is_closed) is True
