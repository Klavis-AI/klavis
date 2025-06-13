from enum import Enum


class BodyFormat(str, Enum):
    STORAGE = "storage"  # Storage representation for editing, with relative urls in the markup

    def to_api_value(self) -> str:
        mapping = {
            BodyFormat.STORAGE: "storage",
        }
        return mapping.get(self, BodyFormat.STORAGE.value)


class PageUpdateMode(str, Enum):
    """The mode of update for a page"""

    PREPEND = "prepend"  # Add content to the beginning of the page.
    APPEND = "append"  # Add content to the end of the page.
    REPLACE = "replace"  # Replace the entire page with the new content.


class PageSortOrder(str, Enum):
    """The order of the pages to sort by"""

    ID_ASCENDING = "id-ascending"
    ID_DESCENDING = "id-descending"
    TITLE_ASCENDING = "title-ascending"
    TITLE_DESCENDING = "title-descending"
    CREATED_DATE_ASCENDING = "created-date-oldest-to-newest"
    CREATED_DATE_DESCENDING = "created-date-newest-to-oldest"
    MODIFIED_DATE_ASCENDING = "modified-date-oldest-to-newest"
    MODIFIED_DATE_DESCENDING = "modified-date-newest-to-oldest"

    def to_api_value(self) -> str:
        mapping = {
            PageSortOrder.ID_ASCENDING: "id",
            PageSortOrder.ID_DESCENDING: "-id",
            PageSortOrder.TITLE_ASCENDING: "title",
            PageSortOrder.TITLE_DESCENDING: "-title",
            PageSortOrder.CREATED_DATE_ASCENDING: "created-date",
            PageSortOrder.CREATED_DATE_DESCENDING: "-created-date",
            PageSortOrder.MODIFIED_DATE_ASCENDING: "modified-date",
            PageSortOrder.MODIFIED_DATE_DESCENDING: "-modified-date",
        }
        return mapping.get(self, PageSortOrder.CREATED_DATE_DESCENDING.value)


class AttachmentSortOrder(str, Enum):
    """The order of the attachments to sort by"""

    CREATED_DATE_ASCENDING = "created-date-oldest-to-newest"
    CREATED_DATE_DESCENDING = "created-date-newest-to-oldest"
    MODIFIED_DATE_ASCENDING = "modified-date-oldest-to-newest"
    MODIFIED_DATE_DESCENDING = "modified-date-newest-to-oldest"

    def to_api_value(self) -> str:
        mapping = {
            AttachmentSortOrder.CREATED_DATE_ASCENDING: "created-date",
            AttachmentSortOrder.CREATED_DATE_DESCENDING: "-created-date",
            AttachmentSortOrder.MODIFIED_DATE_ASCENDING: "modified-date",
            AttachmentSortOrder.MODIFIED_DATE_DESCENDING: "-modified-date",
        }
        return mapping.get(self, AttachmentSortOrder.CREATED_DATE_DESCENDING.value) 