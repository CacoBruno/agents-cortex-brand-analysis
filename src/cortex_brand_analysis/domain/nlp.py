from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

NlpOperation = Literal[
    "sentiment",
    "protagonism",
    "entities",
    "clustering",
    "themes",
]


class NlpRequest(BaseModel):
    operation: NlpOperation
    data: list[dict] = Field(min_length=1)

    title_column: str = "titulo"
    content_column: str = "conteudo"
    date_column: str = "data_da_publicacao"

    brands: list[str] = Field(default_factory=list)
    entity_search: dict[str, list[str]] = Field(default_factory=dict)

    text_column: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    time_delta: int = Field(default=1, ge=1, le=30)

    macrothemes: dict[str, dict] = Field(default_factory=dict)
    theme_rules: dict[str, dict] = Field(default_factory=dict)
    theme_config: dict = Field(default_factory=dict)
    return_scores: bool = False

    @model_validator(mode="after")
    def validate_operation_inputs(self) -> NlpRequest:
        if self.operation == "protagonism" and not self.brands:
            raise ValueError("protagonism requires at least one brand")
        if self.operation == "entities" and not self.entity_search:
            raise ValueError("entities requires entity_search")
        if self.operation == "themes" and not self.macrothemes:
            raise ValueError("themes requires macrothemes")
        return self


class NlpResult(BaseModel):
    operation: NlpOperation
    rows: int
    columns: list[str]
    data: list[dict]
    metadata: dict[str, object] = Field(default_factory=dict)
