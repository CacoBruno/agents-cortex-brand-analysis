from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from src.tools_agents.analysis.coverage_context.schemas import ExtrairContextoNoticiasInput
from services.texts_treatments import (
    extrair_contexto_noticias, extrair_contexto_noticias_fast, 
    filter_dataframe_by_date,
)
from core.dataframe_store import get_dataframe


def run_extrair_contexto_noticias_service(
    params: ExtrairContextoNoticiasInput
) -> Dict[str, Any]:
    """
    Orquestra:
    1. recuperação do DataFrame pelo df_id
    2. filtro opcional por data
    3. extração do contexto das notícias
    """

    df = get_dataframe(params.df_id)

    if df is None:
        raise ValueError(f"Nenhum DataFrame encontrado para df_id='{params.df_id}'.")

    if not isinstance(df, pd.DataFrame):
        raise TypeError("O objeto recuperado do DATAFRAME_STORE não é um pandas.DataFrame.")

    df_processado = df.copy()

    # filtro opcional por datas
    if params.start_date or params.end_date:
        if params.col_data not in df_processado.columns:
            raise ValueError(
                f"A coluna de data '{params.col_data}' não existe no DataFrame."
            )

        df_processado = filter_dataframe_by_date(
            df=df_processado,
            date_col=params.col_data,
            start_date=params.start_date,
            end_date=params.end_date,
            date_format=params.date_format,
        )

    resultado = extrair_contexto_noticias_fast(
        dataframe=df_processado,
        list_search=params.list_search,
        col_data=params.col_data,
        col_titulo=params.col_titulo,
        col_fonte=params.col_fonte,
        col_conteudo=params.col_conteudo,
        col_id=params.col_id,
        col_alcance=params.col_alcance,
        col_tier=params.col_tier,
        col_tipos_de_impactos=params.col_tipos_de_impactos,
        col_sentimento=params.col_sentimento,
        col_protagonismo=params.col_protagonismo,
        col_empresa=params.col_empresa,
        col_produto=params.col_produto,
        col_jornalista=params.col_jornalista,
        col_url_noticia=params.col_url_noticia,
        col_assuntos_especificos=params.col_assuntos_especificos,
        col_midia=params.col_midia,
    )

    return {
        "df_id": params.df_id,
        "rows_input": int(len(df)),
        "rows_after_date_filter": int(len(df_processado)),
        "date_filter_applied": bool(params.start_date or params.end_date),
        "start_date": params.start_date,
        "end_date": params.end_date,
        "list_search": params.list_search,
        "resultado": resultado,
    }

from services.coverage_pattern.coverage_context import (
    build_main_days_from_nps_daily_contrib_and_coverage_dict,
    build_top_vehicles_coverage_from_dict,
    build_specific_topics_reports_dict,
)


def filter_dataframe_by_values(
    df: pd.DataFrame,
    filter_col: str | None = None,
    filter_values: list[Any] | None = None,
) -> pd.DataFrame:
    """
    Filtra dataframe por uma coluna e lista de valores.
    Se filter_col ou filter_values não forem informados, retorna o df original.
    """
    if not filter_col or filter_values is None:
        return df.copy()

    if filter_col not in df.columns:
        raise ValueError(f"Coluna de filtro '{filter_col}' não encontrada no dataframe.")

    return df[df[filter_col].isin(filter_values)].copy()


def build_main_days_coverage_service(
    daily_contrib_df: pd.DataFrame,
    coverage_dict: Dict[str, Dict[str, Any]],
    *,
    daily_date_col: str = "Data",
    contrib_col: str = "contr_nps_score",
    promoter_col: str = "Promotores",
    detractor_col: str = "Detratores",
    zscore_col: str = "z_score_contr_nps",
    top_n_extra_positive: int = 0,
    top_n_extra_negative: int = 0,
    filter_col: str | None = None,
    filter_values: list[Any] | None = None,
) -> Dict[str, Any]:
    """
    Aplica filtro opcional no dataframe diário e monta o contexto
    dos principais dias com base na contribuição ao NPS.
    """
    df = filter_dataframe_by_values(
        df=daily_contrib_df,
        filter_col=filter_col,
        filter_values=filter_values,
    )

    return build_main_days_from_nps_daily_contrib_and_coverage_dict(
        daily_contrib_df=df,
        coverage_dict=coverage_dict,
        daily_date_col=daily_date_col,
        contrib_col=contrib_col,
        promoter_col=promoter_col,
        detractor_col=detractor_col,
        zscore_col=zscore_col,
        top_n_extra_positive=top_n_extra_positive,
        top_n_extra_negative=top_n_extra_negative,
    )


def build_top_vehicles_coverage_service(
    vehicles_df: pd.DataFrame,
    coverage_dict: Dict[str, Dict[str, Any]],
    *,
    source_col: str = "Fonte",
    promoter_col: str = "Promotores",
    detractor_col: str = "Detratores",
    top_n: int = 10,
    filter_col: str | None = None,
    filter_values: list[Any] | None = None,
) -> Dict[str, Any]:
    """
    Aplica filtro opcional no dataframe de veículos e monta o contexto
    dos principais veículos com base no score composto.
    """
    df = filter_dataframe_by_values(
        df=vehicles_df,
        filter_col=filter_col,
        filter_values=filter_values,
    )

    return build_top_vehicles_coverage_from_dict(
        coverage_dict=coverage_dict,
        vehicles_df=df,
        source_col=source_col,
        promoter_col=promoter_col,
        detractor_col=detractor_col,
        top_n=top_n,
    )


def build_specific_topics_reports_service(
    assunto_df_period: pd.DataFrame,
    daily_top_news_dict: Dict[str, Dict[str, Any]],
    *,
    empresa_col: str = "Empresa analisada",
    topic_col: str = "Assunto específico",
    contrib_col: str = "nps_contrib_assunto_especifico",
    topic_nps_col: str = "nps_score_assunto_especifico",
    total_topic_col: str = "total_assunto_especifico",
    denom_total_col: str = "denom_total",
    period_nps_col: str = "nps_score_periodo",
    period_filter_col: str = "mes_index",
    period_filter_value: int = 0,
    top_n_positive: int = 5,
    top_n_negative: int = 5,
    docs_key: str = "documentos",
    doc_topic_key: str = "Assuntos específicos",
    doc_company_key: str = "empresa",
    sort_reports: bool = True,
) -> Dict[str, Any]:
    """
    Monta o contexto dos assuntos específicos promotores e detratores
    cruzando métricas do período com as reportagens diárias.
    """
    return build_specific_topics_reports_dict(
        assunto_df_period=assunto_df_period,
        daily_top_news_dict=daily_top_news_dict,
        empresa_col=empresa_col,
        topic_col=topic_col,
        contrib_col=contrib_col,
        topic_nps_col=topic_nps_col,
        total_topic_col=total_topic_col,
        denom_total_col=denom_total_col,
        period_nps_col=period_nps_col,
        period_filter_col=period_filter_col,
        period_filter_value=period_filter_value,
        top_n_positive=top_n_positive,
        top_n_negative=top_n_negative,
        docs_key=docs_key,
        doc_topic_key=doc_topic_key,
        doc_company_key=doc_company_key,
        sort_reports=sort_reports,
    )


from services.coverage_pattern.media_approach import build_coverage_summary


def build_coverage_summary_service(
    contexto_dia: Dict[str, Any],
    context_veiculos: Dict[str, Any],
    context_assuntos: Dict[str, Any],
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
) -> Dict[str, Any]:
    """
    Orquestra a geração do resumo consolidado da cobertura de mídia
    a partir dos contextos de dias, veículos e assuntos.
    """

    if not isinstance(contexto_dia, dict):
        raise ValueError("contexto_dia deve ser um dicionário.")

    if not isinstance(context_veiculos, dict):
        raise ValueError("context_veiculos deve ser um dicionário.")

    if not isinstance(context_assuntos, dict):
        raise ValueError("context_assuntos deve ser um dicionário.")

    if not target_brand or not str(target_brand).strip():
        raise ValueError("target_brand deve ser informado.")

    return build_coverage_summary(
        contexto_dia=contexto_dia,
        context_veiculos=context_veiculos,
        context_assuntos=context_assuntos,
        target_brand=target_brand,
        model=model,
        temperature=temperature,
        top_n_vehicles=top_n_vehicles,
        top_n_docs_per_day=top_n_docs_per_day,
        top_n_docs_per_vehicle=top_n_docs_per_vehicle,
        top_n_docs_per_topic=top_n_docs_per_topic,
        max_chars_text=max_chars_text,
        include_only_target_brand=include_only_target_brand,
        final_top_highlights=final_top_highlights,
    )