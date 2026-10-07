from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded exclusively from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mcp_api_key: str = Field(min_length=16)
    platform_login: str | None = None
    platform_password: str | None = None
    openai_api_key: str | None = None
    aws_region: str = "sa-east-1"
    log_level: str = "INFO"
    http_timeout_seconds: float = Field(default=20.0, gt=0, le=120)


@lru_cache
def get_settings() -> Settings:
    return Settings()
