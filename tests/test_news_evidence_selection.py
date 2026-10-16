import pandas as pd
import pytest

from cortex_brand_analysis.domain.errors import DomainError
from cortex_brand_analysis.workflows.news_evidence_selection import (
    NewsEvidenceSelectionV1,
)


def test_legacy_default_days_deduplicates_rules():
    frame = pd.DataFrame(
        {
            "Data": ["2026-10-01", "2026-10-02", "2026-10-03"],
            "contr_nps_score": [0.5, -0.6, 0.2],
            "Promotores": [100, 5, 25],
            "Detratores": [0, 80, 2],
            "z_score_contr_nps": [2.0, -1.0, 0.0],
        }
    )
    result = NewsEvidenceSelectionV1().key_days(frame)
    assert result["selected_days"] == ["2026-10-01", "2026-10-02"]
    assert result["rules"]["dia_maior_detrator"] == "2026-10-02"
    assert len(result["reverse_rules"]["2026-10-01"]) == 3


def test_legacy_vehicle_score_and_tiebreak():
    frame = pd.DataFrame(
        {
            "Fonte": ["Veículo A", "Veículo B", "Veículo C"],
            "Promotores": [100, 40, 50],
            "Detratores": [90, 10, 20],
        }
    )
    result = NewsEvidenceSelectionV1().top_vehicles(frame, top_n=2)
    assert result["Fonte"].tolist() == ["Veículo C", "Veículo B"]
    assert result["composite_score"].tolist() == [30, 30]


def test_topics_separate_positive_and_negative_contributions():
    frame = pd.DataFrame(
        {
            "Assunto específico": ["Crédito", "Regulação", "Fraude"],
            "nps_contrib_assunto_especifico": [0.2, -0.4, -0.1],
            "total_assunto_especifico": [10, 6, 3],
            "nps_score_assunto_especifico": [0.8, -0.7, -0.2],
        }
    )
    result = NewsEvidenceSelectionV1().top_topics(frame)
    assert result["assuntos_promotores"][0]["Assunto específico"] == "Crédito"
    assert [row["Assunto específico"] for row in result["assuntos_detratores"]] == [
        "Regulação",
        "Fraude",
    ]


def test_missing_columns_are_rejected():
    with pytest.raises(DomainError, match="missing evidence columns"):
        NewsEvidenceSelectionV1().top_vehicles(pd.DataFrame({"Fonte": ["A"]}))
