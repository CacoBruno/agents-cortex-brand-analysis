from __future__ import annotations

import pandas as pd

from cortex_brand_analysis.domain.communication_indexes import (
    CommunicationIndexRequest,
    CommunicationIndexResult,
)


def _validate(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"unknown columns: {missing}")


def _records(df: pd.DataFrame) -> list[dict]:
    clean = df.where(pd.notna(df), None)
    return clean.to_dict(orient="records")


class CommunicationIndexesWorkflow:
    def run(self, request: CommunicationIndexRequest) -> CommunicationIndexResult:
        df = pd.DataFrame(request.data)
        group_by = request.group_by

        if request.operation == "nps":
            result = self._nps(
                df,
                group_by,
                request.value_column or "alcance",
                request.impact_column or "Tipos de impactos",
            )
        elif request.operation == "nps_contribution":
            result = self._nps_contribution(
                df,
                group_by,
                request.dimension_column,
                request.value_column or "alcance",
                request.impact_column or "Tipos de impactos",
                request.contribution_type,
            )
        elif request.operation == "protagonism":
            result = self._protagonism(
                df,
                group_by,
                request.value_column or "alcance",
                request.impact_column or "Nível de Protagonismo final",
                request.filter_column,
                request.filter_value,
            )
        elif request.operation == "frequency":
            result = self._frequency(
                df,
                group_by,
                request.value_column or "frequencia",
                request.impact_column or "Tipos de impactos",
            )
        elif request.operation == "valoration":
            result = self._sum_single(
                df,
                group_by,
                request.value_column or "valoracao",
            )
        elif request.operation in {"journalist", "action"}:
            defaults = (
                ["jornalista_count", "count"]
                if request.operation == "journalist"
                else ["acao_count", "count"]
            )
            result = self._sum_multiple(
                df,
                group_by,
                request.value_columns or defaults,
            )
        else:
            raise ValueError(f"unsupported index operation: {request.operation}")

        return CommunicationIndexResult(
            operation=request.operation,
            rows=len(result),
            columns=list(result.columns),
            data=_records(result),
        )

    @staticmethod
    def _nps(
        df: pd.DataFrame,
        group_by: list[str],
        value_col: str,
        impact_col: str,
    ) -> pd.DataFrame:
        _validate(df, group_by + [value_col, impact_col])
        pivot = (
            df.pivot_table(
                index=group_by,
                columns=impact_col,
                values=value_col,
                aggfunc="sum",
                fill_value=0,
            )
            .reset_index()
        )
        for col in ["Promotores", "Detratores", "Inócuos"]:
            if col not in pivot.columns:
                pivot[col] = 0
        denom = pivot["Promotores"] + pivot["Detratores"] + pivot["Inócuos"]
        pivot["nps_score"] = (
            (pivot["Promotores"] - pivot["Detratores"])
            / denom.replace(0, pd.NA)
        ).fillna(0).round(4)
        return pivot

    @staticmethod
    def _nps_contribution(
        df: pd.DataFrame,
        group_by: list[str],
        dimension_col: str | None,
        value_col: str,
        impact_col: str,
        contribution_type: str,
    ) -> pd.DataFrame:
        assert dimension_col is not None
        _validate(df, group_by + [dimension_col, value_col, impact_col])

        impacts = ["Promotores", "Detratores", "Inócuos"]
        total = (
            df.pivot_table(
                index=group_by,
                columns=impact_col,
                values=value_col,
                aggfunc="sum",
                fill_value=0,
            )
            .reset_index()
        )
        for col in impacts:
            if col not in total.columns:
                total[col] = 0
        total["denom_total"] = total[impacts].sum(axis=1)
        total["nps_score"] = (
            (total["Promotores"] - total["Detratores"])
            / total["denom_total"].replace(0, pd.NA)
        ).fillna(0).round(2)

        dimension = (
            df.pivot_table(
                index=group_by + [dimension_col],
                columns=impact_col,
                values=value_col,
                aggfunc="sum",
                fill_value=0,
            )
            .reset_index()
        )
        for col in impacts:
            if col not in dimension.columns:
                dimension[col] = 0

        total_col = f"total_{dimension_col}"
        contrib_col = f"nps_contrib_{dimension_col}"
        dimension[total_col] = dimension[impacts].sum(axis=1)
        out = dimension.merge(
            total[group_by + ["denom_total", "nps_score"]],
            on=group_by,
            how="left",
        )
        numerator = (
            out["Promotores"]
            if contribution_type == "Promotor"
            else out["Promotores"] - out["Detratores"]
        )
        out[contrib_col] = (
            numerator / out["denom_total"].replace(0, pd.NA)
        ).fillna(0).round(4)
        return out[
            group_by
            + [dimension_col, "nps_score", contrib_col, total_col, "denom_total"]
        ].sort_values(group_by + [dimension_col]).reset_index(drop=True)

    @staticmethod
    def _protagonism(
        df: pd.DataFrame,
        group_by: list[str],
        value_col: str,
        impact_col: str,
        filter_column: str | None,
        filter_value: object | None,
    ) -> pd.DataFrame:
        if filter_column is not None and filter_value is not None:
            _validate(df, [filter_column])
            values = filter_value if isinstance(filter_value, list) else [filter_value]
            df = df[df[filter_column].isin(values)]

        _validate(df, group_by + [value_col, impact_col])
        pivot = (
            df.pivot_table(
                index=group_by,
                columns=impact_col,
                values=value_col,
                aggfunc="sum",
                fill_value=0,
            )
            .reset_index()
        )
        categories = [
            "Citação relevante",
            "Figurante",
            "Referência contextual / Setor",
            "Protagonismo",
            "Referência em matéria de concorrente",
        ]
        for col in categories:
            if col not in pivot.columns:
                pivot[col] = 0

        denom = pivot[categories].sum(axis=1).astype(float)
        pivot["protagonism_score"] = (
            (pivot["Protagonismo"] + pivot["Referência contextual / Setor"])
            / denom.where(denom != 0)
        ).fillna(0).round(4)
        pivot["total"] = denom
        return pivot

    @staticmethod
    def _frequency(
        df: pd.DataFrame,
        group_by: list[str],
        value_col: str,
        impact_col: str,
    ) -> pd.DataFrame:
        _validate(df, group_by + [value_col, impact_col])
        pivot = (
            df.pivot_table(
                index=group_by,
                columns=impact_col,
                values=value_col,
                aggfunc="sum",
                fill_value=0,
            )
            .reset_index()
        )

        groups = [
            ["Promotores", "Detratores", "Inócuos"],
            ["Positivo", "Negativo", "Neutro", "-"],
        ]
        for categories in groups:
            if any(col in pivot.columns for col in categories):
                for col in categories:
                    if col not in pivot.columns:
                        pivot[col] = 0
                pivot["total"] = pivot[categories].sum(axis=1)
                safe_total = pivot["total"].replace(0, pd.NA)
                for col in categories:
                    pivot[f"% {col}"] = (pivot[col] / safe_total).fillna(0)
                break
        return pivot

    @staticmethod
    def _sum_single(
        df: pd.DataFrame,
        group_by: list[str],
        value_col: str,
    ) -> pd.DataFrame:
        _validate(df, group_by + [value_col])
        result = (
            df.pivot_table(
                index=group_by,
                values=value_col,
                aggfunc="sum",
                fill_value=0,
            )
            .reset_index()
        )
        result[value_col] = result[value_col].round(2)
        return result

    @staticmethod
    def _sum_multiple(
        df: pd.DataFrame,
        group_by: list[str],
        value_cols: list[str],
    ) -> pd.DataFrame:
        _validate(df, group_by + value_cols)
        return (
            df.pivot_table(
                index=group_by,
                values=value_cols,
                aggfunc="sum",
                fill_value=0,
            )
            .reset_index()
        )
