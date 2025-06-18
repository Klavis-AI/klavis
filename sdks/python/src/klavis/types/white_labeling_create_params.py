# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["WhiteLabelingCreateParams"]


class WhiteLabelingCreateParams(TypedDict, total=False):
    client_id: Required[str]
    """OAuth client ID"""

    client_secret: Required[str]
    """OAuth client secret"""

    server_name: Required[
        Literal[
            "Slack",
            "Supabase",
            "Notion",
            "GitHub",
            "Jira",
            "Confluence",
            "WordPress",
            "Gmail",
            "Google Drive",
            "Google Calendar",
            "Google Sheets",
            "Google Docs",
            "Attio",
            "Salesforce",
            "Linear",
            "Asana",
            "Close",
            "ClickUp",
        ]
    ]
    """Optional. The name of the server"""

    account_id: Optional[str]
    """Optional. The UUID of the account"""

    callback_url: Optional[str]
    """Optional. OAuth callback URL"""
