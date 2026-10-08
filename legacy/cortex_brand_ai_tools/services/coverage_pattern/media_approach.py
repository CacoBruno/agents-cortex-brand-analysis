from __future__ import annotations

"""
coverage_summary_pipeline_v2.py

Pipeline híbrido para resumir cobertura de mídia com:
1. camada determinística
2. score editorial híbrido por documento
3. seleção orientada por relevância reputacional
4. prompts estruturados para LLM
5. saída pronta para highlight executivo

Entradas esperadas:
- contexto_dia
- context_veiculos
- context_assuntos

Saídas principais:
- análise por dia
- análise por veículo
- análise por assunto específico
- síntese final
- highlights executivos prontos
- lista consolidada de links/publicações
"""

from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from collections import Counter
import json
import math
import re


# =========================================================
# TIPOS
# =========================================================

LLMCallable = Callable[[str], str]


@dataclass
class CoveragePipelineConfig:
    target_brand: str
    top_n_vehicles: int = 10
    top_n_docs_per_day: int = 10
    top_n_docs_per_vehicle: int = 8
    top_n_docs_per_topic: int = 8
    max_chars_text: int = 2500
    include_only_target_brand: bool = True
    sort_links_by_editorial_score: bool = True
    final_top_highlights: int = 8

    # pesos do score editorial híbrido
    weight_doc_score: float = 0.35
    weight_tier: float = 0.15
    weight_protagonism: float = 0.15
    weight_impact: float = 0.20
    weight_title_brand_presence: float = 0.10
    weight_topic_presence: float = 0.05


# =========================================================
# HELPERS BÁSICOS
# =========================================================

def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_lower(value: Any) -> str:
    return _normalize_text(value).lower()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _truncate_text(text: str, max_chars: int = 2500) -> str:
    text = _normalize_text(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _extract_tier_number(tier_value: Any) -> Optional[int]:
    text = _normalize_lower(tier_value)
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return None


def _brand_in_doc(doc: dict, target_brand: str) -> bool:
    empresa = _normalize_lower(doc.get("empresa"))
    return empresa == _normalize_lower(target_brand)


def _filter_docs_by_brand(
    docs: Sequence[dict],
    target_brand: str,
    include_only_target_brand: bool = True,
) -> List[dict]:
    if not include_only_target_brand:
        return list(docs)
    return [d for d in docs if _brand_in_doc(d, target_brand)]


def _contains_brand_in_title(doc: dict, target_brand: str) -> bool:
    titulo = _normalize_lower(doc.get("titulo"))
    brand = _normalize_lower(target_brand)
    return bool(titulo and brand and brand in titulo)


def _contains_topic(doc: dict) -> bool:
    topic = _normalize_text(doc.get("Assuntos específicos"))
    return bool(topic)


# =========================================================
# MAPEAMENTOS DETERMINÍSTICOS
# =========================================================

def _tier_score(tier_value: Any) -> float:
    tier_num = _extract_tier_number(tier_value)
    if tier_num is None:
        return 0.40
    mapping = {
        1: 1.00,
        2: 0.80,
        3: 0.60,
        4: 0.40,
        5: 0.25,
    }
    return mapping.get(tier_num, max(0.15, 1.0 - 0.15 * (tier_num - 1)))


def _protagonism_score(protagonism_value: Any) -> float:
    value = _normalize_lower(protagonism_value)
    mapping = {
        "protagonismo": 1.00,
        "referência contextual / setor": 0.55,
        "referencia contextual / setor": 0.55,
        "citação relevante": 0.70,
        "citacao relevante": 0.70,
        "figurante": 0.25,
        "referência em matéria de concorrente": 0.15,
        "referencia em materia de concorrente": 0.15,
    }
    if value in mapping:
        return mapping[value]

    # fallback por heurística
    if "protagon" in value:
        return 1.00
    if "cita" in value:
        return 0.70
    if "context" in value or "setor" in value:
        return 0.55
    if "figur" in value:
        return 0.25
    if "concorr" in value:
        return 0.15
    return 0.50


def _impact_score(impact_value: Any, sentiment_value: Any = None) -> float:
    impact = _normalize_lower(impact_value)
    sentiment = _normalize_lower(sentiment_value)

    positive_tokens = ["promotor", "positivo", "favorável", "favoravel"]
    negative_tokens = ["detrator", "negativo", "desfavorável", "desfavoravel"]
    neutral_tokens = ["inócuo", "inocuo", "neutro"]

    if any(tok in impact for tok in positive_tokens):
        return 1.00
    if any(tok in impact for tok in negative_tokens):
        return 0.10
    if any(tok in impact for tok in neutral_tokens):
        return 0.45

    if any(tok in sentiment for tok in positive_tokens):
        return 0.90
    if any(tok in sentiment for tok in negative_tokens):
        return 0.15
    if any(tok in sentiment for tok in neutral_tokens):
        return 0.45

    return 0.50


def _doc_score_normalized(doc_score: Any) -> float:
    value = _safe_float(doc_score, 0.0)
    if value <= 0:
        return 0.0
    # compressão suave para evitar dominância excessiva
    return min(1.0, math.log1p(value) / math.log1p(max(value, 100.0))) if value < 100 else 1.0


# =========================================================
# SCORE EDITORIAL HÍBRIDO
# =========================================================

def compute_editorial_score(doc: dict, config: CoveragePipelineConfig) -> float:
    doc_score = _doc_score_normalized(doc.get("doc_score"))
    tier_score = _tier_score(doc.get("tier"))
    prot_score = _protagonism_score(doc.get("protagonismo"))
    imp_score = _impact_score(doc.get("tipos_de_impactos"), doc.get("sentimento"))
    title_brand_score = 1.0 if _contains_brand_in_title(doc, config.target_brand) else 0.0
    topic_score = 1.0 if _contains_topic(doc) else 0.0

    weighted = (
        config.weight_doc_score * doc_score
        + config.weight_tier * tier_score
        + config.weight_protagonism * prot_score
        + config.weight_impact * imp_score
        + config.weight_title_brand_presence * title_brand_score
        + config.weight_topic_presence * topic_score
    )
    return round(weighted, 4)


def _score_doc_with_reason(doc: dict, config: CoveragePipelineConfig) -> dict:
    editorial_score = compute_editorial_score(doc, config)
    enriched = dict(doc)
    enriched["editorial_score"] = editorial_score
    enriched["editorial_score_breakdown"] = {
        "doc_score_norm": round(_doc_score_normalized(doc.get("doc_score")), 4),
        "tier_score": round(_tier_score(doc.get("tier")), 4),
        "protagonism_score": round(_protagonism_score(doc.get("protagonismo")), 4),
        "impact_score": round(_impact_score(doc.get("tipos_de_impactos"), doc.get("sentimento")), 4),
        "title_brand_presence": 1.0 if _contains_brand_in_title(doc, config.target_brand) else 0.0,
        "topic_presence": 1.0 if _contains_topic(doc) else 0.0,
    }
    return enriched


def _sort_and_limit_docs(docs: Sequence[dict], limit: int) -> List[dict]:
    return sorted(
        list(docs),
        key=lambda d: (
            _safe_float(d.get("editorial_score"), 0.0),
            _safe_float(d.get("doc_score"), 0.0),
            _safe_float(d.get("alcance"), 0.0),
        ),
        reverse=True,
    )[:limit]


# =========================================================
# NORMALIZAÇÃO DE DOC PARA LLM
# =========================================================

def _prepare_doc_for_llm(doc: dict, max_chars_text: int = 2500) -> dict:
    return {
        "data": _normalize_text(doc.get("data")),
        "fonte": _normalize_text(doc.get("fonte")),
        "titulo": _normalize_text(doc.get("titulo")),
        "alcance": _safe_float(doc.get("alcance")),
        "tier": _normalize_text(doc.get("tier")),
        "tipos_de_impactos": _normalize_text(doc.get("tipos_de_impactos")),
        "sentimento": _normalize_text(doc.get("sentimento")),
        "protagonismo": _normalize_text(doc.get("protagonismo")),
        "empresa": _normalize_text(doc.get("empresa")),
        "produto": _normalize_text(doc.get("produto")),
        "jornalista": _normalize_text(doc.get("jornalista")),
        "url_da_noticia": _normalize_text(doc.get("url da notícia")),
        "assuntos_especificos": _normalize_text(doc.get("Assuntos específicos")),
        "midia": _normalize_text(doc.get("Mídia")),
        "doc_score": _safe_float(doc.get("doc_score")),
        "editorial_score": _safe_float(doc.get("editorial_score")),
        "editorial_score_breakdown": doc.get("editorial_score_breakdown", {}),
        "texto": _truncate_text(_normalize_text(doc.get("texto")), max_chars=max_chars_text),
    }


def _build_link_item(doc: dict, date_value: Optional[str] = None) -> dict:
    return {
        "data": date_value or _normalize_text(doc.get("data")),
        "fonte": _normalize_text(doc.get("fonte")),
        "titulo": _normalize_text(doc.get("titulo")),
        "url": _normalize_text(doc.get("url da notícia")),
        "doc_score": _safe_float(doc.get("doc_score")),
        "editorial_score": _safe_float(doc.get("editorial_score")),
        "alcance": _safe_float(doc.get("alcance")),
        "tier": _normalize_text(doc.get("tier")),
        "assuntos_especificos": _normalize_text(doc.get("Assuntos específicos")),
    }


def _unique_links(items: Sequence[dict]) -> List[dict]:
    seen = set()
    result = []
    for item in items:
        key = (
            item.get("data"),
            item.get("fonte"),
            item.get("titulo"),
            item.get("url"),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


# =========================================================
# SUMÁRIOS DETERMINÍSTICOS AUXILIARES
# =========================================================

def _summarize_docs_deterministically(docs: Sequence[dict]) -> dict:
    impact_counter = Counter()
    sentiment_counter = Counter()
    protagonism_counter = Counter()
    topic_counter = Counter()
    source_counter = Counter()

    for doc in docs:
        impact_counter[_normalize_text(doc.get("tipos_de_impactos"))] += 1
        sentiment_counter[_normalize_text(doc.get("sentimento"))] += 1
        protagonism_counter[_normalize_text(doc.get("protagonismo"))] += 1
        topic = _normalize_text(doc.get("Assuntos específicos")) or _normalize_text(doc.get("assuntos_especificos"))
        if topic:
            topic_counter[topic] += 1
        source_counter[_normalize_text(doc.get("fonte"))] += 1

    return {
        "top_impactos": impact_counter.most_common(5),
        "top_sentimentos": sentiment_counter.most_common(5),
        "top_protagonismo": protagonism_counter.most_common(5),
        "top_assuntos": topic_counter.most_common(8),
        "top_fontes": source_counter.most_common(8),
        "total_docs": len(list(docs)),
    }


# =========================================================
# PREPARAÇÃO — DIA
# =========================================================

def prepare_day_context_for_llm(contexto_dia: dict, config: CoveragePipelineConfig) -> dict:
    cobertura_por_dia = contexto_dia.get("cobertura_por_dia", {}) or {}

    day_payload = {}
    all_links = []

    for dia, info_dia in cobertura_por_dia.items():
        tema_dominante = info_dia.get("tema_dominante")
        docs = info_dia.get("documentos", []) or []

        docs_brand = _filter_docs_by_brand(
            docs,
            target_brand=config.target_brand,
            include_only_target_brand=config.include_only_target_brand,
        )
        docs_scored = [_score_doc_with_reason(doc, config) for doc in docs_brand]
        docs_selected = _sort_and_limit_docs(docs_scored, config.top_n_docs_per_day)

        llm_docs = [_prepare_doc_for_llm(doc, config.max_chars_text) for doc in docs_selected]
        deterministic_summary = _summarize_docs_deterministically(docs_selected)

        links = [_build_link_item(doc, date_value=dia) for doc in docs_selected]
        all_links.extend(links)

        day_payload[dia] = {
            "tema_dominante": tema_dominante,
            "resumo_deterministico": deterministic_summary,
            "documentos_selecionados": llm_docs,
            "quantidade_documentos_original": len(docs),
            "quantidade_documentos_marca": len(docs_brand),
            "quantidade_documentos_enviados_llm": len(llm_docs),
        }

    return {
        "target_brand": config.target_brand,
        "criterios_dias": contexto_dia.get("criterios_dias"),
        "dias_selecionados": contexto_dia.get("dias_selecionados"),
        "resumo_dias": contexto_dia.get("resumo_dias"),
        "dias_com_cobertura": contexto_dia.get("dias_com_cobertura"),
        "dias_sem_cobertura": contexto_dia.get("dias_sem_cobertura"),
        "cobertura_por_dia_preparada": day_payload,
        "links_publicacoes": _unique_links(all_links),
    }


# =========================================================
# PREPARAÇÃO — VEÍCULOS
# =========================================================

def prepare_vehicle_context_for_llm(context_veiculos: dict, config: CoveragePipelineConfig) -> dict:
    ranking_veiculos = context_veiculos.get("ranking_veiculos", []) or []
    cobertura = context_veiculos.get("cobertura", {}) or {}

    top_vehicle_names: List[str] = []
    if ranking_veiculos and isinstance(ranking_veiculos, list):
        for item in ranking_veiculos[: config.top_n_vehicles]:
            if isinstance(item, dict):
                fonte = _normalize_text(item.get("fonte") or item.get("Fonte") or item.get("veiculo"))
                if fonte:
                    top_vehicle_names.append(fonte)

    if not top_vehicle_names:
        top_vehicle_names = list(cobertura.keys())[: config.top_n_vehicles]

    vehicle_payload = {}
    all_links = []

    for vehicle in top_vehicle_names:
        docs = cobertura.get(vehicle, []) or []
        docs_brand = _filter_docs_by_brand(
            docs,
            target_brand=config.target_brand,
            include_only_target_brand=config.include_only_target_brand,
        )
        docs_scored = [_score_doc_with_reason(doc, config) for doc in docs_brand]
        docs_selected = _sort_and_limit_docs(docs_scored, config.top_n_docs_per_vehicle)

        llm_docs = [_prepare_doc_for_llm(doc, config.max_chars_text) for doc in docs_selected]
        deterministic_summary = _summarize_docs_deterministically(docs_selected)

        links = [_build_link_item(doc) for doc in docs_selected]
        all_links.extend(links)

        vehicle_payload[vehicle] = {
            "resumo_deterministico": deterministic_summary,
            "documentos_selecionados": llm_docs,
            "quantidade_documentos_original": len(docs),
            "quantidade_documentos_marca": len(docs_brand),
            "quantidade_documentos_enviados_llm": len(llm_docs),
        }

    return {
        "target_brand": config.target_brand,
        "ranking_veiculos": ranking_veiculos[: config.top_n_vehicles],
        "veiculos_selecionados": top_vehicle_names,
        "cobertura_veiculos_preparada": vehicle_payload,
        "links_publicacoes": _unique_links(all_links),
    }


# =========================================================
# PREPARAÇÃO — ASSUNTOS
# =========================================================

def prepare_topic_context_for_llm(context_assuntos: dict, config: CoveragePipelineConfig) -> dict:
    brand_block = context_assuntos.get(config.target_brand, {}) or {}
    assuntos_promotores = brand_block.get("assuntos_promotores", {}) or {}
    assuntos_detratores = brand_block.get("assuntos_detratores", {}) or {}

    def _prepare_topic_group(topic_group: dict, group_name: str) -> Tuple[dict, List[dict]]:
        payload = {}
        all_links: List[dict] = []

        for assunto, assunto_dict in topic_group.items():
            metricas = assunto_dict.get("metricas_assunto")
            reportagens = assunto_dict.get("reportagens", []) or []

            docs_brand = _filter_docs_by_brand(
                reportagens,
                target_brand=config.target_brand,
                include_only_target_brand=config.include_only_target_brand,
            )
            docs_scored = [_score_doc_with_reason(doc, config) for doc in docs_brand]
            docs_selected = _sort_and_limit_docs(docs_scored, config.top_n_docs_per_topic)

            llm_docs = [_prepare_doc_for_llm(doc, config.max_chars_text) for doc in docs_selected]
            deterministic_summary = _summarize_docs_deterministically(docs_selected)

            links = [_build_link_item(doc) for doc in docs_selected]
            all_links.extend(links)

            payload[assunto] = {
                "grupo_assunto": group_name,
                "metricas_assunto": metricas,
                "resumo_deterministico": deterministic_summary,
                "documentos_selecionados": llm_docs,
                "quantidade_documentos_original": len(reportagens),
                "quantidade_documentos_marca": len(docs_brand),
                "quantidade_documentos_enviados_llm": len(llm_docs),
            }

        return payload, all_links

    prom_payload, prom_links = _prepare_topic_group(assuntos_promotores, "promotor")
    det_payload, det_links = _prepare_topic_group(assuntos_detratores, "detrator")

    return {
        "target_brand": config.target_brand,
        "nps_score_periodo": brand_block.get("nps_score_periodo"),
        "assuntos_promotores_preparados": prom_payload,
        "assuntos_detratores_preparados": det_payload,
        "links_publicacoes": _unique_links(prom_links + det_links),
    }


# =========================================================
# PROMPTS
# =========================================================

def build_day_summary_prompt(prepared_day_context: dict) -> str:
    return f"""
Você é um analista sênior de reputação e mídia.

Sua tarefa é resumir a cobertura por dia da marca "{prepared_day_context.get('target_brand')}".

OBJETIVO
Gerar uma análise executiva da cobertura diária, avaliando:
1. qual foi o tema dominante de cada dia,
2. qual foi o tom predominante do dia,
3. se a cobertura foi favorável, mista, neutra ou desfavorável para a marca,
4. como os veículos abordaram os assuntos específicos,
5. o que sustentou a imagem versus o que só deu escala de exposição.

REGRAS
- Analise somente os documentos enviados.
- Use a marca do campo "empresa" como referência principal.
- Não invente fatos.
- Dê mais peso analítico aos documentos com maior editorial_score.
- Considere conjuntamente: tipos_de_impactos, sentimento, protagonismo, assuntos_especificos, título, texto, fonte e tier.
- Diferencie claramente:
  a) vetores que sustentaram a imagem
  b) vetores que pressionaram a imagem
  c) elementos que só ampliaram exposição
- Cite exemplos concretos de fontes, títulos ou assuntos quando isso ajudar.
- Responda em português do Brasil, em tom executivo.

FORMATO DE SAÍDA
Retorne JSON com esta estrutura:
{{
  "resumo_geral": "...",
  "analise_por_dia": [
    {{
      "data": "YYYY-MM-DD",
      "tema_dominante": "...",
      "tom_do_dia": "...",
      "avaliacao_para_marca": "favorável|mista|desfavorável|neutra",
      "o_que_sustentou": ["..."],
      "o_que_pressionou": ["..."],
      "o_que_so_deu_escala": ["..."],
      "como_veiculos_abordaram": "...",
      "principais_evidencias": ["..."]
    }}
  ]
}}

DADOS
{_json_dumps(prepared_day_context)}
""".strip()


def build_vehicle_summary_prompt(prepared_vehicle_context: dict) -> str:
    return f"""
Você é um analista sênior de reputação e mídia.

Sua tarefa é resumir como os principais veículos abordaram a marca "{prepared_vehicle_context.get('target_brand')}".

OBJETIVO
Gerar uma análise executiva por veículo, avaliando:
1. enquadramento editorial,
2. tom predominante,
3. avaliação da abordagem para a marca,
4. assuntos mais associados,
5. se o veículo contribuiu mais para reputação ou apenas para visibilidade.

REGRAS
- Analise somente os documentos enviados.
- Dê mais peso aos documentos com maior editorial_score.
- Não invente fatos.
- Considere tipos_de_impactos, sentimento, protagonismo, tier, assuntos_especificos, título e texto.
- Diferencie reputação versus escala de exposição.
- Responda em português do Brasil, com tom executivo e analítico.

FORMATO DE SAÍDA
Retorne JSON com esta estrutura:
{{
  "resumo_geral": "...",
  "analise_por_veiculo": [
    {{
      "veiculo": "...",
      "tom_predominante": "...",
      "avaliacao_para_marca": "favorável|mista|desfavorável|neutra",
      "assuntos_mais_recorrentes": ["..."],
      "enquadramento_editorial": "...",
      "papel_na_imagem": "mais reputacional|mais exposição|misto",
      "o_que_sustentou": ["..."],
      "o_que_pressionou": ["..."],
      "principais_evidencias": ["..."]
    }}
  ]
}}

DADOS
{_json_dumps(prepared_vehicle_context)}
""".strip()


def build_topic_summary_prompt(prepared_topic_context: dict) -> str:
    return f"""
Você é um analista sênior de reputação e mídia.

Sua tarefa é resumir como os assuntos específicos da marca "{prepared_topic_context.get('target_brand')}" foram abordados na cobertura.

OBJETIVO
Gerar uma análise executiva dos assuntos promotores e detratores, avaliando:
1. como cada assunto foi enquadrado,
2. qual foi o tom dominante,
3. quais veículos deram mais destaque,
4. o que foi mais enfatizado no texto,
5. em que medida o assunto sustentou ou pressionou a imagem.

REGRAS
- Analise somente os documentos enviados.
- Dê mais peso aos documentos com maior editorial_score.
- Não invente fatos.
- Diferencie:
  a) assunto que sustentou a imagem
  b) assunto que pressionou a imagem
  c) assunto que só ampliou exposição
- Responda em português do Brasil, com tom executivo e analítico.

FORMATO DE SAÍDA
Retorne JSON com esta estrutura:
{{
  "resumo_geral": "...",
  "analise_assuntos_promotores": [
    {{
      "assunto": "...",
      "tom_predominante": "...",
      "como_foi_abordado": "...",
      "veiculos_em_destaque": ["..."],
      "pontos_mais_destacados": ["..."],
      "papel_na_imagem": "...",
      "principais_evidencias": ["..."]
    }}
  ],
  "analise_assuntos_detratores": [
    {{
      "assunto": "...",
      "tom_predominante": "...",
      "como_foi_abordado": "...",
      "veiculos_em_destaque": ["..."],
      "pontos_mais_destacados": ["..."],
      "papel_na_imagem": "...",
      "principais_evidencias": ["..."]
    }}
  ]
}}

DADOS
{_json_dumps(prepared_topic_context)}
""".strip()


def build_final_synthesis_prompt(target_brand: str, day_analysis: dict, vehicle_analysis: dict, topic_analysis: dict) -> str:
    return f"""
Você é um analista sênior de reputação e mídia.

Sua tarefa é criar uma síntese final da cobertura da marca "{target_brand}", integrando:
1. contexto dos dias,
2. contexto dos veículos,
3. contexto dos assuntos específicos.

OBJETIVO
Produzir uma leitura integrada da cobertura:
- quadro geral da imagem
- vetores que sustentaram a imagem
- vetores que pressionaram a imagem
- vetores que só ampliaram exposição
- papel dos veículos
- papel dos assuntos

REGRAS
- Integre os três blocos analíticos.
- Não repita mecanicamente as mesmas ideias.
- Faça correlação lógica.
- Escreva em português do Brasil, com tom executivo.

FORMATO DE SAÍDA
Retorne JSON com esta estrutura:
{{
  "final_synthesis": {{
    "quadro_geral_da_imagem": "...",
    "vetores_que_sustentaram": ["..."],
    "vetores_que_pressionaram": ["..."],
    "vetores_que_so_deram_escala": ["..."],
    "papel_dos_veiculos": "...",
    "papel_dos_assuntos": "...",
    "conclusao_executiva": "..."
  }}
}}

DADOS
{_json_dumps({
    'target_brand': target_brand,
    'day_analysis': day_analysis,
    'vehicle_analysis': vehicle_analysis,
    'topic_analysis': topic_analysis,
})}
""".strip()


def build_executive_highlights_prompt(target_brand: str, final_synthesis: dict, day_analysis: dict, vehicle_analysis: dict, topic_analysis: dict, top_n: int = 8) -> str:
    return f"""
Você é um analista sênior de reputação e mídia.

Sua tarefa é transformar as análises sobre a marca "{target_brand}" em highlights executivos prontos para report.

OBJETIVO
Gerar highlights com estrutura:
- headline
- insight
- evidências
- classificação do highlight

REGRAS
- Todo highlight deve ser baseado em evidências das análises fornecidas.
- Não invente fatos.
- Diferencie highlights de imagem, pressão reputacional, exposição, veículos e assuntos.
- O texto deve ser objetivo, executivo e utilizável em slide.
- Faça highlights distintos entre si.
- Priorize os mais importantes.

FORMATO DE SAÍDA
Retorne JSON com esta estrutura:
{{
  "executive_highlights": [
    {{
      "headline": "...",
      "insight": "...",
      "tipo": "imagem|pressao|exposicao|veiculos|assuntos",
      "evidencias": ["..."],
      "prioridade": 1
    }}
  ]
}}

Número máximo de highlights: {top_n}

DADOS
{_json_dumps({
    'target_brand': target_brand,
    'final_synthesis': final_synthesis,
    'day_analysis': day_analysis,
    'vehicle_analysis': vehicle_analysis,
    'topic_analysis': topic_analysis,
})}
""".strip()


# =========================================================
# EXECUÇÃO DO LLM
# =========================================================

def run_llm_json(llm: LLMCallable, prompt: str) -> dict:
    raw = llm(prompt)

    if isinstance(raw, dict):
        return raw

    raw = _normalize_text(raw)
    json_match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if json_match:
        raw = json_match.group(0)

    try:
        return json.loads(raw)
    except Exception:
        return {
            "raw_output": raw,
            "parse_error": True,
        }


# =========================================================
# LINKS CONSOLIDADOS
# =========================================================

def build_links_output(prepared_day_context: dict, prepared_vehicle_context: dict, prepared_topic_context: dict, sort_by_editorial_score: bool = True) -> dict:
    links: List[dict] = []
    links.extend(prepared_day_context.get("links_publicacoes", []))
    links.extend(prepared_vehicle_context.get("links_publicacoes", []))
    links.extend(prepared_topic_context.get("links_publicacoes", []))

    links = _unique_links(links)

    if sort_by_editorial_score:
        links = sorted(
            links,
            key=lambda x: (
                _safe_float(x.get("editorial_score"), 0.0),
                _safe_float(x.get("doc_score"), 0.0),
                _safe_float(x.get("alcance"), 0.0),
            ),
            reverse=True,
        )

    return {"publicacoes": links}


# =========================================================
# PIPELINE PRINCIPAL
# =========================================================

def build_coverage_summary(
    contexto_dia: dict,
    context_veiculos: dict,
    context_assuntos: dict,
    *,
    target_brand: str,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    top_n_vehicles: int = 10,
    top_n_docs_per_day: int = 10,
    top_n_docs_per_vehicle: int = 8,
    top_n_docs_per_topic: int = 8,
    max_chars_text: int = 2500,
    include_only_target_brand: bool = True,
    final_top_highlights: int = 8,
) -> dict:
    from langchain_openai import ChatOpenAI

    chat_model = ChatOpenAI(
        model=model,
        temperature=temperature,
    )

    llm = make_langchain_llm_callable(chat_model)
    config = CoveragePipelineConfig(
        target_brand=target_brand,
        top_n_vehicles=top_n_vehicles,
        top_n_docs_per_day=top_n_docs_per_day,
        top_n_docs_per_vehicle=top_n_docs_per_vehicle,
        top_n_docs_per_topic=top_n_docs_per_topic,
        max_chars_text=max_chars_text,
        include_only_target_brand=include_only_target_brand,
        final_top_highlights=final_top_highlights,
    )

    # 1. preparação determinística
    prepared_day_context = prepare_day_context_for_llm(contexto_dia, config)
    prepared_vehicle_context = prepare_vehicle_context_for_llm(context_veiculos, config)
    prepared_topic_context = prepare_topic_context_for_llm(context_assuntos, config)

    # 2. prompts especializados
    day_prompt = build_day_summary_prompt(prepared_day_context)
    vehicle_prompt = build_vehicle_summary_prompt(prepared_vehicle_context)
    topic_prompt = build_topic_summary_prompt(prepared_topic_context)

    # 3. análises por camada
    day_analysis = run_llm_json(llm, day_prompt)
    vehicle_analysis = run_llm_json(llm, vehicle_prompt)
    topic_analysis = run_llm_json(llm, topic_prompt)

    # 4. síntese final
    final_prompt = build_final_synthesis_prompt(
        target_brand=target_brand,
        day_analysis=day_analysis,
        vehicle_analysis=vehicle_analysis,
        topic_analysis=topic_analysis,
    )
    final_synthesis = run_llm_json(llm, final_prompt)

    # 5. highlights executivos prontos
    highlights_prompt = build_executive_highlights_prompt(
        target_brand=target_brand,
        final_synthesis=final_synthesis,
        day_analysis=day_analysis,
        vehicle_analysis=vehicle_analysis,
        topic_analysis=topic_analysis,
        top_n=final_top_highlights,
    )
    executive_highlights = run_llm_json(llm, highlights_prompt)

    # 6. links consolidados
    links_output = build_links_output(
        prepared_day_context=prepared_day_context,
        prepared_vehicle_context=prepared_vehicle_context,
        prepared_topic_context=prepared_topic_context,
        sort_by_editorial_score=config.sort_links_by_editorial_score,
    )

    return {
        "config": asdict(config),
        "prepared_inputs": {
            "contexto_dia_preparado": prepared_day_context,
            "contexto_veiculos_preparado": prepared_vehicle_context,
            "contexto_assuntos_preparado": prepared_topic_context,
        },
        "prompts": {
            "day_prompt": day_prompt,
            "vehicle_prompt": vehicle_prompt,
            "topic_prompt": topic_prompt,
            "final_prompt": final_prompt,
            "highlights_prompt": highlights_prompt,
        },
        "outputs": {
            "day_analysis": day_analysis,
            "vehicle_analysis": vehicle_analysis,
            "topic_analysis": topic_analysis,
            "final_synthesis": final_synthesis,
            "executive_highlights": executive_highlights,
            "links_publicacoes": links_output,
        },
    }

def make_langchain_llm_callable(chat_model) -> LLMCallable:
    def _call(prompt: str) -> str:
        response = chat_model.invoke(prompt)
        content = getattr(response, "content", response)
        if isinstance(content, list):
            return "\n".join(str(x) for x in content)
        return str(content)

    return _call

# =========================================================
# EXEMPLO DE USO REAL COM LANGCHAIN
# =========================================================

"""
from langchain_openai import ChatOpenAI
from coverage_summary_pipeline_v2 import (
    build_coverage_summary_pipeline_v2,
    make_langchain_llm_callable,
)

chat_model = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.2,
)

llm_callable = make_langchain_llm_callable(chat_model)

result = build_coverage_summary_pipeline_v2(
    contexto_dia=contexto_dia,
    context_veiculos=context_veiculos,
    context_assuntos=context_assuntos,
    llm=llm_callable,
    target_brand="americanas sa",
    top_n_vehicles=10,
    top_n_docs_per_day=10,
    top_n_docs_per_vehicle=8,
    top_n_docs_per_topic=8,
    final_top_highlights=6,
)

highlights = result["outputs"]["executive_highlights"]
final_synthesis = result["outputs"]["final_synthesis"]
links_publicacoes = result["outputs"]["links_publicacoes"]
"""
