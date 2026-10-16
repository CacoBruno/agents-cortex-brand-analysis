from datetime import date

import pytest
from pydantic import ValidationError

from cortex_brand_analysis.domain.analysis import AnalysisIntent
from cortex_brand_analysis.domain.errors import DomainError
from cortex_brand_analysis.workflows.analysis_planning import AnalysisPlanner, AnalysisValidator


def intent(**overrides):
    params = {
        "platform_url": "https://iu-comunicacao.cortex-intelligence.com/",
        "start_date": date(2026, 10, 1),
        "end_date": date(2026, 10, 16),
        "companies": ["Itaú"],
        "dimensions": ["volume", "timeseries", "sentiment", "sources"],
    }
    params.update(overrides)
    return AnalysisIntent(**params)


def test_exposure_plan_has_deterministic_dependencies():
    plan = AnalysisValidator().validate(AnalysisPlanner().plan(intent()))
    assert [step.step_id for step in plan.steps] == [
        "export", "profile", "timeseries", "sentiment", "sources"
    ]
    assert all(s.depends_on == ["export"] for s in plan.steps[1:])


def test_missing_brand_is_rejected():
    with pytest.raises(ValidationError, match="at least one"):
        intent(companies=[])


def test_duplicate_dimensions_are_rejected():
    with pytest.raises(ValidationError, match="unique"):
        intent(dimensions=["volume", "volume"])


def test_wrong_platform_is_rejected():
    with pytest.raises(DomainError, match="unsupported"):
        AnalysisValidator().validate(AnalysisPlanner().plan(intent(platform_url="https://example.com")))


def test_oversized_period_is_rejected():
    with pytest.raises(DomainError, match="period exceeds"):
        AnalysisValidator().validate(
            AnalysisPlanner().plan(intent(start_date=date(2023, 1, 1)))
        )


def test_forward_dependency_is_rejected():
    plan = AnalysisPlanner().plan(intent())
    plan.steps[1].depends_on = ["missing"]
    with pytest.raises(DomainError, match="dependency"):
        AnalysisValidator().validate(plan)
