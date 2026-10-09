from typing import TypedDict


class CoverageGraphState(TypedDict, total=False):
    url_platform: str
    start_date: str
    end_date: str
    analysis_start_date: str
    analysis_end_date: str

    client: str
    client_display_name: str
    company_name: str
    empresa_analisada: list
    produto_analisado: list
    list_search: list

    period: str
    period_label: str
    year: int
    data_ancora_semana: str

    filter_col: str
    filter_values: list

    status_classificacao: list
    tipos_de_impactos: list
    representa_empresa: str
    tier: list

    focus_analysis: str
    return_metric: str
    source_cols: list
    topic_col: str

    model: str
    temperature: float
    max_retries: int

    export_result: dict
    dataview_result: dict
    df_id_base: str
    df_content_id: str

    index_result: dict
    index_df_id: str
    stats_llm: dict
    big_numbers: dict

    fonte_result: dict
    fonte_df_id: str
    sources_llm: dict

    assunto_daily_result: dict
    assunto_daily_df_id: str
    assunto_period_result: dict
    assunto_period_df_id: str
    assunto_llm: dict

    contr_dia_result: dict
    contr_dia_df_id: str
    daily_llm: dict

    daily_top_news_dict: dict
    contexto_dia: dict
    context_veiculos: dict
    context_assuntos: dict
    coverage_context_result: dict

    contexto_negocios: dict
    highlights_results: dict
    insights: dict
    whatsapp_message: dict
    meeting_script: dict
    