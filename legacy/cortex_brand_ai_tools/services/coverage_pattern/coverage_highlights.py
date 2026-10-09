from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from langchain_openai import ChatOpenAI


MONTHS_PT = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}


# =========================================================
# HELPERS
# =========================================================

def safe_json(obj):
    import pandas as pd
    import numpy as np

    if isinstance(obj, pd.Timestamp):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, set):
        return list(obj)
    return str(obj)


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except Exception:
        return None


def _format_date(value: Any) -> str:
    s = str(value)
    if " " in s:
        s = s.split(" ")[0]
    if "T" in s:
        s = s.split("T")[0]
    return s


def _format_day_pt(value: Any, include_year: bool = False) -> str:
    s = _format_date(value)
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if not m:
        return s
    year = int(m.group(1))
    month = int(m.group(2))
    day = int(m.group(3))
    month_name = MONTHS_PT.get(month, str(month))
    if include_year:
        return f"{day:02d} de {month_name} de {year}"
    return f"{day:02d} de {month_name}"


def _format_period_reference_pt(value: Any) -> str:
    s = str(value or "").strip()
    m = re.match(r"^(\d{2})/(\d{4})$", s)
    if m:
        month = int(m.group(1))
        year = int(m.group(2))
        return f"{MONTHS_PT.get(month, str(month))} de {year}"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return _format_day_pt(s, include_year=False)
    return s


def _dedupe_keep_order(items: Iterable[Any]) -> List[Any]:
    seen = set()
    out = []
    for item in items:
        key = json.dumps(item, ensure_ascii=False, default=safe_json, sort_keys=True) if isinstance(item, dict) else str(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _clean_llm_numbered_list(text: str) -> List[str]:
    if not text:
        return []
    lines = [x.strip() for x in text.split("\n") if x.strip()]
    out = []
    for line in lines:
        line = re.sub(r"^\d+[\).\-\s]+", "", line).strip()
        line = re.sub(r"^[•\-]\s*", "", line).strip()
        if line:
            out.append(line)
    return out


def _format_number_br(value: Optional[float], ndigits: int = 2) -> Optional[str]:
    if value is None:
        return None
    s = f"{value:,.{ndigits}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _format_integer_br(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    s = f"{int(round(value)):,}"
    return s.replace(",", ".")


def _format_metric_value(indicator: str, value: Any, text_value: Any = None) -> str:
    if text_value not in (None, ""):
        return str(text_value)

    numeric = _safe_float(value)
    if numeric is None:
        return "n/d"

    if indicator in {"nps", "protagonismo", "nps_score_dia", "protagonism_score_dia"}:
        return _format_number_br(numeric, 2) or "n/d"

    if indicator in {
        "publicacoes_totais",
        "publicacoes_promotoras",
        "publicacoes_detratoras",
        "publicacoes_inocuas",
        "frequencia",
        "total_assunto_especifico",
        "denom_total",
    }:
        return _format_integer_br(numeric) or "n/d"

    if indicator in {
        "impacto_total",
        "impacto_promotor",
        "impacto_detrator",
        "impacto_inocuo",
        "alcance",
        "Promotores",
        "Detratores",
        "Inócuos",
    }:
        if numeric >= 1_000_000:
            return f"{_format_number_br(numeric / 1_000_000, 1)} M"
        if numeric >= 1_000:
            return f"{_format_number_br(numeric / 1_000, 1)} mil"
        return _format_number_br(numeric, 0) or "n/d"

    return _format_number_br(numeric, 2) or "n/d"


def _format_diff(value: Any, unit: Optional[str]) -> Optional[str]:
    numeric = _safe_float(value)
    if numeric is None:
        return None
    sign = "+" if numeric > 0 else ""
    if unit == "p.p.":
        return f"{sign}{_format_number_br(numeric, 2)} p.p."
    if unit == "%":
        return f"{sign}{_format_number_br(numeric, 2)}%"
    if unit == "contrib":
        return f"{sign}{_format_number_br(numeric, 4)}"
    return f"{sign}{_format_number_br(numeric, 2)}"


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _first_not_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _company_display_name(raw_name: str, display_name_map: Optional[Mapping[str, str]] = None) -> str:
    if not raw_name:
        return raw_name
    if not display_name_map:
        return raw_name
    if raw_name in display_name_map:
        return display_name_map[raw_name]
    lowered = _normalize_text(raw_name)
    for key, value in display_name_map.items():
        if _normalize_text(key) == lowered:
            return value
    return raw_name


# =========================================================
# CONFIG
# =========================================================

INDICATOR_LABELS = {
    "nps": "NPS",
    "protagonismo": "Protagonismo",
    "impacto_total": "Impacto Total",
    "impacto_promotor": "Impacto Promotor",
    "impacto_detrator": "Impacto Detrator",
    "impacto_inocuo": "Impacto Inócuo",
    "publicacoes_totais": "Publicações Totais",
    "publicacoes_promotoras": "Publicações Promotoras",
    "publicacoes_detratoras": "Publicações Detratoras",
    "publicacoes_inocuas": "Publicações Inócuas",
    "frequencia": "Frequência",
    "nps_score_dia": "NPS do dia",
    "protagonism_score_dia": "Protagonismo do dia",
    "alcance": "Alcance",
    "Promotores": "Promotores",
    "Detratores": "Detratores",
    "Inócuos": "Inócuos",
    "nps_contrib_assunto_especifico": "Contribuição do assunto para o NPS",
    "total_assunto_especifico": "Frequência do assunto",
}

IMAGE_INDICATORS = {"nps", "protagonismo"}
EXPOSURE_INDICATORS = {
    "impacto_total",
    "impacto_promotor",
    "impacto_detrator",
    "impacto_inocuo",
    "publicacoes_totais",
    "publicacoes_promotoras",
    "publicacoes_detratoras",
    "publicacoes_inocuas",
    "frequencia",
    "alcance",
}

BASE_TAG_SCORES = {
    "melhora_relevante": 10,
    "piora_relevante": 10,
    "alta_relevante": 10,
    "queda_relevante": 10,
    "acima_media_historica": 8,
    "abaixo_media_historica": 8,
    "nps_excelente": 18,
    "nps_otimo": 12,
    "predominio_promotor": 8,
    "predominio_detrator": 8,
    "alta_chance_de_lembranca": 10,
    "dia_com_exposicao_muito_acima_do_padrao": 12,
    "dia_com_predominio_promotor": 8,
    "dia_com_predominio_detrator": 8,
}

TIER_BONUS = {
    "tier 1": 22,
    "tier1": 22,
    "t1": 22,
    "tier 2": 10,
    "tier2": 10,
    "t2": 10,
    "tier 3": 4,
    "tier3": 4,
    "t3": 4,
}

FAIXA_NPS_GUIDE = (
    "NPS < -80: crise; -80 a 0: atenção; 0 a 35: regular; 35 a 50: bom; 50 a 80: ótimo; > 80: excelente."
)


def _classify_nps_band(value: Any) -> Optional[str]:
    numeric = _safe_float(value)
    if numeric is None:
        return None
    if numeric < -80:
        return "crise"
    if numeric < 0:
        return "atenção"
    if numeric < 35:
        return "regular"
    if numeric < 50:
        return "bom"
    if numeric <= 80:
        return "ótimo"
    return "excelente"


def _topic_share(total_topic: Any, denom_total: Any) -> float:
    total = _safe_float(total_topic) or 0.0
    denom = _safe_float(denom_total) or 0.0
    if denom <= 0:
        return 0.0
    return total / denom


def _safe_ratio(numerator: Any, denominator: Any) -> float:
    num = _safe_float(numerator) or 0.0
    den = _safe_float(denominator) or 0.0
    if den == 0:
        return 0.0
    return num / den


def _theme_quality_bonus(nps_score_periodo: Any, contrib_value: Any) -> float:
    nps = _safe_float(nps_score_periodo)
    contrib = _safe_float(contrib_value) or 0.0
    if nps is None:
        return 0.0
    band = _classify_nps_band(nps)
    if contrib >= 0:
        return {"excelente": 18.0, "ótimo": 12.0, "bom": 8.0, "regular": 2.0, "atenção": -8.0, "crise": -14.0}.get(band, 0.0)
    return {"excelente": -6.0, "ótimo": -3.0, "bom": 0.0, "regular": 8.0, "atenção": 14.0, "crise": 18.0}.get(band, 0.0)


# =========================================================
# NORMALIZAÇÃO DE INPUTS
# =========================================================

def _find_company_block(items: Sequence[dict], company_name: str) -> Optional[dict]:
    target = _normalize_text(company_name)
    for item in items:
        raw = item.get("empresa_analisada")
        if _normalize_text(raw) == target:
            return item
    return None


def _extract_period_info(stats_llm: Optional[dict], sources_llm: Optional[dict], daily_llm: Optional[dict], assunto_llm: Optional[dict]) -> Dict[str, Optional[str]]:
    period_kind = _first_not_none(
        stats_llm.get("periodo") if stats_llm else None,
        assunto_llm.get("periodo_analitico") if assunto_llm else None,
    )
    period_reference = _first_not_none(
        sources_llm.get("periodo_referencia") if sources_llm else None,
        stats_llm.get("empresas", [{}])[0].get("estatisticas_ultimo_periodo", {}).get("periodo_referencia") if stats_llm and stats_llm.get("empresas") else None,
        assunto_llm.get("empresas", [{}])[0].get("periodo_analitico_referencia") if assunto_llm and assunto_llm.get("empresas") else None,
    )
    return {
        "periodo": period_kind,
        "periodo_referencia": period_reference,
    }


def normalize_inputs_by_company(
    stats_llm: dict,
    sources_llm: dict,
    daily_llm: dict,
    assunto_llm: dict,
    *,
    company_display_names: Optional[Mapping[str, str]] = None,
) -> Dict[str, Dict[str, Any]]:
    companies: Dict[str, Dict[str, Any]] = {}

    all_raw_names: List[str] = []
    for payload in [stats_llm, sources_llm, daily_llm, assunto_llm]:
        for item in payload.get("empresas", []):
            if item.get("empresa_analisada"):
                all_raw_names.append(item["empresa_analisada"])

    for raw_name in _dedupe_keep_order(all_raw_names):
        stats_company = _find_company_block(stats_llm.get("empresas", []), raw_name)
        sources_company = _find_company_block(sources_llm.get("empresas", []), raw_name)
        daily_company = _find_company_block(daily_llm.get("empresas", []), raw_name)
        assunto_company = _find_company_block(assunto_llm.get("empresas", []), raw_name)

        if not any([stats_company, sources_company, daily_company, assunto_company]):
            continue

        tipo_empresa = _first_not_none(
            stats_company.get("tipo_empresa") if stats_company else None,
            sources_company.get("tipo_empresa") if sources_company else None,
            daily_company.get("tipo_empresa") if daily_company else None,
            assunto_company.get("tipo_empresa") if assunto_company else None,
        )

        period_info = _extract_period_info(stats_llm, sources_llm, daily_llm, assunto_llm)

        companies[raw_name] = {
            "empresa_analisada": raw_name,
            "empresa_display": _company_display_name(raw_name, company_display_names),
            "tipo_empresa": tipo_empresa or "empresa",
            "periodo": period_info.get("periodo"),
            "periodo_referencia": period_info.get("periodo_referencia"),
            "stats": deepcopy(stats_company) if stats_company else None,
            "sources": deepcopy(sources_company) if sources_company else None,
            "daily": deepcopy(daily_company) if daily_company else None,
            "assunto": deepcopy(assunto_company) if assunto_company else None,
        }

    return companies


# =========================================================
# EXTRAÇÃO DE CANDIDATOS
# =========================================================

def extract_stats_candidates(company_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    stats = company_payload.get("stats") or {}
    bloco = stats.get("estatisticas_ultimo_periodo") or {}
    indicadores = bloco.get("indicadores") or {}
    padrao = bloco.get("padrao_midia_periodo") or {}

    out: List[Dict[str, Any]] = []
    for key, ind in indicadores.items():
        leitura = ind.get("leitura_deterministica") or {}
        base = {
            "scope": "stats",
            "empresa": company_payload["empresa_analisada"],
            "empresa_display": company_payload["empresa_display"],
            "tipo_empresa": company_payload["tipo_empresa"],
            "periodo": company_payload.get("periodo"),
            "periodo_referencia": company_payload.get("periodo_referencia") or bloco.get("periodo_referencia"),
            "indicator": key,
            "label": ind.get("label", INDICATOR_LABELS.get(key, key)),
            "value": ind.get("valor_atual"),
            "value_text": ind.get("valor_atual_texto"),
            "zscore": ind.get("z_score_periodo"),
            "media": ind.get("media"),
            "mediana": ind.get("mediana"),
            "desvio_padrao": ind.get("desvio_padrao"),
            "driver": leitura.get("leitura_principal"),
            "faixa_valor": leitura.get("faixa_valor"),
            "tags": leitura.get("tags", []) or [],
            "indicator_group": "imagem" if key in IMAGE_INDICATORS else "exposicao",
        }

        prev = ind.get("variacao_vs_periodo_anterior") or {}
        hist = ind.get("variacao_vs_media_historica") or {}

        out.append({
            **base,
            "candidate_type": "metric_snapshot",
            "difference": prev.get("valor"),
            "difference_unit": prev.get("unidade"),
            "reference": "período anterior",
            "difference_hist": hist.get("valor"),
            "difference_hist_unit": hist.get("unidade"),
            "reference_hist": "média histórica",
        })

    if padrao:
        out.append({
            "scope": "stats",
            "candidate_type": "period_pattern",
            "empresa": company_payload["empresa_analisada"],
            "empresa_display": company_payload["empresa_display"],
            "tipo_empresa": company_payload["tipo_empresa"],
            "periodo": company_payload.get("periodo"),
            "periodo_referencia": company_payload.get("periodo_referencia") or bloco.get("periodo_referencia"),
            "indicator": "period_pattern",
            "label": "Padrão do período",
            "tags": padrao.get("tags_gerais", []) or [],
            "leituras": padrao.get("leituras_gerais", []) or [],
            "alertas": padrao.get("alertas", []) or [],
            "oportunidades": padrao.get("oportunidades", []) or [],
        })

    return out


def extract_source_candidates(
    company_payload: Dict[str, Any],
    *,
    selected_sources: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    sources = company_payload.get("sources") or {}
    fontes = sources.get("fontes") or []

    selected_normalized = {_normalize_text(x) for x in selected_sources or []}
    out: List[Dict[str, Any]] = []

    for order, item in enumerate(fontes, start=1):
        fonte = item.get("fonte")
        if selected_normalized and _normalize_text(fonte) not in selected_normalized:
            continue

        padrao = item.get("padrao_fonte_periodo") or {}
        tier = _first_not_none(item.get("tier"), item.get("tier_cortex"), padrao.get("tier"))
        indicadores = item.get("indicadores") or {}

        total_freq = _first_not_none(
            (indicadores.get("frequencia") or {}).get("valor_atual"),
            (indicadores.get("publicacoes_totais") or {}).get("valor_atual"),
        )
        total_alcance = _first_not_none(
            (indicadores.get("alcance") or {}).get("valor_atual"),
            (indicadores.get("impacto_total") or {}).get("valor_atual"),
        )
        proxy_nps = (indicadores.get("nps") or {}).get("valor_atual")
        proxy_protag = (indicadores.get("protagonismo") or {}).get("valor_atual")

        for key, ind in indicadores.items():
            leitura = ind.get("leitura_deterministica") or {}
            prev = ind.get("variacao_vs_periodo_anterior") or {}
            hist = ind.get("variacao_vs_media_historica") or {}
            out.append({
                "scope": "sources",
                "candidate_type": "source_metric",
                "empresa": company_payload["empresa_analisada"],
                "empresa_display": company_payload["empresa_display"],
                "tipo_empresa": company_payload["tipo_empresa"],
                "periodo": company_payload.get("periodo"),
                "periodo_referencia": company_payload.get("periodo_referencia"),
                "source_rank": order,
                "fonte": fonte,
                "midia": item.get("midia"),
                "tier": tier,
                "indicator": key,
                "label": ind.get("label", INDICATOR_LABELS.get(key, key)),
                "value": ind.get("valor_atual"),
                "value_text": ind.get("valor_atual_texto"),
                "difference": prev.get("valor"),
                "difference_unit": prev.get("unidade"),
                "reference": "período anterior",
                "difference_hist": hist.get("valor"),
                "difference_hist_unit": hist.get("unidade"),
                "reference_hist": "média histórica da fonte",
                "zscore": ind.get("z_score_periodo"),
                "driver": leitura.get("leitura_principal"),
                "tags": _dedupe_keep_order((leitura.get("tags") or []) + (padrao.get("tags") or [])),
                "source_total_freq": total_freq,
                "source_total_alcance": total_alcance,
                "source_nps": proxy_nps,
                "source_protagonismo": proxy_protag,
                "indicator_group": "imagem" if key in IMAGE_INDICATORS else "exposicao",
            })

        if padrao:
            out.append({
                "scope": "sources",
                "candidate_type": "source_pattern",
                "empresa": company_payload["empresa_analisada"],
                "empresa_display": company_payload["empresa_display"],
                "tipo_empresa": company_payload["tipo_empresa"],
                "periodo": company_payload.get("periodo"),
                "periodo_referencia": company_payload.get("periodo_referencia"),
                "source_rank": order,
                "fonte": fonte,
                "midia": item.get("midia"),
                "tier": tier,
                "indicator": "source_pattern",
                "label": "Padrão do veículo",
                "tags": padrao.get("tags", []) or [],
                "leituras": padrao.get("leituras", []) or padrao.get("leituras_gerais", []) or [],
                "alertas": padrao.get("alertas", []) or [],
                "oportunidades": padrao.get("oportunidades", []) or [],
                "source_total_freq": total_freq,
                "source_total_alcance": total_alcance,
                "source_nps": proxy_nps,
                "source_protagonismo": proxy_protag,
            })

    return out


def extract_daily_candidates(company_payload: Dict[str, Any], *, top_n: int = 10) -> List[Dict[str, Any]]:
    daily = company_payload.get("daily") or {}
    dias = daily.get("dias") or []

    ordered = sorted(
        dias,
        key=lambda d: (
            abs(_safe_float(d.get("nps_contrib_dia")) or 0.0),
            abs(_safe_float(d.get("z_score_alcance")) or 0.0),
            abs(_safe_float(d.get("alcance")) or 0.0),
        ),
        reverse=True,
    )

    out: List[Dict[str, Any]] = []
    for item in ordered[:top_n]:
        padrao = item.get("padrao_midia_dia") or {}
        out.append({
            "scope": "daily",
            "candidate_type": "day",
            "empresa": company_payload["empresa_analisada"],
            "empresa_display": company_payload["empresa_display"],
            "tipo_empresa": company_payload["tipo_empresa"],
            "periodo": company_payload.get("periodo"),
            "periodo_referencia": company_payload.get("periodo_referencia"),
            "dia": _format_date(item.get("dia")),
            "indicator": "nps_contrib_dia",
            "label": "Contribuição do dia",
            "value": item.get("nps_contrib_dia"),
            "value_text": None,
            "nps_score_dia": item.get("nps_score_dia"),
            "protagonism_score_dia": item.get("protagonism_score_dia"),
            "alcance": item.get("alcance"),
            "zscore": item.get("z_score_alcance"),
            "promotores": item.get("Promotores"),
            "detratores": item.get("Detratores"),
            "inocuos": item.get("Inócuos"),
            "tags": padrao.get("tags", []) or [],
            "leituras": padrao.get("leituras", []) or [],
            "alertas": padrao.get("alertas", []) or [],
            "driver": "; ".join(padrao.get("leituras", []) or []),
        })
    return out


def extract_topic_candidates(
    company_payload: Dict[str, Any],
    *,
    top_period_n: int = 10,
    top_days_n: int = 7,
    top_topics_per_day: int = 3,
) -> List[Dict[str, Any]]:
    assunto = company_payload.get("assunto") or {}
    out: List[Dict[str, Any]] = []

    for order, item in enumerate((assunto.get("top_assuntos_periodo") or [])[:top_period_n], start=1):
        contrib = item.get("nps_contrib_assunto_especifico") or item.get("contribuicao") or {}
        nps_periodo = item.get("nps_score_periodo") or {}
        out.append({
            "scope": "topics",
            "candidate_type": "topic_period",
            "empresa": company_payload["empresa_analisada"],
            "empresa_display": company_payload["empresa_display"],
            "tipo_empresa": company_payload["tipo_empresa"],
            "periodo": assunto.get("periodo") or company_payload.get("periodo"),
            "periodo_referencia": assunto.get("periodo_referencia") or company_payload.get("periodo_referencia"),
            "periodo_analitico": assunto.get("periodo_analitico") or company_payload.get("periodo"),
            "periodo_analitico_referencia": assunto.get("periodo_analitico_referencia") or company_payload.get("periodo_referencia"),
            "rank": order,
            "assunto_especifico": item.get("assunto_especifico"),
            "indicator": "nps_contrib_assunto_especifico",
            "label": "Contribuição do assunto no período",
            "value": contrib.get("valor"),
            "value_text": None,
            "difference_unit": contrib.get("unidade"),
            "nps_score_periodo": nps_periodo.get("valor"),
            "nps_score_periodo_unit": nps_periodo.get("unidade"),
            "total_assunto_especifico": item.get("total_assunto_especifico"),
            "denom_total": item.get("denom_total"),
        })

    dias = assunto.get("dias") or []
    ordered_days = sorted(
        dias,
        key=lambda d: sum(abs(_safe_float((a.get("nps_contrib_assunto_especifico") or {}).get("valor")) or 0.0) for a in (d.get("assuntos") or [])[:top_topics_per_day]),
        reverse=True,
    )

    for item in ordered_days[:top_days_n]:
        dia = _format_date(item.get("dia"))
        assuntos = item.get("assuntos") or []
        for order, assunto_item in enumerate(assuntos[:top_topics_per_day], start=1):
            contrib = assunto_item.get("nps_contrib_assunto_especifico") or assunto_item.get("contribuicao") or {}
            nps_periodo = assunto_item.get("nps_score_periodo") or {}
            out.append({
                "scope": "topics",
                "candidate_type": "topic_day",
                "empresa": company_payload["empresa_analisada"],
                "empresa_display": company_payload["empresa_display"],
                "tipo_empresa": company_payload["tipo_empresa"],
                "periodo": assunto.get("periodo") or company_payload.get("periodo"),
                "periodo_referencia": assunto.get("periodo_referencia") or company_payload.get("periodo_referencia"),
                "periodo_analitico": assunto.get("periodo_analitico") or company_payload.get("periodo"),
                "periodo_analitico_referencia": assunto.get("periodo_analitico_referencia") or company_payload.get("periodo_referencia"),
                "dia": dia,
                "rank": order,
                "assunto_especifico": assunto_item.get("assunto_especifico"),
                "indicator": "nps_contrib_assunto_especifico",
                "label": "Contribuição do assunto no dia",
                "value": contrib.get("valor"),
                "value_text": None,
                "difference_unit": contrib.get("unidade"),
                "nps_score_periodo": nps_periodo.get("valor"),
                "nps_score_periodo_unit": nps_periodo.get("unidade"),
                "total_assunto_especifico": assunto_item.get("total_assunto_especifico"),
                "denom_total": assunto_item.get("denom_total"),
            })

    return out


# =========================================================
# SCORE E SELEÇÃO
# =========================================================

def _tier_bonus_value(tier: Any) -> float:
    if tier is None:
        return 0.0
    return float(TIER_BONUS.get(_normalize_text(tier), 0.0))


def score_candidate(candidate: Dict[str, Any]) -> float:
    score = 0.0
    scope = candidate.get("scope")
    ctype = candidate.get("candidate_type")
    indicator = candidate.get("indicator")

    value_abs = abs(_safe_float(candidate.get("value")) or 0.0)
    score += value_abs * (1.0 if scope != "topics" else 6.0)
    score += abs(_safe_float(candidate.get("difference")) or 0.0) * 1.5
    score += abs(_safe_float(candidate.get("difference_hist")) or 0.0) * 1.5
    score += abs(_safe_float(candidate.get("zscore")) or 0.0) * 6.0

    if indicator in IMAGE_INDICATORS:
        score += 35
    elif indicator in EXPOSURE_INDICATORS:
        score += 18

    for tag in candidate.get("tags", []) or []:
        score += BASE_TAG_SCORES.get(tag, 0)

    if ctype == "period_pattern":
        score += 25
    if ctype == "source_pattern":
        score += 18
    if ctype == "day":
        score += 20
    if ctype == "topic_period":
        score += 30
    if ctype == "topic_day":
        score += 16

    if scope == "sources":
        score += _tier_bonus_value(candidate.get("tier"))
        score += min((_safe_float(candidate.get("source_total_freq")) or 0.0) * 0.5, 20)
        alcance = _safe_float(candidate.get("source_total_alcance")) or 0.0
        if alcance >= 1_000_000:
            score += 18
        elif alcance >= 300_000:
            score += 10
        elif alcance >= 100_000:
            score += 5

    if scope == "topics":
        contrib = _safe_float(candidate.get("value")) or 0.0
        freq = _safe_float(candidate.get("total_assunto_especifico")) or 0.0
        share = _topic_share(candidate.get("total_assunto_especifico"), candidate.get("denom_total"))
        band_bonus = _theme_quality_bonus(candidate.get("nps_score_periodo"), contrib)
        rank = _safe_float(candidate.get("rank")) or 99.0

        score += min(freq * 0.20, 12.0)
        score += min(share * 100.0, 25.0)
        score += band_bonus

        if contrib > 0:
            score += 4.0
        elif contrib < 0:
            score += 8.0

        if freq <= 2 and share < 0.05:
            score -= 10.0
        elif freq <= 4 and share < 0.08:
            score -= 4.0

        if ctype == "topic_day":
            score += min(freq * 0.4, 6.0)
            if share >= 0.25:
                score += 10.0
            elif share >= 0.15:
                score += 6.0
            if rank == 1:
                score += 4.0
        else:
            score += min(freq * 0.12, 10.0)
            if share >= 0.20:
                score += 12.0
            elif share >= 0.10:
                score += 7.0
            if rank <= 3:
                score += 6.0

    return round(score, 4)


def rank_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    scored = []
    for c in candidates:
        item = dict(c)
        item["priority_score"] = score_candidate(item)
        scored.append(item)
    return sorted(scored, key=lambda x: x["priority_score"], reverse=True)


def _distinct_by(candidates: List[Dict[str, Any]], max_items: int, keys: Tuple[str, ...]) -> List[Dict[str, Any]]:
    out = []
    seen = set()
    for item in candidates:
        sig = tuple(item.get(k) for k in keys)
        if sig in seen:
            continue
        seen.add(sig)
        out.append(item)
        if len(out) >= max_items:
            break
    return out


def select_stats_editorial(candidates: List[Dict[str, Any]], *, total_max: int = 8) -> List[Dict[str, Any]]:
    ranked = rank_candidates(candidates)
    metrics = [c for c in ranked if c.get("candidate_type") == "metric_snapshot"]
    patterns = [c for c in ranked if c.get("candidate_type") == "period_pattern"]
    image = [c for c in metrics if c.get("indicator") in IMAGE_INDICATORS]
    exposure = [c for c in metrics if c.get("indicator") in EXPOSURE_INDICATORS]
    out = []
    out.extend(_distinct_by(patterns, 1, ("candidate_type",)))
    out.extend(_distinct_by(image, 3, ("indicator",)))
    out.extend(_distinct_by(exposure, 4, ("indicator",)))
    used = {json.dumps(x, ensure_ascii=False, default=safe_json, sort_keys=True) for x in out}
    for item in ranked:
        key = json.dumps(item, ensure_ascii=False, default=safe_json, sort_keys=True)
        if key in used:
            continue
        out.append(item)
        used.add(key)
        if len(out) >= total_max:
            break
    return out[:total_max]


def select_sources_editorial(candidates: List[Dict[str, Any]], *, total_max: int = 8) -> List[Dict[str, Any]]:
    ranked = rank_candidates(candidates)
    patterns = [c for c in ranked if c.get("candidate_type") == "source_pattern"]
    metrics = [c for c in ranked if c.get("candidate_type") == "source_metric"]
    image = [c for c in metrics if c.get("indicator") in IMAGE_INDICATORS]
    structural = [c for c in metrics if c.get("indicator") in {"impacto_total", "publicacoes_totais", "alcance", "frequencia"}]
    out = []
    out.extend(_distinct_by(patterns, 2, ("fonte", "candidate_type")))
    out.extend(_distinct_by(image, 3, ("fonte", "indicator")))
    out.extend(_distinct_by(structural, 3, ("fonte", "indicator")))
    used = {json.dumps(x, ensure_ascii=False, default=safe_json, sort_keys=True) for x in out}
    for item in ranked:
        key = json.dumps(item, ensure_ascii=False, default=safe_json, sort_keys=True)
        if key in used:
            continue
        out.append(item)
        used.add(key)
        if len(out) >= total_max:
            break
    return out[:total_max]


def select_daily_editorial(candidates: List[Dict[str, Any]], *, total_max: int = 5) -> List[Dict[str, Any]]:
    ranked = rank_candidates(candidates)
    return _distinct_by(ranked, total_max, ("dia",))


def select_topics_editorial(candidates: List[Dict[str, Any]], *, total_max: int = 8) -> List[Dict[str, Any]]:
    ranked = rank_candidates(candidates)
    period_topics = [c for c in ranked if c.get("candidate_type") == "topic_period"]
    day_topics = [c for c in ranked if c.get("candidate_type") == "topic_day"]
    out = []
    out.extend(_distinct_by(period_topics, 4, ("assunto_especifico", "candidate_type")))
    out.extend(_distinct_by(day_topics, 4, ("dia", "assunto_especifico", "candidate_type")))
    used = {json.dumps(x, ensure_ascii=False, default=safe_json, sort_keys=True) for x in out}
    for item in ranked:
        key = json.dumps(item, ensure_ascii=False, default=safe_json, sort_keys=True)
        if key in used:
            continue
        out.append(item)
        used.add(key)
        if len(out) >= total_max:
            break
    return out[:total_max]


# =========================================================
# BASE HIGHLIGHTS DETERMINÍSTICOS
# =========================================================

def render_stats_base(candidate: Dict[str, Any]) -> Optional[str]:
    empresa = candidate["empresa_display"]
    periodo = candidate.get("periodo") or "período"
    periodo_ref = _format_period_reference_pt(candidate.get("periodo_referencia")) or periodo

    if candidate.get("candidate_type") == "period_pattern":
        leituras = "; ".join(candidate.get("leituras", [])[:2])
        oportunidades = "; ".join(candidate.get("oportunidades", [])[:1])
        alertas = "; ".join(candidate.get("alertas", [])[:1])
        parts = [f"No {periodo_ref}, o padrão de mídia de {empresa} no {periodo} indicou {leituras.lower() if leituras else 'um padrão relevante de exposição'}"]
        if alertas:
            parts.append(f"com alerta de {alertas.lower()}")
        if oportunidades:
            parts.append(f"e oportunidade de {oportunidades.lower()}")
        return ", ".join(parts) + "."

    if candidate.get("candidate_type") != "metric_snapshot":
        return None

    label = candidate["label"]
    value = _format_metric_value(candidate["indicator"], candidate.get("value"), candidate.get("value_text"))
    diff_prev = _format_diff(candidate.get("difference"), candidate.get("difference_unit"))
    diff_hist = _format_diff(candidate.get("difference_hist"), candidate.get("difference_hist_unit"))
    driver = candidate.get("driver")

    text = f"No {periodo_ref}, {empresa} registrou {label} de {value}"
    if diff_prev:
        text += f", com variação de {diff_prev} versus o período anterior"
    if diff_hist:
        text += f" e de {diff_hist} versus a média histórica"
    if driver:
        text += f", indicando {driver.lower()}"
    return text + "."


def render_sources_base(candidate: Dict[str, Any]) -> Optional[str]:
    empresa = candidate["empresa_display"]
    periodo_ref = _format_period_reference_pt(candidate.get("periodo_referencia")) or candidate.get("periodo") or "período"
    fonte = candidate.get("fonte")
    tier = candidate.get("tier")
    tier_text = f" ({tier})" if tier else ""

    if candidate.get("candidate_type") == "source_pattern":
        leituras = "; ".join(candidate.get("leituras", [])[:2])
        return f"No {periodo_ref}, {fonte}{tier_text} apresentou um padrão editorial relevante na cobertura de {empresa}: {leituras or 'sem leitura textual disponível'}, com frequência de {_format_metric_value('frequencia', candidate.get('source_total_freq'))} e impacto de {_format_metric_value('impacto_total', candidate.get('source_total_alcance'))}."

    if candidate.get("candidate_type") != "source_metric":
        return None

    label = candidate["label"].lower()
    value = _format_metric_value(candidate["indicator"], candidate.get("value"), candidate.get("value_text"))
    diff_prev = _format_diff(candidate.get("difference"), candidate.get("difference_unit"))
    diff_hist = _format_diff(candidate.get("difference_hist"), candidate.get("difference_hist_unit"))
    driver = candidate.get("driver")
    text = f"No {periodo_ref}, o veículo {fonte}{tier_text} registrou {label} de {value} na cobertura de {empresa}"
    if diff_prev:
        text += f", variando {diff_prev} versus o período anterior"
    if diff_hist:
        text += f" e {diff_hist} versus sua média histórica"
    if driver:
        text += f", sugerindo {driver.lower()}"
    return text + "."


def render_daily_base(candidate: Dict[str, Any]) -> Optional[str]:
    empresa = candidate["empresa_display"]
    periodo_ref = _format_period_reference_pt(candidate.get("periodo_referencia")) or candidate.get("periodo") or "período"
    dia = _format_day_pt(candidate.get("dia"))
    if not dia:
        return None
    contrib = _format_diff(candidate.get("value"), "contrib")
    nps = _format_metric_value("nps_score_dia", candidate.get("nps_score_dia"))
    protagonismo = _format_metric_value("protagonism_score_dia", candidate.get("protagonism_score_dia"))
    alcance = _format_metric_value("alcance", candidate.get("alcance"))
    driver = "; ".join(candidate.get("leituras", [])[:2])
    return (
        f"No recorte diário de {periodo_ref}, o dia {dia} foi um dos mais relevantes para {empresa}, com contribuição de {contrib} para o NPS, NPS diário de {nps}, protagonismo de {protagonismo}, alcance de {alcance} e leitura de que {driver.lower() if driver else 'houve um padrão estatístico relevante de exposição'}."
    )


def render_topics_base(candidate: Dict[str, Any]) -> Optional[str]:
    empresa = candidate["empresa_display"]
    periodo_ref = _format_period_reference_pt(candidate.get("periodo_analitico_referencia")) or _format_period_reference_pt(candidate.get("periodo_referencia")) or candidate.get("periodo") or "período"
    assunto = candidate.get("assunto_especifico")
    contrib = _format_diff(candidate.get("value"), candidate.get("difference_unit"))
    freq = _format_metric_value("total_assunto_especifico", candidate.get("total_assunto_especifico"))
    denom = _format_metric_value("denom_total", candidate.get("denom_total"))
    nps = _format_number_br(_safe_float(candidate.get("nps_score_periodo")), 2)
    if candidate.get("candidate_type") == "topic_period":
        return (
            f"No {periodo_ref}, o assunto '{assunto}' esteve entre os mais influentes para {empresa}, com contribuição de {contrib} para o NPS do período, frequência de {freq} menções em um universo de {denom} e NPS associado de {nps}%."
        )
    if candidate.get("candidate_type") == "topic_day":
        dia = _format_day_pt(candidate.get("dia"))
        return (
            f"No dia {dia} do período {periodo_ref}, o assunto '{assunto}' foi um dos principais vetores de repercussão de {empresa}, com contribuição de {contrib}, {freq} menções em um universo de {denom} e NPS do dia associado de {nps}%."
        )
    return None


def build_base_highlights(scope: str, candidates: List[Dict[str, Any]], max_items: int) -> List[str]:
    renderer = {
        "stats": render_stats_base,
        "sources": render_sources_base,
        "daily": render_daily_base,
        "topics": render_topics_base,
    }[scope]
    out = []
    for item in candidates:
        text = renderer(item)
        if text:
            out.append(text)
        if len(out) >= max_items:
            break
    return out


# =========================================================
# PAYLOADS POR ESCOPO
# =========================================================

def compress_candidates(candidates: List[Dict[str, Any]], max_items: int = 12) -> List[Dict[str, Any]]:
    fields = {
        "scope", "candidate_type", "empresa", "empresa_display", "tipo_empresa",
        "periodo", "periodo_referencia", "periodo_analitico", "periodo_analitico_referencia",
        "indicator", "label", "value", "value_text", "difference", "difference_unit",
        "difference_hist", "difference_hist_unit", "reference", "reference_hist", "zscore",
        "driver", "tags", "leituras", "alertas", "oportunidades", "fonte", "midia", "tier",
        "source_rank", "source_total_freq", "source_total_alcance", "source_nps", "source_protagonismo",
        "dia", "nps_score_dia", "protagonism_score_dia", "alcance", "promotores", "detratores",
        "inocuos", "assunto_especifico", "rank", "nps_score_periodo", "nps_score_periodo_unit",
        "total_assunto_especifico", "denom_total", "priority_score", "faixa_valor"
    }
    compact = []
    for item in candidates[:max_items]:
        compact.append({k: v for k, v in item.items() if k in fields})
    return compact


def build_company_scope_payloads(
    company_payload: Dict[str, Any],
    *,
    selected_sources: Optional[Sequence[str]] = None,
    stats_total_max: int = 8,
    sources_total_max: int = 8,
    daily_total_max: int = 5,
    topics_total_max: int = 8,
) -> Dict[str, Any]:
    stats_candidates = extract_stats_candidates(company_payload)
    source_candidates = extract_source_candidates(company_payload, selected_sources=selected_sources)
    daily_candidates = extract_daily_candidates(company_payload)
    topic_candidates = extract_topic_candidates(company_payload)

    stats_selected = select_stats_editorial(stats_candidates, total_max=stats_total_max)
    source_selected = select_sources_editorial(source_candidates, total_max=sources_total_max)
    daily_selected = select_daily_editorial(daily_candidates, total_max=daily_total_max)
    topic_selected = select_topics_editorial(topic_candidates, total_max=topics_total_max)

    meta = {
        "empresa": company_payload["empresa_analisada"],
        "empresa_display": company_payload["empresa_display"],
        "tipo_empresa": company_payload["tipo_empresa"],
        "periodo": company_payload.get("periodo"),
        "periodo_referencia": company_payload.get("periodo_referencia"),
        "periodo_referencia_display": _format_period_reference_pt(company_payload.get("periodo_referencia")),
    }

    return {
        "meta": meta,
        "stats": {
            "scope": "stats",
            "highlight_candidates": compress_candidates(stats_selected, stats_total_max),
            "base_highlights": build_base_highlights("stats", stats_selected, stats_total_max),
        },
        "sources": {
            "scope": "sources",
            "highlight_candidates": compress_candidates(source_selected, sources_total_max),
            "base_highlights": build_base_highlights("sources", source_selected, sources_total_max),
        },
        "daily": {
            "scope": "daily",
            "highlight_candidates": compress_candidates(daily_selected, daily_total_max),
            "base_highlights": build_base_highlights("daily", daily_selected, daily_total_max),
        },
        "topics": {
            "scope": "topics",
            "highlight_candidates": compress_candidates(topic_selected, topics_total_max),
            "base_highlights": build_base_highlights("topics", topic_selected, topics_total_max),
        },
    }



# =========================================================
# EVIDÊNCIA CRUZADA PARA SÍNTESE FINAL
# =========================================================

def _candidate_text_blob(candidate: Dict[str, Any]) -> str:
    parts = [
        candidate.get("label"),
        candidate.get("driver"),
        candidate.get("assunto_especifico"),
        candidate.get("fonte"),
        candidate.get("indicator"),
        " ".join(candidate.get("tags", []) or []),
        " ".join(candidate.get("leituras", []) or []),
    ]
    return " ".join(str(x or "") for x in parts).lower()


def _is_positive_image_candidate(candidate: Dict[str, Any]) -> bool:
    blob = _candidate_text_blob(candidate)
    indicator = candidate.get("indicator")
    value = _safe_float(candidate.get("value"))
    diff = _safe_float(candidate.get("difference"))
    diff_hist = _safe_float(candidate.get("difference_hist"))
    tags = set(candidate.get("tags", []) or [])

    if candidate.get("scope") == "daily":
        return (
            (value is not None and value > 0)
            and (
                "predominio_promotor" in tags
                or "dia_com_predominio_promotor" in tags
                or "nps_excelente" in tags
                or "nps_otimo" in tags
                or (candidate.get("nps_score_dia") is not None and (_safe_float(candidate.get("nps_score_dia")) or 0) > 35)
            )
        )

    if candidate.get("scope") == "topics":
        topic_nps = _safe_float(candidate.get("nps_score_periodo"))
        share = _topic_share(candidate.get("total_assunto_especifico"), candidate.get("denom_total"))
        freq = _safe_float(candidate.get("total_assunto_especifico")) or 0.0
        return (
            (value is not None and value > 0)
            and (topic_nps is not None and topic_nps >= 35)
            and (freq >= 3 or share >= 0.08)
        )

    if indicator in IMAGE_INDICATORS:
        if value is not None and value >= 35:
            return True
        if (diff is not None and diff > 0) or (diff_hist is not None and diff_hist > 0):
            return True
        if {"nps_otimo", "nps_excelente", "melhora_relevante", "predominio_promotor"} & tags:
            return True

    return any(term in blob for term in [
        "qualidade reputacional muito favorável",
        "predomínio de exposição promotora",
        "cobertura combinou favorabilidade reputacional",
        "alta chance de lembrança",
    ])


def _is_negative_image_candidate(candidate: Dict[str, Any]) -> bool:
    blob = _candidate_text_blob(candidate)
    indicator = candidate.get("indicator")
    value = _safe_float(candidate.get("value"))
    diff = _safe_float(candidate.get("difference"))
    diff_hist = _safe_float(candidate.get("difference_hist"))
    tags = set(candidate.get("tags", []) or [])

    if candidate.get("scope") == "daily":
        return (
            (value is not None and value < 0)
            or "predominio_detrator" in tags
            or "dia_com_predominio_detrator" in tags
        )

    if candidate.get("scope") == "topics":
        topic_nps = _safe_float(candidate.get("nps_score_periodo"))
        share = _topic_share(candidate.get("total_assunto_especifico"), candidate.get("denom_total"))
        freq = _safe_float(candidate.get("total_assunto_especifico")) or 0.0
        return (
            (value is not None and value < 0)
            and ((topic_nps is None) or topic_nps < 35 or freq >= 2 or share >= 0.05)
        )

    if indicator in IMAGE_INDICATORS:
        if value is not None and value < 0:
            return True
        if (diff is not None and diff < 0) or (diff_hist is not None and diff_hist < 0):
            return True
        if {"piora_relevante", "queda_relevante", "predominio_detrator"} & tags:
            return True

    return any(term in blob for term in [
        "pressão reputacional",
        "predomínio de exposição detratora",
        "deterioração reputacional",
        "risco reputacional",
    ])


def _is_exposure_scale_candidate(candidate: Dict[str, Any]) -> bool:
    indicator = candidate.get("indicator")
    if indicator in {"impacto_total", "impacto_promotor", "impacto_detrator", "impacto_inocuo",
                     "publicacoes_totais", "publicacoes_promotoras", "publicacoes_detratoras",
                     "publicacoes_inocuas", "alcance", "frequencia"}:
        return True
    if candidate.get("scope") == "sources":
        return indicator in {"impacto_total", "publicacoes_totais", "alcance", "frequencia"}
    return False


def _select_top_cross_items(candidates: List[Dict[str, Any]], n: int, unique_keys: Tuple[str, ...]) -> List[Dict[str, Any]]:
    ranked = rank_candidates(candidates)
    return _distinct_by(ranked, n, unique_keys)


def build_cross_evidence_bundle(
    *,
    meta: Dict[str, Any],
    stats_candidates: List[Dict[str, Any]],
    sources_candidates: List[Dict[str, Any]],
    daily_candidates: List[Dict[str, Any]],
    topics_candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    positive_stats = [c for c in stats_candidates if _is_positive_image_candidate(c)]
    negative_stats = [c for c in stats_candidates if _is_negative_image_candidate(c)]
    positive_days = [c for c in daily_candidates if _is_positive_image_candidate(c)]
    negative_days = [c for c in daily_candidates if _is_negative_image_candidate(c)]
    positive_topics = [c for c in topics_candidates if _is_positive_image_candidate(c)]
    negative_topics = [c for c in topics_candidates if _is_negative_image_candidate(c)]

    support_is_cross_validated = bool(positive_stats and positive_days and positive_topics)
    pressure_is_cross_validated = bool(negative_stats and negative_days and negative_topics)

    support_stats = _select_top_cross_items(positive_stats, 3, ("indicator", "candidate_type"))
    support_days = _select_top_cross_items(positive_days, 3, ("dia",))
    support_topics = _select_top_cross_items(positive_topics, 4, ("assunto_especifico", "candidate_type"))
    pressure_stats = _select_top_cross_items(negative_stats, 3, ("indicator", "candidate_type"))
    pressure_days = _select_top_cross_items(negative_days, 3, ("dia",))
    pressure_topics = _select_top_cross_items(negative_topics, 4, ("assunto_especifico", "candidate_type"))

    source_image = [
        c for c in sources_candidates
        if c.get("indicator") in IMAGE_INDICATORS or c.get("candidate_type") == "source_pattern"
    ]
    source_scale = [c for c in sources_candidates if _is_exposure_scale_candidate(c)]

    source_image_selected = _select_top_cross_items(source_image, 4, ("fonte", "indicator", "candidate_type"))
    source_scale_selected = _select_top_cross_items(source_scale, 4, ("fonte", "indicator", "candidate_type"))

    period_topics = [c for c in topics_candidates if c.get("candidate_type") == "topic_period"]
    day_topics = [c for c in topics_candidates if c.get("candidate_type") == "topic_day"]

    return {
        "empresa": meta.get("empresa"),
        "empresa_display": meta.get("empresa_display"),
        "periodo": meta.get("periodo"),
        "periodo_referencia": meta.get("periodo_referencia"),
        "periodo_referencia_display": meta.get("periodo_referencia_display"),
        "support_is_cross_validated": support_is_cross_validated,
        "pressure_is_cross_validated": pressure_is_cross_validated,
        "support_evidence": {
            "stats": compress_candidates(support_stats, max_items=3),
            "daily": compress_candidates(support_days, max_items=3),
            "topics": compress_candidates(support_topics, max_items=4),
        },
        "pressure_evidence": {
            "stats": compress_candidates(pressure_stats, max_items=3),
            "daily": compress_candidates(pressure_days, max_items=3),
            "topics": compress_candidates(pressure_topics, max_items=4),
        },
        "vehicle_evidence": {
            "image_vehicles": compress_candidates(source_image_selected, max_items=4),
            "scale_vehicles": compress_candidates(source_scale_selected, max_items=4),
        },
        "topic_frame": {
            "period_topics": compress_candidates(_select_top_cross_items(period_topics, 5, ("assunto_especifico", "candidate_type")), max_items=5),
            "day_topics": compress_candidates(_select_top_cross_items(day_topics, 5, ("dia", "assunto_especifico", "candidate_type")), max_items=5),
        },
    }

# =========================================================
# PROMPTS
# =========================================================

def build_scope_prompts(
    *,
    scope_payload: Dict[str, Any],
    meta: Dict[str, Any],
    competitors: Optional[Sequence[str]] = None,
    max_highlights: int = 6,
) -> Dict[str, str]:
    empresa = meta["empresa_display"]
    periodo = meta.get("periodo") or "período"
    periodo_ref = meta.get("periodo_referencia_display") or _format_period_reference_pt(meta.get("periodo_referencia")) or periodo
    tipo_empresa = meta.get("tipo_empresa") or "empresa"
    competitor_text = ", ".join(competitors or []) if competitors else "não informado"

    scope = scope_payload["scope"]
    instruction = {
        "stats": (
            "Foque nos big numbers. NPS e Protagonismo são os indicadores centrais de imagem; "
            "impacto e publicações são indicadores de exposição. Sempre destaque o valor do período, a comparação com o período anterior, a comparação com a média histórica e a leitura determinística. "
            "Use também o padrão geral do período quando disponível."
        ),
        "sources": (
            "Foque em como os veículos estão expondo a empresa. Dê mais peso editorial a Tier 1, veículos de maior impacto, maior frequência e maior alcance. "
            "Não valorize demais crescimento relativo isolado em veículo pouco relevante. Explique o padrão da cobertura do veículo e a comparação com o histórico."
        ),
        "daily": (
            "Foque nos dias mais relevantes do período. Use contribuição para o NPS, NPS diário, protagonismo diário, alcance, z-score de alcance e o resumo de padrão do dia. "
            "Diferencie dia que elevou imagem de dia que pressionou imagem."
        ),
        "topics": (
            "Foque nos assuntos mais influentes do período e nos principais assuntos dos dias-chave. "
            "Use contribuição para o NPS, frequência do assunto, peso no universo do período e NPS associado. "
            "Priorize assuntos que realmente tenham massa crítica no período, e não apenas contribuição alta com baixa frequência. "
            "Diferencie assuntos estruturais do período de assuntos concentrados em dias específicos, e diferencie tópicos que sustentaram imagem de tópicos que só ampliaram a exposição."
        ),
    }[scope]

    system_prompt = f"""
Você é um analista sênior de reputação e mídia.

Sua tarefa é escrever highlights executivos sobre {empresa}, classificada como {tipo_empresa}, no recorte de {periodo} ({periodo_ref}).

CONTEXTO
- Empresa cliente: {empresa}
- Concorrentes relevantes: {competitor_text}
- Guia de NPS: {FAIXA_NPS_GUIDE}

OBJETIVO
Gerar highlights analíticos, objetivos e densos, preservando números, unidades e comparações.

REGRAS OBRIGATÓRIAS
1. Todo highlight deve mencionar explicitamente {empresa} e o período {periodo_ref} ou o recorte temporal correspondente.
2. Todo highlight deve usar pelo menos um dado quantitativo explícito.
3. Não invente fatos, causalidades externas ou inferências sem suporte.
4. Escreva em tom executivo, com leitura analítica, não apenas descritiva.
5. Gere no máximo {max_highlights} highlights.
6. Cada highlight deve ter uma frase.
7. Evite repetição de números idênticos e evite dizer a mesma ideia duas vezes.

INSTRUÇÃO ESPECÍFICA DO ESCOPO
{instruction}

FORMATO
- Retorne apenas uma lista numerada.
- Sem introdução.
- Sem conclusão.
""".strip()

    user_prompt = f"""
BASE_HIGHLIGHTS:
{json.dumps(scope_payload.get('base_highlights', []), ensure_ascii=False, indent=2, default=safe_json)}

CANDIDATES:
{json.dumps(scope_payload.get('highlight_candidates', []), ensure_ascii=False, indent=2, default=safe_json)}
""".strip()

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


def build_final_synthesis_prompts(
    *,
    meta: Dict[str, Any],
    competitors: Optional[Sequence[str]],
    stats_highlights: List[str],
    sources_highlights: List[str],
    daily_highlights: List[str],
    topics_highlights: List[str],
    cross_evidence: Dict[str, Any],
    max_highlights: int = 8,
) -> Dict[str, str]:
    empresa = meta["empresa_display"]
    periodo = meta.get("periodo") or "período"
    periodo_ref = meta.get("periodo_referencia_display") or _format_period_reference_pt(meta.get("periodo_referencia")) or periodo
    competitor_text = ", ".join(competitors or []) if competitors else "não informado"

    support_validated = cross_evidence.get("support_is_cross_validated", False)
    pressure_validated = cross_evidence.get("pressure_is_cross_validated", False)

    support_rule = (
        "Há evidência cruzada suficiente em stats + topics + daily para afirmar o que sustentou a imagem."
        if support_validated
        else "NÃO há evidência cruzada suficiente em stats + topics + daily para afirmar de forma categórica o que sustentou a imagem; trate sinais positivos apenas como indícios, nunca como vetor comprovado de sustentação."
    )

    pressure_rule = (
        "Há evidência cruzada suficiente em stats + topics + daily para afirmar o que pressionou a imagem."
        if pressure_validated
        else "NÃO há evidência cruzada suficiente em stats + topics + daily para afirmar de forma categórica o que pressionou a imagem; trate sinais negativos apenas como indícios, nunca como vetor comprovado de pressão estrutural."
    )

    system_prompt = f"""
Você é um analista sênior de reputação e mídia.

Sua tarefa é produzir uma síntese executiva estruturada sobre {empresa} no recorte de {periodo} ({periodo_ref}).

CONTEXTO
- Empresa foco: {empresa}
- Concorrentes relevantes: {competitor_text}
- Guia de NPS: {FAIXA_NPS_GUIDE}

OBJETIVO
Gerar uma leitura integrada e causal da cobertura, explicando:
- como está a imagem da marca,
- o que sustentou essa imagem,
- o que pressionou,
- qual foi o papel dos veículos,
- e quais temas/dias explicam o resultado.

REGRAS DE VALIDAÇÃO CRUZADA
1. Só use a expressão "sustentou a imagem", "vetor de sustentação" ou equivalentes quando houver evidência cruzada consistente em stats + topics + daily.
2. Só use a expressão "pressionou a imagem", "vetor de pressão" ou equivalentes quando houver evidência cruzada consistente em stats + topics + daily.
3. Quando não houver evidência cruzada suficiente, use formulações como "sinal positivo isolado", "indício pontual", "ganho de escala" ou "pressão episódica", sem tratá-los como vetores comprovados.
4. Veículos sozinhos não comprovam sustentação de imagem; eles podem reforçar, distribuir ou escalar a narrativa, mas a sustentação precisa ser confirmada nas camadas de imagem, temas e repercussão diária.
5. Diferencie explicitamente qualidade de imagem versus escala de exposição.
6. Diferencie estrutural versus episódico.

REGRAS DESTA RODADA
- {support_rule}
- {pressure_rule}

ESTRUTURA OBRIGATÓRIA DO TEXTO
1. Quadro geral da imagem
2. Vetores que sustentaram
3. Vetores que pressionaram
4. Papel dos veículos
5. Papel dos assuntos e dias

DETALHAMENTO DE CADA BLOCO
1. QUADRO GERAL DA IMAGEM
- Descreva o estado da reputação usando NPS e Protagonismo
- Classifique a imagem com base na régua de NPS
- Diferencie claramente imagem vs exposição

2. VETORES QUE SUSTENTARAM
- Só afirme sustentação quando houver evidência cruzada
- Conecte stats, topics e daily
- Se não houver cruzamento suficiente, diga explicitamente que houve sinais positivos, mas não sustentação comprovada

3. VETORES QUE PRESSIONARAM
- Só afirme pressão quando houver evidência cruzada
- Diferencie pressão estrutural de episódio isolado
- Se não houver cruzamento suficiente, diga explicitamente que houve sinais de atenção, mas não pressão estrutural comprovada

4. PAPEL DOS VEÍCULOS
- Explique quais veículos ajudaram a construir percepção e quais apenas deram escala
- Dê mais peso editorial a Tier 1, frequência e alcance
- Diferencie veículos que combinaram escala e favorabilidade de veículos que só ampliaram o volume

5. PAPEL DOS ASSUNTOS E DOS DIAS
- Explique quais assuntos estruturaram a narrativa do período
- Explique quais dias concentraram impacto
- Diferencie agenda estrutural de picos pontuais

REGRAS FINAIS
1. Sempre citar "{empresa}" e "{periodo_ref}"
2. Usar números explicitamente
3. Não inventar relações externas
4. Produzir texto corrido, com 5 parágrafos curtos, um para cada bloco da estrutura
5. Não usar lista numerada, bullets ou títulos soltos
6. Não repetir a mesma evidência em mais de um bloco sem acrescentar interpretação nova
""".strip()

    user_prompt = f"""
Gere a síntese executiva para {empresa} no {periodo_ref}.

HIGHLIGHTS_STATS:
{json.dumps(stats_highlights, ensure_ascii=False, indent=2, default=safe_json)}

HIGHLIGHTS_SOURCES:
{json.dumps(sources_highlights, ensure_ascii=False, indent=2, default=safe_json)}

HIGHLIGHTS_DAILY:
{json.dumps(daily_highlights, ensure_ascii=False, indent=2, default=safe_json)}

HIGHLIGHTS_TOPICS:
{json.dumps(topics_highlights, ensure_ascii=False, indent=2, default=safe_json)}

EVIDÊNCIA_CRUZADA_OBRIGATÓRIA:
{json.dumps(cross_evidence, ensure_ascii=False, indent=2, default=safe_json)}

INSTRUÇÃO CRÍTICA:
- Use a evidência cruzada acima como regra de validação.
- Só trate algo como "sustentação da imagem" se houver cruzamento consistente em stats + daily + topics.
- Só trate algo como "pressão sobre a imagem" se houver cruzamento consistente em stats + daily + topics.
- Quando o volume vier sem confirmação de qualidade, enquadre isso como escala de exposição, não como sustentação.
""".strip()

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


# =========================================================
# LLM EXECUTION
# =========================================================

def run_highlight_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
) -> str:
    llm = ChatOpenAI(model=model, temperature=temperature)
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])
    return response.content


def run_scope_highlights(
    *,
    scope_payload: Dict[str, Any],
    meta: Dict[str, Any],
    competitors: Optional[Sequence[str]] = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_highlights: int = 6,
) -> Dict[str, Any]:
    prompts = build_scope_prompts(
        scope_payload=scope_payload,
        meta=meta,
        competitors=competitors,
        max_highlights=max_highlights,
    )
    final_text = run_highlight_llm(
        prompts["system_prompt"],
        prompts["user_prompt"],
        model=model,
        temperature=temperature,
    )
    cleaned_list = _clean_llm_numbered_list(final_text)
    return {
        "scope": scope_payload["scope"],
        "base_highlights": scope_payload.get("base_highlights", []),
        "final_text": final_text,
        "final_list": cleaned_list,
        "highlights": cleaned_list,
        "candidates": scope_payload.get("highlight_candidates", []),
        "system_prompt": prompts["system_prompt"],
        "user_prompt": prompts["user_prompt"],
    }


def run_final_synthesis(
    *,
    meta: Dict[str, Any],
    competitors: Optional[Sequence[str]] = None,
    stats_result: Dict[str, Any],
    sources_result: Dict[str, Any],
    daily_result: Dict[str, Any],
    topics_result: Dict[str, Any],
    cross_evidence: Dict[str, Any],
    model: str = "gpt-4o-mini",
    temperature: float = 0.35,
    max_highlights: int = 8,
) -> Dict[str, Any]:
    prompts = build_final_synthesis_prompts(
        meta=meta,
        competitors=competitors,
        stats_highlights=stats_result.get("final_list", []),
        sources_highlights=sources_result.get("final_list", []),
        daily_highlights=daily_result.get("final_list", []),
        topics_highlights=topics_result.get("final_list", []),
        cross_evidence=cross_evidence,
        max_highlights=max_highlights,
    )
    final_text = run_highlight_llm(
        prompts["system_prompt"],
        prompts["user_prompt"],
        model=model,
        temperature=temperature,
    )
    return {
        "synthesis_text": final_text.strip(),
        "final_text": final_text.strip(),
        "final_list": _clean_llm_numbered_list(final_text),
        "cross_evidence": cross_evidence,
        "system_prompt": prompts["system_prompt"],
        "user_prompt": prompts["user_prompt"],
    }


# =========================================================
# PIPELINE MULTIEMPRESA
# =========================================================

def _resolve_company_sequence(
    companies_map: Mapping[str, Dict[str, Any]],
    company_order: Optional[Sequence[str]] = None,
) -> List[str]:
    if not company_order:
        return list(companies_map.keys())

    resolved = []
    for name in company_order:
        target = _normalize_text(name)
        for raw_name, payload in companies_map.items():
            if target in {_normalize_text(raw_name), _normalize_text(payload.get("empresa_display"))}:
                if raw_name not in resolved:
                    resolved.append(raw_name)
                break
    return resolved


def generate_company_highlights_multistage(
    *,
    company_payload: Dict[str, Any],
    competitors: Optional[Sequence[str]] = None,
    selected_sources: Optional[Sequence[str]] = None,
    model_scope: str = "gpt-4o-mini",
    model_final: str = "gpt-4o-mini",
    temperature_scope: float = 0.3,
    temperature_final: float = 0.35,
    stats_scope_highlights: int = 6,
    sources_scope_highlights: int = 6,
    daily_scope_highlights: int = 5,
    topics_scope_highlights: int = 6,
    final_max_highlights: int = 8,
) -> Dict[str, Any]:
    payloads = build_company_scope_payloads(
        company_payload,
        selected_sources=selected_sources,
    )
    meta = payloads["meta"]

    stats_result = run_scope_highlights(
        scope_payload=payloads["stats"],
        meta=meta,
        competitors=competitors,
        model=model_scope,
        temperature=temperature_scope,
        max_highlights=stats_scope_highlights,
    )
    sources_result = run_scope_highlights(
        scope_payload=payloads["sources"],
        meta=meta,
        competitors=competitors,
        model=model_scope,
        temperature=temperature_scope,
        max_highlights=sources_scope_highlights,
    )
    daily_result = run_scope_highlights(
        scope_payload=payloads["daily"],
        meta=meta,
        competitors=competitors,
        model=model_scope,
        temperature=temperature_scope,
        max_highlights=daily_scope_highlights,
    )
    topics_result = run_scope_highlights(
        scope_payload=payloads["topics"],
        meta=meta,
        competitors=competitors,
        model=model_scope,
        temperature=temperature_scope,
        max_highlights=topics_scope_highlights,
    )

    cross_evidence = build_cross_evidence_bundle(
        meta=meta,
        stats_candidates=payloads["stats"].get("highlight_candidates", []),
        sources_candidates=payloads["sources"].get("highlight_candidates", []),
        daily_candidates=payloads["daily"].get("highlight_candidates", []),
        topics_candidates=payloads["topics"].get("highlight_candidates", []),
    )

    final_result = run_final_synthesis(
        meta=meta,
        competitors=competitors,
        stats_result=stats_result,
        sources_result=sources_result,
        daily_result=daily_result,
        topics_result=topics_result,
        cross_evidence=cross_evidence,
        model=model_final,
        temperature=temperature_final,
        max_highlights=final_max_highlights,
    )

    return {
        "meta": meta,
        "stats_layer": stats_result,
        "sources_layer": sources_result,
        "daily_layer": daily_result,
        "topics_layer": topics_result,
        "cross_evidence": cross_evidence,
        "final_synthesis": final_result,
        "layer_highlights": {
            "stats_layer": stats_result.get("highlights", []),
            "sources_layer": sources_result.get("highlights", []),
            "daily_layer": daily_result.get("highlights", []),
            "topics_layer": topics_result.get("highlights", []),
        },
        "final_highlights": {
            "synthesis": final_result.get("synthesis_text", ""),
            "stats_layer": stats_result.get("highlights", []),
            "sources_layer": sources_result.get("highlights", []),
            "daily_layer": daily_result.get("highlights", []),
            "topics_layer": topics_result.get("highlights", []),
        },
    }


def generate_highlights_multistage(
    *,
    stats_llm: dict,
    sources_llm: dict,
    daily_llm: dict,
    assunto_llm: dict,
    company_display_names: Optional[Mapping[str, str]] = None,
    companies_to_run: Optional[Sequence[str]] = None,
    competitors_by_company: Optional[Mapping[str, Sequence[str]]] = None,
    selected_sources_by_company: Optional[Mapping[str, Sequence[str]]] = None,
    model_scope: str = "gpt-4o-mini",
    model_final: str = "gpt-4o-mini",
    temperature_scope: float = 0.3,
    temperature_final: float = 0.35,
    stats_scope_highlights: int = 6,
    sources_scope_highlights: int = 6,
    daily_scope_highlights: int = 5,
    topics_scope_highlights: int = 6,
    final_max_highlights: int = 8,
) -> Dict[str, Any]:
    companies_map = normalize_inputs_by_company(
        stats_llm=stats_llm,
        sources_llm=sources_llm,
        daily_llm=daily_llm,
        assunto_llm=assunto_llm,
        company_display_names=company_display_names,
    )

    ordered_companies = _resolve_company_sequence(companies_map, companies_to_run)
    results: Dict[str, Any] = {}

    for raw_name in ordered_companies:
        payload = companies_map[raw_name]
        display_name = payload["empresa_display"]

        competitors = None
        if competitors_by_company:
            competitors = _first_not_none(
                competitors_by_company.get(raw_name),
                competitors_by_company.get(display_name),
            )

        selected_sources = None
        if selected_sources_by_company:
            selected_sources = _first_not_none(
                selected_sources_by_company.get(raw_name),
                selected_sources_by_company.get(display_name),
            )

        results[raw_name] = generate_company_highlights_multistage(
            company_payload=payload,
            competitors=competitors,
            selected_sources=selected_sources,
            model_scope=model_scope,
            model_final=model_final,
            temperature_scope=temperature_scope,
            temperature_final=temperature_final,
            stats_scope_highlights=stats_scope_highlights,
            sources_scope_highlights=sources_scope_highlights,
            daily_scope_highlights=daily_scope_highlights,
            topics_scope_highlights=topics_scope_highlights,
            final_max_highlights=final_max_highlights,
        )

    return {
        "companies": results,
        "company_order": ordered_companies,
    }


# =========================================================
# EXEMPLO DE CHAMADA
# =========================================================

EXAMPLE_USAGE = r'''
result = generate_highlights_multistage_v3_2(
    stats_llm=stats_llm,
    sources_llm=sources_llm,
    daily_llm=daily_llm,
    assunto_llm=assunto_llm,
    company_display_names={
        "americanas sa": "Americanas",
        "Itaú (Grupo)": "Itaú",
    },
    companies_to_run=["americanas sa"],
    competitors_by_company={
        "americanas sa": ["Magazine Luiza", "Mercado Livre"],
    },
    selected_sources_by_company={
        "americanas sa": ["Valor Econômico", "Folha de S.Paulo", "Exame"],
    },
)

# síntese final do cliente
result["companies"]["americanas sa"]["final_synthesis"]["synthesis_text"]

# highlights por camada
result["companies"]["americanas sa"]["final_highlights"]["stats_layer"]

# layer de assuntos
result["companies"]["americanas sa"]["topics_layer"]["final_list"]
'''
