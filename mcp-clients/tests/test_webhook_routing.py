"""Tests for the WhatsApp bot's webhook routing.

The bot builds its pywa client with `server=app`, so pywa registers the webhook routes
on the FastAPI app at construction time, before any route declared later in the module.
pywa serves them at its default endpoint "/", which is where CALLBACK_URL points, and it
verifies the X-Hub-Signature-256 header on every update. That path works.

The module then hand-wrote a second pair of handlers at /webhook doing the same job
badly, and declared a health check on "/" that pywa had already taken:

  1. The health check never ran. GET / answered 422 for a missing hub.verify_token
     parameter, so any container healthcheck or load balancer reads it as unhealthy.
  2. The hand-written POST /webhook called wa.process_webhook, which is not a method of
     pywa's WhatsApp class in any release, so it raised AttributeError.
  3. It read request.json() and passed the parsed body on, discarding the raw bytes and
     the signature header, so it authenticated nothing. Pointing Meta at /webhook would
     pass verification and then silently deliver nothing.
  4. Its GET counterpart compared the verify token with == (CWE-208, issue #1400).

The fix deletes the duplicates and moves the health check to /health. These tests pin
the behaviour of the surviving path end to end.
"""

import hashlib
import hmac
import json
from .conftest import TEST_APP_SECRET, TEST_VERIFY_TOKEN, wait_for

# An inbound text message shaped as Meta sends it.
MESSAGE_UPDATE = {
    "object": "whatsapp_business_account",
    "entry": [{"id": "WABA", "changes": [{"field": "messages", "value": {
        "messaging_product": "whatsapp",
        "metadata": {"display_phone_number": "15550001111",
                     "phone_number_id": "9876543210"},
        # "user_id" is the business-scoped id Meta now sends alongside wa_id. pywa 4.x
        # requires it when building the contact; 2.x ignores it. Including it keeps this
        # fixture working on both.
        "contacts": [{"profile": {"name": "Tester"}, "wa_id": "15551234567",
                      "user_id": "BSUID15551234567"}],
        "messages": [{"from": "15551234567", "id": "wamid.TEST",
                      "timestamp": "1700000000", "type": "text",
                      "text": {"body": "hello there"}}],
    }}]}],
}


def _body(update=None) -> bytes:
    """Serialise once: the signature covers these exact bytes, not a re-encoding."""
    return json.dumps(update if update is not None else MESSAGE_UPDATE).encode()


def _sign(body: bytes, secret: str = TEST_APP_SECRET) -> str:
    """The X-Hub-Signature-256 header Meta sends."""
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _headers(body: bytes, secret: str = TEST_APP_SECRET) -> dict:
    return {"Content-Type": "application/json", "X-Hub-Signature-256": _sign(body, secret)}


class TestRouteOwnership:
    """Who serves what, once the duplicates are gone."""

    def test_pywa_owns_the_webhook_root(self, bot_app):
        """pywa's handlers serve "/", which is where CALLBACK_URL points."""
        served = {(r.path, m): r.endpoint.__name__
                  for r in bot_app.routes
                  for m in (getattr(r, "methods", None) or ())}
        assert "pywa" in served[("/", "GET")]
        assert "pywa" in served[("/", "POST")]

    def test_root_has_exactly_one_handler_per_method(self, bot_app):
        """A second registration would be shadowed and silently never run."""
        for method in ("GET", "POST"):
            n = sum(1 for r in bot_app.routes
                    if r.path == "/" and method in (getattr(r, "methods", None) or ()))
            assert n == 1, f"{n} handlers registered for {method} /"

    def test_no_hand_written_webhook_routes_remain(self, bot_app):
        """/webhook is gone rather than left serving an unauthenticated endpoint."""
        assert not [r for r in bot_app.routes if r.path == "/webhook"]


class TestHealthCheck:
    """The health check was unreachable while pywa held "/"."""

    def test_health_endpoint_responds(self, client):
        """Reports status instead of 422 for a missing hub.verify_token."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok", "service": "WhatsApp Bot"}


class TestVerificationChallenge:
    """GET /, the handshake Meta performs when registering the webhook."""

    def test_correct_token_returns_the_challenge(self, client):
        r = client.get("/", params={"hub.mode": "subscribe",
                                    "hub.verify_token": TEST_VERIFY_TOKEN,
                                    "hub.challenge": "1158201444"})
        assert r.status_code == 200
        assert r.text == "1158201444"

    def test_wrong_token_does_not_return_the_challenge(self, client):
        r = client.get("/", params={"hub.mode": "subscribe",
                                    "hub.verify_token": "wrong-token",
                                    "hub.challenge": "1158201444"})
        assert r.status_code == 403
        assert "1158201444" not in r.text

    def test_missing_token_does_not_return_the_challenge(self, client):
        r = client.get("/", params={"hub.mode": "subscribe",
                                    "hub.challenge": "1158201444"})
        assert r.status_code in (403, 422)
        assert "1158201444" not in r.text


class TestSignatureEnforcement:
    """Updates that cannot be attributed to Meta must not be processed.

    These assert that a forged update is refused, not which status code carries the
    refusal: pywa answers 401 for both missing and invalid signatures in the 2.x line
    and separates 401 from 403 in 4.x.
    """

    @staticmethod
    def _assert_refused(response) -> None:
        assert 400 <= response.status_code < 500, (
            f"forged update was not refused: {response.status_code} {response.text}")

    def test_unsigned_update_is_refused(self, client):
        r = client.post("/", content=_body(),
                        headers={"Content-Type": "application/json"})
        self._assert_refused(r)

    def test_wrong_secret_is_refused(self, client):
        body = _body()
        r = client.post("/", content=body, headers=_headers(body, "not-the-app-secret"))
        self._assert_refused(r)

    def test_signature_over_other_bytes_is_refused(self, client):
        """Guards a fix that verifies a re-serialised body rather than what was sent."""
        r = client.post("/", content=_body(), headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": _sign(b'{"object":"other","entry":[]}')})
        self._assert_refused(r)

    def test_replayed_signature_on_tampered_body_is_refused(self, client):
        original = _body()
        tampered = _body({**MESSAGE_UPDATE, "object": "tampered"})
        r = client.post("/", content=tampered, headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": _sign(original)})
        self._assert_refused(r)


class TestMessageIsActuallyDelivered:
    """The point of the endpoint: a genuine message must reach the bot's handler.

    A 200 alone proves nothing here. pywa answers 200 for a well-signed update it does
    not recognise, so a status assertion would pass even if the message were dropped on
    the floor. These assert the module's own @wa.on_message callback ran and saw the
    message. The captured_messages fixture restores the real callback afterwards, so the
    tests do not depend on running in any particular order.
    """

    def test_signed_message_reaches_the_handler(self, client, captured_messages):
        """A properly signed inbound text message is delivered, intact."""
        body = _body()
        response = client.post("/", content=body, headers=_headers(body))
        assert response.status_code == 200

        assert wait_for(lambda: len(captured_messages) == 1), (
            f"message was not delivered to the handler: {captured_messages}")
        assert captured_messages == [("hello there", "15551234567")]

    def test_unsigned_message_never_reaches_the_handler(self, client, captured_messages):
        """The security property stated as an effect, not as a status code.

        Refusing with a 4xx is only half of it. What matters is that the payload never
        reaches application code.
        """
        client.post("/", content=_body(),
                    headers={"Content-Type": "application/json"})
        assert not wait_for(lambda: bool(captured_messages), timeout=0.5)
        assert captured_messages == [], "a forged update was dispatched to the handler"

    def test_wrongly_signed_message_never_reaches_the_handler(self, client,
                                                             captured_messages):
        """Same, for a signature computed with the wrong secret."""
        body = _body()
        client.post("/", content=body, headers=_headers(body, "not-the-app-secret"))
        assert not wait_for(lambda: bool(captured_messages), timeout=0.5)
        assert captured_messages == []


class TestModuleNoLongerCarriesTheDuplicates:
    """The duplicates are removed, not merely bypassed."""

    def test_no_manual_webhook_decorators(self):
        import inspect
        from mcp_clients import whatsapp_bot
        src = inspect.getsource(whatsapp_bot)
        assert '@app.get("/webhook")' not in src
        assert '@app.post("/webhook")' not in src

    def test_no_call_to_a_method_pywa_does_not_have(self):
        """wa.process_webhook is absent from every pywa release."""
        import inspect
        from mcp_clients import whatsapp_bot
        assert "process_webhook" not in inspect.getsource(whatsapp_bot)

    def test_client_is_configured_to_validate_updates(self):
        from mcp_clients import whatsapp_bot
        wa = whatsapp_bot.wa
        assert wa._app_secret == TEST_APP_SECRET
        assert wa._validate_updates is True
        assert wa._webhook_endpoint == "/"
