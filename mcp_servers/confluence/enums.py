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


# Conversion functions to convert string values to enum objects
def convert_sort_by_to_enum(sort_by_str: str | None) -> PageSortOrder | None:
    """Convert string sort_by value to PageSortOrder enum"""
    if sort_by_str is None:
        return None
    
    # Create a mapping from string values to enum values
    string_to_enum = {
        "id-ascending": PageSortOrder.ID_ASCENDING,
        "id-descending": PageSortOrder.ID_DESCENDING,
        "title-ascending": PageSortOrder.TITLE_ASCENDING,
        "title-descending": PageSortOrder.TITLE_DESCENDING,
        "created-date-oldest-to-newest": PageSortOrder.CREATED_DATE_ASCENDING,
        "created-date-newest-to-oldest": PageSortOrder.CREATED_DATE_DESCENDING,
        "modified-date-oldest-to-newest": PageSortOrder.MODIFIED_DATE_ASCENDING,
        "modified-date-newest-to-oldest": PageSortOrder.MODIFIED_DATE_DESCENDING,
    }
    
    return string_to_enum.get(sort_by_str, PageSortOrder.CREATED_DATE_DESCENDING)


def convert_sort_order_to_enum(sort_order_str: str | None) -> AttachmentSortOrder | None:
    """Convert string sort_order value to AttachmentSortOrder enum"""
    if sort_order_str is None:
        return None
    
    # Create a mapping from string values to enum values
    string_to_enum = {
        "created-date-oldest-to-newest": AttachmentSortOrder.CREATED_DATE_ASCENDING,
        "created-date-newest-to-oldest": AttachmentSortOrder.CREATED_DATE_DESCENDING,
        "modified-date-oldest-to-newest": AttachmentSortOrder.MODIFIED_DATE_ASCENDING,
        "modified-date-newest-to-oldest": AttachmentSortOrder.MODIFIED_DATE_DESCENDING,
    }
    
    return string_to_enum.get(sort_order_str, AttachmentSortOrder.CREATED_DATE_DESCENDING)


def convert_update_mode_to_enum(update_mode_str: str | None) -> PageUpdateMode:
    """Convert string update_mode value to PageUpdateMode enum"""
    if update_mode_str is None:
        return PageUpdateMode.APPEND
    
    # Create a mapping from string values to enum values
    string_to_enum = {
        "prepend": PageUpdateMode.PREPEND,
        "append": PageUpdateMode.APPEND,
        "replace": PageUpdateMode.REPLACE,
    }
    
    return string_to_enum.get(update_mode_str, PageUpdateMode.APPEND) 