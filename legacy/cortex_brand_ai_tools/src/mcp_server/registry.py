# src/mcp_server/registry.py


def get_langchain_insights():
    from src.tools_agents.insights_tools.tools import (
        insights_orchestrator_analysis_media_tool,
        insights_orchestrator_with_whatsapp_tool,
        insights_orchestrator_analysis_media_tool_async, 
        insights_orchestrator_with_whatsapp_tool_async
    )

    from src.tools_agents.insights_structural.tools import (
        generate_company_context_tool,
        generate_coverage_insights_tool,
    )

    from src.tools_agents.highlights.tools import generate_highlights_tool

    return [
        insights_orchestrator_analysis_media_tool,
        insights_orchestrator_with_whatsapp_tool,
        generate_company_context_tool,
        generate_coverage_insights_tool,
        generate_highlights_tool,
         insights_orchestrator_analysis_media_tool_async, 
        insights_orchestrator_with_whatsapp_tool_async
    ]


def get_langchain_platform():
    from src.tools_agents.platform.tools import (
        get_dataframe_tool,
        get_brand_info_tool,
        export_publications_database_tool,
        export_media_analysis_database_tool,
        export_action_database_tool,
        get_prdata_dataframe_tool,
        get_prdata_opensource_tool,
        get_mss_dataframe_tool,
    )

    return [
        get_dataframe_tool,
        get_brand_info_tool,
        export_publications_database_tool,
        export_media_analysis_database_tool,
        export_action_database_tool,
        get_prdata_dataframe_tool,
        get_prdata_opensource_tool,
        get_mss_dataframe_tool,
    ]


def get_langchain_measurements():
    from src.tools_agents.measurements.tools import (
        sentiment_classification_tool,
        protagonism_classification_tool,
        clustering_to_classification_tool,
        identify_entities_in_dataframe_tool,
        thems_classification_tool,
    )

    return [
        sentiment_classification_tool,
        protagonism_classification_tool,
        clustering_to_classification_tool,
        identify_entities_in_dataframe_tool,
        thems_classification_tool,
    ]


def get_langchain_index():
    from src.tools_agents.communication_indexes.tools import (
        gen_dataviews_tool,
        calc_nps_score_tool,
        nps_total_and_contrib_tool,
        protagonism_score_tool,
        freq_score_tool,
        valoration_score_tool,
        jornalista_score_tool,
        action_score_tool,
    )

    return [
        gen_dataviews_tool,
        calc_nps_score_tool,
        nps_total_and_contrib_tool,
        protagonism_score_tool,
        freq_score_tool,
        valoration_score_tool,
        jornalista_score_tool,
        action_score_tool,
    ]


def get_langchain_context():
    from src.tools_agents.analysis.coverage_context.tools import (
        extrair_contexto_noticias_tool,
        build_main_days_coverage_tool,
        build_top_vehicles_coverage_tool,
        build_specific_topics_reports_tool,
        build_coverage_summary_tool,
    )

    return [
        extrair_contexto_noticias_tool,
        build_main_days_coverage_tool,
        build_top_vehicles_coverage_tool,
        build_specific_topics_reports_tool,
        build_coverage_summary_tool,
    ]


def get_langchain_pattern():
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

    return [
        build_media_metrics_view_tool,
        build_media_metrics_view_by_source_tool,
        build_topic_contrib_df_tool,
        build_topic_contrib_llm_dict_tool,
        build_last_period_statistics_tool,
        build_company_big_number_dict_tool,
        build_sources_last_period_multi_company_dict_enriched_tool,
        build_daily_metrics_enriched_tool,
        build_daily_pattern_dict_tool,
    ]


def get_langchain_tools(groups: list[str] | None = None):
    """
    Carrega as tools sob demanda.

    groups disponíveis:
    - insights
    - platform
    - measurements
    - index
    - context
    - pattern
    """

    

    registry = {
        "insights": get_langchain_insights,
        "platform": get_langchain_platform,
        "measurements": get_langchain_measurements,
        "index": get_langchain_index,
        "context": get_langchain_context,
        "pattern": get_langchain_pattern,
    }


    if groups is None:
        groups = list(registry.keys())
    
    tools = []

    for group in groups:
        if group not in registry:
            raise ValueError(
                f"Grupo inválido: {group}. "
                f"Use um de: {list(registry.keys())}"
            )

        print(f">>> Carregando grupo de tools: {group}")
        tools.extend(registry[group]())

    return tools