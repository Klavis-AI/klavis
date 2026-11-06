"""Replace notion_client.Client with a fake, before the server imports it.

Python runs sitecustomize at interpreter startup, ahead of any application import, so
putting this directory on PYTHONPATH swaps the SDK for a stub without the server under
test knowing. Every other layer, the MCP framework, the transport, the dispatch and the
normalizers, is the real thing.

The stub decides what to do from the id it is given, so one server process can serve
every case the live tests need:

    page-404 / user-404 / block-404  -> APIResponseError, object_not_found
    page-401                         -> APIResponseError, unauthorized
    page-403                         -> APIResponseError, restricted_resource
    anything else                    -> a valid payload for that object kind
"""

import httpx
import notion_client
from notion_client.errors import APIResponseError, APIErrorCode

# Message text as Notion actually sends it. The 404 wording is the one quoted in
# issue #1664; the others are Notion's documented messages. They deliberately contain
# none of the words the old string-matching classifier looked for.
_FAILURES = {
    "404": (404, APIErrorCode.ObjectNotFound,
            "Could not find page with ID: 00000000-0000-0000-0000-000000000000."),
    "401": (401, APIErrorCode.Unauthorized, "API token is invalid."),
    "403": (403, APIErrorCode.RestrictedResource,
            "Insufficient permissions for this endpoint."),
}


def _maybe_fail(object_id: str) -> None:
    for suffix, (status, code, message) in _FAILURES.items():
        if str(object_id).endswith(suffix):
            request = httpx.Request("GET", f"https://api.notion.com/v1/{object_id}")
            response = httpx.Response(status_code=status, text=message, request=request)
            raise APIResponseError(response, message, code)


class _Pages:
    def retrieve(self, page_id, **kwargs):
        _maybe_fail(page_id)
        return {
            "object": "page", "id": page_id,
            "created_time": "2026-01-01T00:00:00.000Z",
            "last_edited_time": "2026-01-02T00:00:00.000Z",
            "created_by": {"object": "user", "id": "user-1"},
            "archived": False,
            "properties": {"Name": {"type": "title", "title": []}},
            "url": "https://notion.so/page",
        }


class _Users:
    def retrieve(self, user_id, **kwargs):
        _maybe_fail(user_id)
        return {"object": "user", "id": user_id, "type": "person",
                "name": "Ada", "person": {"email": "ada@example.com"}}

    def me(self, **kwargs):
        return self.retrieve("user-me")


class _Blocks:
    def retrieve(self, block_id, **kwargs):
        _maybe_fail(block_id)
        return {"object": "block", "id": block_id, "type": "paragraph",
                "has_children": False, "archived": False,
                "paragraph": {"rich_text": []}}


class FakeClient:
    """Stands in for notion_client.Client. Only the surface the tests touch."""

    def __init__(self, *args, **kwargs):
        self.pages = _Pages()
        self.users = _Users()
        self.blocks = _Blocks()


notion_client.Client = FakeClient
