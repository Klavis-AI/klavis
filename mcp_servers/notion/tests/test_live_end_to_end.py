"""End-to-end tests against a running Notion MCP server.

These start server.py as a real subprocess and talk to it over the MCP streamable HTTP
transport with the real client, so the whole path is exercised: transport, session,
the framework's CallToolRequest handler, the dispatch layer, handle_notion_error and
the normalizers. Only the Notion SDK is replaced, by a sitecustomize on PYTHONPATH, so
the tests need no credentials and make no outbound call.

What they are here to prove, which the unit tests cannot:

  1. a failed call arrives with isError set, so a client can detect it from the
     protocol rather than by inspecting the body
  2. the body is the structured envelope, correctly classified, rather than {} or a
     fabricated field such as {"userType": "not_found_error"}
  3. a successful call is unaffected
"""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parent.parent
FAKE_SDK_DIR = Path(__file__).resolve().parent / "fake_sdk"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_port(port: int, proc: subprocess.Popen, timeout: float = 30.0) -> None:
    """Block until the server accepts connections, failing loudly if it died."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            out, _ = proc.communicate(timeout=5)
            raise RuntimeError(f"server exited early with {proc.returncode}:\n{out}")
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.1)
    raise TimeoutError(f"server did not listen on {port} within {timeout}s")


@pytest.fixture(scope="module")
def live_server():
    """A real server process with the Notion SDK faked. Yields its /mcp URL."""
    port = _free_port()
    env = dict(os.environ)
    # sitecustomize runs before the server's own imports, so Client is already fake.
    env["PYTHONPATH"] = os.pathsep.join(
        [str(FAKE_SDK_DIR)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    env["NOTION_API_KEY"] = "test-token-not-a-real-key"
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [sys.executable, "server.py", "--port", str(port)],
        cwd=str(SERVER_DIR), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        _wait_for_port(port, proc)
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


async def _call(url: str, tool: str, arguments: dict):
    """Open a session, call one tool, return the CallToolResult."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool, arguments)


def _body(result):
    """The tool's JSON payload, as the client receives it."""
    assert result.content, "no content returned"
    return json.loads(result.content[0].text)


@pytest.mark.asyncio
class TestLiveFailuresAreReportedAsErrors:
    """A failed Notion call must reach the client as a protocol-level error."""

    async def test_not_found_sets_is_error(self, live_server):
        """404 arrives with isError set rather than looking like a success."""
        result = await _call(live_server, "notion_get_page", {"page_id": "page-404"})
        assert result.isError is True

    async def test_not_found_carries_the_classified_envelope(self, live_server):
        """The body is the envelope, classified from the SDK's error code.

        Before, this call returned {} with isError false, and the type would have been
        "api_error" because the classifier searched the message for "Not found" while
        Notion sends "Could not find page with ID: ...".
        """
        result = await _call(live_server, "notion_get_page", {"page_id": "page-404"})
        body = _body(result)
        assert body != {}
        assert body["type"] == "not_found_error"
        assert body["code"] == "object_not_found"
        assert body["status"] == 404
        assert "Could not find page with ID" in body["details"]

    async def test_unauthorized_is_classified(self, live_server):
        """401 becomes authentication_error, not the generic api_error."""
        body = _body(await _call(live_server, "notion_get_page", {"page_id": "page-401"}))
        assert body["type"] == "authentication_error"
        assert body["code"] == "unauthorized"
        assert body["status"] == 401

    async def test_forbidden_is_classified(self, live_server):
        """403 becomes permission_error."""
        body = _body(await _call(live_server, "notion_get_page", {"page_id": "page-403"}))
        assert body["type"] == "permission_error"
        assert body["code"] == "restricted_resource"
        assert body["status"] == 403

    async def test_user_failure_is_not_laundered_into_a_payload_field(self, live_server):
        """normalize_user used to turn the envelope into {"userType": "not_found_error"}.

        That is the dangerous half of the bug: a structurally valid-looking object.
        """
        result = await _call(live_server, "notion_get_user", {"user_id": "user-404"})
        body = _body(result)
        assert result.isError is True
        assert "userType" not in body
        assert body["type"] == "not_found_error"

    async def test_block_failure_is_not_laundered_into_a_payload_field(self, live_server):
        """Same collision on normalize_block, which produced {"blockType": ...}."""
        result = await _call(live_server, "notion_retrieve_block", {"block_id": "block-404"})
        body = _body(result)
        assert result.isError is True
        assert "blockType" not in body
        assert body["type"] == "not_found_error"


    async def test_internal_validation_error_also_sets_is_error(self, live_server):
        """A failure raised inside a tool, before any API call, reports the same way.

        create_page raises ValueError("Properties are required") and its own handler
        converts it with handle_notion_error, so this exercises the api_error branch
        and confirms the fix is not specific to SDK exceptions.
        """
        result = await _call(live_server, "notion_create_page", {"page": {}})
        body = _body(result)
        assert result.isError is True
        assert body["type"] == "api_error"
        assert "Properties are required" in body["details"]


@pytest.mark.asyncio
class TestLiveSuccessPathUnaffected:
    """The happy path must be untouched by any of the three changes."""

    async def test_get_page_succeeds_and_normalizes(self, live_server):
        """A real page still normalizes onto its rule-defined names, isError false."""
        result = await _call(live_server, "notion_get_page", {"page_id": "page-ok"})
        body = _body(result)
        assert result.isError is False
        assert body["pageId"] == "page-ok"
        assert body["objectType"] == "page"
        assert body["createdBy"] == "user-1"

    async def test_get_user_keeps_its_real_type(self, live_server):
        """userType must still carry "person", the field the bug overwrote."""
        result = await _call(live_server, "notion_get_user", {"user_id": "user-ok"})
        body = _body(result)
        assert result.isError is False
        assert body["userType"] == "person"
        assert body["personEmail"] == "ada@example.com"

    async def test_retrieve_block_keeps_its_real_type(self, live_server):
        """blockType must still carry "paragraph"."""
        result = await _call(live_server, "notion_retrieve_block", {"block_id": "block-ok"})
        body = _body(result)
        assert result.isError is False
        assert body["blockType"] == "paragraph"


@pytest.mark.asyncio
class TestLiveServerContract:
    """Basic protocol sanity, so a failure above is not mistaken for a broken harness."""

    async def test_tools_are_listed(self, live_server):
        """The server advertises its tools over the real transport."""
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(live_server) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
        names = {t.name for t in tools.tools}
        assert {"notion_get_page", "notion_get_user", "notion_retrieve_block"} <= names
