import os
from typing import ClassVar

from pydantic_settings import BaseSettings


class SlackSettings(BaseSettings):
    """Settings for Slack integration"""

    # Application settings
    WEBSITE_URL: str = ""

    # LLM API keys
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
    GEMINI_API_KEY: str

    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_API_KEY: str

    # Slack settings
    SLACK_CLIENT_ID: str
    SLACK_CLIENT_SECRET: str
    SLACK_SIGNING_SECRET: str
    SLACK_SCOPES: str
    SLACK_REDIRECT_URI: str
    SLACK_BOT_TOKEN: str

    # Message configuration - Mark these as ClassVar
    MAX_MESSAGE_LENGTH: ClassVar[int] = 3000
    MAX_BLOCK_MESSAGE_LENGTH: ClassVar[int] = 2000
    STREAMING_TIMEOUT: ClassVar[float] = 200.0
    STREAMING_SLEEP_DELAY: ClassVar[float] = 0.05

    # UI configuration - Mark this as ClassVar
    SLACK_APP_COLOR: ClassVar[str] = os.getenv("SLACK_APP_COLOR", "#4A154B")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Create a global settings instance
settings = SlackSettings()
