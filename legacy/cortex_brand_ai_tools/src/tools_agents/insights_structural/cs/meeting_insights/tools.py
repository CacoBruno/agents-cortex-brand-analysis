from __future__ import annotations

from typing import Any, Dict

from langchain_core.tools import tool

from src.tools_agents.insights_structural.cs.meeting_insights.schemas import (
    MeetingScriptToolInput,
    SaveMeetingScriptToolInput,
    ToolErrorOutput,
)
from src.tools_agents.insights_structural.cs.meeting_insights.services import (
    generate_meeting_script_with_llm,
    save_meeting_script_files,
)


@tool(
    "generate_meeting_script",
    args_schema=MeetingScriptToolInput,
)
def generate_meeting_script_tool(
    company_name: str,
    analysis_period: str,
    big_number: Dict[str, Any] | None = None,
    highlight_infos: Dict[str, Any] | None = None,
    coverage_context_result: Dict[str, Any] | None = None,
    insights: Dict[str, Any] | None = None,
    contexto_negocios: Dict[str, Any] | None = None,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
Gera um script executivo de reunião a partir dos insights estratégicos
da cobertura de mídia da empresa.

Esta tool transforma indicadores quantitativos, highlights executivos,
contexto narrativo da cobertura, insights consolidados e contexto de
negócios em um roteiro estruturado para reuniões executivas com clientes.

O objetivo é converter os outputs analíticos do pipeline de mídia em
uma narrativa clara, acionável e pronta para apresentação oral.

O script gerado inclui:
    - tom sugerido da reunião;
    - mensagem central para o cliente;
    - leitura estratégica dos big numbers;
    - interpretação dos highlights;
    - análise do contexto da cobertura;
    - síntese dos aprendizados;
    - oportunidades observadas;
    - riscos reputacionais;
    - recomendações de atuação;
    - conexão com o contexto de negócios;
    - fechamento executivo;
    - pontos narrativos de apoio.

Os conteúdos são gerados utilizando:
    - métricas reputacionais;
    - indicadores de exposição;
    - NPS;
    - protagonismo;
    - highlights executivos;
    - contexto narrativo da imprensa;
    - contexto estratégico do negócio.

Args:
    company_name:
        Nome da empresa analisada.

    analysis_period:
        Label textual do período analisado.
        Exemplo: "Março de 2026".

    big_number:
        Dicionário contendo os principais indicadores quantitativos
        do período analisado.

    highlight_infos:
        Resultado consolidado do pipeline de highlights executivos.

    coverage_context_result:
        Resultado do pipeline de contexto narrativo da cobertura,
        incluindo sínteses de temas, veículos e vetores reputacionais.

    insights:
        Insights estratégicos consolidados gerados no pipeline.

    contexto_negocios:
        Contexto estratégico da empresa, incluindo oportunidades,
        riscos, objetivos e contexto setorial.

    model:
        Modelo LLM utilizado na geração do script.
        Default: "gpt-4.1-mini".

    temperature:
        Temperatura utilizada no modelo generativo.
        Default: 0.2.

    max_retries:
        Número máximo de tentativas para execução do pipeline.
        Default: 3.

Returns:
    Dict[str, Any]:
        Estrutura contendo:

            success:
                Status booleano da execução.

            result:
                Resultado completo do script gerado, incluindo:
                    - prompt utilizado;
                    - metadados;
                    - saída estruturada do LLM;
                    - texto bruto retornado;
                    - script executivo final.

            error:
                Mensagem de erro, se houver falha na execução.
"""
    try:
        result = generate_meeting_script_with_llm(
            company_name=company_name,
            analysis_period=analysis_period,
            big_number=big_number or {},
            highlight_infos=highlight_infos or {},
            coverage_context_result=coverage_context_result or {},
            insights=insights or {},
            contexto_negocios=contexto_negocios or {},
            model=model,
            temperature=temperature,
        )

        return {
            "success": True,
            "result": result,
        }

    except Exception as e:
        return ToolErrorOutput(
            message="Erro ao gerar script executivo de reunião.",
            error_type=type(e).__name__,
            details=str(e),
        ).model_dump()