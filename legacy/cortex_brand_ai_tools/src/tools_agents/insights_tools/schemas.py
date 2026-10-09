from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CoverageOrchestratorInput(BaseModel):
    url_platform: str = Field(...)

    end_date: str = Field(..., description="Data final da análise. Ex: 2026-03-31")
    analysis_start_date: str = Field(..., description="Início do período que o usuário quer analisar.")

    client: str = Field(..., description="Nome normalizado da empresa na base. Ex: americanas sa")
    client_display_name: str = Field(..., description="Nome amigável da empresa. Ex: Americanas")

    produto_analisado: List[str] = Field(default_factory=list)

    period: str = Field(default="mes", description="dia, semana, mes ou ano")
    period_label: Optional[str] = Field(default=None, description="Ex: Março de 2026")

    anchor_weekday: str = Field(
        default="segunda-feira",
        description="Dia da semana usado para calcular data_ancora_semana a partir do end_date."
    )

    list_search: Optional[List[str]] = Field(
        default=None,
        description="Termos usados no contexto da exposição. Se None, usa [client, client_display_name]."
    )

    status_classificacao: List[str] = Field(default_factory=lambda: ["Classificado"])
    tipos_de_impactos: List[str] = Field(default_factory=lambda: ["Promotores", "Detratores", "Inócuos"])
    representa_empresa: str = "Sim"
    tier: List[str] = Field(default_factory=lambda: ["Tier 1", "Tier 2"])

    model: str = "gpt-4.1-mini"
    temperature: float = 0.2
    max_retries: int = 3


class CoverageOrchestratorOutput(BaseModel):
    status: str
    output_type: str
    final_answer: Any = None
    files: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    debug: Optional[Dict[str, Any]] = None