"""Unit tests for error handling in the Notion MCP server.

A failed Notion call has to survive three steps to be useful to a client: it must be
classified correctly, it must not be destroyed by response normalization, and it must
reach the client flagged as an error. Each step had a defect.

1. Classification. handle_notion_error searched str(error) for "Unauthorized", "Not
   found" and "Forbidden". Notion sends "API token is invalid.", "Could not find page
   with ID: ..." and "Insufficient permissions for this endpoint.", so none of the
   three branches could match and every failure became a generic api_error. The SDK
   supplies APIResponseError.code and .status, which is what it now reads.

2. Normalization. The dispatch layer guarded on isinstance(result, dict), and an error
   envelope is a dict, so it went into a normalizer built from mapping rules. Page,
   database, comment and list lost every field and returned {}. Block, user and
   property item copied the envelope's "type" into a payload field, returning
   plausible-looking objects such as {"userType": "not_found_error"}.

3. Reporting. CallToolResult.isError is set only for a handler that raises, and every
   branch caught its exceptions and returned the message as content, so failures
   arrived as successful calls.

These tests cover the three in isolation. The end-to-end behaviour, through a real
server process and the real MCP transport, is in test_live_end_to_end.py.
"""

import httpx
import pytest
from notion_client.errors import APIErrorCode, APIResponseError, RequestTimeoutError


def _api_error(status: int, code: APIErrorCode, message: str) -> APIResponseError:
    """Build the exception the Notion SDK would raise for a given failure."""
    request = httpx.Request("GET", "https://api.notion.com/v1/pages/x")
    return APIResponseError(httpx.Response(status_code=status, text=message,
                                           request=request), message, code)


# Notion's real message text. None of it contains the words the old classifier looked
# for, which is why all three of its branches were unreachable. The 404 wording is the
# one quoted in issue #1664.
SDK_FAILURES = [
    (404, APIErrorCode.ObjectNotFound, "Could not find page with ID: 0000.",
     "not_found_error"),
    (401, APIErrorCode.Unauthorized, "API token is invalid.",
     "authentication_error"),
    (403, APIErrorCode.RestrictedResource, "Insufficient permissions for this endpoint.",
     "permission_error"),
    (429, APIErrorCode.RateLimited, "You have been rate limited.", "api_error"),
    (400, APIErrorCode.ValidationError, "body failed validation.", "api_error"),
    (409, APIErrorCode.ConflictError, "Conflict occurred while saving.", "api_error"),
    (503, APIErrorCode.ServiceUnavailable, "Notion is unavailable.", "api_error"),
]

ERROR_ENVELOPES = [
    {"error": "Authentication failed. Please check your Notion API key.",
     "type": "authentication_error"},
    {"error": "The requested resource was not found. Check the ID and permissions.",
     "type": "not_found_error"},
    {"error": "Access denied. The integration may not have permission to access this resource.",
     "type": "permission_error"},
    {"error": "Notion API error: boom", "type": "api_error"},
]

NORMALIZER_NAMES = ["page", "database", "block", "user", "comment",
                    "property_item", "list"]


@pytest.fixture
def page():
    """A minimal but realistic page payload."""
    return {
        "object": "page", "id": "1a2b3c4d-0000-0000-0000-000000000000",
        "created_time": "2026-01-01T00:00:00.000Z",
        "last_edited_time": "2026-01-02T00:00:00.000Z",
        "created_by": {"object": "user", "id": "user-1"},
        "archived": False,
        "properties": {"Name": {"type": "title", "title": []}},
        "url": "https://notion.so/page",
    }


@pytest.fixture
def block():
    """A paragraph block. Its "type" collides with the envelope's "type"."""
    return {"object": "block", "id": "block-1", "type": "paragraph",
            "has_children": False, "archived": False, "paragraph": {"rich_text": []}}


@pytest.fixture
def user():
    """A person user. Same collision on "type"."""
    return {"object": "user", "id": "user-1", "type": "person", "name": "Ada",
            "person": {"email": "ada@example.com"}}


@pytest.fixture
def list_response():
    """A paginated list of pages."""
    return {"object": "list",
            "results": [{"object": "page", "id": "page-1"},
                        {"object": "page", "id": "page-2"}],
            "next_cursor": None, "has_more": False}


def _normalizers():
    """Resolve NORMALIZER_NAMES to the callables the dispatch layer uses."""
    from functools import partial
    import server
    return {
        "page": server.normalize_page,
        "database": server.normalize_database,
        "block": server.normalize_block,
        "user": server.normalize_user,
        "comment": server.normalize_comment,
        "property_item": server.normalize_property_item,
        "list": partial(server.normalize_list_response,
                        item_normalizer=server.normalize_page),
    }


# --------------------------------------------------------------------------
# 1. Classification
# --------------------------------------------------------------------------

class TestErrorClassification:
    """handle_notion_error must read the SDK's structured fields, not the message."""

    @pytest.mark.parametrize("status,code,message,expected", SDK_FAILURES,
                             ids=[c.value for _, c, _, _ in SDK_FAILURES])
    def test_classifies_from_the_sdk_error_code(self, status, code, message, expected):
        """Every documented Notion error code lands in the right category."""
        from tools.base import handle_notion_error
        assert handle_notion_error(_api_error(status, code, message))["type"] == expected

    @pytest.mark.parametrize("status,code,message,expected", SDK_FAILURES,
                             ids=[c.value for _, c, _, _ in SDK_FAILURES])
    def test_carries_vendor_code_status_and_message(self, status, code, message, expected):
        """The precise Notion detail is preserved rather than replaced by prose.

        The old envelope discarded which page was missing. "details" keeps it.
        """
        from tools.base import handle_notion_error
        envelope = handle_notion_error(_api_error(status, code, message))
        assert envelope["code"] == code.value
        assert envelope["status"] == status
        assert envelope["details"] == message

    def test_message_text_alone_does_not_drive_classification(self):
        """An exception whose text says "Not found" but carries no code is generic.

        This is the inverse of the old bug and guards against reintroducing string
        matching: prose must not be able to promote an error into a category.
        """
        from tools.base import handle_notion_error
        assert handle_notion_error(Exception("Not found"))["type"] == "api_error"

    def test_non_sdk_exception_still_produces_an_envelope(self):
        """A plain exception is still reported, without code or status."""
        from tools.base import handle_notion_error
        envelope = handle_notion_error(ValueError("something odd"))
        assert envelope["type"] == "api_error"
        assert "something odd" in envelope["error"]
        assert "code" not in envelope
        assert "status" not in envelope

    def test_timeout_is_reported_as_a_generic_error(self):
        """RequestTimeoutError has a code attribute that is a plain string, not an
        APIErrorCode, so it must not crash the lookup or be miscategorised."""
        from tools.base import handle_notion_error
        envelope = handle_notion_error(RequestTimeoutError())
        assert envelope["type"] == "api_error"
        assert envelope["code"] == "notionhq_client_request_timeout"


# --------------------------------------------------------------------------
# 2. The predicate that separates envelopes from payloads
# --------------------------------------------------------------------------

class TestIsErrorEnvelope:
    """The single definition of the envelope shape."""

    @pytest.mark.parametrize("envelope", ERROR_ENVELOPES,
                             ids=[e["type"] for e in ERROR_ENVELOPES])
    def test_accepts_every_category(self, envelope):
        """Each of the four categories is recognised."""
        from tools.base import is_error_envelope
        assert is_error_envelope(envelope) is True

    def test_accepts_what_the_producer_emits(self):
        """The predicate and the producer must agree on the real article."""
        from tools.base import handle_notion_error, is_error_envelope
        envelope = handle_notion_error(
            _api_error(404, APIErrorCode.ObjectNotFound, "Could not find page."))
        assert is_error_envelope(envelope) is True

    def test_rejects_payload_whose_property_is_named_error(self, page):
        """Notion property names are arbitrary, so "error" is a legal one.

        This is the false positive a looser predicate would hit.
        """
        from tools.base import is_error_envelope
        page["properties"]["error"] = {"type": "rich_text", "rich_text": []}
        page["error"] = "a page can legitimately carry this key"
        assert is_error_envelope(page) is False

    def test_rejects_object_whose_type_is_a_notion_type(self, block):
        """A block's type is "paragraph", never an error category."""
        from tools.base import is_error_envelope
        assert is_error_envelope(block) is False

    def test_rejects_error_key_with_unknown_type(self):
        """A message with a type outside the vocabulary is not an envelope."""
        from tools.base import is_error_envelope
        assert is_error_envelope({"error": "boom", "type": "teapot_error"}) is False

    def test_rejects_missing_type(self):
        """An error message alone is not enough."""
        from tools.base import is_error_envelope
        assert is_error_envelope({"error": "boom"}) is False

    def test_rejects_missing_error(self):
        """A recognised type alone is not enough."""
        from tools.base import is_error_envelope
        assert is_error_envelope({"type": "api_error"}) is False

    def test_rejects_non_string_error(self):
        """A property holding a dict under "error" cannot masquerade."""
        from tools.base import is_error_envelope
        assert is_error_envelope({"error": {"nested": 1}, "type": "api_error"}) is False

    @pytest.mark.parametrize("value", [None, [], "", 0, 3.5, True, set()],
                             ids=["none", "list", "str", "int", "float", "bool", "set"])
    def test_rejects_non_dict(self, value):
        """Anything that is not a dict is not an envelope."""
        from tools.base import is_error_envelope
        assert is_error_envelope(value) is False

    def test_rejects_empty_dict(self):
        """An empty dict is the symptom of the old bug, not an envelope."""
        from tools.base import is_error_envelope
        assert is_error_envelope({}) is False


class TestProducerPredicateContract:
    """The two must not drift apart."""

    @pytest.mark.parametrize("status,code,message,expected", SDK_FAILURES,
                             ids=[c.value for _, c, _, _ in SDK_FAILURES])
    def test_every_produced_envelope_is_recognised(self, status, code, message, expected):
        """A new category added to the producer without ERROR_TYPES fails here."""
        from tools.base import handle_notion_error, is_error_envelope
        assert is_error_envelope(handle_notion_error(_api_error(status, code, message)))

    def test_error_types_has_no_unreachable_entries(self):
        """A category left in ERROR_TYPES after its mapping is deleted fails here."""
        from tools.base import handle_notion_error, ERROR_TYPES
        produced = {handle_notion_error(_api_error(s, c, m))["type"]
                    for s, c, m, _ in SDK_FAILURES}
        produced.add(handle_notion_error(ValueError("x"))["type"])
        assert produced == set(ERROR_TYPES)


# --------------------------------------------------------------------------
# 3. Failures escalate instead of being normalized away
# --------------------------------------------------------------------------

class TestFailuresEscalate:
    """apply_normalizer turns an envelope into an exception the framework can flag."""

    @pytest.mark.parametrize("kind", NORMALIZER_NAMES)
    @pytest.mark.parametrize("envelope", ERROR_ENVELOPES,
                             ids=[e["type"] for e in ERROR_ENVELOPES])
    def test_every_normalizer_raises_on_an_envelope(self, kind, envelope):
        """No normalizer may quietly consume a failure."""
        from server import apply_normalizer, NotionToolError
        with pytest.raises(NotionToolError):
            apply_normalizer(dict(envelope), _normalizers()[kind])

    def test_raised_error_carries_the_envelope(self):
        """The structured detail is available to anything catching the exception."""
        from server import apply_normalizer, NotionToolError, normalize_page
        envelope = dict(ERROR_ENVELOPES[1])
        with pytest.raises(NotionToolError) as excinfo:
            apply_normalizer(envelope, normalize_page)
        assert excinfo.value.envelope == envelope

    def test_string_form_is_the_json_envelope(self):
        """The framework builds error content from str(exception), so it has to be
        the serialised envelope rather than a repr."""
        import json
        from server import apply_normalizer, NotionToolError, normalize_page
        envelope = dict(ERROR_ENVELOPES[1])
        with pytest.raises(NotionToolError) as excinfo:
            apply_normalizer(envelope, normalize_page)
        assert json.loads(str(excinfo.value)) == envelope


# --------------------------------------------------------------------------
# 4. The golden path must be untouched
# --------------------------------------------------------------------------

class TestGoldenPathStillNormalizes:
    """Real payloads normalize exactly as before."""

    def test_page_normalizes(self, page):
        """A page maps onto its rule-defined field names."""
        from server import apply_normalizer, normalize_page
        out = apply_normalizer(page, normalize_page)
        assert out["pageId"] == page["id"]
        assert out["objectType"] == "page"
        assert out["createdBy"] == "user-1"
        assert out["urlPath"] == "https://notion.so/page"

    def test_block_keeps_its_real_type(self, block):
        """blockType still carries the Notion type the bug overwrote."""
        from server import apply_normalizer, normalize_block
        out = apply_normalizer(block, normalize_block)
        assert out["blockId"] == "block-1"
        assert out["blockType"] == "paragraph"
        assert out["hasChildren"] is False

    def test_user_keeps_its_real_type(self, user):
        """Same collision, on the user object."""
        from server import apply_normalizer, normalize_user
        out = apply_normalizer(user, normalize_user)
        assert out["userId"] == "user-1"
        assert out["userType"] == "person"
        assert out["personEmail"] == "ada@example.com"

    def test_list_response_normalizes(self, list_response):
        """Pagination and item mapping are unaffected."""
        from functools import partial
        from server import apply_normalizer, normalize_list_response, normalize_page
        out = apply_normalizer(list_response,
                               partial(normalize_list_response,
                                       item_normalizer=normalize_page))
        assert out["itemCount"] == 2
        assert out["hasMoreResults"] is False
        assert out["items"][0]["pageId"] == "page-1"

    def test_page_with_property_named_error_still_normalizes(self, page):
        """The false-positive case reaches the normalizer rather than raising."""
        from server import apply_normalizer, normalize_page
        page["properties"]["error"] = {"type": "rich_text", "rich_text": []}
        out = apply_normalizer(page, normalize_page)
        assert out["pageId"] == page["id"]
        assert "error" in out["pageProperties"]


class TestDegenerateInputs:
    """Inputs that are neither a payload nor an envelope."""

    @pytest.mark.parametrize("value", [None, [], "text", 0],
                             ids=["none", "list", "str", "int"])
    def test_non_dict_passes_through_unchanged(self, value):
        """Preserves the behaviour of the isinstance guard this replaced."""
        from server import apply_normalizer, normalize_page
        assert apply_normalizer(value, normalize_page) == value

    def test_empty_dict_is_normalized_not_raised(self):
        """An empty dict is a payload as far as the boundary is concerned."""
        from server import apply_normalizer, normalize_page
        assert apply_normalizer({}, normalize_page) == {}


# --------------------------------------------------------------------------
# 5. What the guard is protecting against
# --------------------------------------------------------------------------

class TestRegressionDocumentsOldBehaviour:
    """Pins what the normalizers do to an envelope when called directly.

    These describe the defect, not desired behaviour. They exist so anyone who later
    removes apply_normalizer can see exactly what breaks, and so a change to the
    normalizers that alters the collision is noticed here rather than in production.
    """

    def test_mapping_normalizers_erase_the_envelope(self):
        """page, database and comment drop every field and return {}."""
        import server
        envelope = dict(ERROR_ENVELOPES[1])
        assert server.normalize_page(envelope) == {}
        assert server.normalize_database(envelope) == {}
        assert server.normalize_comment(envelope) == {}

    def test_type_copying_normalizers_fabricate_a_field(self):
        """block, user and property item launder the error into a payload field.

        The more dangerous half: the caller receives a structurally valid object.
        """
        import server
        envelope = dict(ERROR_ENVELOPES[1])
        assert server.normalize_block(envelope) == {"blockType": "not_found_error"}
        assert server.normalize_user(envelope) == {"userType": "not_found_error"}
        assert server.normalize_property_item(envelope) == {"propertyType": "not_found_error"}
