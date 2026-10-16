from __future__ import annotations

from langchain.tools import tool

from src.tools_agents.analysis.coverage_context.schemas import ExtrairContextoNoticiasInput
from src.tools_agents.analysis.coverage_context.services import run_extrair_contexto_noticias_service


@tool("extrair_contexto_noticias_tool", args_schema=ExtrairContextoNoticiasInput)
def extrair_contexto_noticias_tool(
    df_id: str,
    list_search: list[str],
    start_date: str | None = None,
    end_date: str | None = None,
    date_format: str | None = None,
    col_data: str = "data",
    col_titulo: str = "titulo",
    col_fonte: str = "fonte",
    col_conteudo: str = "conteudo",
    col_id: str = "Chave Análise de Mídia Hash",
    col_alcance: str | None = "alcance",
    col_tier: str | None = "tier",
    col_tipos_de_impactos: str | None = "tipos_de_impactos",
    col_sentimento: str | None = "sentimento",
    col_protagonismo: str | None = "protagonismo",
    col_empresa: str | None = "Empresa analisada",
    col_produto: str | None = "Produto analisado",
    col_jornalista: str | None = "Jornalista",
    col_url_noticia: str | None = "url da notícia",
    col_assuntos_especificos: str | None = "Assuntos específicos",
    col_midia: str | None = "Mídia",
):
    """
    Extrai contexto narrativo de notícias a partir de um DataFrame salvo no DATAFRAME_STORE,
    buscando frases relacionadas a termos de interesse.

    A tool também permite aplicar filtro opcional por data antes da extração,
    usando start_date e end_date.

    Parâmetros principais:
    - df_id: identificador do DataFrame salvo
    - list_search: termos a buscar no conteúdo das notícias
    - start_date: data inicial do filtro (inclusive)
    - end_date: data final do filtro (inclusive)
    - date_format: formato opcional de parsing da data

    Retorno:
    - metadados da execução
    - quantidade de linhas antes e depois do filtro
    - dicionário final organizado por data com contexto e documentos
    """

    params = ExtrairContextoNoticiasInput(
        df_id=df_id,
        list_search=list_search,
        start_date=start_date,
        end_date=end_date,
        date_format=date_format,
        col_data=col_data,
        col_titulo=col_titulo,
        col_fonte=col_fonte,
        col_conteudo=col_conteudo,
        col_id=col_id,
        col_alcance=col_alcance,
        col_tier=col_tier,
        col_tipos_de_impactos=col_tipos_de_impactos,
        col_sentimento=col_sentimento,
        col_protagonismo=col_protagonismo,
        col_empresa=col_empresa,
        col_produto=col_produto,
        col_jornalista=col_jornalista,
        col_url_noticia=col_url_noticia,
        col_assuntos_especificos=col_assuntos_especificos,
        col_midia=col_midia,
    )

    return run_extrair_contexto_noticias_service(params)



from src.tools_agents.analysis.coverage_context.schemas import (
    BuildMainDaysCoverageSchema,
    BuildTopVehiclesCoverageSchema,
    BuildSpecificTopicsReportsSchema,
)

from src.tools_agents.analysis.coverage_context.services import (
    build_main_days_coverage_service,
    build_top_vehicles_coverage_service,
    build_specific_topics_reports_service,
)

from core.dataframe_store import DATAFRAME_STORE



def _get_df_from_store(df_id: str):
    """
    Recupera um dataframe salvo no DATAFRAME_STORE.
    """
    if df_id not in DATAFRAME_STORE:
        raise ValueError(f"df_id '{df_id}' não encontrado no DATAFRAME_STORE.")

    item = DATAFRAME_STORE[df_id]

    if isinstance(item, dict) and "df" in item:
        return item["df"]

    return item


@tool(args_schema=BuildMainDaysCoverageSchema)
def build_main_days_coverage_tool(
    df_daily_contrib_id: str,
    coverage_dict: dict,
    daily_date_col: str = "Data",
    contrib_col: str = "contr_nps_score",
    promoter_col: str = "Promotores",
    detractor_col: str = "Detratores",
    zscore_col: str = "z_score_contr_nps",
    top_n_extra_positive: int = 0,
    top_n_extra_negative: int = 0,
    filter_col: str | None = None,
    filter_values: list | None = None,
) -> dict:
    """
    Constrói o contexto dos principais dias da cobertura a partir de um dataframe
    diário de contribuição ao NPS e de um dicionário de notícias por dia.

    Permite aplicar filtro opcional no dataframe antes da análise, por exemplo:
    mes_index == 0.
    """
    df_daily_contrib = _get_df_from_store(df_daily_contrib_id)

    return build_main_days_coverage_service(
        daily_contrib_df=df_daily_contrib,
        coverage_dict=coverage_dict,
        daily_date_col=daily_date_col,
        contrib_col=contrib_col,
        promoter_col=promoter_col,
        detractor_col=detractor_col,
        zscore_col=zscore_col,
        top_n_extra_positive=top_n_extra_positive,
        top_n_extra_negative=top_n_extra_negative,
        filter_col=filter_col,
        filter_values=filter_values,
    )


@tool(args_schema=BuildTopVehiclesCoverageSchema)
def build_top_vehicles_coverage_tool(
    df_vehicles_id: str,
    coverage_dict: dict,
    source_col: str = "Fonte",
    promoter_col: str = "Promotores",
    detractor_col: str = "Detratores",
    top_n: int = 10,
    filter_col: str | None = None,
    filter_values: list | None = None,
) -> dict:
    """
    Constrói o contexto dos principais veículos da cobertura a partir de um dataframe
    agregado de fontes/veículos e de um dicionário diário de notícias.

    Permite aplicar filtro opcional no dataframe antes da análise.
    """
    df_vehicles = _get_df_from_store(df_vehicles_id)

    return build_top_vehicles_coverage_service(
        vehicles_df=df_vehicles,
        coverage_dict=coverage_dict,
        source_col=source_col,
        promoter_col=promoter_col,
        detractor_col=detractor_col,
        top_n=top_n,
        filter_col=filter_col,
        filter_values=filter_values,
    )


@tool(args_schema=BuildSpecificTopicsReportsSchema)
def build_specific_topics_reports_tool(
    df_assunto_period_id: str,
    daily_top_news_dict: dict,
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
) -> dict:
    """
    Constrói o contexto dos assuntos específicos mais promotores e detratores
    do período, cruzando métricas agregadas com as reportagens do dicionário diário.
    """
    df_assunto_period = _get_df_from_store(df_assunto_period_id)

    return build_specific_topics_reports_service(
        assunto_df_period=df_assunto_period,
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

from src.tools_agents.analysis.coverage_context.schemas import BuildCoverageSummarySchema
from src.tools_agents.analysis.coverage_context.services import build_coverage_summary_service


@tool(args_schema=BuildCoverageSummarySchema)
def build_coverage_summary_tool(
    contexto_dia: dict,
    context_veiculos: dict,
    context_assuntos: dict,
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
    """
    Gera o resumo consolidado da cobertura de mídia com base nos contextos
    de dias, veículos e assuntos específicos da marca.

    A saída inclui:
    - preparação determinística dos inputs
    - prompts gerados
    - análises por dia, veículo e assunto
    - síntese final
    - highlights executivos
    - links consolidados das publicações
    """
    return build_coverage_summary_service(
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