from typing import Any
from langchain_openai import ChatOpenAI


def _safe_get(d: dict, path: list[str], default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _format_big_number_dict(big_number: dict) -> str:
    if not big_number:
        return "Big Numbers não informados."

    ordered_keys = [
        "NPS",
        "Protagonismo",
        "Impacto Total",
        "Impacto Promotor",
        "Impacto Inócuo",
        "Impacto Detrator",
        "Publicações Totais",
        "Publicações Promotoras",
        "Publicações Inócuas",
        "Publicações Detratoras",
    ]

    lines = []
    used = set()

    for k in ordered_keys:
        if k in big_number:
            lines.append(f"- {k}: {big_number[k]}")
            used.add(k)

    for k, v in big_number.items():
        if k not in used:
            lines.append(f"- {k}: {v}")

    return "\n".join(lines)


def _truncate_list(items: list, max_items: int = 5) -> list:
    if not isinstance(items, list):
        return []
    return items[:max_items]


def _format_items(items: list[dict], title: str) -> str:
    if not items:
        return f"{title}: sem dados."

    lines = [f"{title}:"]
    for i, item in enumerate(items, 1):
        if isinstance(item, dict):
            parts = [f"{k}={v}" for k, v in item.items()]
            lines.append(f"{i}. " + " | ".join(parts))
        else:
            lines.append(f"{i}. {str(item)}")

    return "\n".join(lines)


def _format_insights(insights: dict) -> str:
    if not insights:
        return "Insights não informados."

    return "\n".join([f"- {k}: {v}" for k, v in insights.items()])


def build_whatsapp_insights_prompt(
    company_name: str,
    analysis_period: str,
    big_number: dict,
    coverage_context_result: dict,
    insights: dict,
    top_n_vehicles: int = 5,
    top_n_topics: int = 4,
) -> dict[str, str]:

    assuntos_promotores = _safe_get(
        coverage_context_result,
        ["outputs", "topic_analysis", "analise_assuntos_promotores"],
        default=[],
    )

    assuntos_detratores = _safe_get(
        coverage_context_result,
        ["outputs", "topic_analysis", "analise_assuntos_detratores"],
        default=[],
    )

    analise_veiculos = _safe_get(
        coverage_context_result,
        ["outputs", "vehicle_analysis", "analise_por_veiculo"],
        default=[],
    )

    assuntos_promotores = _truncate_list(assuntos_promotores, top_n_topics)
    assuntos_detratores = _truncate_list(assuntos_detratores, top_n_topics)
    analise_veiculos = _truncate_list(analise_veiculos, top_n_vehicles)

    system_prompt = """
Você é um analista sênior de reputação e mídia especializado em comunicação executiva.

Sua tarefa é escrever uma mensagem para WhatsApp com leitura rápida, curta e analítica.

FORMATO OBRIGATÓRIO:
1. Título: "Direto ao ponto 📊 - {período}"
2. Abertura curta com Big Numbers e interpretação executiva.
3. Bloco de assuntos, separando sinais promotores e detratores.
4. Síntese do período começando com "👉".
5. Oportunidades começando com "🎯 Oportunidades:".
6. Sensibilidades começando com "📉 Sensibilidades:".
7. Cobertura da imprensa com top veículos relevantes.

REGRAS:
- Não invente dados.
- Não faça texto longo.
- Não repita os mesmos números várias vezes.
- Priorize análise, não descrição bruta.
- Use português do Brasil.
- Use emojis com moderação.
""".strip()

    user_prompt = f"""
EMPRESA
{company_name}

PERÍODO DA ANÁLISE
{analysis_period}

BIG NUMBERS
{_format_big_number_dict(big_number)}

INSIGHTS
{_format_insights(insights)}

ASSUNTOS PROMOTORES
{_format_items(assuntos_promotores, "Assuntos promotores")}

ASSUNTOS DETRATORES
{_format_items(assuntos_detratores, "Assuntos detratores")}

VEÍCULOS
{_format_items(analise_veiculos, "Cobertura da imprensa - top veículos")}

INSTRUÇÃO FINAL
Escreva agora a mensagem final de WhatsApp, pronta para envio.
""".strip()

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


def run_generate_whatsapp_insights_service(
    company_name: str,
    analysis_period: str,
    big_number: dict,
    coverage_context_result: dict,
    insights: dict,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    top_n_vehicles: int = 5,
    top_n_topics: int = 4,
) -> dict[str, Any]:

    prompts = build_whatsapp_insights_prompt(
        company_name=company_name,
        analysis_period=analysis_period,
        big_number=big_number,
        coverage_context_result=coverage_context_result,
        insights=insights,
        top_n_vehicles=top_n_vehicles,
        top_n_topics=top_n_topics,
    )

    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
    )

    response = llm.invoke([
        ("system", prompts["system_prompt"]),
        ("user", prompts["user_prompt"]),
    ])

    final_text = response.content if hasattr(response, "content") else str(response)

    return {
        "status": "success",
        "meta": {
            "company_name": company_name,
            "analysis_period": analysis_period,
            "model": model,
            "temperature": temperature,
            "top_n_vehicles": top_n_vehicles,
            "top_n_topics": top_n_topics,
        },
        "prompts": prompts,
        "output": {
            "final_text": final_text,
        },
    }