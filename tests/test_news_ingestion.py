from datetime import date

import pytest
from pydantic import ValidationError

from cortex_brand_analysis.domain.errors import NewsEnrichmentError
from cortex_brand_analysis.domain.models import PublicationMatch
from cortex_brand_analysis.domain.news_ingestion import (
    EnrichedNews,
    NewsIngestionApplyRequest,
    NewsIngestionRequest,
    news_idempotency_key,
)
from cortex_brand_analysis.workflows.news_ingestion import NewsIngestionWorkflow


class FakeCortex:
    @staticmethod
    def client_name(platform_url):
        return "cliente"

    def check_publications(self, platform_url, original_urls, clipping_urls):
        return [
            PublicationMatch(
                cortex_id="1",
                original_url="https://example.com/already",
            )
        ]

    def check_pr_data(self, original_urls, client):
        return [{"cliente": client, "original_link": "https://example.com/lake"}]


class FakeEnricher:
    def __init__(self):
        self.calls = []

    def enrich(self, url, client_name):
        self.calls.append(url)
        return EnrichedNews(
            idempotency_key=news_idempotency_key(client_name, url),
            url=url,
            title="Título",
            outlet="Veículo",
            domain="example.com",
            content="Conteúdo",
            publication_date=date(2026, 10, 7),
            captured_at="2026-10-07T12:00:00-03:00",
        )


class FailingEnricher:
    def enrich(self, url, client_name):
        if url.endswith("/known"):
            raise NewsEnrichmentError("page responded with HTTP 404")
        raise RuntimeError("Incorrect API key provided: sk-proj-****abcd (org-123)")


class FakeStorage:
    def __init__(self):
        self.items = None

    def store(self, items, platform_url):
        self.items = items
        return [f"prefix/{item.idempotency_key}.json" for item in items]


def test_idempotency_key_is_stable_for_trailing_slash():
    assert news_idempotency_key("Cliente", "https://example.com/a") == news_idempotency_key(
        "cliente", "https://example.com/a/"
    )


def test_preview_only_enriches_items_missing_from_platform_and_lake():
    enricher = FakeEnricher()
    storage = FakeStorage()
    workflow = NewsIngestionWorkflow(FakeCortex(), enricher, storage)

    result = workflow.preview(
        NewsIngestionRequest(
            platform_url="cliente.cortex-intelligence.com",
            urls=[
                "https://example.com/already",
                "https://example.com/lake",
                "https://example.com/new",
            ],
        )
    )

    assert result.to_enrich == ["https://example.com/new"]
    assert enricher.calls == ["https://example.com/new"]
    assert storage.items is None


def test_preview_does_not_leak_internal_error_messages():
    workflow = NewsIngestionWorkflow(FakeCortex(), FailingEnricher(), FakeStorage())

    result = workflow.preview(
        NewsIngestionRequest(
            platform_url="cliente.cortex-intelligence.com",
            urls=["https://example.com/known", "https://example.com/boom"],
        )
    )

    assert result.failed == {
        "https://example.com/known": "page responded with HTTP 404",
        "https://example.com/boom": "unexpected failure while enriching the news",
    }


def test_apply_stores_using_deterministic_keys():
    enricher = FakeEnricher()
    storage = FakeStorage()
    workflow = NewsIngestionWorkflow(FakeCortex(), enricher, storage)

    result = workflow.apply(
        NewsIngestionApplyRequest(
            platform_url="cliente.cortex-intelligence.com",
            urls=["https://example.com/new"],
            confirm=True,
        )
    )

    assert result.stored == 1
    assert result.storage_keys[0].endswith(".json")
    assert storage.items[0].idempotency_key in result.storage_keys[0]


def test_apply_requires_explicit_confirmation():
    with pytest.raises(ValidationError):
        NewsIngestionApplyRequest(
            platform_url="cliente.cortex-intelligence.com",
            urls=["https://example.com/new"],
            confirm=False,
        )
