from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

Operation = Literal[
    "describe",
    "value_counts",
    "groupby",
    "correlation",
    "timeseries",
]

Aggregation = Literal["count", "sum", "mean", "median", "min", "max"]


class AnalyticsFilter(BaseModel):
    column: str
    operator: Literal["eq", "ne", "in", "contains", "gte", "lte"]
    value: object


class AnalyticsRequest(BaseModel):
    data: list[dict] = Field(min_length=1)
    operation: Operation
    columns: list[str] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    metric: str | None = None
    aggregation: Aggregation | None = None
    date_column: str | None = None
    frequency: Literal["D", "W", "M", "Q", "Y"] | None = None
    filters: list[AnalyticsFilter] = Field(default_factory=list)
    limit: int = Field(default=50, ge=1, le=500)

    @model_validator(mode="after")
    def validate_operation(self) -> "AnalyticsRequest":
        if self.operation == "groupby":
            if not self.group_by:
                raise ValueError("groupby requires group_by")
            if self.aggregation != "count" and not self.metric:
                raise ValueError("groupby requires metric unless aggregation=count")

        if self.operation == "timeseries":
            if not self.date_column:
                raise ValueError("timeseries requires date_column")
            if not self.frequency:
                self.frequency = "M"
            if self.aggregation != "count" and not self.metric:
                raise ValueError("timeseries requires metric unless aggregation=count")

        if self.operation == "correlation" and len(self.columns) < 2:
            raise ValueError("correlation requires at least two columns")

        return self


class AnalyticsResult(BaseModel):
    operation: Operation
    rows: int
    data: list[dict] = Field(default_factory=list)
    summary: dict[str, object] = Field(default_factory=dict)
