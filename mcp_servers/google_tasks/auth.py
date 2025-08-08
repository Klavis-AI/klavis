import os
import logging
from functools import lru_cache
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource

logger = logging.getLogger(__name__)

# Environment variable names expected
GOOGLE_CLIENT_ID = "GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET"
GOOGLE_REFRESH_TOKEN = "GOOGLE_REFRESH_TOKEN"
GOOGLE_TOKEN_URI = os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")


class GoogleTasksAuthError(Exception):
    """Raised when credentials cannot be constructed."""


@lru_cache(maxsize=1)
def _build_credentials() -> Credentials:
    """Builds and returns a cached Google OAuth2 Credentials object.

    Expects a refresh token workflow (installed app or OAuth web) with the
    refresh token and client ID/secret stored in environment variables.
    """

    client_id = os.getenv(GOOGLE_CLIENT_ID)
    client_secret = os.getenv(GOOGLE_CLIENT_SECRET)
    refresh_token = os.getenv(GOOGLE_REFRESH_TOKEN)

    if not all([client_id, client_secret, refresh_token]):
        raise GoogleTasksAuthError(
            "Missing one or more of GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN"
        )

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=GOOGLE_TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=[
            "https://www.googleapis.com/auth/tasks",
        ],
    )

    if not creds.valid or creds.expired:
        logger.debug("Refreshing Google OAuth2 credentials for Tasks API")
        creds.refresh(Request())

    return creds


def get_tasks_service() -> Resource:
    """Return an authorized googleapiclient Resource for the Tasks API (v1)."""
    creds = _build_credentials()
    return build("tasks", "v1", credentials=creds, cache_discovery=False)

