import pandas as pd
import pytest

from cortex_brand_analysis.domain.errors import DomainError
from cortex_brand_analysis.workflows.exposure_method import ExposureMethodV1


@pytest.fixture
def rows():
    return pd.DataFrame(
        [
            {
                "Empresa": "Itaú",
                "Tema": "A",
                "alcance": 100,
                "Tipos de impactos": "Promotores",
                "Nível de Protagonismo final": "Protagonismo",
            },
            {
                "Empresa": "Itaú",
                "Tema": "B",
                "alcance": 50,
                "Tipos de impactos": "Detratores",
                "Nível de Protagonismo final": "Figurante",
            },
            {
                "Empresa": "Itaú",
                "Tema": "B",
                "alcance": 50,
                "Tipos de impactos": "Inócuos",
                "Nível de Protagonismo final": "Referência contextual / Setor",
            },
        ]
    )


def test_reach_weighted_nps(rows):
    result = ExposureMethodV1().nps(rows, ["Empresa"])
    assert result.iloc[0]["nps_score"] == 0.25
    assert result.iloc[0]["Promotores"] == 100


def test_dimension_contribution_is_additive(rows):
    result = ExposureMethodV1().contribution(rows, ["Empresa"], "Tema")
    assert result["nps_contribution"].sum() == pytest.approx(0.25)
    assert result.set_index("Tema").loc["A", "nps_contribution"] == 0.5
    assert result.set_index("Tema").loc["B", "nps_contribution"] == -0.25


def test_promoter_only_contribution(rows):
    result = ExposureMethodV1().contribution(rows, ["Empresa"], "Tema", "Promotor")
    assert result["nps_contribution"].sum() == pytest.approx(0.5)


def test_protagonism_is_reach_weighted(rows):
    result = ExposureMethodV1().protagonism(rows, ["Empresa"])
    assert result.iloc[0]["protagonism_score"] == 0.75
    assert result.iloc[0]["total"] == 200


def test_unknown_dimension_fails(rows):
    with pytest.raises(DomainError, match="missing analytical columns"):
        ExposureMethodV1().contribution(rows, ["Empresa"], "inexistente")
