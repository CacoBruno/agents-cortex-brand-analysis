from __future__ import annotations

from typing import Protocol

from cortex_brand_analysis.domain.models import PublicationMatch


class CortexGateway(Protocol):
    def check_publications(
        self,
        platform_url: str,
        original_urls: list[str],
        clipping_urls: list[str],
    ) -> list[PublicationMatch]: ...

    def check_pr_data(self, original_urls: list[str], client: str) -> list[dict]: ...
