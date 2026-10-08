import pytest
from pydantic import ValidationError

from cortex_brand_analysis.domain.analytics import AnalyticsRequest
from cortex_brand_analysis.domain.errors import DomainError
from cortex_brand_analysis.workflows.analytics import AnalyticsWorkflow

DATA = [
    {"tema": "Crédito", "valor": 10, "data": "2026-01-01"},
    {"tema": "Crédito", "valor": 20, "data": "2026-02-01"},
    {"tema": "Fraude", "valor": 5, "data": "2026-02-15"},
]


def test_groupby_mean():
    result = AnalyticsWorkflow().run(
        AnalyticsRequest(
            data=DATA,
            operation="groupby",
            group_by=["tema"],
            metric="valor",
            aggregation="mean",
        )
    )

    assert result.rows == 2
    credito = next(row for row in result.data if row["tema"] == "Crédito")
    assert credito["valor"] == 15.0


def test_correlation_requires_known_columns():
    with pytest.raises(DomainError, match="unknown columns"):
        AnalyticsWorkflow().run(
            AnalyticsRequest(
                data=DATA,
                operation="correlation",
                columns=["valor", "missing"],
            )
        )


def test_timeseries_count():
    result = AnalyticsWorkflow().run(
        AnalyticsRequest(
            data=DATA,
            operation="timeseries",
            date_column="data",
            aggregation="count",
            frequency="M",
        )
    )

    assert result.rows == 2
    assert [row["count"] for row in result.data] == [1, 2]


@pytest.mark.parametrize("operation", ["groupby", "timeseries"])
def test_metric_without_aggregation_is_rejected(operation):
    with pytest.raises(ValidationError, match=f"{operation} requires aggregation"):
        AnalyticsRequest(
            data=DATA,
            operation=operation,
            group_by=["tema"],
            date_column="data",
            metric="valor",
        )
