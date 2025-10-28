import os
from enum import Enum

ASANA_BASE_URL = "https://app.asana.com/api"
ASANA_API_VERSION = "1.0"

try:
    ASANA_MAX_CONCURRENT_REQUESTS = int(os.getenv("ASANA_MAX_CONCURRENT_REQUESTS", 3))
except ValueError:
    ASANA_MAX_CONCURRENT_REQUESTS = 3

try:
    ASANA_MAX_TIMEOUT_SECONDS = int(os.getenv("ASANA_MAX_TIMEOUT_SECONDS", 20))
except ValueError:
    ASANA_MAX_TIMEOUT_SECONDS = 20

MAX_PROJECTS_TO_SCAN_BY_NAME = 1000
MAX_TAGS_TO_SCAN_BY_NAME = 1000

PROJECT_OPT_FIELDS = [
    "gid",
    "resource_type",
    "name",
    "workspace",
    "color",
    "created_at",
    "modified_at",
    "current_status_update",
    "due_on",
    "members",
    "notes",
    "completed",
    "completed_at",
    "completed_by",
    "owner",
    "team",
    "workspace",
    "permalink_url",
]

TASK_OPT_FIELDS = [
    "gid",
    "name",
    "notes",
    "completed",
    "completed_at",
    "completed_by",
    "created_at",
    "created_by",
    "due_on",
    "start_on",
    "owner",
    "team",
    "workspace",
    "permalink_url",
    "approval_status",
    "assignee",
    "assignee_status",
    "dependencies",
    "dependents",
    "memberships",
    "num_subtasks",
    "resource_type",
    "custom_type",
    "custom_type_status_option",
    "parent",
    "tags",
    "workspace",
]


TAG_OPT_FIELDS = [
    "gid",
    "name",
    "workspace",
]

TEAM_OPT_FIELDS = [
    "gid",
    "name",
    "description",
    "organization",
    "permalink_url",
]

USER_OPT_FIELDS = [
    "gid",
    "resource_type",
    "name",
    "email",
    "photo",
    "workspaces",
]

WORKSPACE_OPT_FIELDS = [
    "gid",
    "resource_type",
    "name",
    "email_domains",
    "is_organization",
]


class TaskSortBy(Enum):
    DUE_DATE = "due_date"
    CREATED_AT = "created_at"
    COMPLETED_AT = "completed_at"
    MODIFIED_AT = "modified_at"
    LIKES = "likes"


class SortOrder(Enum):
    ASCENDING = "ascending"
    DESCENDING = "descending"


class TagColor(Enum):
    DARK_GREEN = "dark-green"
    DARK_RED = "dark-red"
    DARK_BLUE = "dark-blue"
    DARK_PURPLE = "dark-purple"
    DARK_PINK = "dark-pink"
    DARK_ORANGE = "dark-orange"
    DARK_TEAL = "dark-teal"
    DARK_BROWN = "dark-brown"
    DARK_WARM_GRAY = "dark-warm-gray"
    LIGHT_GREEN = "light-green"
    LIGHT_RED = "light-red"
    LIGHT_BLUE = "light-blue"
    LIGHT_PURPLE = "light-purple"
    LIGHT_PINK = "light-pink"
    LIGHT_ORANGE = "light-orange"
    LIGHT_TEAL = "light-teal"
    LIGHT_BROWN = "light-brown"
    LIGHT_WARM_GRAY = "light-warm-gray"


class ReturnType(Enum):
    FULL_ITEMS_DATA = "full_items_data"
    ITEMS_COUNT = "items_count" 