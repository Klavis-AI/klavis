import httpx
from typing import Any, Dict
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide configuration loaded from env vars (12-factor)."""

    serpapi_key: str = Field(alias="SERPAPI_API_KEY")
    serpapi_base: str = "https://serpapi.com"
    extra: str = "ignore"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:  # pragma: no cover
    return Settings()  # cached singleton


class ToolExecutionError(Exception):
    def __init__(self, message: str, status_code: int = 400, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


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
