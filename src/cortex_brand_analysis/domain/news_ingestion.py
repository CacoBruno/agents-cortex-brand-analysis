from __future__ import annotations

import hashlib
from datetime import date
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, Field, HttpUrl


def normalize_url(url: str) -> str:
    value = url.strip()
    parts = urlsplit(value)
    if not parts.scheme or not parts.netloc:
        raise ValueError(f"invalid URL: {url}")
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def news_idempotency_key(client: str, url: str) -> str:
    canonical = f"{client.strip().lower()}|{normalize_url(url)}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class NewsIngestionRequest(BaseModel):
    platform_url: str
    urls: list[HttpUrl] = Field(min_length=1)


class EnrichedNews(BaseModel):
    idempotency_key: str
    url: str
    title: str
    outlet: str
    domain: str
    city: str | None = None
    state: str | None = None
    author: str | None = None
    content: str
    publication_date: date | None = None
    captured_at: str
    provider: str = "Oráculo"
    media_type: str = "Online"


class NewsIngestionPreview(BaseModel):
    requested: int
    already_in_platform: list[str] = Field(default_factory=list)
    already_in_data_lake: list[str] = Field(default_factory=list)
    to_enrich: list[str] = Field(default_factory=list)
    enriched: list[EnrichedNews] = Field(default_factory=list)
    failed: dict[str, str] = Field(default_factory=dict)


class NewsIngestionApplyRequest(NewsIngestionRequest):
    confirm: bool


class NewsIngestionApplyResult(BaseModel):
    stored: int
    storage_keys: list[str] = Field(default_factory=list)
    preview: NewsIngestionPreview
