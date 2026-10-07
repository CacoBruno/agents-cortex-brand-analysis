from __future__ import annotations

from cortex_brand_analysis.domain.models import NewsCheckRequest, NewsCheckResult
from cortex_brand_analysis.services.protocols import CortexGateway


def url_variants(url: str) -> set[str]:
    clean = url.strip()
    if not clean:
        return set()
    return {clean, clean.rstrip("/"), f"{clean.rstrip('/')}/"}


def _matched_urls(matches: list, attribute: str) -> set[str]:
    values: set[str] = set()
    for match in matches:
        value = getattr(match, attribute, None)
        if value:
            values.update(url_variants(value))
    return values


class NewsCheckWorkflow:
    def __init__(self, cortex: CortexGateway) -> None:
        self.cortex = cortex

    def run(self, request: NewsCheckRequest) -> NewsCheckResult:
        matches = self.cortex.check_publications(
            platform_url=request.platform_url,
            original_urls=request.original_urls,
            clipping_urls=request.clipping_urls,
        )

        platform_original = _matched_urls(matches, "original_url")
        platform_clipping = _matched_urls(matches, "clipping_url")

        missing_original = [
            url for url in request.original_urls
            if url_variants(url).isdisjoint(platform_original)
        ]
        missing_clipping = [
            url for url in request.clipping_urls
            if url_variants(url).isdisjoint(platform_clipping)
        ]
        missing_platform = missing_original + missing_clipping

        client = self.cortex.client_name(request.platform_url)  # type: ignore[attr-defined]
        lake_matches = self.cortex.check_pr_data(missing_original, client=client)

        lake_urls: set[str] = set()
        for item in lake_matches:
            original = item.get("original_link")
            if original:
                lake_urls.update(url_variants(str(original)))

        missing_lake = [
            url for url in missing_original
            if url_variants(url).isdisjoint(lake_urls)
        ]

        return NewsCheckResult(
            requested=len(request.original_urls) + len(request.clipping_urls),
            found_in_platform=matches,
            missing_from_platform=missing_platform,
            found_in_data_lake=lake_matches,
            missing_from_data_lake=missing_lake,
        )
