from langchain_core.tools import tool

from src.tools_agents.highlights.schemas import GenerateHighlightsInput
from src.tools_agents.highlights.services import run_generate_highlights_service


@tool(args_schema=GenerateHighlightsInput)
def generate_highlights_tool(
    stats_llm: dict,
    sources_llm: dict,
    daily_llm: dict,
    assunto_llm: dict,
    company_display_names: dict,
    companies_to_run: list,
    competitors_by_company: dict | None = None,
    selected_sources_by_company: dict | None = None,
    model_scope: str = "gpt-4o-mini",
    model_final: str = "gpt-4o-mini",
    temperature_scope: float = 0.3,
    temperature_final: float = 0.35,
):
    """
    Gera highlights executivos e síntese final de cobertura
    a partir das camadas de stats, veículos, dias e assuntos.

    Args:
        stats_llm: Dicionário com a camada de estatísticas.
        sources_llm: Dicionário com a camada de veículos/fontes.
        daily_llm: Dicionário com a camada diária.
        assunto_llm: Dicionário com a camada de assuntos.
        company_display_names: Mapeamento entre nome técnico e nome de exibição.
        companies_to_run: Lista de empresas a serem processadas.
        competitors_by_company: Mapa opcional de concorrentes por empresa.
        selected_sources_by_company: Mapa opcional de fontes selecionadas por empresa.
        model_scope: Modelo usado na etapa intermediária.
        model_final: Modelo usado na etapa final.
        temperature_scope: Temperatura da etapa intermediária.
        temperature_final: Temperatura da etapa final.

    Returns:
        dict: Resultado da geração de highlights.
    """

    params = GenerateHighlightsInput(
        stats_llm=stats_llm,
        sources_llm=sources_llm,
        daily_llm=daily_llm,
        assunto_llm=assunto_llm,
        company_display_names=company_display_names,
        companies_to_run=companies_to_run,
        competitors_by_company=competitors_by_company,
        selected_sources_by_company=selected_sources_by_company,
        model_scope=model_scope,
        model_final=model_final,
        temperature_scope=temperature_scope,
        temperature_final=temperature_final,
    )

    return run_generate_highlights_service(params)