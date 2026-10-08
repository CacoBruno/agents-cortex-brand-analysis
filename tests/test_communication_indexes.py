from cortex_brand_analysis.domain.communication_indexes import (
    CommunicationIndexRequest,
)
from cortex_brand_analysis.workflows.communication_indexes import (
    CommunicationIndexesWorkflow,
)


def test_nps_score_matches_source_formula():
    data = [
        {"Empresa": "A", "impacto": "Promotores", "alcance": 60},
        {"Empresa": "A", "impacto": "Detratores", "alcance": 20},
        {"Empresa": "A", "impacto": "Inócuos", "alcance": 20},
    ]

    result = CommunicationIndexesWorkflow().run(
        CommunicationIndexRequest(
            data=data,
            operation="nps",
            group_by=["Empresa"],
            value_column="alcance",
            impact_column="impacto",
        )
    )

    assert result.rows == 1
    assert result.data[0]["nps_score"] == 0.4


def test_protagonism_score_matches_source_formula():
    data = [
        {"Empresa": "A", "prot": "Protagonismo", "alcance": 40},
        {"Empresa": "A", "prot": "Referência contextual / Setor", "alcance": 10},
        {"Empresa": "A", "prot": "Figurante", "alcance": 50},
    ]

    result = CommunicationIndexesWorkflow().run(
        CommunicationIndexRequest(
            data=data,
            operation="protagonism",
            group_by=["Empresa"],
            value_column="alcance",
            impact_column="prot",
        )
    )

    assert result.data[0]["protagonism_score"] == 0.5


def test_valoration_sum():
    data = [
        {"Empresa": "A", "valor": 10.25},
        {"Empresa": "A", "valor": 20.25},
    ]

    result = CommunicationIndexesWorkflow().run(
        CommunicationIndexRequest(
            data=data,
            operation="valoration",
            group_by=["Empresa"],
            value_column="valor",
        )
    )

    assert result.data[0]["valor"] == 30.5
