from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ModelRole = Literal["conversation", "planning", "interpretation", "evaluation"]
ReasoningEffort = Literal["low", "medium", "high", "xhigh"]


class ModelSpec(BaseModel):
    model: str = Field(min_length=1)
    reasoning_effort: ReasoningEffort | None = None


class ModelPolicy(BaseModel):
    """Routing configuration; model availability must be validated at runtime."""

    conversation: ModelSpec
    planning: ModelSpec
    interpretation: ModelSpec
    evaluation: ModelSpec

    def for_role(self, role: ModelRole) -> ModelSpec:
        return getattr(self, role)

    @classmethod
    def from_settings(cls, settings: object) -> ModelPolicy:
        base = str(getattr(settings, "openai_conversation_model"))
        analytical = str(getattr(settings, "openai_analytical_model"))
        return cls(
            conversation=ModelSpec(model=base),
            planning=ModelSpec(model=analytical, reasoning_effort="high"),
            interpretation=ModelSpec(model=analytical, reasoning_effort="high"),
            evaluation=ModelSpec(model=analytical, reasoning_effort="high"),
        )
