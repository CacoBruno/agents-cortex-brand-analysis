from src.tools_agents.highlights.schemas import GenerateHighlightsInput
from services.coverage_pattern.coverage_highlights import generate_highlights_multistage


def run_generate_highlights_service(
    params: GenerateHighlightsInput,
) -> dict:
    """
    Executa o serviço de geração de highlights multistage.

    Args:
        params: Schema validado com todos os insumos necessários.

    Returns:
        dict: Resultado completo retornado pela função
        generate_highlights_multistage.
    """

    result = generate_highlights_multistage(
        stats_llm=params.stats_llm,
        sources_llm=params.sources_llm,
        daily_llm=params.daily_llm,
        assunto_llm=params.assunto_llm,
        company_display_names=params.company_display_names,
        companies_to_run=params.companies_to_run,
        competitors_by_company=params.competitors_by_company,
        selected_sources_by_company=params.selected_sources_by_company,
        model_scope=params.model_scope,
        model_final=params.model_final,
        temperature_scope=params.temperature_scope,
        temperature_final=params.temperature_final,
    )

    return result