# klavis_google_news/client.py
import httpx
from typing import Any, Dict
from klavis_google_news.config import get_settings
from klavis_google_news.errors import ToolExecutionError


class SerpApiClient:
    """Thin async wrapper around SerpAPI with 429-retry back-off."""

    def __init__(self):
        settings = get_settings()
        self._client = httpx.AsyncClient(
            base_url=settings.serpapi_base,
            params={"api_key": settings.serpapi_key},
            timeout=20.0,
        )

    async def get(
        self, path: str, params: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        response = await self._client.get(path, params=params)

        if response.status_code == 429:  # simple back-off; exponential optional
            await httpx.sleep(1.0)
            response = await self._client.get(path, params=params)

        if response.status_code >= 400:
            raise ToolExecutionError(
                message="SerpAPI request failed",
                status_code=response.status_code,
                details=response.text,
            )

        data = response.json()
        if "error" in data:
            raise ToolExecutionError(message=data["error"], status_code=500)

        return data

    async def aclose(self):
        await self._client.aclose()
