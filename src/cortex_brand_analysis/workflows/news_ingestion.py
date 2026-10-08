from __future__ import annotations

import logging
from typing import Protocol

from cortex_brand_analysis.domain.errors import (
    ConfigurationError,
    DomainError,
    NewsEnrichmentError,
)
from cortex_brand_analysis.domain.models import NewsCheckRequest
from cortex_brand_analysis.domain.news_ingestion import (
    EnrichedNews,
    NewsIngestionApplyRequest,
    NewsIngestionApplyResult,
    NewsIngestionPreview,
    NewsIngestionRequest,
)
from cortex_brand_analysis.services.protocols import CortexGateway
from cortex_brand_analysis.workflows.news_check import NewsCheckWorkflow

logger = logging.getLogger(__name__)


class NewsEnricher(Protocol):
    def enrich(self, url: str, client_name: str) -> EnrichedNews: ...


class NewsStorage(Protocol):
    def store(self, items: list[EnrichedNews], platform_url: str) -> list[str]: ...


class NewsIngestionWorkflow:
    def __init__(
        self,
        cortex: CortexGateway,
        enricher: NewsEnricher,
        storage: NewsStorage,
    ) -> None:
        self.cortex = cortex
        self.enricher = enricher
        self.storage = storage

    def preview(self, request: NewsIngestionRequest) -> NewsIngestionPreview:
        urls = [str(url) for url in request.urls]
        check = NewsCheckWorkflow(self.cortex).run(
            NewsCheckRequest(
                platform_url=request.platform_url,
                original_urls=urls,
            )
        )

        platform_urls = {
            match.original_url
            for match in check.found_in_platform
            if match.original_url
        }
        lake_urls = {
            str(item.get("original_link"))
            for item in check.found_in_data_lake
            if item.get("original_link")
        }

        to_enrich = list(check.missing_from_data_lake)
        client_name = self.cortex.client_name(request.platform_url)

        enriched: list[EnrichedNews] = []
        failed: dict[str, str] = {}
        for url in to_enrich:
            try:
                enriched.append(self.enricher.enrich(url, client_name))
            except NewsEnrichmentError as exc:
                failed[url] = str(exc)
            except ConfigurationError:
                raise
            except Exception:
                logger.exception("Unexpected failure enriching news URL")
                failed[url] = "unexpected failure while enriching the news"

        return NewsIngestionPreview(
            requested=len(urls),
            already_in_platform=sorted(platform_urls),
            already_in_data_lake=sorted(lake_urls),
            to_enrich=to_enrich,
            enriched=enriched,
            failed=failed,
        )

    def apply(self, request: NewsIngestionApplyRequest) -> NewsIngestionApplyResult:
        if request.confirm is not True:
            raise DomainError("confirm=true is required to store enriched news")

        preview = self.preview(
            NewsIngestionRequest(
                platform_url=request.platform_url,
                urls=request.urls,
            )
        )
        keys = self.storage.store(preview.enriched, request.platform_url)
        return NewsIngestionApplyResult(
            stored=len(keys),
            storage_keys=keys,
            preview=preview,
        )
