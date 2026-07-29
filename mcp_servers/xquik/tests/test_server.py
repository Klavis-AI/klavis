from __future__ import annotations

import asyncio
import base64
import json
from collections.abc import Callable, Coroutine

import httpx
import pytest

from mcp_servers.xquik import server

MockHandler = Callable[
    [httpx.Request],
    Coroutine[None, None, httpx.Response],
]


@pytest.fixture(autouse=True)
def clear_auth_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in (*server.AUTH_ENVIRONMENT_VARIABLES, "AUTH_DATA"):
        monkeypatch.delenv(variable, raising=False)


def round_trip(
    handler: MockHandler,
    *,
    content: bytes = b"",
    headers: dict[str, str] | None = None,
    method: str = "POST",
    path: str = "/mcp",
) -> httpx.Response:
    async def run() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as upstream_client:
            app = server.create_app(upstream_client)
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                base_url="http://testserver",
                transport=transport,
            ) as client:
                return await client.request(
                    method,
                    path,
                    content=content,
                    headers=headers,
                )

    return asyncio.run(run())


def test_parse_auth_data_accepts_json_and_base64() -> None:
    json_value = '{"token":"json-credential"}'
    base64_value = base64.b64encode(b'{"api_key":"base64-credential"}').decode()

    assert server.parse_auth_data(json_value) == "json-credential"
    assert server.parse_auth_data(base64_value) == "base64-credential"
    assert server.parse_auth_data('{"access_token":"oauth_token"}') == "oauth_token"
    assert server.parse_auth_data('{"token":7}') is None
    assert server.parse_auth_data("not-auth-data") is None


def test_proxy_forwards_protocol_and_base64_auth_headers() -> None:
    request_body = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/list",
        "params": {},
    }
    encoded_auth = base64.b64encode(b'{"api_key":"test-credential"}').decode()

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == server.UPSTREAM_MCP_URL
        assert request.headers["authorization"] == "Bearer test-credential"
        assert request.headers["accept-encoding"] == "identity"
        assert "x-auth-data" not in request.headers
        assert request.headers["mcp-protocol-version"] == "2025-11-25"
        assert request.headers["mcp-method"] == "tools/list"
        assert json.loads(await request.aread()) == request_body
        return httpx.Response(
            200,
            headers={
                "Content-Type": "application/json",
                "Mcp-Session-Id": "session-1",
                "X-Request-ID": "request-1",
            },
            json={
                "jsonrpc": "2.0",
                "id": 7,
                "result": {"tools": [{"name": "explore"}, {"name": "xquik"}]},
            },
        )

    response = round_trip(
        handler,
        content=json.dumps(request_body).encode(),
        headers={
            "Content-Type": "application/json",
            "MCP-Method": "tools/list",
            "MCP-Protocol-Version": "2025-11-25",
            "X-Auth-Data": encoded_auth,
        },
    )

    assert response.status_code == 200
    assert response.headers["mcp-session-id"] == "session-1"
    assert response.headers["x-request-id"] == "request-1"
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.json()["result"]["tools"] == [
        {"name": "explore"},
        {"name": "xquik"},
    ]


def test_configured_api_key_takes_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XQUIK_API_KEY", "configured-credential")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer configured-credential"
        return httpx.Response(202)

    response = round_trip(
        handler,
        headers={
            "Authorization": "Bearer inbound",
            "X-Auth-Data": '{"token":"header"}',
        },
    )

    assert response.status_code == 202


def test_direct_authorization_passes_through_without_configured_auth() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer oauth-token"
        return httpx.Response(200, json={"ok": True})

    response = round_trip(
        handler,
        headers={"Authorization": "Bearer oauth-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_unauthenticated_challenge_is_preserved() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        assert "x-api-key" not in request.headers
        return httpx.Response(
            401,
            headers={
                "WWW-Authenticate": (
                    'Bearer resource_metadata="https://xquik.com/'
                    '.well-known/oauth-protected-resource/mcp"'
                )
            },
            json={"error": "Authentication required"},
        )

    response = round_trip(handler)

    assert response.status_code == 401
    assert "resource_metadata" in response.headers["www-authenticate"]
    assert response.json() == {"error": "Authentication required"}


def test_large_requests_are_rejected_before_upstream() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("The upstream must not receive oversized requests.")

    response = round_trip(
        handler,
        content=b"x" * (server.MAX_REQUEST_BYTES + 1),
    )

    assert response.status_code == 413
    assert response.json()["error"]["message"] == (
        "MCP request exceeds the 4 MiB limit."
    )


def test_upstream_errors_return_sanitized_json_rpc_failure() -> None:
    body = b'{"jsonrpc":"2.0","id":"request-9","method":"tools/list"}'

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("secret transport details", request=request)

    response = round_trip(handler, content=body)

    assert response.status_code == 502
    assert response.json() == {
        "jsonrpc": "2.0",
        "error": {
            "code": -32603,
            "message": "Xquik MCP is temporarily unavailable.",
        },
        "id": "request-9",
    }
    assert "secret transport details" not in response.text


def test_health_does_not_contact_upstream() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("Health checks must stay local.")

    response = round_trip(handler, method="GET", path="/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
