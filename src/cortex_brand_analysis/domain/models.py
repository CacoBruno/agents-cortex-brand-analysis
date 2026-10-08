from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


def normalize_platform_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if not value:
        raise ValueError("platform_url cannot be empty")
    if "://" not in value:
        value = f"https://{value}"
    return value


class NewsCheckRequest(BaseModel):
    platform_url: str
    original_urls: list[str] = Field(default_factory=list)
    clipping_urls: list[str] = Field(default_factory=list)

    @field_validator("platform_url")
    @classmethod
    def validate_platform_url(cls, value: str) -> str:
        return normalize_platform_url(value)

    @field_validator("original_urls", "clipping_urls")
    @classmethod
    def clean_urls(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in values:
            url = raw.strip()
            if url and url not in seen:
                cleaned.append(url)
                seen.add(url)
        return cleaned


class PublicationMatch(BaseModel):
    cortex_id: str | None = None
    title: str | None = None
    source: str | None = None
    date: str | None = None
    original_url: str | None = None
    clipping_url: str | None = None


class NewsCheckResult(BaseModel):
    requested: int
    found_in_platform: list[PublicationMatch]
    missing_from_platform: list[str]
    found_in_data_lake: list[dict] = Field(default_factory=list)
    missing_from_data_lake: list[str] = Field(default_factory=list)

    @property
    def all_accounted_for(self) -> bool:
        return not self.missing_from_platform or not self.missing_from_data_lake


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "cortex-brand-analysis"
