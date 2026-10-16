from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlparse

from cortex_brand_analysis.domain.analysis import (
    AnalysisIntent,
    AnalysisPlan,
    AnalysisStep,
    ExportStep,
    GroupByStep,
    ProfileStep,
    TimeseriesStep,
    ValueCountsStep,
)
from cortex_brand_analysis.domain.errors import DomainError

DIMENSIONS = {
    "sentiment": "Sentimento",
    "protagonism": "Nível de Protagonismo",
    "themes": "Temas",
    "sources": "Fonte",
}


class AnalysisPlanner:
    """Build a deterministic allow-listed plan; no model-generated executable code."""

    def plan(self, intent: AnalysisIntent) -> AnalysisPlan:
        steps: list[AnalysisStep] = [
            ExportStep(step_id="export"),
            ProfileStep(step_id="profile", depends_on=["export"]),
        ]
        for dimension in intent.dimensions:
            if dimension == "timeseries":
                steps.append(TimeseriesStep(step_id=dimension, depends_on=["export"]))
            elif dimension in DIMENSIONS:
                steps.append(
                    ValueCountsStep(
                        step_id=dimension,
                        depends_on=["export"],
                        column=DIMENSIONS[dimension],
                    )
                )
            elif dimension == "reach":
                steps.append(GroupByStep(step_id=dimension, depends_on=["export"]))
        return AnalysisPlan(plan_id="brand_exposure_v1", intent=intent, steps=steps)


class AnalysisValidator:
    """Preflight; does not access Cortex and does not authorize platform access."""

    def __init__(self, max_days: int = 366) -> None:
        self.max_days = max_days

    def validate(self, plan: AnalysisPlan) -> AnalysisPlan:
        intent = plan.intent
        parsed = urlparse(intent.platform_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise DomainError("platform_url must be an HTTPS URL")
        if not parsed.hostname.endswith(".cortex-intelligence.com"):
            raise DomainError("unsupported Cortex platform host")
        if intent.end_date - intent.start_date > timedelta(days=self.max_days):
            raise DomainError("analysis period exceeds configured limit")
        if any(not v.strip() for v in intent.companies + intent.products):
            raise DomainError("empty company or product filter")
        ids = [step.step_id for step in plan.steps]
        if len(ids) != len(set(ids)):
            raise DomainError("duplicate analysis step ID")
        if sum(isinstance(s, ExportStep) for s in plan.steps) != 1:
            raise DomainError("plan must contain exactly one export step")
        seen: set[str] = set()
        for step in plan.steps:
            if any(dep not in seen for dep in step.depends_on):
                raise DomainError("invalid or forward step dependency")
            if step.operation != "export" and "export" not in seen:
                raise DomainError("all analysis steps must follow export")
            seen.add(step.step_id)
        return plan
