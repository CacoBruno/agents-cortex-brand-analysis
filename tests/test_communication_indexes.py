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


def test_nps_contribution_and_frequency():
    workflow = CommunicationIndexesWorkflow()

    contribution = workflow.run(
        CommunicationIndexRequest(
            data=[
                {"Empresa": "A", "tema": "X", "impacto": "Promotores", "alcance": 60},
                {"Empresa": "A", "tema": "X", "impacto": "Detratores", "alcance": 20},
                {"Empresa": "A", "tema": "Y", "impacto": "Inócuos", "alcance": 20},
            ],
            operation="nps_contribution",
            group_by=["Empresa"],
            dimension_column="tema",
            value_column="alcance",
            impact_column="impacto",
        )
    )
    assert contribution.rows == 2
    assert "nps_contrib_tema" in contribution.columns

    frequency = workflow.run(
        CommunicationIndexRequest(
            data=[
                {"Empresa": "A", "impacto": "Positivo", "freq": 3},
                {"Empresa": "A", "impacto": "Negativo", "freq": 1},
            ],
            operation="frequency",
            group_by=["Empresa"],
            value_column="freq",
            impact_column="impacto",
        )
    )
    assert frequency.data[0]["total"] == 4
    assert frequency.data[0]["% Positivo"] == 0.75


def test_protagonism_filter_and_multi_sum_operations():
    workflow = CommunicationIndexesWorkflow()

    protagonism = workflow.run(
        CommunicationIndexRequest(
            data=[
                {"Empresa": "A", "tipo": "usar", "prot": "Protagonismo", "alcance": 10},
                {"Empresa": "A", "tipo": "ignorar", "prot": "Figurante", "alcance": 90},
            ],
            operation="protagonism",
            group_by=["Empresa"],
            value_column="alcance",
            impact_column="prot",
            filter_column="tipo",
            filter_value="usar",
        )
    )
    assert protagonism.data[0]["protagonism_score"] == 1.0

    journalist = workflow.run(
        CommunicationIndexRequest(
            data=[
                {"Empresa": "A", "jornalista_count": 2, "count": 1},
                {"Empresa": "A", "jornalista_count": 3, "count": 4},
            ],
            operation="journalist",
            group_by=["Empresa"],
        )
    )
    assert journalist.data[0]["jornalista_count"] == 5
    assert journalist.data[0]["count"] == 5

    action = workflow.run(
        CommunicationIndexRequest(
            data=[
                {"Empresa": "A", "acao_count": 1, "count": 2},
                {"Empresa": "A", "acao_count": 2, "count": 3},
            ],
            operation="action",
            group_by=["Empresa"],
        )
    )
    assert action.data[0]["acao_count"] == 3
    assert action.data[0]["count"] == 5
