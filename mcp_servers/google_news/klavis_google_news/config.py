# klavis_google_news/config.py
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
