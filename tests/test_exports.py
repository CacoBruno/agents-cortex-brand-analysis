from datetime import date

from cortex_brand_analysis.domain.exports import (
    MediaAnalysisExportRequest,
    PublicationExportRequest,
)
from cortex_brand_analysis.workflows.exports import ExportWorkflow


class FakeGateway:
    def export_publications(self, request):
        assert request.companies == ["Itaú"]
        return [
            {
                "ID Cortex": "1",
                "Título": "Notícia",
                "Data": "2026-10-01",
            }
        ]

    def export_media_analysis(self, request):
        assert request.products == ["Cartão"]
        return [
            {
                "Chave Análise de Mídia Hash": "abc",
                "Sentimento": "Neutro",
            }
        ]


def test_publications_export_returns_structured_result():
    result = ExportWorkflow(FakeGateway()).publications(
        PublicationExportRequest(
            platform_url="cliente.cortex-intelligence.com",
            companies=["Itaú"],
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 7),
        )
    )
    assert result.rows == 1
    assert "Título" in result.columns


def test_media_analysis_export_returns_structured_result():
    result = ExportWorkflow(FakeGateway()).media_analysis(
        MediaAnalysisExportRequest(
            platform_url="cliente.cortex-intelligence.com",
            products=["Cartão"],
        )
    )
    assert result.rows == 1
    assert result.data[0]["Sentimento"] == "Neutro"
