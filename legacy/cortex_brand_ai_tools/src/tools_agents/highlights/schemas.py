from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class GenerateHighlightsInput(BaseModel):
    """
    Schema de entrada para geração de highlights executivos
    a partir das camadas de estatísticas, veículos, dias e assuntos.
    """

    stats_llm: Dict[str, Any] = Field(
        ...,
        description="Dicionário com a camada de estatísticas já preparada para o LLM."
    )
    sources_llm: Dict[str, Any] = Field(
        ...,
        description="Dicionário com a camada de veículos/fontes já preparada para o LLM."
    )
    daily_llm: Dict[str, Any] = Field(
        ...,
        description="Dicionário com a camada diária já preparada para o LLM."
    )
    assunto_llm: Dict[str, Any] = Field(
        ...,
        description="Dicionário com a camada de assuntos já preparada para o LLM."
    )

    company_display_names: Dict[str, str] = Field(
        ...,
        description="Mapeamento entre o nome técnico da empresa e o nome de exibição."
    )
    companies_to_run: List[str] = Field(
        ...,
        description="Lista de empresas que devem ser processadas."
    )

    competitors_by_company: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Mapa opcional de concorrentes por empresa."
    )
    selected_sources_by_company: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Mapa opcional com os veículos/fontes selecionados por empresa."
    )

    model_scope: str = Field(
        default="gpt-4o-mini",
        description="Modelo usado para a etapa intermediária/escopo."
    )
    model_final: str = Field(
        default="gpt-4o-mini",
        description="Modelo usado para a síntese final."
    )

    temperature_scope: float = Field(
        default=0.3,
        description="Temperatura usada na etapa intermediária."
    )
    temperature_final: float = Field(
        default=0.35,
        description="Temperatura usada na etapa final."
    )