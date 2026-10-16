from langchain_core.tools import tool

from src.tools_agents.insights_structural.cs.whatsapp_insights.schemas import WhatsAppInsightsInput
from src.tools_agents.insights_structural.cs.whatsapp_insights.services import (
    run_generate_whatsapp_insights_service,
)


@tool(args_schema=WhatsAppInsightsInput)
def generate_whatsapp_insights_message_tool(
    company_name: str,
    analysis_period: str,
    big_number: dict,
    coverage_context_result: dict,
    insights: dict,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    top_n_vehicles: int = 10,
    top_n_topics: int = 6,
):
    """
    Gera uma mensagem executiva de WhatsApp a partir dos big numbers,
    contexto de cobertura, assuntos, veículos e insights estratégicos.
    """

    try:
        return run_generate_whatsapp_insights_service(
            company_name=company_name,
            analysis_period=analysis_period,
            big_number=big_number,
            coverage_context_result=coverage_context_result,
            insights=insights,
            model=model,
            temperature=temperature,
            top_n_vehicles=top_n_vehicles,
            top_n_topics=top_n_topics,
        )

    except Exception as e:
        return {
            "status": "error",
            "message": "Erro ao gerar mensagem executiva de WhatsApp.",
            "error_type": type(e).__name__,
            "details": str(e),
        }