from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Dimension = Literal[
    "volume", "timeseries", "sentiment", "protagonism", "themes", "sources", "reach"
]
StepOperation = Literal["export", "profile", "timeseries", "value_counts", "groupby"]


class AnalysisIntent(BaseModel):
    analysis_type: Literal["brand_exposure", "theme", "comparison"] = "brand_exposure"
    platform_url: str = Field(min_length=1)
    start_date: date
    end_date: date
    companies: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    dimensions: list[Dimension] = Field(min_length=1, max_length=7)
    session_id: str | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> AnalysisIntent:
        if self.start_date > self.end_date:
            raise ValueError("start_date must not exceed end_date")
        if not any(value.strip() for value in self.companies + self.products):
            raise ValueError("at least one company or product is required")
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ValueError("dimensions must be unique")
        return self


class ExportStep(BaseModel):
    step_id: str
    operation: Literal["export"] = "export"
    depends_on: list[str] = Field(default_factory=list)


class ProfileStep(BaseModel):
    step_id: str
    operation: Literal["profile"] = "profile"
    depends_on: list[str]


class TimeseriesStep(BaseModel):
    step_id: str
    operation: Literal["timeseries"] = "timeseries"
    depends_on: list[str]
    date_column: Literal["Data"] = "Data"
    frequency: Literal["D", "W", "M", "Q", "Y"] = "D"


class ValueCountsStep(BaseModel):
    step_id: str
    operation: Literal["value_counts"] = "value_counts"
    depends_on: list[str]
    column: Literal[
        "Sentimento", "Nível de Protagonismo", "Temas", "Fonte"
    ]


class GroupByStep(BaseModel):
    step_id: str
    operation: Literal["groupby"] = "groupby"
    depends_on: list[str]
    column: Literal["Fonte"] = "Fonte"
    metric: Literal["Alcance orgânico"] = "Alcance orgânico"
    aggregation: Literal["sum"] = "sum"


AnalysisStep = ExportStep | ProfileStep | TimeseriesStep | ValueCountsStep | GroupByStep


class AnalysisPlan(BaseModel):
    plan_id: str
    intent: AnalysisIntent
    steps: list[AnalysisStep] = Field(min_length=2, max_length=15)


class AnalysisState(BaseModel):
    session_id: str
    tenant_id: str
    platform_url: str
    dataset_ids: list[str] = Field(default_factory=list)
    active_dataset_id: str | None = None
    plan_id: str | None = None
    executed_steps: list[str] = Field(default_factory=list)
    result_ids: list[str] = Field(default_factory=list)
    status: Literal["draft", "validated", "running", "complete", "failed"] = "draft"
