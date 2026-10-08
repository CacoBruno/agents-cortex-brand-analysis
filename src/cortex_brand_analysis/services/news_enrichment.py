from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

from cortex_brand_analysis.config import Settings
from cortex_brand_analysis.domain.errors import ConfigurationError, NewsEnrichmentError
from cortex_brand_analysis.domain.news_ingestion import EnrichedNews, news_idempotency_key

__all__ = ["NewsEnrichmentError", "OpenAINewsEnricher"]


class OpenAINewsEnricher:
    """Fetch a news page and use OpenAI structured output to extract metadata."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        if not settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for news enrichment")
        self.settings = settings
        self.client = client or httpx.Client(
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
        )

    def enrich(self, url: str, client_name: str) -> EnrichedNews:
        response = self.client.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 CortexBrandAnalysis/1.0"},
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(soup.stripped_strings)
        if not text:
            raise NewsEnrichmentError("page did not contain readable text")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise NewsEnrichmentError(
                "install the project with the 'ai' extra to enable enrichment"
            ) from exc

        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "outlet": {"type": "string"},
                "city": {"type": ["string", "null"]},
                "state": {"type": ["string", "null"]},
                "author": {"type": ["string", "null"]},
                "content": {"type": "string"},
                "publication_date": {"type": ["string", "null"]},
            },
            "required": [
                "title",
                "outlet",
                "city",
                "state",
                "author",
                "content",
                "publication_date",
            ],
            "additionalProperties": False,
        }

        ai = OpenAI(api_key=self.settings.openai_api_key)
        result = ai.responses.create(
            model="gpt-6-luna",
            input=[
                {
                    "role": "system",
                    "content": (
                        "Extraia os metadados da publicação jornalística. "
                        "Preserve o conteúdo factual e não invente informações."
                    ),
                },
                {"role": "user", "content": text[:120000]},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "news_metadata",
                    "strict": True,
                    "schema": schema,
                }
            },
        )

        import json

        data = json.loads(result.output_text)
        captured_at = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
        domain = urlparse(str(response.url)).hostname or urlparse(url).hostname or ""

        return EnrichedNews(
            idempotency_key=news_idempotency_key(client_name, url),
            url=url,
            title=data["title"],
            outlet=data["outlet"],
            domain=domain.removeprefix("www."),
            city=data["city"],
            state=data["state"],
            author=data["author"],
            content=data["content"],
            publication_date=data["publication_date"],
            captured_at=captured_at,
        )
