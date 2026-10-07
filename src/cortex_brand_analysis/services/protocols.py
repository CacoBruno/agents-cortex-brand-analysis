from __future__ import annotations

from typing import Protocol

from cortex_brand_analysis.domain.classification import (
    ClassificationRecord,
    ClassificationSelector,
)
from cortex_brand_analysis.domain.exports import (
    MediaAnalysisExportRequest,
    PublicationExportRequest,
)
from cortex_brand_analysis.domain.models import PublicationMatch


class CortexGateway(Protocol):
    def client_name(self, platform_url: str) -> str: ...

    def check_publications(
        self,
        platform_url: str,
        original_urls: list[str],
        clipping_urls: list[str],
    ) -> list[PublicationMatch]: ...

    def check_pr_data(self, original_urls: list[str], client: str) -> list[dict]: ...

    def find_classifications(
        self,
        platform_url: str,
        selectors: list[ClassificationSelector],
    ) -> list[ClassificationRecord]: ...

    def upload_classification_changes(
        self,
        platform_url: str,
        rows: list[dict],
    ) -> list[str]: ...

    def export_publications(
        self,
        request: PublicationExportRequest,
    ) -> list[dict]: ...

    def export_media_analysis(
        self,
        request: MediaAnalysisExportRequest,
    ) -> list[dict]: ...
