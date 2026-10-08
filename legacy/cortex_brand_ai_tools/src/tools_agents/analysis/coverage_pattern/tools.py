from __future__ import annotations

from typing import Any

import pandas as pd
from langchain_core.tools import tool

from src.tools_agents.analysis.coverage_pattern.schemas import (
    BigNumberInput,
    BuildBigNumbersToolInput,
    BuildDailyMetricsEnrichedToolInput,
    BuildDailyPatternDictToolInput,
    BuildLastPeriodStatisticsToolInput,
    BuildMediaMetricsViewBySourceToolInput,
    BuildMediaMetricsViewToolInput,
    BuildSourcesLastPeriodToolInput,
    BuildTopicContribLLMToolInput,
    BuildTopicContribToolInput,
    DailyMetricsEnrichedInput,
    DailyPatternDictInput,
    LastPeriodStatisticsInput,
    MediaMetricsViewBySourceInput,
    MediaMetricsViewInput,
    SourcesLastPeriodInput,
    ToolResult,
    TopicContribInput,
    TopicContribLLMInput,
)
from src.tools_agents.analysis.coverage_pattern.services import MediaPatternService

try:
    from core.dataframe_store import get_dataframe, save_dataframe
except Exception:
    DATAFRAME_STORE: dict[str, dict[str, Any]] = {}

    def get_dataframe(df_id: str) -> pd.DataFrame:
        if df_id not in DATAFRAME_STORE:
            raise KeyError(f"df_id não encontrado: {df_id}")
        return DATAFRAME_STORE[df_id]["df"]

    def save_dataframe(
        df: pd.DataFrame,
        source: str,
        filters: dict[str, Any] | None = None,
    ) -> str:
        import uuid

        df_id = str(uuid.uuid4())
        DATAFRAME_STORE[df_id] = {
            "df": df.copy(),
            "source": source,
            "filters": filters or {},
            "rows": len(df),
            "columns": list(df.columns),
        }
        return df_id


service = MediaPatternService()


def _df_preview(df: pd.DataFrame, n: int = 10) -> list[dict[str, Any]]:
    return df.head(n).to_dict(orient="records")


@tool("build_media_metrics_view_tool", args_schema=BuildMediaMetricsViewToolInput)
def build_media_metrics_view_tool(**kwargs) -> dict[str, Any]:
    """
    Gera um dataframe agregado de métricas de mídia a partir de um dataframe salvo.

    Esta tool calcula a visão consolidada por período, retornando métricas como
    NPS, protagonismo, frequência ou o merge completo, conforme o parâmetro
    `return_metric`.

    Inputs:
    - df_id: ID do dataframe base salvo no DATAFRAME_STORE.
    - client: empresa principal da análise.
    - contest: concorrentes da análise (opcional).
    - focus_analysis: coluna de foco analítico. Ex.: "Empresa analisada".
    - period: granularidade temporal. Ex.: "dia", "semana", "mes", "ano".
    - return_metric: "nps", "protagonismo", "frequencia" ou "merged".

    Output:
    - df_id: ID do novo dataframe salvo.
    - rows: número de linhas do resultado.
    - columns: colunas do dataframe gerado.
    - preview: amostra das primeiras linhas.
    """
    params = BuildMediaMetricsViewToolInput(**kwargs)
    df = get_dataframe(params.df_id)

    result_df = service.build_media_metrics_view(
        dataview_df=df,
        params=MediaMetricsViewInput(
            client=params.client,
            contest=params.contest,
            focus_analysis=params.focus_analysis,
            period=params.period,
            return_metric=params.return_metric,
        ),
    )

    result_id = save_dataframe(
        result_df,
        source="build_media_metrics_view_tool",
        filters=params.model_dump(),
    )

    return ToolResult(
        payload={
            "df_id": result_id,
            "rows": len(result_df),
            "columns": list(result_df.columns),
            "preview": _df_preview(result_df),
        }
    ).model_dump()


@tool("build_media_metrics_view_by_source_tool",  args_schema=BuildMediaMetricsViewToolInput)
def build_media_metrics_view_by_source_tool(**kwargs) -> dict[str, Any]:
    """
    Gera um dataframe agregado de métricas de mídia por período e por fonte.

    Esta tool calcula a visão consolidada por período + colunas editoriais
    (`source_cols`), retornando métricas como NPS, protagonismo, frequência
    ou o merge completo.

    Inputs:
    - df_id: ID do dataframe base salvo no DATAFRAME_STORE.
    - client: empresa principal da análise.
    - contest: concorrentes da análise (opcional).
    - focus_analysis: coluna de foco analítico. Ex.: "Empresa analisada".
    - source_cols: colunas de agrupamento editorial. Ex.: ["Fonte", "Mídia"].
    - period: granularidade temporal. Ex.: "dia", "semana", "mes", "ano".
    - return_metric: "nps", "protagonismo", "frequencia" ou "merged".

    Output:
    - df_id: ID do novo dataframe salvo.
    - rows: número de linhas do resultado.
    - columns: colunas do dataframe gerado.
    - preview: amostra das primeiras linhas.
    """
    params = BuildMediaMetricsViewBySourceToolInput(**kwargs)
    df = get_dataframe(params.df_id)

    result_df = service.build_media_metrics_view_by_source(
        dataview_df=df,
        params=MediaMetricsViewBySourceInput(
            client=params.client,
            contest=params.contest,
            focus_analysis=params.focus_analysis,
            source_cols=params.source_cols,
            period=params.period,
            return_metric=params.return_metric,
        ),
    )

    result_id = save_dataframe(
        result_df,
        source="build_media_metrics_view_by_source_tool",
        filters=params.model_dump(),
    )

    return ToolResult(
        payload={
            "df_id": result_id,
            "rows": len(result_df),
            "columns": list(result_df.columns),
            "preview": _df_preview(result_df),
        }
    ).model_dump()


@tool("build_topic_contrib_df_tool", args_schema=BuildMediaMetricsViewToolInput)
def build_topic_contrib_df_tool(**kwargs) -> dict[str, Any]:
    """
    Calcula a contribuição de NPS por assunto específico dentro de um período.

    Esta tool gera um dataframe com o NPS do assunto, o NPS do período,
    o volume por assunto e a contribuição proporcional do assunto
    para a construção do NPS no período.

    Inputs:
    - df_id: ID do dataframe base salvo.
    - client: empresa principal.
    - contest: concorrentes (opcional).
    - period: granularidade temporal. Ex.: "dia", "semana", "mes".
    - focus_analysis: coluna de foco analítico.
    - topic_col: coluna do assunto específico.
    - rename_*: parâmetros opcionais para renomear colunas de saída.
    - sort_by: colunas de ordenação (opcional).
    - ascending: direção de ordenação.

    Output:
    - df_id: ID do novo dataframe salvo.
    - rows: número de linhas.
    - columns: colunas do dataframe gerado.
    - preview: amostra das primeiras linhas.
    """
    params = BuildTopicContribToolInput(**kwargs)
    df = get_dataframe(params.df_id)

    result_df = service.build_topic_contrib_df(
        dataview_df=df,
        params=TopicContribInput(
            client=params.client,
            contest=params.contest,
            period=params.period,
            focus_analysis=params.focus_analysis,
            topic_col=params.topic_col,
            rename_nps_group=params.rename_nps_group,
            rename_nps_contrib=params.rename_nps_contrib,
            rename_total_topic=params.rename_total_topic,
            rename_denom_total=params.rename_denom_total,
            sort_by=params.sort_by,
            ascending=params.ascending,
        ),
    )

    result_id = save_dataframe(
        result_df,
        source="build_topic_contrib_df_tool",
        filters=params.model_dump(),
    )

    return ToolResult(
        payload={
            "df_id": result_id,
            "rows": len(result_df),
            "columns": list(result_df.columns),
            "preview": _df_preview(result_df),
        }
    ).model_dump()


@tool("build_topic_contrib_llm_dict_tool", args_schema=BuildTopicContribLLMToolInput)
def build_topic_contrib_llm_dict_tool(**kwargs) -> dict[str, Any]:
    """
    Gera um dicionário estruturado para LLM com os principais assuntos do período e por dia.

    Esta tool consome dois dataframes já preparados:
    - um dataframe diário de contribuição por assunto;
    - um dataframe do período agregado por assunto.

    Inputs:
    - df_daily_id: ID do dataframe diário salvo.
    - df_period_id: ID do dataframe agregado do período salvo.
    - client: empresa principal.
    - competitors: concorrentes (opcional).
    - focus_analysis: coluna de foco analítico.
    - topic_col: coluna de assunto específico.
    - daily_period_col: coluna temporal diária.
    - period_period_col: coluna temporal do período.
    - contrib_col: coluna de contribuição de NPS.
    - total_topic_col: coluna de volume do assunto.
    - nps_period_col: coluna de NPS do período.
    - denom_total_col: coluna do denominador total.
    - top_n_topics_period: quantidade de assuntos principais do período.
    - top_n_topics_per_day: quantidade de assuntos principais por dia.

    Output:
    - payload: dicionário estruturado pronto para uso por LLM.
    """
    params = BuildTopicContribLLMToolInput(**kwargs)

    assunto_df_daily = get_dataframe(params.df_daily_id)
    assunto_df_period = get_dataframe(params.df_period_id)

    payload = service.build_topic_contrib_llm(
        assunto_df_daily=assunto_df_daily,
        assunto_df_period=assunto_df_period,
        params=TopicContribLLMInput(
            client=params.client,
            competitors=params.competitors,
            focus_analysis=params.focus_analysis,
            topic_col=params.topic_col,
            daily_period_col=params.daily_period_col,
            period_period_col=params.period_period_col,
            contrib_col=params.contrib_col,
            total_topic_col=params.total_topic_col,
            nps_period_col=params.nps_period_col,
            denom_total_col=params.denom_total_col,
            top_n_topics_period=params.top_n_topics_period,
            top_n_topics_per_day=params.top_n_topics_per_day,
        ),
    )

    return ToolResult(payload=payload).model_dump()


@tool("build_last_period_statistics_tool", args_schema=BuildMediaMetricsViewToolInput)
def build_last_period_statistics_tool(**kwargs) -> dict[str, Any]:
    """
    Gera estatísticas detalhadas do último período a partir de um index_df salvo.

    A saída é útil para leituras analíticas, highlights e prompts de LLM,
    trazendo variações, médias históricas, extremos e z-score.

    Inputs:
    - df_id: ID do index_df salvo.
    - client: empresa principal.
    - competitors: concorrentes (opcional).
    - period_col: coluna explícita do período (opcional).

    Output:
    - payload: dicionário com estatísticas enriquecidas do último período.
    """
    params = BuildLastPeriodStatisticsToolInput(**kwargs)
    index_df = get_dataframe(params.df_id)

    payload = service.build_last_period_statistics(
        index_df=index_df,
        params=LastPeriodStatisticsInput(
            client=params.client,
            competitors=params.competitors,
            period_col=params.period_col,
        ),
    )

    return ToolResult(payload=payload).model_dump()


@tool("build_company_big_number_dict_tool", args_schema=BuildMediaMetricsViewToolInput)
def build_company_big_number_dict_tool(**kwargs) -> dict[str, Any]:
    """
    Gera os big numbers da empresa a partir de um index_df salvo.

    Esta tool retorna indicadores executivos consolidados, úteis para
    slides, WhatsApp e sínteses rápidas de performance.

    Inputs:
    - df_id: ID do index_df salvo.

    Output:
    - payload: dicionário com os big numbers da empresa.
    """
    params = BuildBigNumbersToolInput(**kwargs)
    index_df = get_dataframe(params.df_id)

    payload = service.build_big_numbers(
        index_df=index_df,
        params=BigNumberInput(),
    )

    return ToolResult(payload=payload).model_dump()


@tool("build_sources_last_period_multi_company_dict_enriched_tool", args_schema=BuildMediaMetricsViewToolInput)
def build_sources_last_period_multi_company_dict_enriched_tool(**kwargs) -> dict[str, Any]:
    """
    Gera um dicionário estruturado com as principais fontes do último período.

    Esta tool consome um dataframe por fonte já agregado e devolve uma estrutura
    enriquecida com indicadores, leituras determinísticas e padrão de mídia por fonte.

    Inputs:
    - df_id: ID do dataframe por fonte salvo.
    - client: empresa principal.
    - competitors: concorrentes (opcional).
    - period_col: coluna explícita do período (opcional).
    - include_metrics: lista opcional de métricas a incluir.
    - sort_by: coluna de ordenação das fontes. Ex.: "alcance".
    - ascending: direção da ordenação.

    Output:
    - payload: dicionário estruturado com as fontes do último período.
    """
    params = BuildSourcesLastPeriodToolInput(**kwargs)
    fonte_df = get_dataframe(params.df_id)

    payload = service.build_sources_last_period(
        fonte_df=fonte_df,
        params=SourcesLastPeriodInput(
            client=params.client,
            competitors=params.competitors,
            period_col=params.period_col,
            include_metrics=params.include_metrics,
            sort_by=params.sort_by,
            ascending=params.ascending,
        ),
    )

    return ToolResult(payload=payload).model_dump()


@tool("build_daily_metrics_enriched_tool", args_schema=BuildMediaMetricsViewToolInput)
def build_daily_metrics_enriched_tool(**kwargs) -> dict[str, Any]:
    """
    Gera um dataframe diário enriquecido com métricas e contribuição de NPS.

    A tool combina NPS diário, protagonismo diário, base agregada do período,
    contribuição diária para o NPS e métricas auxiliares como z-score de alcance.

    Inputs:
    - df_id: ID do dataframe base salvo.
    - client: empresa principal.
    - contest: concorrentes (opcional).
    - focus_analysis: coluna de foco analítico.
    - period: deve ser "dia".
    - contrib_dim_col: dimensão da contribuição.
    - contrib_group_cols: agrupamento base da contribuição.
    - merge_how: tipo de merge.
    - merge_validate: validação estrutural do merge.
    - rename_nps_daily: renome da coluna de NPS diário.
    - rename_protagonism_daily: renome da coluna de protagonismo diário.
    - rename_nps_contrib_base: renome do NPS base do período.
    - contrib_col_name: nome final da coluna de contribuição.

    Output:
    - df_id: ID do novo dataframe salvo.
    - rows: número de linhas.
    - columns: colunas do dataframe gerado.
    - preview: amostra das primeiras linhas.
    """
    params = BuildDailyMetricsEnrichedToolInput(**kwargs)
    df = get_dataframe(params.df_id)

    result_df = service.build_daily_metrics_enriched(
        dataview_df=df,
        params=DailyMetricsEnrichedInput(
            client=params.client,
            contest=params.contest,
            focus_analysis=params.focus_analysis,
            period=params.period,
            contrib_dim_col=params.contrib_dim_col,
            contrib_group_cols=params.contrib_group_cols,
            merge_how=params.merge_how,
            merge_validate=params.merge_validate,
            rename_nps_daily=params.rename_nps_daily,
            rename_protagonism_daily=params.rename_protagonism_daily,
            rename_nps_contrib_base=params.rename_nps_contrib_base,
            contrib_col_name=params.contrib_col_name,
        ),
    )

    result_id = save_dataframe(
        result_df,
        source="build_daily_metrics_enriched_tool",
        filters=params.model_dump(),
    )

    return ToolResult(
        payload={
            "df_id": result_id,
            "rows": len(result_df),
            "columns": list(result_df.columns),
            "preview": _df_preview(result_df),
        }
    ).model_dump()


@tool("build_daily_pattern_dict_tool", args_schema=BuildMediaMetricsViewToolInput)
def build_daily_pattern_dict_tool(**kwargs) -> dict[str, Any]:
    """
    Gera um dicionário diário estruturado para LLM a partir do dataframe enriquecido.

    Esta tool resume os dias mais relevantes do período, organizando a
    leitura diária da cobertura para uso em highlights, reuniões e roteiros.

    Inputs:
    - df_id: ID do dataframe diário enriquecido salvo.
    - client: empresa principal.
    - competitors: concorrentes (opcional).
    - focus_analysis: coluna de foco analítico.
    - date_col: coluna de data.
    - date_index_col: coluna de ordenação temporal.
    - top_n_days: quantidade de dias mais relevantes.
    - contrib_col: coluna de contribuição diária.

    Output:
    - payload: dicionário estruturado com os padrões diários da cobertura.
    """
    params = BuildDailyPatternDictToolInput(**kwargs)
    contr_dia_df = get_dataframe(params.df_id)

    payload = service.build_daily_pattern_dict(
        contr_dia_df=contr_dia_df,
        params=DailyPatternDictInput(
            client=params.client,
            competitors=params.competitors,
            focus_analysis=params.focus_analysis,
            date_col=params.date_col,
            date_index_col=params.date_index_col,
            top_n_days=params.top_n_days,
            contrib_col=params.contrib_col,
        ),
    )

    return ToolResult(payload=payload).model_dump()


ALL_MEDIA_PATTERN_TOOLS = [
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
