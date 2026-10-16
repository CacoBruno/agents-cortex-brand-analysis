from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple


from langchain_openai import ChatOpenAI
from langchain_community.utilities import SerpAPIWrapper



from src.tools_agents.insights_structural.schemas import (
    ContextGenerationInput,
    ContextGenerationOutput,
    ContextBlock
)

from src.tools_agents.insights_structural.prompts import (
    build_context_prompt,
    build_objectives_prompt,
    build_opportunities_prompt,
    build_risk_prompt,
    build_media_highlights_prompt,
)

from services.insights_delivery.gens_fuctions.insights_gen import (
    generate_coverage_insights_llm,
)


# ============================================================
# CONTEXTO ESTRATÉGICO COM GOOGLE SEARCH + LLM
# ============================================================

def _google_search_br(query: str, num_results: int = 5) -> str:
    """
    Executa busca no Google Brasil via SerpAPI.
    Retorna texto consolidado para enriquecer o prompt do LLM.
    """

    try:
        search = SerpAPIWrapper(
            params={
                "gl": "br",
                "hl": "pt",
                "num": num_results,
                "google_domain": "google.com.br",
            }
        )

        result = search.run(query)

        if not result:
            return ""

        return str(result)

    except Exception as e:
        return f"Erro na busca Google para query '{query}': {type(e).__name__}: {e}"


def _build_research_queries(client_name: str, year: int) -> Dict[str, str]:
    """
    Monta buscas estratégicas para contexto de comunicação e reputação.
    """

    return {
        "contexto_geral": (
            f"{client_name} empresa Brasil contexto institucional notícias {year}"
        ),
        "negocios_mercado": (
            f"{client_name} resultados negócio mercado estratégia Brasil {year}"
        ),
        "comunicacao_reputacao": (
            f"{client_name} reputação comunicação imprensa stakeholders Brasil {year}"
        ),
        "oportunidades": (
            f"{client_name} oportunidades mercado expansão inovação estratégia Brasil {year}"
        ),
        "riscos": (
            f"{client_name} riscos crise reputação reclamações imprensa Brasil {year}"
        ),
    }


def _build_research_context(
    client_name: str,
    year: int,
    num_results: int = 5,
) -> Dict[str, str]:
    """
    Executa múltiplas buscas para enriquecer o contexto estratégico.
    """

    queries = _build_research_queries(client_name=client_name, year=year)

    results: Dict[str, str] = {}

    for key, query in queries.items():
        results[key] = _google_search_br(
            query=query,
            num_results=num_results,
        )

    return results


def _format_research_context(research: Dict[str, str]) -> str:
    """
    Transforma resultados da busca em texto organizado para o LLM.
    """

    blocks = []

    for key, value in research.items():
        blocks.append(
            f"""
### {key}

{value or "Nenhum resultado relevante retornado."}
""".strip()
        )

    return "\n\n".join(blocks)


def _run_prompt_llm(
    llm: ChatOpenAI,
    prompt: str,
    title: str,
    research_context: str | None = None,
) -> ContextBlock:
    """
    Executa prompt diretamente no LLM, sem initialize_agent.
    """

    try:
        full_prompt = f"""
Você é um analista sênior de comunicação, reputação, imprensa e negócios.

Use o contexto de pesquisa abaixo como insumo.
Não invente fatos.
Quando fizer inferências, sinalize claramente como inferência.
Quando houver incerteza, sinalize a incerteza.

CONTEXTO DE PESQUISA:
{research_context or "Não fornecido."}

TAREFA:
{prompt}

REGRAS DE RESPOSTA:
- Responda em português do Brasil.
- Seja executivo, analítico e objetivo.
- Separe fatos, inferências e implicações quando fizer sentido.
- Priorize impactos para reputação, imprensa, stakeholders, comunicação e negócio.
- Não cite links fictícios.
- Não invente números.
""".strip()

        response = llm.invoke(full_prompt)
        content = getattr(response, "content", None)

        if not content:
            return ContextBlock(
                title=title,
                content=None,
                status="empty",
                error="Nenhum conteúdo foi retornado pelo LLM.",
            )

        return ContextBlock(
            title=title,
            content=str(content),
            status="success",
        )

    except Exception as e:
        return ContextBlock(
            title=title,
            content=None,
            status="error",
            error=f"{type(e).__name__}: {e}",
        )


def generate_context(payload: ContextGenerationInput) -> ContextGenerationOutput:
    """
    Gera contexto estratégico enriquecido com Google Search,
    sem usar initialize_agent.
    """

    year = payload.year or datetime.now().year

    llm = ChatOpenAI(
        model=payload.model_name,
        temperature=payload.temperature,
        max_tokens=1600,
        timeout=90,
    )

    research = _build_research_context(
        client_name=payload.client_name,
        year=year,
        num_results=payload.search_num_results,
    )

    research_context = _format_research_context(research)

    result = ContextGenerationOutput(
        client_name=payload.client_name,
        year=year,
        meta={
            "model_name": payload.model_name,
            "temperature": payload.temperature,
            "search_num_results": payload.search_num_results,
            "search_enabled": True,
            "search_queries": _build_research_queries(payload.client_name, year),
            "search_results": research,
        },
    )

    if payload.include_context:
        result.contexto = _run_prompt_llm(
            llm=llm,
            prompt=build_context_prompt(payload.client_name, year),
            title="contexto",
            research_context=research_context,
        )

    if payload.include_objectives:
        result.objetivos_comunicacao = _run_prompt_llm(
            llm=llm,
            prompt=build_objectives_prompt(payload.client_name, year),
            title="objetivos_comunicacao",
            research_context=research_context,
        )

    if payload.include_opportunities:
        result.oportunidade = _run_prompt_llm(
            llm=llm,
            prompt=build_opportunities_prompt(payload.client_name, year),
            title="oportunidade",
            research_context=research_context,
        )

    if payload.include_risks:
        result.risco = _run_prompt_llm(
            llm=llm,
            prompt=build_risk_prompt(payload.client_name, year),
            title="risco",
            research_context=research_context,
        )

    return result


# ============================================================
# INSIGHTS EXECUTIVOS DE COBERTURA
# ============================================================

def run_generate_coverage_insights_service(
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
    Serviço para gerar insights executivos de cobertura.

    Retorna:
    {
        "status": "success" | "error",
        "data": dict | None,
        "message": str,
        "error_type": str | None,
        "details": str | None
    }
    """

    try:
        result = generate_coverage_insights_llm(
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

        return {
            "status": "success",
            "message": "Insights executivos gerados com sucesso.",
            "data": result,
            "error_type": None,
            "details": None,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Erro ao gerar insights executivos de cobertura.",
            "data": None,
            "error_type": type(e).__name__,
            "details": str(e),
        }