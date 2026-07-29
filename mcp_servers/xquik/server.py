from __future__ import annotations

import base64
import binascii
import json
import logging
import os
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from typing import Final

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route

LOGGER = logging.getLogger("xquik-mcp-gateway")

UPSTREAM_MCP_URL: Final = "https://xquik.com/mcp"
MAX_REQUEST_BYTES: Final = 4 * 1024 * 1024
DEFAULT_PORT: Final = 5000
DEFAULT_HOST: Final = "127.0.0.1"

AUTH_DATA_FIELDS: Final = ("token", "api_key", "access_token")
AUTH_ENVIRONMENT_VARIABLES: Final = ("XQUIK_API_KEY", "API_KEY")
FORWARDED_REQUEST_HEADERS: Final = (
    "accept",
    "content-type",
    "last-event-id",
    "mcp-method",
    "mcp-name",
    "mcp-protocol-version",
    "mcp-session-id",
)
FORWARDED_RESPONSE_HEADERS: Final = (
    "cache-control",
    "content-type",
    "mcp-session-id",
    "retry-after",
    "www-authenticate",
    "x-request-id",
    "x-robots-tag",
)


def _cors_headers() -> dict[str, str]:
    return {
        "Access-Control-Allow-Headers": (
            "Authorization, Content-Type, Last-Event-ID, MCP-Method, MCP-Name, "
            "MCP-Protocol-Version, MCP-Session-Id, X-API-Key, X-Auth-Data"
        ),
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Expose-Headers": (
            "MCP-Session-Id, Retry-After, WWW-Authenticate, X-Request-ID"
        ),
    }


def _json_object(value: str) -> Mapping[str, object] | None:
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _decode_base64(value: str) -> str | None:
    padded = value + ("=" * (-len(value) % 4))
    try:
        return base64.b64decode(padded, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        try:
            return base64.urlsafe_b64decode(padded).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return None


def parse_auth_data(value: str | bytes | None) -> str | None:
    if value is None:
        return None
    try:
        decoded = value.decode("utf-8") if isinstance(value, bytes) else value
    except UnicodeDecodeError:
        return None

    raw = decoded.strip()
    if not raw:
        return None

    auth_data = _json_object(raw)
    if auth_data is None:
        base64_value = _decode_base64(raw)
        auth_data = None if base64_value is None else _json_object(base64_value)
    if auth_data is None:
        return None

    for field in AUTH_DATA_FIELDS:
        credential = auth_data.get(field)
        if isinstance(credential, str) and credential.strip():
            return credential.strip()
    return None


def _configured_credential(request: Request) -> str | None:
    for variable in AUTH_ENVIRONMENT_VARIABLES:
        credential = os.getenv(variable)
        if credential is not None and credential.strip():
            return credential.strip()

    credential = parse_auth_data(os.getenv("AUTH_DATA"))
    if credential is not None:
        return credential
    return parse_auth_data(request.headers.get("x-auth-data"))


def _upstream_headers(request: Request) -> dict[str, str]:
    headers = {
        name: value
        for name in FORWARDED_REQUEST_HEADERS
        if (value := request.headers.get(name)) is not None
    }
    headers.setdefault("accept", "application/json, text/event-stream")
    headers["accept-encoding"] = "identity"
    headers["user-agent"] = "klavis-xquik-mcp-gateway/1.0"

    credential = _configured_credential(request)
    if credential is not None:
        headers["authorization"] = f"Bearer {credential}"
        return headers

    authorization = request.headers.get("authorization")
    if authorization is not None:
        headers["authorization"] = authorization
        return headers

    api_key = request.headers.get("x-api-key")
    if api_key is not None:
        headers["x-api-key"] = api_key
    return headers


def _response_headers(response: httpx.Response) -> dict[str, str]:
    headers = {
        name: value
        for name in FORWARDED_RESPONSE_HEADERS
        if (value := response.headers.get(name)) is not None
    }
    headers.update(_cors_headers())
    return headers


async def _response_body(response: httpx.Response) -> AsyncIterator[bytes]:
    if response.is_stream_consumed:
        yield response.content
        return
    async for chunk in response.aiter_bytes():
        yield chunk


def _request_id(body: bytes) -> int | str | None:
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    request_id = payload.get("id")
    if isinstance(request_id, bool):
        return None
    return request_id if isinstance(request_id, (int, str)) else None


def _json_rpc_error(
    body: bytes,
    *,
    status_code: int,
    message: str,
) -> JSONResponse:
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": message},
            "id": _request_id(body),
        },
        status_code=status_code,
        headers=_cors_headers(),
    )


async def _bounded_body(request: Request) -> bytes | Response:
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except ValueError:
            return _json_rpc_error(
                b"",
                status_code=400,
                message="Invalid Content-Length header.",
            )
        if declared_length > MAX_REQUEST_BYTES:
            return _json_rpc_error(
                b"",
                status_code=413,
                message="MCP request exceeds the 4 MiB limit.",
            )

    body = await request.body()
    if len(body) > MAX_REQUEST_BYTES:
        return _json_rpc_error(
            body,
            status_code=413,
            message="MCP request exceeds the 4 MiB limit.",
        )
    return body


async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def options(_request: Request) -> Response:
    return Response(status_code=204, headers=_cors_headers())


async def proxy_mcp(request: Request) -> Response:
    body_or_response = await _bounded_body(request)
    if isinstance(body_or_response, Response):
        return body_or_response
    body = body_or_response

    client: httpx.AsyncClient = request.app.state.upstream_client
    upstream_request = client.build_request(
        request.method,
        UPSTREAM_MCP_URL,
        content=body,
        headers=_upstream_headers(request),
    )

    try:
        upstream_response = await client.send(upstream_request, stream=True)
    except httpx.HTTPError:
        LOGGER.exception("Xquik MCP upstream request failed")
        return _json_rpc_error(
            body,
            status_code=502,
            message="Xquik MCP is temporarily unavailable.",
        )

    return StreamingResponse(
        _response_body(upstream_response),
        status_code=upstream_response.status_code,
        headers=_response_headers(upstream_response),
        background=BackgroundTask(upstream_response.aclose),
    )


@asynccontextmanager
async def _lifespan(app: Starlette) -> AsyncIterator[None]:
    if getattr(app.state, "upstream_client", None) is not None:
        yield
        return

    timeout = httpx.Timeout(connect=10, read=75, write=10, pool=10)
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
    async with httpx.AsyncClient(
        follow_redirects=False,
        limits=limits,
        timeout=timeout,
    ) as client:
        app.state.upstream_client = client
        yield


def create_app(upstream_client: httpx.AsyncClient | None = None) -> Starlette:
    app = Starlette(
        debug=False,
        routes=[
            Route("/health", endpoint=health, methods=["GET"]),
            Route("/mcp", endpoint=proxy_mcp, methods=["GET", "POST", "DELETE"]),
            Route("/mcp", endpoint=options, methods=["OPTIONS"]),
            Route("/mcp/", endpoint=proxy_mcp, methods=["GET", "POST", "DELETE"]),
            Route("/mcp/", endpoint=options, methods=["OPTIONS"]),
        ],
        lifespan=_lifespan,
    )
    if upstream_client is not None:
        app.state.upstream_client = upstream_client
    return app


app = create_app()


def main() -> None:
    port = int(os.getenv("XQUIK_MCP_SERVER_PORT", str(DEFAULT_PORT)))
    host = os.getenv("XQUIK_MCP_SERVER_HOST", DEFAULT_HOST)
    log_level = os.getenv("XQUIK_MCP_LOG_LEVEL", "info").lower()
    uvicorn.run(app, host=host, port=port, log_level=log_level)


if __name__ == "__main__":
    main()
