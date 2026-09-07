"""Test setup for the WhatsApp bot.

whatsapp_bot imports four project modules that pull in Supabase, the LLM clients and
the MCP client stack. None of them takes part in webhook routing, so they are stubbed
here to keep these tests on the thing under test: which handler serves each route, and
what it does with a request. Everything else, FastAPI and pywa included, is real.
"""

import importlib
import os
import sys
import types as pytypes
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest_plugins = ('pytest_asyncio',)

# The real mcp_clients package must be importable so mcp_clients.whatsapp_bot resolves.
# Only its heavyweight siblings are replaced.
_SRC = str(Path(__file__).resolve().parent.parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def _stub(name: str, **attrs) -> None:
    """Register a stub module under `name`, pre-empting the real import."""
    mod = pytypes.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod


def _install_project_stubs() -> None:
    # Import the real package first. Stubbing a submodule only works once its parent
    # exists in sys.modules, and shadowing mcp_clients itself would hide
    # mcp_clients.whatsapp_bot, which is the module under test.
    importlib.import_module("mcp_clients")

    _stub("mcp_clients.base_bot",
          BaseBot=MagicMock,
          BotContext=type("BotContext", (), {"__init__": lambda self, *a, **k: None}))
    _stub("mcp_clients.config", USE_PRODUCTION_DB=False)

    llms = pytypes.ModuleType("mcp_clients.llms")
    llms.__path__ = []
    sys.modules.setdefault("mcp_clients.llms", llms)
    _stub("mcp_clients.llms.base",
          ChatMessage=MagicMock, Conversation=MagicMock, MessageRole=MagicMock,
          TextContent=MagicMock, FileContent=MagicMock)
    _stub("mcp_clients.mcp_client", MCPClient=MagicMock)


_install_project_stubs()


# Credentials the module reads at import time. They are fake, and nothing leaves the
# process: pywa contacts Meta only when callback_url is set, and it is cleared below.
#
# These are applied at import of this file rather than inside a fixture. whatsapp_bot
# reads the environment and constructs its pywa client at module scope, and pywa raises
# if the verify token is missing, so the values have to be in place before any test
# imports the module. Doing it in a fixture made the suite pass or fail depending on
# which test pytest happened to run first.
TEST_VERIFY_TOKEN = "test-verify-token-abc123"
TEST_APP_SECRET = "test-app-secret-xyz789"

os.environ.update({
    "WHATSAPP_ACCESS_TOKEN": "test-access-token",
    "WHATSAPP_APP_ID": "1234567890",
    "WHATSAPP_APP_SECRET": TEST_APP_SECRET,
    "WHATSAPP_PHONE_NUMBER_ID": "9876543210",
    "WHATSAPP_VERIFY_TOKEN": TEST_VERIFY_TOKEN,
})
os.environ.pop("CALLBACK_URL", None)


@pytest.fixture(scope="module")
def bot_app():
    """The real whatsapp_bot module's FastAPI app."""
    from mcp_clients import whatsapp_bot
    return whatsapp_bot.app


@pytest.fixture(scope="module")
def client(bot_app):
    """A TestClient over the real app, exercising the real route table."""
    from fastapi.testclient import TestClient
    return TestClient(bot_app)


@pytest.fixture
def captured_messages():
    """Swap the module's @wa.on_message callback for a recorder, then put it back.

    pywa holds its own reference to the decorated function on the handler object, so
    patching the module attribute alone changes nothing. Restoring afterwards is the
    part that matters: a recorder left in place makes the suite order dependent, and a
    test that only passes when it runs first is not worth much.

    Yields the list the recorder appends to, as (text, wa_id) pairs.
    """
    from mcp_clients import whatsapp_bot

    received = []

    async def record(_client, message):
        received.append((message.text, message.from_user.wa_id))

    handlers = [h for hs in whatsapp_bot.wa._handlers.values() for h in hs
                if hasattr(h, "_callback")]
    assert handlers, "no registered pywa handler found to intercept"

    originals = [(h, h._callback) for h in handlers]
    for handler, _ in originals:
        handler._callback = record
    try:
        yield received
    finally:
        for handler, callback in originals:
            handler._callback = callback


def wait_for(predicate, timeout: float = 2.0, interval: float = 0.02) -> bool:
    """Poll until `predicate` holds or the timeout expires.

    pywa dispatches handlers off the request, so a delivered message may land a moment
    after the response returns. Polling with a generous ceiling beats a fixed sleep,
    which either wastes time or goes flaky on a loaded machine.
    """
    import time as _time
    deadline = _time.monotonic() + timeout
    while _time.monotonic() < deadline:
        if predicate():
            return True
        _time.sleep(interval)
    return predicate()
