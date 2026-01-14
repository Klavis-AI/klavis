import os, time, base64
from typing import Any, Dict, Optional
import httpx

# Zoom API endpoints
ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE = "https://api.zoom.us/v2"

class ZoomError(Exception):
    """
    Custom exception for Zoom API errors.
    Includes HTTP status code and any returned payload for debugging.
    """
    def __init__(self, message: str, status: int = 0, payload: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status = status
        self.payload = payload or {}

class ZoomClient:
    def __init__(self):
        # Read required API credentials from environment
        self.account_id = os.environ.get("ZOOM_ACCOUNT_ID")
        self.client_id = os.environ.get("ZOOM_CLIENT_ID")
        self.client_secret = os.environ.get("ZOOM_CLIENT_SECRET")

        # Fail early if missing credentials
        if not all([self.account_id, self.client_id, self.client_secret]):
            raise ZoomError("Missing env vars: ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET")

        # Token cache
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0

        # Shared async HTTP client
        self._client = httpx.AsyncClient(timeout=30)

    async def _refresh_token(self) -> None:
        """
        Request a new OAuth access token using the Account Credentials flow.
        """
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        params = {"grant_type": "account_credentials", "account_id": self.account_id}
        headers = {"Authorization": f"Basic {auth}"}

        r = await self._client.post(ZOOM_TOKEN_URL, params=params, headers=headers)

        if r.status_code >= 400:
            try:
                payload = r.json()
            except Exception:
                payload = {"text": r.text}
            raise ZoomError("Failed to obtain access token", r.status_code, payload)

        data = r.json()
        self._access_token = data["access_token"]
        
        self._expires_at = time.time() + float(data.get("expires_in", 0)) - 60

    async def _get_token(self) -> str:
        """
        Return a valid access token, refreshing it if expired or missing.
        """
        if not self._access_token or time.time() >= self._expires_at:
            await self._refresh_token()
        return self._access_token  

    async def _request(self, method: str, path: str, *, params=None, json_body=None) -> Dict[str, Any]:
        """
        Core request helper for talking to the Zoom API.
        Automatically handles authentication and common error cases.
        """
        token = await self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{ZOOM_API_BASE}{path}"

        r = await self._client.request(method, url, params=params, json=json_body, headers=headers)

        # Zoom rate limit hit
        if r.status_code == 429:
            try:
                payload = r.json()
            except Exception:
                payload = {"text": r.text}
            raise ZoomError("Rate limited by Zoom (HTTP 429)", 429, payload)

        if r.status_code >= 400:
            try:
                payload = r.json()
            except Exception:
                payload = {"text": r.text}
            raise ZoomError(f"Zoom API error {r.status_code}", r.status_code, payload)

        return r.json() if r.content else {}

    # API Methods

    async def list_meetings_for_user(self, user_id_or_email: str, page_size: int = 10, type_: str = "upcoming"):
        """
        Get meetings for a given user (by email or user ID).
        Type can be 'scheduled', 'live', or 'upcoming'.
        """
        params = {"type": type_, "page_size": min(max(page_size, 1), 100)}
        return await self._request("GET", f"/users/{user_id_or_email}/meetings", params=params)

    async def create_meeting(
        self,
        user_id_or_email: str,
        topic: str,
        start_time_iso: str,
        duration_minutes: int,
        timezone: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ):
        """
        Create a new scheduled meeting for a specific user.
        start_time_iso should be in ISO 8601 format.
        """
        body = {
            "topic": topic,
            "type": 2,  
            "start_time": start_time_iso,
            "duration": duration_minutes,
        }
        if timezone:
            body["timezone"] = timezone
        if settings:
            body["settings"] = settings
        return await self._request("POST", f"/users/{user_id_or_email}/meetings", json_body=body)

    async def get_meeting(self, meeting_id: str | int):
        """Retrieve detailed info for a single meeting."""
        return await self._request("GET", f"/meetings/{meeting_id}")

    async def update_meeting(self, meeting_id: str | int, patch_fields: dict):
        """Update fields for an existing meeting."""
        return await self._request("PATCH", f"/meetings/{meeting_id}", json_body=patch_fields)

    async def delete_meeting(self, meeting_id: str | int):
        """Delete/cancel a meeting."""
        return await self._request("DELETE", f"/meetings/{meeting_id}")

    async def list_users(self, page_size: int = 30, status: str = "active"):
        """List all account users with optional status filter."""
        params = {"status": status, "page_size": min(max(page_size, 1), 300)}
        return await self._request("GET", "/users", params=params)
