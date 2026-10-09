from src.tools_agents.insights_tools.state import CoverageGraphState
from services.output_configs.output_mspack import make_msgpack_safe

def find_msgpack_unsafe(obj, path="root", max_items=50, found=None):
    import numpy as np
    import pandas as pd
    from datetime import datetime, date

    if found is None:
        found = []

    if len(found) >= max_items:
        return found

    if isinstance(obj, dict):
        for k, v in obj.items():
            find_msgpack_unsafe(v, f"{path}.{k}", max_items, found)

    elif isinstance(obj, (list, tuple, set)):
        for i, v in enumerate(obj):
            find_msgpack_unsafe(v, f"{path}[{i}]", max_items, found)

    elif isinstance(obj, np.generic):
        found.append((path, type(obj).__name__, repr(obj)))

    elif isinstance(obj, np.ndarray):
        found.append((path, type(obj).__name__, f"shape={obj.shape}"))

    elif isinstance(obj, pd.DataFrame):
        found.append((path, "DataFrame", f"shape={obj.shape}"))

    elif isinstance(obj, pd.Series):
        found.append((path, "Series", f"shape={obj.shape}"))

    elif isinstance(obj, pd.Timestamp):
        found.append((path, "Timestamp", repr(obj)))

    elif obj is pd.NA:
        found.append((path, "pd.NA", repr(obj)))

    return found


def safe_node_output(node_name: str, output: dict) -> dict:
    unsafe = find_msgpack_unsafe(output)

    if unsafe:
        print(f"\n[DEBUG MSGPACK] {node_name}: objetos não serializáveis encontrados")
        for path, typ, value in unsafe:
            print(f" - {path}: {typ} = {value}")

    return make_msgpack_safe(output)

DEFAULTS = {
    "focus_analysis": "Empresa analisada",
    "return_metric": "merged",
    "source_cols": ["Fonte", "Mídia"],
    "topic_col": "Assunto específico",

    "date_col": "dia",
    "date_index_col": "dia_index",
    "daily_period_col": "dia",

    "top_n_topics_period": 10,
    "top_n_topics_per_day": 5,
    "top_n_days": 10,
    "top_n_sources": 10,

    "top_n_extra_positive": 10,
    "top_n_extra_negative": 5,
    "top_n_positive": 5,
    "top_n_negative": 5,

    "filter_col": "mes_index",
    "filter_values": [0],
    "period_filter_col": "mes_index",
    "period_filter_value": 0,

    "model": "gpt-4.1-mini",
    "temperature": 0.2,
    "max_retries": 3,

    "top_n_vehicles": 10,
    "top_n_docs_per_day": 10,
    "top_n_docs_per_vehicle": 8,
    "top_n_docs_per_topic": 8,
    "max_chars_text": 2500,
    "include_only_target_brand": True,
    "final_top_highlights": 8,
}


def gv(state, key, default=None):
    if default is None:
        default = DEFAULTS.get(key)
    return state.get(key, default)


def require_keys(state, node_name, keys):
    missing = [k for k in keys if k not in state or state[k] is None]
    if missing:
        raise ValueError(
            f"[{node_name}] Faltam chaves obrigatórias no state: {missing}. "
            f"Chaves disponíveis: {sorted(list(state.keys()))}"
        )


def get_payload_df_id(result, node_name, result_name):
    try:
        return result["payload"]["df_id"]
    except Exception as e:
        raise ValueError(
            f"[{node_name}] Não encontrei payload.df_id em {result_name}. "
            f"Resultado recebido: {result}"
        ) from e


def node_captura_dados(state: CoverageGraphState):
    node_name = "node_captura_dados"

    require_keys(state, node_name, [
        "url_platform",
        "start_date",
        "end_date",
        "empresa_analisada",
        "produto_analisado",
        "status_classificacao",
        "tipos_de_impactos",
        "representa_empresa",
        "tier",
        "data_ancora_semana",
    ])

    from src.tools_agents.platform.tools import export_media_analysis_database_tool
    from src.tools_agents.communication_indexes.tools import gen_dataviews_tool

    export_result = export_media_analysis_database_tool.invoke({
        "url_platform": state["url_platform"],
        "start_date": state["start_date"],
        "end_date": state["end_date"],
        "empresa_analisada": state["client"],
        "produto_analisado": state["produto_analisado"],
        "status_classificacao": state["status_classificacao"],
        "tipos_de_impactos": state["tipos_de_impactos"],
        "representa_empresa": state["representa_empresa"],
        "tier": state["tier"],
    })

    print("-------> export_media_analysis_database_tool: done")
    if "dataframe_id" not in export_result:
        raise ValueError(
            f"[{node_name}] export_media_analysis_database_tool não retornou dataframe_id. "
            f"Resultado recebido: {export_result}"
        )

    dataview_result = gen_dataviews_tool.invoke({
        "dataframe_id": export_result["dataframe_id"],
        "data_ancora_semana": state["data_ancora_semana"],
    })
    print(dataview_result['meta'][ 'result_rows'])
    print("-------> gen_dataviews_tool: done")

    if "dataframe_id" not in dataview_result:
        raise ValueError(
            f"[{node_name}] gen_dataviews_tool não retornou dataframe_id. "
            f"Resultado recebido: {dataview_result}"
        )

    return safe_node_output(node_name, {
        "export_result": export_result,
        "dataview_result": dataview_result,
        "df_content_id": export_result["dataframe_id"],
        "df_id_base": dataview_result["dataframe_id"],
    })

def node_padrao_exposicao(state: CoverageGraphState):
    node_name = "node_padrao_exposicao"

    require_keys(state, node_name, [
        "df_id_base",
        "client",
        "period",
    ])

    from src.tools_agents.analysis.coverage_pattern.tools import (
        build_media_metrics_view_tool,
        build_media_metrics_view_by_source_tool,
        build_topic_contrib_df_tool,
        build_topic_contrib_llm_dict_tool,
        build_last_period_statistics_tool,
        build_company_big_number_dict_tool,
        build_sources_last_period_multi_company_dict_enriched_tool,
        build_daily_metrics_enriched_tool,
        build_daily_pattern_dict_tool,
    )

    df_id_base = state["df_id_base"]
    client = state["client"]
    period = state["period"]

    print('---> padrão de cobertura')

    index_result = build_media_metrics_view_tool.invoke({
        "df_id": df_id_base,
        "client": client,
        "focus_analysis": gv(state, "focus_analysis"),
        "period": period,
        "return_metric": gv(state, "return_metric"),
    })

    index_df_id = get_payload_df_id(index_result, node_name, "index_result")

    stats_llm = build_last_period_statistics_tool.invoke({
        "df_id": index_df_id,
        "client": client,
    })
    print("-------> build_last_period_statistics_tool: done")

    big_numbers = build_company_big_number_dict_tool.invoke({
        "df_id": index_df_id,
    })
    print("-------> build_company_big_number_dict_tool: done")

    fonte_result = build_media_metrics_view_by_source_tool.invoke({
        "df_id": df_id_base,
        "client": client,
        "focus_analysis": gv(state, "focus_analysis"),
        "period": period,
        "return_metric": gv(state, "return_metric"),
        "source_cols": gv(state, "source_cols"),
    })
    print("-------> build_media_metrics_view_by_source_tool: done")

    fonte_df_id = get_payload_df_id(fonte_result, node_name, "fonte_result")

    sources_llm = build_sources_last_period_multi_company_dict_enriched_tool.invoke({
        "df_id": fonte_df_id,
        "client": client,
        "sort_by": gv(state, "sort_by", "alcance"),
        "ascending": gv(state, "ascending", False),
    })
    print("-------> build_sources_last_period_multi_company_dict_enriched_tool: done")

    assunto_daily_result = build_topic_contrib_df_tool.invoke({
        "df_id": df_id_base,
        "client": client,
        "period": "dia",
        "focus_analysis": gv(state, "focus_analysis"),
        "topic_col": gv(state, "topic_col"),
    })
    print("-------> assunto_daily_result: done")

    assunto_daily_df_id = get_payload_df_id(
        assunto_daily_result,
        node_name,
        "assunto_daily_result"
    )

    assunto_period_result = build_topic_contrib_df_tool.invoke({
        "df_id": df_id_base,
        "client": client,
        "period": period,
        "focus_analysis": gv(state, "focus_analysis"),
        "topic_col": gv(state, "topic_col"),
    })
    print("-------> assunto_period_result: done")

    assunto_period_df_id = get_payload_df_id(
        assunto_period_result,
        node_name,
        "assunto_period_result"
    )

    assunto_llm = build_topic_contrib_llm_dict_tool.invoke({
        "df_daily_id": assunto_daily_df_id,
        "df_period_id": assunto_period_df_id,
        "client": client,
        "focus_analysis": gv(state, "focus_analysis"),
        "topic_col": gv(state, "topic_col"),
        "daily_period_col": gv(state, "daily_period_col"),
        "period_period_col": period,
        "top_n_topics_period": gv(state, "top_n_topics_period"),
        "top_n_topics_per_day": gv(state, "top_n_topics_per_day"),
    })
    print("-------> build_topic_contrib_llm_dict_tool: done")

    contr_dia_result = build_daily_metrics_enriched_tool.invoke({
        "df_id": df_id_base,
        "client": client,
        "focus_analysis": gv(state, "focus_analysis"),
    })
    print("-------> build_daily_metrics_enriched_tool: done")

    contr_dia_df_id = get_payload_df_id(
        contr_dia_result,
        node_name,
        "contr_dia_result"
    )

    daily_llm = build_daily_pattern_dict_tool.invoke({
        "df_id": contr_dia_df_id,
        "client": client,
        "focus_analysis": gv(state, "focus_analysis"),
        "date_col": gv(state, "date_col"),
        "date_index_col": gv(state, "date_index_col"),
        "top_n_days": gv(state, "top_n_days"),
        "contrib_col": gv(state, "contrib_col", "nps_contrib_dia"),
    })
    print("-------> build_daily_pattern_dict_tool: done")

    return safe_node_output(node_name, {
        "index_result": index_result,
        "index_df_id": index_df_id,
        "stats_llm": stats_llm,
        "big_numbers": big_numbers,
        "fonte_result": fonte_result,
        "fonte_df_id": fonte_df_id,
        "sources_llm": sources_llm,
        "assunto_daily_result": assunto_daily_result,
        "assunto_daily_df_id": assunto_daily_df_id,
        "assunto_period_result": assunto_period_result,
        "assunto_period_df_id": assunto_period_df_id,
        "assunto_llm": assunto_llm,
        "contr_dia_result": contr_dia_result,
        "contr_dia_df_id": contr_dia_df_id,
        "daily_llm": daily_llm,
    })

def node_contexto_exposicao(state: CoverageGraphState):
    node_name = "node_contexto_exposicao"

    require_keys(state, node_name, [
        "df_content_id",
        "list_search",
        "analysis_start_date",
        "analysis_end_date",
        "contr_dia_df_id",
        "fonte_df_id",
        "assunto_period_df_id",
        "client",
    ])

    from src.tools_agents.analysis.coverage_context.tools import (
        extrair_contexto_noticias_tool,
        build_main_days_coverage_tool,
        build_top_vehicles_coverage_tool,
        build_specific_topics_reports_tool,
        build_coverage_summary_tool,
    )

    daily_top_news_dict = extrair_contexto_noticias_tool.invoke({
        "df_id": state["df_content_id"],
        "list_search": state["list_search"],
        "start_date": state["analysis_start_date"],
        "end_date": state["analysis_end_date"],

        "col_data": gv(state, "col_data", "Data"),
        "col_titulo": gv(state, "col_titulo", "Título"),
        "col_fonte": gv(state, "col_fonte", "Fonte"),
        "col_conteudo": gv(state, "col_conteudo", "Conteúdo"),
        "col_id": gv(state, "col_id", "Chave Análise de Mídia Hash"),
        "col_tier": gv(state, "col_tier", "Tier"),
        "col_alcance": gv(state, "col_alcance", "Alcance orgânico"),
        "col_tipos_de_impactos": gv(state, "col_tipos_de_impactos", "Tipos de Impactos"),
        "col_sentimento": gv(state, "col_sentimento", "Sentimento final"),
        "col_protagonismo": gv(state, "col_protagonismo", "Nível de Protagonismo final"),
        "col_empresa": gv(state, "col_empresa", "Empresa analisada"),
        "col_produto": gv(state, "col_produto", "Produto analisado"),
        "col_jornalista": gv(state, "col_jornalista", "Jornalista"),
        "col_url_noticia": gv(state, "col_url_noticia", "Link original da publicação"),
        "col_assuntos_especificos": gv(state, "col_assuntos_especificos", "Assunto específico"),
        "col_midia": gv(state, "col_midia", "Mídia"),
    })
    print("-------> extrair_contexto_noticias_tool: done")

    coverage_dict = daily_top_news_dict.get("resultado", daily_top_news_dict)
    
    print('---> contexto exposição por dia')
    contexto_dia = build_main_days_coverage_tool.invoke({
        "df_daily_contrib_id": state["contr_dia_df_id"],
        "coverage_dict": coverage_dict,
        "daily_date_col": gv(state, "date_col"),
        "contrib_col": gv(state, "contrib_col", "nps_contrib_dia"),
        "promoter_col": gv(state, "promoter_col", "Promotores"),
        "detractor_col": gv(state, "detractor_col", "Detratores"),
        "zscore_col": gv(state, "zscore_col", "z-score_alcance"),
        "top_n_extra_positive": gv(state, "top_n_extra_positive"),
        "top_n_extra_negative": gv(state, "top_n_extra_negative"),
        "filter_col": gv(state, "filter_col"),
        "filter_values": gv(state, "filter_values"),
    })
    print("-------> build_main_days_coverage_tool: done")

    print('---> contexto veículos')
    context_veiculos = build_top_vehicles_coverage_tool.invoke({
        "df_vehicles_id": state["fonte_df_id"],
        "coverage_dict": coverage_dict,
        "source_col": gv(state, "source_col", "Fonte"),
        "promoter_col": gv(state, "promoter_col", "Promotores"),
        "detractor_col": gv(state, "detractor_col", "Detratores"),
        "top_n": gv(state, "top_n_sources"),
        "filter_col": gv(state, "filter_col"),
        "filter_values": gv(state, "filter_values"),
    })
    print("-------> build_top_vehicles_coverage_tool: done")

    print('---> contexto assuntos')
    context_assuntos = build_specific_topics_reports_tool.invoke({
        "df_assunto_period_id": state["assunto_period_df_id"],
        "daily_top_news_dict": coverage_dict,
        "period_filter_col": gv(state, "period_filter_col"),
        "period_filter_value": gv(state, "period_filter_value"),
        "top_n_positive": gv(state, "top_n_positive"),
        "top_n_negative": gv(state, "top_n_negative"),
    })
    print("-------> build_specific_topics_reports_tool: done")

    print('---> contexto exposição')
    coverage_context_result = build_coverage_summary_tool.invoke({
        "contexto_dia": contexto_dia,
        "context_veiculos": context_veiculos,
        "context_assuntos": context_assuntos,
        "target_brand": state["client"],
        "model": gv(state, "model"),
        "temperature": gv(state, "temperature"),
        "top_n_vehicles": gv(state, "top_n_vehicles"),
        "top_n_docs_per_day": gv(state, "top_n_docs_per_day"),
        "top_n_docs_per_vehicle": gv(state, "top_n_docs_per_vehicle"),
        "top_n_docs_per_topic": gv(state, "top_n_docs_per_topic"),
        "max_chars_text": gv(state, "max_chars_text"),
        "include_only_target_brand": gv(state, "include_only_target_brand"),
        "final_top_highlights": gv(state, "final_top_highlights"),
    })
    print("-------> build_coverage_summary_tool: done")

    return safe_node_output(node_name, {
        "daily_top_news_dict": daily_top_news_dict,
        "contexto_dia": contexto_dia,
        "context_veiculos": context_veiculos,
        "context_assuntos": context_assuntos,
        "coverage_context_result": coverage_context_result,
    })


def node_contexto_negocios(state: CoverageGraphState):
    node_name = "node_contexto_negocios"

    require_keys(state, node_name, [
        "client_display_name",
        "year",
    ])

    from src.tools_agents.insights_structural.tools import generate_company_context_tool

    print('---> contexto de negócios')
    contexto_negocios = generate_company_context_tool.invoke({
        "client_name": state["client_display_name"],
        "year": state["year"],
        "include_context": gv(state, "include_context", True),
        "include_objectives": gv(state, "include_objectives", False),
        "include_opportunities": gv(state, "include_opportunities", False),
        "include_risks": gv(state, "include_risks", False),
    })
    print("-------> generate_company_context_tool: done")

    return safe_node_output(node_name, {
        "contexto_negocios": contexto_negocios,
    })


def node_highlights(state: CoverageGraphState):
    node_name = "node_highlights"

    require_keys(state, node_name, [
        "stats_llm",
        "sources_llm",
        "daily_llm",
        "assunto_llm",
        "client",
        "client_display_name",
    ])

    from src.tools_agents.highlights.tools import generate_highlights_tool

    client = state["client"]

    fontes = (
        state.get("sources_llm", {})
        .get("payload", {})
        .get("empresas", [{}])[0]
        .get("fontes", [])
    )

    top_10 = [
        x.get("fonte")
        for x in fontes[:gv(state, "top_n_sources")]
        if isinstance(x, dict) and x.get("fonte")
    ]

    print('---> highlights')
    highlights_results = generate_highlights_tool.invoke({
        "stats_llm": state["stats_llm"].get("payload", state["stats_llm"]),
        "sources_llm": state["sources_llm"].get("payload", state["sources_llm"]),
        "daily_llm": state["daily_llm"].get("payload", state["daily_llm"]),
        "assunto_llm": state["assunto_llm"].get("payload", state["assunto_llm"]),
        "company_display_names": {
            client: state["client_display_name"],
        },
        "companies_to_run": [client],
        "selected_sources_by_company": {
            client: top_10,
        },
    })
    print("-------> generate_highlights_tool: done")

    return safe_node_output(node_name, {
        "highlights_results": highlights_results,
    })


def node_insights(state: CoverageGraphState):
    node_name = "node_insights"

    require_keys(state, node_name, [
        "big_numbers",
        "highlights_results",
        "coverage_context_result",
        "contexto_negocios",
        "client",
        "client_display_name",
    ])

    from src.tools_agents.insights_structural.tools import generate_coverage_insights_tool

    client = state["client"]
    print('---> insights')

    big_number = (
        state.get("big_numbers", {})
        .get("payload", {})
        .get(client, {})
        .get("periodos", [{}])[0]
        .get("metricas")
    )

    if big_number is None:
        raise ValueError(
            f"[{node_name}] Não encontrei big_numbers.payload[{client}].periodos[0].metricas. "
            f"big_numbers recebido: {state.get('big_numbers')}"
        )
    print("-------> big_number: done")

    highlight_infos = (
        state.get("highlights_results", {})
        .get("companies", {})
        .get(client)
    )

    if highlight_infos is None:
        raise ValueError(
            f"[{node_name}] Não encontrei highlights_results.companies[{client}]. "
            f"highlights_results recebido: {state.get('highlights_results')}"
        )
 
    print("-------> highlight_infos: done")

    insights = generate_coverage_insights_tool.invoke({
        "company_name": state.get("company_name", state["client_display_name"]),
        "period_label": state.get("period_label"),
        "big_number": big_number,
        "highlight_infos": highlight_infos,
        "coverage_context_result": state["coverage_context_result"],
        "contexto_negocios": state["contexto_negocios"],
        "model": gv(state, "model"),
        "temperature": gv(state, "temperature"),
        "max_retries": gv(state, "max_retries"),
    })
    print("-------> generate_coverage_insights_tool: done")

    return safe_node_output(node_name, {
        "insights": insights,
    })


def node_whatsapp(state: CoverageGraphState):
    from src.tools_agents.insights_structural.cs.whatsapp_insights.tools import generate_whatsapp_insights_message_tool

    node_name = "node_whatsapp"
    client = state["client"]

    big_number = (
        state.get("big_numbers", {})
        .get("payload", {})
        .get(client, {})
        .get("periodos", [{}])[0]
        .get("metricas")
    )

    if big_number is None:
        raise ValueError(
            f"[{node_name}] big_number não encontrado em "
            f"big_numbers.payload[{client}].periodos[0].metricas"
        )

    insights = state.get("insights")
    if insights is None:
        raise ValueError(f"[{node_name}] insights ausente no state.")

    coverage_context_result = state.get("coverage_context_result")
    if coverage_context_result is None:
        raise ValueError(f"[{node_name}] coverage_context_result ausente no state.")

    
    print('---> whatsapp')

    whatsapp_result = generate_whatsapp_insights_message_tool.invoke({
        "company_name": state.get("company_name", state["client_display_name"]),
        "analysis_period": state.get("period_label"),
        "big_number": big_number,
        "coverage_context_result": coverage_context_result,
        "insights": insights,
        "model": state.get("model", "gpt-4.1-mini"),
        "temperature": state.get("temperature", 0.2),
        "top_n_vehicles": state.get("top_n_vehicles", 5),
        "top_n_topics": state.get("top_n_topics", 4),
    })

    return safe_node_output(node_name, {
        "whatsapp_message": whatsapp_result,
    })


def node_meeting_insights(state: CoverageGraphState):
    from src.tools_agents.insights_structural.cs.meeting_insights.tools import (
        generate_meeting_script_tool,
    )

    node_name = "node_meeting_insights"
    client = state["client"]

    big_number = (
        state.get("big_numbers", {})
        .get("payload", {})
        .get(client, {})
        .get("periodos", [{}])[0]
        .get("metricas")
    )

    if big_number is None:
        raise ValueError(
            f"[{node_name}] big_number não encontrado em "
            f"big_numbers.payload[{client}].periodos[0].metricas"
        )

    insights = state.get("insights")
    if insights is None:
        raise ValueError(f"[{node_name}] insights ausente no state.")

    coverage_context_result = state.get("coverage_context_result")
    if coverage_context_result is None:
        raise ValueError(f"[{node_name}] coverage_context_result ausente no state.")

    print('---> script da reunião')
    meeting_result = generate_meeting_script_tool.invoke({
        "company_name": state.get("company_name", state["client_display_name"]),
        "analysis_period": state.get("period_label"),
        "big_number": big_number,
        "coverage_context_result": coverage_context_result,
        "insights": insights,
        "highlight_infos": state.get("highlights_results"),
        "contexto_negocios": state.get("contexto_negocios"),
        "model": state.get("model", "gpt-4.1-mini"),
        "temperature": state.get("temperature", 0.2),
        "max_retries": state.get("max_retries", 3),
    })

    return safe_node_output(node_name, {
        "meeting_insights": meeting_result,
        "meeting_script": meeting_result.get("result") if isinstance(meeting_result, dict) else None,
    })