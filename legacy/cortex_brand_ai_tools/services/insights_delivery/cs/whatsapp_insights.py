from __future__ import annotations

from typing import Any, Dict, List, Optional
from langchain_openai import ChatOpenAI


# =========================================================
# Helpers
# =========================================================

def _safe_get(d: dict, path: list[str], default=None):
    """
    Acessa dicionários aninhados com segurança.
    """
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _format_big_number_dict(big_number: dict) -> str:
    """
    Converte o dict de big numbers em texto curto e legível para prompt.
    """
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


def _format_topic_items(topic_items: list[dict], titulo: str) -> str:
    """
    Formata lista de assuntos para prompt.
    """
    if not topic_items:
        return f"{titulo}: sem dados."

    lines = [f"{titulo}:"]
    for i, item in enumerate(topic_items, 1):
        if isinstance(item, dict):
            parts = []
            for k, v in item.items():
                parts.append(f"{k}={v}")
            lines.append(f"{i}. " + " | ".join(parts))
        else:
            lines.append(f"{i}. {str(item)}")
    return "\n".join(lines)


def _format_vehicle_items(vehicle_items: list[dict], titulo: str = "Top veículos") -> str:
    """
    Formata lista de veículos para prompt.
    """
    if not vehicle_items:
        return f"{titulo}: sem dados."

    lines = [f"{titulo}:"]
    for i, item in enumerate(vehicle_items, 1):
        if isinstance(item, dict):
            parts = []
            for k, v in item.items():
                parts.append(f"{k}={v}")
            lines.append(f"{i}. " + " | ".join(parts))
        else:
            lines.append(f"{i}. {str(item)}")
    return "\n".join(lines)


def _format_insights(insights: dict) -> str:
    """
    Formata o dict de insights para o prompt.
    Espera algo como:
    {
        "insights": "...",
        "oportunidades": "...",
        "riscos_observados": "..."
    }
    ou chaves equivalentes.
    """
    if not insights:
        return "Insights não informados."

    lines = []
    for k, v in insights.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)


# =========================================================
# Prompt builder
# =========================================================

def build_whatsapp_insights_prompt(
    company_name: str,
    analysis_period: str,
    big_number: dict,
    coverage_context_result: dict,
    insights: dict,
    top_n_vehicles: int = 5,
    top_n_topics: int = 4,
) -> dict[str, str]:
    """
    Monta os prompts de sistema e usuário para geração do texto de WhatsApp.
    """

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

    big_numbers_txt = _format_big_number_dict(big_number)
    insights_txt = _format_insights(insights)
    promotores_txt = _format_topic_items(assuntos_promotores, "Assuntos promotores")
    detratores_txt = _format_topic_items(assuntos_detratores, "Assuntos detratores")
    veiculos_txt = _format_vehicle_items(analise_veiculos, "Cobertura da imprensa - top veículos")

    system_prompt = """
Você é um analista sênior de reputação e mídia especializado em comunicação executiva.

Sua tarefa é escrever uma mensagem para WhatsApp com leitura rápida, curta e analítica.

OBJETIVO
Transformar dados estruturados de exposição da marca em uma mensagem executiva de WhatsApp.

ESTILO
- Tom executivo, claro, direto e analítico.
- Texto curto.
- Frases curtas.
- Linguagem natural de WhatsApp corporativo.
- Evitar blocos longos.
- Priorizar legibilidade imediata.

FORMATO OBRIGATÓRIO
1. Título:
   "Direto ao ponto 📊 - {período}"

2. Abertura:
   - 1 parágrafo curto com leitura dos Big Numbers
   - combinar números + interpretação executiva
   - dizer o que os dados mostram sobre a exposição da marca

3. Bloco de assuntos:
   - bullets curtos
   - separar sinais promotores e detratores
   - destacar apenas o que realmente moveu a percepção

4. Síntese do período:
   - começar com "👉"
   - 1 ou 2 frases no máximo
   - resumir o que definiu o período

5. Oportunidades:
   - começar com "🎯 Oportunidades:"
   - 1 ou 2 bullets curtos

6. Sensibilidades/Riscos:
   - começar com "📉 Sensibilidades:"
   - 1 ou 2 bullets curtos

7. Cobertura da imprensa:
   - usar um emoji adequado de imprensa/jornal
   - trazer top 5 veículos mais relevantes
   - não listar por listar; resumir o papel deles na cobertura

REGRAS OBRIGATÓRIAS
- Não invente dados.
- Não use jargão excessivo.
- Não faça texto longo.
- Não repetir os mesmos números várias vezes.
- Priorizar análise, não descrição bruta.
- Quando citar números, usar apenas os mais importantes.
- Em assuntos e veículos, resumir o significado da cobertura.
- O texto precisa caber confortavelmente em uma mensagem de WhatsApp executiva.
- Use emojis apenas nos títulos/blocos, sem exagero.
- O nome da empresa precisa aparecer naturalmente na abertura ou síntese.
"""

    user_prompt = f"""
EMPRESA
{company_name}

PERÍODO DA ANÁLISE
{analysis_period}

BIG NUMBERS
{big_numbers_txt}

INSIGHTS
{insights_txt}

ASSUNTOS
{promotores_txt}

{detratores_txt}

VEÍCULOS
{veiculos_txt}

INSTRUÇÃO FINAL
Escreva agora a mensagem final de WhatsApp, pronta para envio, em português do Brasil.
"""

    return {
        "system_prompt": system_prompt.strip(),
        "user_prompt": user_prompt.strip(),
    }


# =========================================================
# Main function
# =========================================================

def generate_whatsapp_insights_message(
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
    """
    Gera mensagem de WhatsApp executiva e resumida.

    Returns
    -------
    dict
        {
            "meta": {...},
            "prompts": {...},
            "output": {
                "final_text": str
            }
        }
    """

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
            "final_text": final_text
        }
    }