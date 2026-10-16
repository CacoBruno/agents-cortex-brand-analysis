# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


# =========================================================
# Helpers
# =========================================================

DEFAULT_MAX_CHARS_POR_CAMPO = {
    "slide_1.titulo": 90,
    "slide_1.insight_1": 240,
    "slide_1.insight_2": 240,
    "slide_2.titulo": 90,
    "slide_2.texto": 1100,
    "slide_3.titulo": 90,
    "slide_3.insight_1": 240,
    "slide_3.insight_2": 240,
    "slide_4.titulo": 90,
    "slide_4.texto": 900,
    "slide_5.titulo": 90,
    "slide_5.recomendacoes_de_atuacao.item": 180,
    "slide_5.oportunidades_observadas.item": 180,
    "slide_5.riscos_observados.item": 180,
}


def _safe_get(d: dict, path: list[str], default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _clean_text(text: Any) -> str:
    if text is None:
        return ""
    text = str(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _truncate_text(text: str, max_chars: int = 2000) -> str:
    text = _clean_text(text)
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars].rstrip()

    # tenta cortar em final de frase
    for sep in [". ", "; ", ": ", ", "]:
        idx = truncated.rfind(sep)
        if idx > int(max_chars * 0.6):
            truncated = truncated[: idx + len(sep)].rstrip()
            break

    if len(truncated) > max_chars - 3:
        truncated = truncated[: max_chars - 3].rstrip()

    return truncated + "..."


def _serialize_for_prompt(obj: Any, max_chars: int = 5000) -> str:
    try:
        txt = json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        txt = str(obj)
    return _truncate_text(txt, max_chars=max_chars)


def _json_loads_safe(text: str) -> dict:
    text = text.strip()

    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError("Resposta da LLM não está em JSON válido.")


def _ensure_keys(d: dict, keys: list[str], where: str = ""):
    missing = [k for k in keys if k not in d]
    if missing:
        raise ValueError(f"Faltam chaves em {where}: {missing}")


def _merge_max_chars(custom: Optional[dict]) -> dict:
    merged = DEFAULT_MAX_CHARS_POR_CAMPO.copy()
    if custom:
        merged.update(custom)
    return merged


# =========================================================
# LLM
# =========================================================

def call_chatopenai_json(
    prompt: str,
    *,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    system_message: Optional[str] = None,
) -> dict:
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
    )

    sys_msg = system_message or (
        "Você é um analista sênior de reputação e mídia. "
        "Você escreve com clareza executiva para apresentações em PowerPoint. "
        "Responda somente em JSON válido."
    )

    response = llm.invoke(
        [
            SystemMessage(content=sys_msg),
            HumanMessage(content=prompt),
        ]
    )

    content = response.content
    if isinstance(content, list):
        content = " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )

    return _json_loads_safe(str(content))


def _call_with_retry_json(
    prompt: str,
    *,
    llm_callable: Callable[[str], dict],
    max_retries: int = 3,
    retry_sleep: float = 0.8,
) -> dict:
    last_error = None

    for attempt in range(max_retries):
        try:
            result = llm_callable(prompt)
            if not isinstance(result, dict):
                raise ValueError("A LLM não retornou dict.")
            return result
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_sleep)

    raise ValueError(f"Falha após {max_retries} tentativas. Erro: {last_error}")


# =========================================================
# Validation
# =========================================================

def validate_slide_brief_output(output: dict) -> dict:
    _ensure_keys(output, ["meta", "slides"], "output_brief")
    slides = output["slides"]
    _ensure_keys(
        slides,
        ["slide_1", "slide_2", "slide_3", "slide_4", "slide_5"],
        "output_brief.slides",
    )

    for slide_name, slide_obj in slides.items():
        _ensure_keys(
            slide_obj,
            ["mensagem_central", "evidencias", "direcao_textual"],
            f"output_brief.slides.{slide_name}",
        )
        if not isinstance(slide_obj["evidencias"], list):
            raise ValueError(f"{slide_name}.evidencias deve ser lista.")

    return output


def validate_ppt_text_output(output: dict) -> dict:
    _ensure_keys(output, ["meta", "slides"], "output_final")
    slides = output["slides"]

    _ensure_keys(
        slides,
        ["slide_1", "slide_2", "slide_3", "slide_4", "slide_5"],
        "output_final.slides",
    )

    _ensure_keys(slides["slide_1"], ["titulo", "insight_1", "insight_2"], "slide_1")
    _ensure_keys(slides["slide_2"], ["titulo", "texto"], "slide_2")
    _ensure_keys(slides["slide_3"], ["titulo", "insight_1", "insight_2"], "slide_3")
    _ensure_keys(slides["slide_4"], ["titulo", "texto"], "slide_4")
    _ensure_keys(
        slides["slide_5"],
        ["titulo", "recomendacoes_de_atuacao", "oportunidades_observadas", "riscos_observados"],
        "slide_5",
    )

    for field in ["recomendacoes_de_atuacao", "oportunidades_observadas", "riscos_observados"]:
        if not isinstance(slides["slide_5"][field], list):
            raise ValueError(f"slide_5.{field} deve ser lista.")

    return output


# =========================================================
# Post-process de tamanho
# =========================================================

def _apply_max_chars_to_output(output: dict, max_chars: dict) -> dict:
    slides = output.get("slides", {})

    # Slide 1
    if "slide_1" in slides:
        slides["slide_1"]["titulo"] = _truncate_text(
            slides["slide_1"].get("titulo", ""),
            max_chars["slide_1.titulo"],
        )
        slides["slide_1"]["insight_1"] = _truncate_text(
            slides["slide_1"].get("insight_1", ""),
            max_chars["slide_1.insight_1"],
        )
        slides["slide_1"]["insight_2"] = _truncate_text(
            slides["slide_1"].get("insight_2", ""),
            max_chars["slide_1.insight_2"],
        )

    # Slide 2
    if "slide_2" in slides:
        slides["slide_2"]["titulo"] = _truncate_text(
            slides["slide_2"].get("titulo", ""),
            max_chars["slide_2.titulo"],
        )
        slides["slide_2"]["texto"] = _truncate_text(
            slides["slide_2"].get("texto", ""),
            max_chars["slide_2.texto"],
        )

    # Slide 3
    if "slide_3" in slides:
        slides["slide_3"]["titulo"] = _truncate_text(
            slides["slide_3"].get("titulo", ""),
            max_chars["slide_3.titulo"],
        )
        slides["slide_3"]["insight_1"] = _truncate_text(
            slides["slide_3"].get("insight_1", ""),
            max_chars["slide_3.insight_1"],
        )
        slides["slide_3"]["insight_2"] = _truncate_text(
            slides["slide_3"].get("insight_2", ""),
            max_chars["slide_3.insight_2"],
        )

    # Slide 4
    if "slide_4" in slides:
        slides["slide_4"]["titulo"] = _truncate_text(
            slides["slide_4"].get("titulo", ""),
            max_chars["slide_4.titulo"],
        )
        slides["slide_4"]["texto"] = _truncate_text(
            slides["slide_4"].get("texto", ""),
            max_chars["slide_4.texto"],
        )

    # Slide 5
    if "slide_5" in slides:
        slides["slide_5"]["titulo"] = _truncate_text(
            slides["slide_5"].get("titulo", ""),
            max_chars["slide_5.titulo"],
        )

        for field in [
            "recomendacoes_de_atuacao",
            "oportunidades_observadas",
            "riscos_observados",
        ]:
            items = slides["slide_5"].get(field, [])
            if not isinstance(items, list):
                items = [str(items)]

            slides["slide_5"][field] = [
                _truncate_text(item, max_chars[f"slide_5.{field}.item"])
                for item in items
            ]

    output["slides"] = slides
    return output


# =========================================================
# Contexto
# =========================================================

def _prepare_ppt_inputs(
    *,
    nome_empresa: str,
    periodo_analise: str,
    big_number: dict,
    highlight_infos: dict,
    coverage_context_result: dict,
    insights: dict,
    contexto_negocios: dict | str | None,
) -> dict:
    stats_text = _safe_get(highlight_infos, ["stats_layer", "final_text"], "")
    daily_text = _safe_get(highlight_infos, ["daily_layer", "final_text"], "")
    topics_text = _safe_get(highlight_infos, ["topics_layer", "final_text"], "")
    sources_text = _safe_get(highlight_infos, ["sources_layer", "final_text"], "")

    day_analysis = _safe_get(coverage_context_result, ["outputs", "day_analysis"], {})
    vehicle_analysis = _safe_get(coverage_context_result, ["outputs", "vehicle_analysis"], {})
    topic_analysis = _safe_get(coverage_context_result, ["outputs", "topic_analysis"], {})
    final_synthesis = _safe_get(coverage_context_result, ["outputs", "final_synthesis"], {})

    return {
        "empresa": nome_empresa,
        "periodo_analise": periodo_analise,
        "big_number": big_number,
        "highlight_infos": {
            "stats_layer_final_text": stats_text,
            "daily_layer_final_text": daily_text,
            "topics_layer_final_text": topics_text,
            "sources_layer_final_text": sources_text,
        },
        "coverage_context_result": {
            "day_analysis": {
                "resumo_geral": _safe_get(day_analysis, ["resumo_geral"], ""),
                "analise_por_dia": _safe_get(day_analysis, ["analise_por_dia"], []) or [],
            },
            "topic_analysis": {
                "resumo_geral": _safe_get(topic_analysis, ["resumo_geral"], ""),
                "analise_assuntos_promotores": _safe_get(topic_analysis, ["analise_assuntos_promotores"], []) or [],
                "analise_assuntos_detratores": _safe_get(topic_analysis, ["analise_assuntos_detratores"], []) or [],
            },
            "vehicle_analysis": {
                "resumo_geral": _safe_get(vehicle_analysis, ["resumo_geral"], ""),
                "analise_por_veiculo": _safe_get(vehicle_analysis, ["analise_por_veiculo"], []) or [],
                "top_5_veiculos": (_safe_get(vehicle_analysis, ["analise_por_veiculo"], []) or [])[:5],
            },
            "final_synthesis": final_synthesis,
        },
        "insights": insights,
        "contexto_negocios": contexto_negocios,
    }


# =========================================================
# Prompts
# =========================================================

def build_slide_brief_prompt(context: dict) -> str:
    return f"""
Você vai estruturar o raciocínio editorial de uma apresentação em PowerPoint sobre exposição de marca na mídia.

OBJETIVO
Antes de escrever o texto final dos slides, organize a lógica de cada slide:
- mensagem central;
- evidências que sustentam essa mensagem;
- direção textual;
- foco interpretativo.

EMPRESA
{context['empresa']}

PERÍODO
{context['periodo_analise']}

REGRAS
1. Responda somente em JSON válido.
2. Não escreva texto final de slide ainda.
3. Evite repetição entre slides.
4. Não invente dados.
5. Seja executivo, analítico e orientado a negócio.

FORMATO DE SAÍDA
{{
  "meta": {{
    "empresa": "{context['empresa']}",
    "periodo_analise": "{context['periodo_analise']}"
  }},
  "slides": {{
    "slide_1": {{
      "mensagem_central": "string",
      "evidencias": ["string", "string", "string"],
      "direcao_textual": "string"
    }},
    "slide_2": {{
      "mensagem_central": "string",
      "evidencias": ["string", "string", "string"],
      "direcao_textual": "string"
    }},
    "slide_3": {{
      "mensagem_central": "string",
      "evidencias": ["string", "string", "string"],
      "direcao_textual": "string"
    }},
    "slide_4": {{
      "mensagem_central": "string",
      "evidencias": ["string", "string", "string"],
      "direcao_textual": "string"
    }},
    "slide_5": {{
      "mensagem_central": "string",
      "evidencias": ["string", "string", "string"],
      "direcao_textual": "string"
    }}
  }}
}}

BIG NUMBERS
{_serialize_for_prompt(context["big_number"], 3000)}

HIGHLIGHTS
{_serialize_for_prompt(context["highlight_infos"], 5000)}

DAY ANALYSIS
{_serialize_for_prompt(context["coverage_context_result"]["day_analysis"], 5000)}

TOPIC ANALYSIS
{_serialize_for_prompt(context["coverage_context_result"]["topic_analysis"], 5000)}

VEHICLE ANALYSIS
{_serialize_for_prompt(context["coverage_context_result"]["vehicle_analysis"], 5000)}

FINAL SYNTHESIS
{_serialize_for_prompt(context["coverage_context_result"]["final_synthesis"], 2500)}

INSIGHTS
{_serialize_for_prompt(context["insights"], 4000)}

CONTEXTO DE NEGÓCIOS
{_serialize_for_prompt(context["contexto_negocios"], 3000)}

ORIENTAÇÃO POR SLIDE
- Slide 1: big numbers + NPS + protagonismo + leitura central do período
- Slide 2: dias de destaque + evolução diária + vetores de sustentação e pressão
- Slide 3: temas promotores e detratores + papel dos assuntos na imagem
- Slide 4: top veículos + enquadramento editorial + contribuição reputacional
- Slide 5: transformar achados em ação, oportunidade e risco
""".strip()


def build_ppt_from_brief_prompt(context: dict, slide_brief: dict, max_chars: dict) -> str:
    return f"""
Você vai escrever o texto final dos slides de uma apresentação em PowerPoint.

OBJETIVO
Converter o briefing editorial em textos curtos, claros e executivos para PPT.

EMPRESA
{context['empresa']}

PERÍODO
{context['periodo_analise']}

REGRAS GERAIS
1. Responda somente em JSON válido.
2. Não invente dados.
3. Escreva em português do Brasil.
4. Títulos devem ser interpretativos.
5. Conecte evidência e interpretação.
6. Respeite os limites máximos aproximados de tamanho abaixo.

LIMITES DE TAMANHO
- slide_1.titulo: até {max_chars["slide_1.titulo"]} caracteres
- slide_1.insight_1: até {max_chars["slide_1.insight_1"]} caracteres
- slide_1.insight_2: até {max_chars["slide_1.insight_2"]} caracteres
- slide_2.titulo: até {max_chars["slide_2.titulo"]} caracteres
- slide_2.texto: até {max_chars["slide_2.texto"]} caracteres
- slide_3.titulo: até {max_chars["slide_3.titulo"]} caracteres
- slide_3.insight_1: até {max_chars["slide_3.insight_1"]} caracteres
- slide_3.insight_2: até {max_chars["slide_3.insight_2"]} caracteres
- slide_4.titulo: até {max_chars["slide_4.titulo"]} caracteres
- slide_4.texto: até {max_chars["slide_4.texto"]} caracteres
- slide_5.titulo: até {max_chars["slide_5.titulo"]} caracteres
- cada bullet de recomendacoes_de_atuacao: até {max_chars["slide_5.recomendacoes_de_atuacao.item"]} caracteres
- cada bullet de oportunidades_observadas: até {max_chars["slide_5.oportunidades_observadas.item"]} caracteres
- cada bullet de riscos_observados: até {max_chars["slide_5.riscos_observados.item"]} caracteres

FORMATO DE SAÍDA
{{
  "meta": {{
    "empresa": "{context['empresa']}",
    "periodo_analise": "{context['periodo_analise']}"
  }},
  "slides": {{
    "slide_1": {{
      "titulo": "string",
      "insight_1": "string",
      "insight_2": "string"
    }},
    "slide_2": {{
      "titulo": "string",
      "texto": "string"
    }},
    "slide_3": {{
      "titulo": "string",
      "insight_1": "string",
      "insight_2": "string"
    }},
    "slide_4": {{
      "titulo": "string",
      "texto": "string"
    }},
    "slide_5": {{
      "titulo": "string",
      "recomendacoes_de_atuacao": ["string", "string", "string"],
      "oportunidades_observadas": ["string", "string", "string"],
      "riscos_observados": ["string", "string", "string"]
    }}
  }}
}}

BRIEF EDITORIAL
{_serialize_for_prompt(slide_brief, 6000)}

BASE DE APOIO
BIG NUMBERS
{_serialize_for_prompt(context["big_number"], 2500)}

HIGHLIGHTS
{_serialize_for_prompt(context["highlight_infos"], 4000)}

COBERTURA
{_serialize_for_prompt(context["coverage_context_result"], 5000)}

INSIGHTS
{_serialize_for_prompt(context["insights"], 3000)}

CONTEXTO DE NEGÓCIOS
{_serialize_for_prompt(context["contexto_negocios"], 2500)}
""".strip()


# =========================================================
# Função principal V3
# =========================================================

def build_ppt_texts_llm(
    *,
    nome_empresa: str,
    periodo_analise: str,
    big_number: dict,
    highlight_infos: dict,
    coverage_context_result: dict,
    insights: dict,
    contexto_negocios: dict | str | None = None,
    llm_callable: Optional[Callable[[str], dict]] = None,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    max_retries: int = 3,
    max_chars_por_campo: Optional[dict] = None,
    return_brief: bool = True,
) -> dict:
    """
    Retorna sempre um dicionário Python.

    Estrutura:
    {
      "meta": {...},
      "slides": {...},
      "slide_brief": {...}  # opcional
    }
    """

    max_chars = _merge_max_chars(max_chars_por_campo)

    context = _prepare_ppt_inputs(
        nome_empresa=nome_empresa,
        periodo_analise=periodo_analise,
        big_number=big_number,
        highlight_infos=highlight_infos,
        coverage_context_result=coverage_context_result,
        insights=insights,
        contexto_negocios=contexto_negocios,
    )

    if llm_callable is None:
        def _default_llm(prompt: str) -> dict:
            return call_chatopenai_json(
                prompt,
                model=model,
                temperature=temperature,
            )
        llm_callable = _default_llm

    # Etapa 1
    prompt_brief = build_slide_brief_prompt(context)
    slide_brief = _call_with_retry_json(
        prompt_brief,
        llm_callable=llm_callable,
        max_retries=max_retries,
    )
    slide_brief = validate_slide_brief_output(slide_brief)

    # Etapa 2
    prompt_final = build_ppt_from_brief_prompt(context, slide_brief, max_chars)
    final_output = _call_with_retry_json(
        prompt_final,
        llm_callable=llm_callable,
        max_retries=max_retries,
    )
    final_output = validate_ppt_text_output(final_output)

    # Pós-processamento de tamanho
    final_output = _apply_max_chars_to_output(final_output, max_chars)

    result = {
        "meta": {
            "empresa": nome_empresa,
            "periodo_analise": periodo_analise,
            "model": model,
            "temperature": temperature,
            "max_chars_por_campo": max_chars,
        },
        "slides": final_output["slides"],
    }

    if return_brief:
        result["slide_brief"] = slide_brief

    return result