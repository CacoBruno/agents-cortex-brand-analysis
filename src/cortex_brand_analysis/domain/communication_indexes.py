from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

IndexOperation = Literal[
    "nps",
    "nps_contribution",
    "protagonism",
    "frequency",
    "valoration",
    "journalist",
    "action",
]


class CommunicationIndexRequest(BaseModel):
    data: list[dict] = Field(min_length=1)
    operation: IndexOperation
    group_by: list[str] = Field(default_factory=lambda: ["Data", "Empresa analisada"])
    value_column: str | None = None
    impact_column: str | None = None
    dimension_column: str | None = None
    value_columns: list[str] = Field(default_factory=list)
    filter_column: str | None = None
    filter_value: object | None = None
    contribution_type: Literal["Total", "Promotor"] = "Total"

    @model_validator(mode="after")
    def validate_request(self) -> CommunicationIndexRequest:
        if not self.group_by:
            raise ValueError("group_by must contain at least one column")
        if self.operation == "nps_contribution" and not self.dimension_column:
            raise ValueError("nps_contribution requires dimension_column")
        return self


class CommunicationIndexResult(BaseModel):
    operation: IndexOperation
    rows: int
    columns: list[str]
    data: list[dict]
