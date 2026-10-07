from __future__ import annotations

from cortex_brand_analysis.domain.exports import (
    ExportResult,
    MediaAnalysisExportRequest,
    PublicationExportRequest,
)
from cortex_brand_analysis.services.protocols import CortexGateway


class ExportWorkflow:
    def __init__(self, cortex: CortexGateway) -> None:
        self.cortex = cortex

    def publications(self, request: PublicationExportRequest) -> ExportResult:
        data = self.cortex.export_publications(request)
        columns = list(data[0].keys()) if data else []
        return ExportResult(rows=len(data), columns=columns, data=data)

    def media_analysis(self, request: MediaAnalysisExportRequest) -> ExportResult:
        data = self.cortex.export_media_analysis(request)
        columns = list(data[0].keys()) if data else []
        return ExportResult(rows=len(data), columns=columns, data=data)
