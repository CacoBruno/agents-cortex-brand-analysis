from cortex_brand_analysis.domain.models import NewsCheckRequest, PublicationMatch
from cortex_brand_analysis.workflows.news_check import NewsCheckWorkflow, url_variants


class FakeCortexGateway:
    @staticmethod
    def client_name(platform_url: str) -> str:
        return "cliente"

    def check_publications(
        self,
        platform_url: str,
        original_urls: list[str],
        clipping_urls: list[str],
    ) -> list[PublicationMatch]:
        return [
            PublicationMatch(
                cortex_id="123",
                title="Já existente",
                original_url="https://example.com/a/",
            )
        ]

    def check_pr_data(self, original_urls: list[str], client: str) -> list[dict]:
        return [
            {
                "cliente": client,
                "original_link": "https://example.com/b",
                "titulo_da_publicacao": "No data lake",
            }
        ]


def test_url_variants_handles_trailing_slash() -> None:
    assert url_variants("https://example.com/a") == {
        "https://example.com/a",
        "https://example.com/a/",
    }


def test_news_check_separates_platform_lake_and_missing() -> None:
    workflow = NewsCheckWorkflow(FakeCortexGateway())
    result = workflow.run(
        NewsCheckRequest(
            platform_url="cliente.cortex-intelligence.com",
            original_urls=[
                "https://example.com/a",
                "https://example.com/b",
                "https://example.com/c",
            ],
        )
    )

    assert result.requested == 3
    assert len(result.found_in_platform) == 1
    assert result.missing_from_platform == [
        "https://example.com/b",
        "https://example.com/c",
    ]
    assert result.found_in_data_lake[0]["original_link"] == "https://example.com/b"
    assert result.missing_from_data_lake == ["https://example.com/c"]
