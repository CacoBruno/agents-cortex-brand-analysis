from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ContextGenerationInput(BaseModel):
    client_name: str = Field(..., description="Nome da empresa ou cliente analisado.")
    year: Optional[int] = Field(
        default=None,
        description="Ano de referência da análise. Se None, usa o ano atual."
    )
    include_context: bool = Field(default=True, description="Gerar bloco de contexto de negócio.")
    include_objectives: bool = Field(default=True, description="Gerar bloco de objetivos de comunicação.")
    include_opportunities: bool = Field(default=True, description="Gerar bloco de oportunidades.")
    include_risks: bool = Field(default=True, description="Gerar bloco de riscos.")
    search_num_results: int = Field(default=20, ge=5, le=100, description="Quantidade de resultados da busca.")
    max_iterations: int = Field(default=6, ge=1, le=15, description="Máximo de iterações do agente/pipeline.")
    model_name: str = Field(default="gpt-4o-mini", description="Modelo a ser usado.")
    temperature: float = Field(default=0.3, ge=0.0, le=1.5)

    model_config = ConfigDict(extra="forbid")


class ContextBlock(BaseModel):
    title: str = Field(..., description="Nome do bloco.")
    content: Optional[str] = Field(default=None, description="Texto gerado para o bloco.")
    status: str = Field(default="success", description="success | empty | error")
    error: Optional[str] = Field(default=None, description="Erro, se houver.")


class ContextGenerationOutput(BaseModel):
    client_name: str
    year: int
    contexto: Optional[ContextBlock] = None
    objetivos_comunicacao: Optional[ContextBlock] = None
    oportunidade: Optional[ContextBlock] = None
    risco: Optional[ContextBlock] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ToolErrorOutput(BaseModel):
    status: str = Field(default="error")
    message: str
    error_type: Optional[str] = None
    details: Optional[str] = None


class GenerateMediaHighlightsInput(BaseModel):
    dataframe_ids: List[str] = Field(
        ...,
        description="Lista de IDs dos dataframes salvos no DATAFRAME_STORE."
    )
    max_entities: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Número máximo de entidades analíticas a destacar."
    )
    max_highlights_per_entity: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Número de highlights por entidade."
    )
    model_name: str = Field(
        default="gpt-4o-mini",
        description="Modelo usado no agent."
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.5,
        description="Temperatura do modelo."
    )
    allow_dangerous_code: bool = Field(
        default=True,
        description="Permite execução de código Python no pandas agent."
    )
    allow_dangerous_requests: bool = Field(
        default=False,
        description="Permite requests externos."
    )

    model_config = ConfigDict(extra="forbid")


class HighlightBlock(BaseModel):
    entity_name: str = Field(..., description="Nome da entidade destacada.")
    entity_type: Optional[str] = Field(
        default=None,
        description="Tipo da entidade identificado automaticamente, ex: produto, marca, tema, veículo."
    )
    highlights: List[str] = Field(default_factory=list)
    status: str = Field(default="success")
    error: Optional[str] = Field(default=None)


class GenerateMediaHighlightsOutput(BaseModel):
    status: str = Field(default="success")
    detected_entity_dimension: Optional[str] = Field(
        default=None,
        description="Dimensão principal detectada automaticamente."
    )
    detected_relevant_columns: List[str] = Field(default_factory=list)
    blocks: List[HighlightBlock] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


from typing import Any, Dict
from pydantic import BaseModel, Field


class GenerateCoverageInsightsInput(BaseModel):
    company_name: str = Field(..., description="Nome da empresa analisada.")
    period_label: str = Field(..., description="Rótulo do período analisado. Ex: Março de 2026.")

    big_number: Dict[str, Any] = Field(
        ...,
        description="Dicionário com os principais números do período."
    )

    highlight_infos: Dict[str, Any] = Field(
        ...,
        description="Resultado do pipeline de highlights multistage."
    )

    coverage_context_result: Dict[str, Any] = Field(
        ...,
        description="Resultado do build_coverage_summary ou pipeline equivalente."
    )

    contexto_negocios: Dict[str, Any] = Field(
        ...,
        description="Contexto de negócios da empresa."
    )

    model: str = Field(default="gpt-4.1-mini")
    temperature: float = Field(default=0.2)
    max_retries: int = Field(default=3)
