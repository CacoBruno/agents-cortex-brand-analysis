from cortex_brand_analysis.domain.classification import (
    ClassificationApplyRequest,
    ClassificationChange,
    ClassificationPatch,
    ClassificationRecord,
    ClassificationReviewRequest,
    ClassificationSelector,
)
from cortex_brand_analysis.workflows.classification_review import ClassificationReviewWorkflow


class FakeGateway:
    uploaded: list[dict] | None = None

    def find_classifications(self, platform_url, selectors):
        return [
            ClassificationRecord(
                media_analysis_id="abc",
                title="Matéria",
                original_url="https://example.com/a",
                company="Itaú",
                values={
                    "Sentimento": "Neutro",
                    "Tier": "Tier 2",
                    "Tópicos": "Crédito",
                },
            )
        ]

    def upload_classification_changes(self, platform_url, rows):
        self.uploaded = rows
        return ["exec-123"]


def _change():
    return ClassificationChange(
        selector=ClassificationSelector(media_analysis_id="abc"),
        patch=ClassificationPatch(sentiment="Negativo", tier="Tier 1"),
    )


def test_preview_does_not_write() -> None:
    gateway = FakeGateway()
    workflow = ClassificationReviewWorkflow(gateway)

    result = workflow.preview(
        ClassificationReviewRequest(
            platform_url="cliente.cortex-intelligence.com",
            changes=[_change()],
        )
    )

    assert result.matched == 1
    assert gateway.uploaded is None
    assert result.changes[0].before["Sentimento"] == "Neutro"
    assert result.changes[0].after["Sentimento"] == "Negativo"
    assert set(result.changes[0].changed_fields) == {"Sentimento", "Tier"}


def test_apply_requires_explicit_confirm_and_writes_only_changed_record() -> None:
    gateway = FakeGateway()
    workflow = ClassificationReviewWorkflow(gateway)

    result = workflow.apply(
        ClassificationApplyRequest(
            platform_url="cliente.cortex-intelligence.com",
            changes=[_change()],
            confirm=True,
        )
    )

    assert result.updated == 1
    assert result.execution_ids == ["exec-123"]
    assert gateway.uploaded is not None
    assert gateway.uploaded[0]["Chave Análise de Mídia Hash"] == "abc"
    assert gateway.uploaded[0]["Sentimento"] == "Negativo"
