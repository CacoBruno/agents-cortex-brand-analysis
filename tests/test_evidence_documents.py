from datetime import date

import pytest
from pydantic import ValidationError

from cortex_brand_analysis.domain.evidence import EvidenceDocument, EvidenceSelection
from cortex_brand_analysis.domain.errors import DomainError
from cortex_brand_analysis.workflows.evidence_documents import EvidenceDocumentSelectorV1


def document(
    identifier: str,
    source: str = "Veiculo A",
    topic: str = "Credito",
    reach: float = 100,
    tier: str = "Tier 2",
    score: float = 1,
) -> EvidenceDocument:
    return EvidenceDocument(
        document_id=identifier,
        publication_date=date(2026, 10, 14),
        title=f"Noticia {identifier}",
        source=source,
        url=f"https://example.com/{identifier}",
        reach=reach,
        tier=tier,
        document_score=score,
        company="Itau",
        topic=topic,
    )


def test_evidence_by_source_prioritizes_reach_tier_and_score():
    docs = [
        document("low", reach=90),
        document("tier2", reach=100, tier="Tier 2", score=9),
        document("tier1", reach=100, tier="Tier 1", score=2),
        document("highest", reach=110),
    ]
    result = EvidenceDocumentSelectorV1().select(
        dataset_id="ds1", documents=docs, dimension="source", values=["Veiculo A"]
    )
    selection = result.selections[0]
    assert selection.document_ids == ["highest", "tier1", "tier2", "low"]
    assert selection.eligible_count == 4
    assert str(selection.documents[0].url) == "https://example.com/highest"
    assert selection.selection_reason


def test_evidence_topic_has_company_scope_and_deduplicates():
    docs = [
        document("a"),
        document("a"),
        document("b", topic="Outro"),
        document("c", topic="Credito"),
        document("d", topic="Credito").model_copy(update={"company": "Outro"}),
    ]
    result = EvidenceDocumentSelectorV1().select(
        dataset_id="ds1",
        documents=docs,
        dimension="topic",
        values=["Credito"],
        company="Itau",
    )
    assert result.selections[0].document_ids == ["a", "c"]
    assert result.selections[0].eligible_count == 3


def test_evidence_by_day_and_truncation():
    result = EvidenceDocumentSelectorV1().select(
        dataset_id="ds1",
        documents=[document("b"), document("a")],
        dimension="day",
        values=["2026-10-14"],
        top_n_per_value=1,
    )
    assert result.selections[0].document_ids == ["a"]


def test_invalid_day_and_missing_id_rejected():
    with pytest.raises(DomainError, match="ISO"):
        EvidenceDocumentSelectorV1().select(
            dataset_id="ds1", documents=[], dimension="day", values=["14/10/2026"]
        )
    with pytest.raises(ValidationError, match="document_ids must match"):
        EvidenceSelection(
            method_id="test",
            method_version="1",
            dataset_id="ds1",
            selection_dimension="source",
            selection_value="x",
            document_ids=["incorrect"],
            documents=[document("a")],
            selection_reason="test",
            eligible_count=1,
        )
