from __future__ import annotations

from pydantic import BaseModel, Field


class PriaRequest(BaseModel):
    message: str = Field(min_length=1)
    previous_response_id: str | None = None


class PriaResult(BaseModel):
    answer: str
    response_id: str
    tool_calls: list[str] = Field(default_factory=list)
