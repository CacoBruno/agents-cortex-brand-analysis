from __future__ import annotations

import pandas as pd

from cortex_brand_analysis.domain.analytics import (
    AnalyticsFilter,
    AnalyticsRequest,
    AnalyticsResult,
)
from cortex_brand_analysis.domain.errors import DomainError


def _validate_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise DomainError(f"unknown columns: {missing}")


def _apply_filter(df: pd.DataFrame, item: AnalyticsFilter) -> pd.DataFrame:
    _validate_columns(df, [item.column])
    series = df[item.column]

    if item.operator == "eq":
        return df[series == item.value]
    if item.operator == "ne":
        return df[series != item.value]
    if item.operator == "in":
        values = item.value if isinstance(item.value, list) else [item.value]
        return df[series.isin(values)]
    if item.operator == "contains":
        return df[series.astype(str).str.contains(str(item.value), case=False, na=False)]
    if item.operator == "gte":
        return df[series >= item.value]
    if item.operator == "lte":
        return df[series <= item.value]
    raise DomainError(f"unsupported operator: {item.operator}")


def _records(df: pd.DataFrame, limit: int) -> list[dict]:
    clean: pd.DataFrame = df.head(limit).copy()
    clean = clean.where(pd.notna(clean), None)  # type: ignore[call-overload]
    return clean.to_dict(orient="records")


class AnalyticsWorkflow:
    """Executes a fixed allow-list of analytical operations.

    No eval, exec, Python REPL, filesystem access, or network access is available.
    """

    def run(self, request: AnalyticsRequest) -> AnalyticsResult:
        df = pd.DataFrame(request.data)

        for item in request.filters:
            df = _apply_filter(df, item)

        if request.operation == "describe":
            columns = request.columns or df.select_dtypes(include="number").columns.tolist()
            _validate_columns(df, columns)
            result = df[columns].describe(include="all").transpose().reset_index()
            result = result.rename(columns={"index": "column"})
            return AnalyticsResult(
                operation=request.operation,
                rows=len(result),
                data=_records(result, request.limit),
                summary={"filtered_rows": len(df)},
            )

        if request.operation == "value_counts":
            if len(request.columns) != 1:
                raise DomainError("value_counts requires exactly one column")
            column = request.columns[0]
            _validate_columns(df, [column])
            result = (
                df[column].value_counts(dropna=False).rename_axis(column).reset_index(name="count")
            )
            return AnalyticsResult(
                operation=request.operation,
                rows=len(result),
                data=_records(result, request.limit),
                summary={"filtered_rows": len(df)},
            )

        if request.operation == "groupby":
            _validate_columns(df, request.group_by)
            if request.aggregation == "count":
                result = df.groupby(request.group_by, dropna=False).size().reset_index(name="count")
            else:
                assert request.metric is not None
                assert request.aggregation is not None
                _validate_columns(df, [request.metric])
                grouped = df.groupby(request.group_by, dropna=False)[request.metric]
                result = getattr(grouped, request.aggregation)().reset_index()
            return AnalyticsResult(
                operation=request.operation,
                rows=len(result),
                data=_records(result, request.limit),
                summary={"filtered_rows": len(df)},
            )

        if request.operation == "correlation":
            _validate_columns(df, request.columns)
            numeric = df[request.columns].apply(pd.to_numeric, errors="coerce")
            corr = numeric.corr().reset_index().rename(columns={"index": "variable"})
            return AnalyticsResult(
                operation=request.operation,
                rows=len(corr),
                data=_records(corr, request.limit),
                summary={"filtered_rows": len(df)},
            )

        if request.operation == "timeseries":
            assert request.date_column is not None
            assert request.frequency is not None
            _validate_columns(df, [request.date_column])
            work = df.copy()
            work[request.date_column] = pd.to_datetime(
                work[request.date_column],
                errors="coerce",
            )
            work = work.dropna(subset=[request.date_column]).set_index(request.date_column)

            if request.aggregation == "count":
                result = work.resample(request.frequency).size().reset_index(name="count")
            else:
                assert request.metric is not None
                assert request.aggregation is not None
                _validate_columns(work, [request.metric])
                numeric = pd.to_numeric(work[request.metric], errors="coerce")
                aggregated = getattr(
                    numeric.resample(request.frequency),
                    request.aggregation,
                )()
                result = aggregated.reset_index()

            return AnalyticsResult(
                operation=request.operation,
                rows=len(result),
                data=_records(result, request.limit),
                summary={"filtered_rows": len(df)},
            )

        raise DomainError(f"unsupported operation: {request.operation}")
