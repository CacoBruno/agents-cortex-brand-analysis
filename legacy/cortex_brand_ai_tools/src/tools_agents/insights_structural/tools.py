from __future__ import annotations

from typing import Any, Dict

from langchain_core.tools import tool

from .schemas import (
    ContextGenerationInput,
    GenerateMediaHighlightsInput,
    GenerateCoverageInsightsInput,
    ToolErrorOutput,
)

from .services import (
    generate_context,
    run_generate_coverage_insights_service,
)


@tool("generate_company_insights", args_schema=ContextGenerationInput)
def generate_company_context_tool(
    client_name: str,
    year: int | None = None,
    include_context: bool = True,
    include_objectives: bool = True,
    include_opportunities: bool = True,
    include_risks: bool = True,
    search_num_results: int = 20,
    max_iterations: int = 6,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.3,
) -> dict:
    """
    Gera insights estratégicos para uma empresa a partir de pesquisa web,
    cobrindo contexto, objetivos de comunicação, oportunidades e riscos.
    """
    try:
        payload = ContextGenerationInput(
            client_name=client_name,
            year=year,
            include_context=include_context,
            include_objectives=include_objectives,
            include_opportunities=include_opportunities,
            include_risks=include_risks,
            search_num_results=search_num_results,
            max_iterations=max_iterations,
            model_name=model_name,
            temperature=temperature,
        )

        result = generate_context(payload)
        return result.model_dump()

    except Exception as e:
        return ToolErrorOutput(
            message="Erro ao gerar insights.",
            error_type=type(e).__name__,
            details=str(e),
        ).model_dump()



@tool("generate_coverage_insights", args_schema=GenerateCoverageInsightsInput)
def generate_coverage_insights_tool(
    company_name: str,
    period_label: str,
    big_number: Dict[str, Any],
    highlight_infos: Dict[str, Any],
    coverage_context_result: Dict[str, Any],
    contexto_negocios: Dict[str, Any],
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Gera insights executivos de cobertura a partir de big numbers,
    highlights, contexto de cobertura e contexto de negócios.
    """
    try:
        return run_generate_coverage_insights_service(
            company_name=company_name,
            period_label=period_label,
            big_number=big_number,
            highlight_infos=highlight_infos,
            coverage_context_result=coverage_context_result,
            contexto_negocios=contexto_negocios,
            model=model,
            temperature=temperature,
            max_retries=max_retries,
        )

    except Exception as e:
        return ToolErrorOutput(
            message="Erro ao gerar insights executivos de cobertura.",
            error_type=type(e).__name__,
            details=str(e),
        ).model_dump()