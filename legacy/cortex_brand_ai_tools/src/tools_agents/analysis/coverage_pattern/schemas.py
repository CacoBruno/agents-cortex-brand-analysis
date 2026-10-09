from __future__ import annotations

from typing import Any, Dict, List, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field


PeriodType = Literal["dia", "semana", "mes", "mês", "ano"]
MetricsReturnType = Literal["nps", "protagonismo", "frequencia", "merged"]


class MediaMetricsViewInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: str | list[str] | None = Field(default=None)
    contest: str | list[str] | None = Field(default=None)
    focus_analysis: str = Field(default="Empresa analisada")
    period: PeriodType = Field(default="dia")
    return_metric: MetricsReturnType = Field(default="merged")


class MediaMetricsViewBySourceInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: str | list[str] | None = Field(default=None)
    contest: str | list[str] | None = Field(default=None)
    focus_analysis: str = Field(default="Empresa analisada")
    source_cols: list[str] = Field(default_factory=lambda: ["Fonte", "Mídia"])
    period: PeriodType = Field(default="dia")
    return_metric: MetricsReturnType = Field(default="merged")


class TopicContribInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: str | list[str] | None = Field(default=None)
    contest: str | list[str] | None = Field(default=None)
    period: PeriodType = Field(default="mes")
    focus_analysis: str = Field(default="Empresa analisada")
    topic_col: str = Field(default="Assunto específico")
    rename_nps_group: str = Field(default="nps_score_periodo")
    rename_nps_contrib: str = Field(default="nps_contrib_assunto_especifico")
    rename_total_topic: str = Field(default="total_assunto_especifico")
    rename_denom_total: str = Field(default="denom_total")
    sort_by: list[str] | None = Field(default=None)
    ascending: bool = Field(default=False)


class TopicContribLLMInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: str = Field(...)
    competitors: list[str] | None = Field(default=None)
    focus_analysis: str = Field(default="Empresa analisada")
    topic_col: str = Field(default="Assunto específico")
    daily_period_col: str | None = Field(default="dia")
    period_period_col: str | None = Field(default="mes")
    contrib_col: str = Field(default="nps_contrib_assunto_especifico")
    total_topic_col: str = Field(default="total_assunto_especifico")
    nps_period_col: str = Field(default="nps_score_periodo")
    denom_total_col: str = Field(default="denom_total")
    top_n_topics_period: int | None = Field(default=10)
    top_n_topics_per_day: int | None = Field(default=5)


class LastPeriodStatisticsInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: str = Field(...)
    competitors: list[str] | None = Field(default=None)
    period_col: str | None = Field(default=None)


class SourcesLastPeriodInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: str = Field(...)
    competitors: list[str] | None = Field(default=None)
    period_col: str | None = Field(default=None)
    include_metrics: list[str] | None = Field(default=None)
    sort_by: str = Field(default="alcance")
    ascending: bool = Field(default=False)


class BigNumberInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    pass


class DailyMetricsEnrichedInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: str | list[str] | None = Field(default=None)
    contest: str | list[str] | None = Field(default=None)
    focus_analysis: str = Field(default="Empresa analisada")
    period: str = Field(default="dia")
    contrib_dim_col: str = Field(default="dia")
    contrib_group_cols: list[str] = Field(
        default_factory=lambda: ["mes", "mes_index", "Empresa analisada"]
    )
    merge_how: str = Field(default="left")
    merge_validate: str = Field(default="one_to_one")
    rename_nps_daily: str = Field(default="nps_score_dia")
    rename_protagonism_daily: str = Field(default="protagonism_score_dia")
    rename_nps_contrib_base: str = Field(default="nps_score_mes")
    contrib_col_name: str = Field(default="nps_contrib_dia")


class DailyPatternDictInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: str = Field(...)
    competitors: list[str] | None = Field(default=None)
    focus_analysis: str = Field(default="Empresa analisada")
    date_col: str = Field(default="dia")
    date_index_col: str = Field(default="dia_index")
    top_n_days: int = Field(default=10)
    contrib_col: str = Field(default="nps_contrib_dia")


class DataFrameToolInput(BaseModel):
    df_id: str = Field(..., description="ID do dataframe salvo no DATAFRAME_STORE.")


class BuildMediaMetricsViewToolInput(DataFrameToolInput, MediaMetricsViewInput):
    pass


class BuildMediaMetricsViewBySourceToolInput(DataFrameToolInput, MediaMetricsViewBySourceInput):
    pass


class BuildTopicContribToolInput(DataFrameToolInput, TopicContribInput):
    pass


class BuildLastPeriodStatisticsToolInput(DataFrameToolInput, LastPeriodStatisticsInput):
    pass


class BuildSourcesLastPeriodToolInput(DataFrameToolInput, SourcesLastPeriodInput):
    pass


class BuildBigNumbersToolInput(DataFrameToolInput, BigNumberInput):
    pass


class BuildDailyMetricsEnrichedToolInput(DataFrameToolInput, DailyMetricsEnrichedInput):
    pass


class BuildDailyPatternDictToolInput(DataFrameToolInput, DailyPatternDictInput):
    pass


class BuildTopicContribLLMToolInput(BaseModel):
    df_daily_id: str = Field(...)
    df_period_id: str = Field(...)
    client: str = Field(...)
    competitors: list[str] | None = Field(default=None)
    focus_analysis: str = Field(default="Empresa analisada")
    topic_col: str = Field(default="Assunto específico")
    daily_period_col: str | None = Field(default="dia")
    period_period_col: str | None = Field(default="mes")
    contrib_col: str = Field(default="nps_contrib_assunto_especifico")
    total_topic_col: str = Field(default="total_assunto_especifico")
    nps_period_col: str = Field(default="nps_score_periodo")
    denom_total_col: str = Field(default="denom_total")
    top_n_topics_period: int | None = Field(default=10)
    top_n_topics_per_day: int | None = Field(default=5)


class ToolResult(BaseModel):
    success: bool = Field(default=True)
    message: str = Field(default="ok")
    payload: Dict[str, Any] | List[Dict[str, Any]] | List[Any] | Any = Field(default_factory=dict)
