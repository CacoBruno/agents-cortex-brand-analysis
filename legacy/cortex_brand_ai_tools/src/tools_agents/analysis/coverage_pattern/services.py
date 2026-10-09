from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.tools_agents.analysis.coverage_pattern.schemas import (
    BigNumberInput,
    DailyMetricsEnrichedInput,
    DailyPatternDictInput,
    LastPeriodStatisticsInput,
    MediaMetricsViewBySourceInput,
    MediaMetricsViewInput,
    SourcesLastPeriodInput,
    TopicContribInput,
    TopicContribLLMInput,
)
from services.coverage_pattern.pattern_and_statistic import (
    build_company_big_number_dict,
    build_daily_media_metrics_with_nps_contrib_enriched,
    build_daily_media_pattern_dict,
    build_media_metrics_view,
    build_media_metrics_view_by_source,
    build_media_statistics_last_period_enriched,
    build_nps_contrib_by_specific_topic,
    build_sources_last_period_multi_company_dict_enriched,
    build_topic_contrib_llm_dict,
)


@dataclass(slots=True)
class MediaPatternService:
    """
    Fachada de serviço para encapsular as funções analíticas de pattern_and_statistic.
    """

    def build_media_metrics_view(
        self,
        dataview_df: pd.DataFrame,
        params: MediaMetricsViewInput,
    ) -> pd.DataFrame:
        return build_media_metrics_view(
            dataview_df=dataview_df,
            client=params.client,
            contest=params.contest,
            focus_analysis=params.focus_analysis,
            period=params.period,
            return_metric=params.return_metric,
        )

    def build_media_metrics_view_by_source(
        self,
        dataview_df: pd.DataFrame,
        params: MediaMetricsViewBySourceInput,
    ) -> pd.DataFrame:
        return build_media_metrics_view_by_source(
            dataview_df=dataview_df,
            client=params.client,
            contest=params.contest,
            focus_analysis=params.focus_analysis,
            source_cols=params.source_cols,
            period=params.period,
            return_metric=params.return_metric,
        )

    def build_topic_contrib_df(
        self,
        dataview_df: pd.DataFrame,
        params: TopicContribInput,
    ) -> pd.DataFrame:
        return build_nps_contrib_by_specific_topic(
            dataview_df=dataview_df,
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
        )

    def build_topic_contrib_llm(
        self,
        assunto_df_daily: pd.DataFrame,
        assunto_df_period: pd.DataFrame,
        params: TopicContribLLMInput,
    ) -> dict[str, Any]:
        return build_topic_contrib_llm_dict(
            assunto_df_daily=assunto_df_daily,
            assunto_df_period=assunto_df_period,
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
        )

    def build_last_period_statistics(
        self,
        index_df: pd.DataFrame,
        params: LastPeriodStatisticsInput,
    ) -> dict[str, Any]:
        return build_media_statistics_last_period_enriched(
            index_df=index_df,
            client=params.client,
            competitors=params.competitors,
            period_col=params.period_col,
        )

    def build_sources_last_period(
        self,
        fonte_df: pd.DataFrame,
        params: SourcesLastPeriodInput,
    ) -> dict[str, Any]:
        return build_sources_last_period_multi_company_dict_enriched(
            fonte_df=fonte_df,
            client=params.client,
            competitors=params.competitors,
            period_col=params.period_col,
            include_metrics=params.include_metrics,
            sort_by=params.sort_by,
            ascending=params.ascending,
        )

    def build_big_numbers(
        self,
        index_df: pd.DataFrame,
        params: BigNumberInput | None = None,
    ) -> dict[str, Any]:
        _ = params
        return build_company_big_number_dict(index_df)

    def build_daily_metrics_enriched(
        self,
        dataview_df: pd.DataFrame,
        params: DailyMetricsEnrichedInput,
    ) -> pd.DataFrame:
        return build_daily_media_metrics_with_nps_contrib_enriched(
            dataview_df=dataview_df,
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
        )

    def build_daily_pattern_dict(
        self,
        contr_dia_df: pd.DataFrame,
        params: DailyPatternDictInput,
    ) -> dict[str, Any]:
        return build_daily_media_pattern_dict(
            contr_dia_df=contr_dia_df,
            client=params.client,
            competitors=params.competitors,
            focus_analysis=params.focus_analysis,
            date_col=params.date_col,
            date_index_col=params.date_index_col,
            top_n_days=params.top_n_days,
            contrib_col=params.contrib_col,
        )
