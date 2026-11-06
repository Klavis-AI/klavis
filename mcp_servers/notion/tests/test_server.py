import unittest

from server import (
    normalize_block,
    normalize_comment,
    normalize_database,
    normalize_list_response,
    normalize_page,
    normalize_property_item,
    normalize_user,
)
from tools.base import handle_notion_error


class NotionResponseNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.error_responses = (
            handle_notion_error(Exception("Unauthorized")),
            handle_notion_error(Exception("Not found")),
            handle_notion_error(Exception("Forbidden")),
        )

    def test_resource_normalizers_preserve_handled_errors(self) -> None:
        normalizers = (
            normalize_page,
            normalize_database,
            normalize_block,
            normalize_user,
            normalize_comment,
            normalize_property_item,
        )

        for error_response in self.error_responses:
            for normalizer in normalizers:
                with self.subTest(
                    error_type=error_response["type"],
                    normalizer=normalizer.__name__,
                ):
                    normalized = normalizer(error_response)

                    self.assertEqual(normalized, error_response)
                    self.assertIsNot(normalized, error_response)

    def test_list_normalizer_preserves_handled_errors(self) -> None:
        for error_response in self.error_responses:
            with self.subTest(error_type=error_response["type"]):
                normalized = normalize_list_response(error_response, normalize_page)

                self.assertEqual(normalized, error_response)
                self.assertIsNot(normalized, error_response)

    def test_successful_page_normalization_is_unchanged(self) -> None:
        raw_page = {
            "id": "page-id",
            "object": "page",
            "created_time": "2026-05-30T00:00:00.000Z",
            "archived": False,
            "properties": {"Title": {"type": "title"}},
        }

        self.assertEqual(
            normalize_page(raw_page),
            {
                "pageId": "page-id",
                "objectType": "page",
                "createdAt": "2026-05-30T00:00:00.000Z",
                "isArchived": False,
                "pageProperties": {"Title": {"type": "title"}},
            },
        )


if __name__ == "__main__":
    unittest.main()
