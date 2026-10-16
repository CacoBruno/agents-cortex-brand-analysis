from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, List, Dict, Any

def resolve_period_filter_col(period: str | None) -> str:
    period_map = {
        "dia": "dia_index",
        "diario": "dia_index",
        "semana": "semana_index",
        "semanal": "semana_index",
        "mes": "mes_index",
        "mensal": "mes_index",
        "trimestre": "trimestre_index",
        "trimestral": "trimestre_index",
        "semestre": "semestre_index",
        "semestral": "semestre_index",
        "ano": "ano_index",
        "anual": "ano_index",
    }

    period_norm = str(period or "").strip().lower()

    if period_norm not in period_map:
        raise ValueError(f"Período inválido: {period}")

    return period_map[period_norm]


def get_week_anchor_from_end_date(end_date: str, anchor_weekday: str) -> str:
    weekday_map = {
        "segunda-feira": 0,
        "segunda": 0,
        "terça-feira": 1,
        "terça": 1,
        "terca-feira": 1,
        "terca": 1,
        "quarta-feira": 2,
        "quarta": 2,
        "quinta-feira": 3,
        "quinta": 3,
        "sexta-feira": 4,
        "sexta": 4,
        "sábado": 5,
        "sabado": 5,
        "domingo": 6,
    }

    anchor_weekday = anchor_weekday.lower().strip()

    if anchor_weekday not in weekday_map:
        raise ValueError(
            f"Dia da semana inválido: {anchor_weekday}. "
            f"Use: {list(weekday_map.keys())}"
        )

    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    target_weekday = weekday_map[anchor_weekday]

    days_back = (end_dt.weekday() - target_weekday) % 7
    anchor_dt = end_dt - timedelta(days=days_back)

    return anchor_dt.strftime("%Y-%m-%d")


def build_initial_coverage_state(
    url_platform: str,
    end_date: str,
    analysis_start_date: str,
    client: str,
    client_display_name: str,
    produto_analisado: List[str],
    period: str = "mes",
    period_label: Optional[str] = None,
    anchor_weekday: str = "segunda-feira",
    list_search: Optional[List[str]] = None,
    status_classificacao: Optional[List[str]] = None,
    tipos_de_impactos: Optional[List[str]] = None,
    representa_empresa: str = "Sim",
    tier: Optional[List[str]] = None,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    max_retries: int = 3,
) -> Dict[str, Any]:

    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    capture_start_date = (
        end_dt - relativedelta(years=1)
    ).strftime("%Y-%m-%d")

    year = end_dt.year

    data_ancora_semana = get_week_anchor_from_end_date(
        end_date=end_date,
        anchor_weekday=anchor_weekday,
    )
    period_filter_col = resolve_period_filter_col(period)

    if list_search is None:
        list_search = list(dict.fromkeys([
            client,
            client_display_name,
        ]))

    if status_classificacao is None:
        status_classificacao = ["Classificado"]

    if tipos_de_impactos is None:
        tipos_de_impactos = ["Promotores", "Detratores", "Inócuos"]

    if tier is None:
        tier = ["Tier 1", "Tier 2"]

    return {
        "url_platform": url_platform,

        # Datas
        "start_date": capture_start_date,
        "end_date": end_date,
        "analysis_start_date": analysis_start_date,
        "analysis_end_date": end_date,
        "year": year,

        # Semana
        "anchor_weekday": anchor_weekday,
        "data_ancora_semana": data_ancora_semana,

        # Empresa
        "client": client,
        "client_display_name": client_display_name,
        "company_name": client_display_name,
        "empresa_analisada": [client],
        "produto_analisado": produto_analisado,
        "list_search": list_search,

        # Período
        "period": period,
        "period_label": period_label,

        # Captura
        "status_classificacao": status_classificacao,
        "tipos_de_impactos": tipos_de_impactos,
        "representa_empresa": representa_empresa,
        "tier": tier,

        # Defaults analíticos
        "focus_analysis": "Empresa analisada",
        "return_metric": "merged",
        "source_cols": ["Fonte", "Mídia"],
        "topic_col": "Assunto específico",

        # Colunas de período
        "daily_period_col": "dia",
        "date_col": "dia",
        "date_index_col": "dia_index",

        # Filtros
        "filter_col": period_filter_col,
        "filter_values": [0],
        "period_filter_col": period_filter_col,
        "period_filter_value": 0,

        # Rankings
        "top_n_sources": 10,
        "top_n_topics_period": 10,
        "top_n_topics_per_day": 5,
        "top_n_days": 10,
        "top_n_extra_positive": 10,
        "top_n_extra_negative": 5,
        "top_n_positive": 5,
        "top_n_negative": 5,

        # LLM
        "model": model,
        "temperature": temperature,
        "max_retries": max_retries,

        # Coverage summary
        "top_n_vehicles": 10,
        "top_n_docs_per_day": 10,
        "top_n_docs_per_vehicle": 8,
        "top_n_docs_per_topic": 8,
        "max_chars_text": 2500,
        "include_only_target_brand": True,
        "final_top_highlights": 8,
    }