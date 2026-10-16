from typing import Any
from pydantic import BaseModel, Field


class WhatsAppInsightsInput(BaseModel):
    company_name: str = Field(..., description="Nome da empresa analisada.")
    analysis_period: str = Field(..., description="Período da análise. Ex: Março de 2026.")

    big_number: dict[str, Any] = Field(
        ...,
        description="Dicionário com os principais indicadores do período."
    )

    coverage_context_result: dict[str, Any] = Field(
        ...,
        description="Resultado estruturado do contexto de cobertura."
    )

    insights: dict[str, Any] = Field(
        ...,
        description="Dicionário com insights, oportunidades e riscos."
    )

    model: str = Field(default="gpt-4.1-mini")
    temperature: float = Field(default=0.2)

    top_n_vehicles: int = Field(default=5)
    top_n_topics: int = Field(default=4)