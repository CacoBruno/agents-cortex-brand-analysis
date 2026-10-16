from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from cortex_brand_analysis.domain.errors import DomainError

Impact = Literal["Promotores", "Detratores", "Inócuos"]
PROTAGONISM_CATEGORIES = (
    "Citação relevante",
    "Figurante",
    "Referência contextual / Setor",
    "Protagonismo",
    "Referência em matéria de concorrente",
)


@dataclass(frozen=True)
class ExposureMethodV1:
    """Native implementation of the verified legacy reach-weighted formulas.

    Input rows must already reflect the authorized Cortex analytical universe.
    No classification inference, arbitrary code, or network access happens here.
    """

    reach_column: str = "alcance"
    impact_column: str = "Tipos de impactos"
    protagonism_column: str = "Nível de Protagonismo final"

    @staticmethod
    def _require(df: pd.DataFrame, columns: list[str]) -> None:
        missing = [column for column in columns if column not in df.columns]
        if missing:
            raise DomainError(f"missing analytical columns: {missing}")

    def nps(self, data: pd.DataFrame, group_by: list[str]) -> pd.DataFrame:
        self._require(data, group_by + [self.reach_column, self.impact_column])
        if not group_by:
            raise DomainError("at least one grouping column is required")
        pivot = data.pivot_table(
            index=group_by,
            columns=self.impact_column,
            values=self.reach_column,
            aggfunc="sum",
            fill_value=0,
        ).reset_index()
        for impact in ("Promotores", "Detratores", "Inócuos"):
            if impact not in pivot:
                pivot[impact] = 0
        denominator = pivot["Promotores"] + pivot["Detratores"] + pivot["Inócuos"]
        pivot["nps_score"] = (
            (pivot["Promotores"] - pivot["Detratores"])
            / denominator.where(denominator.ne(0))
        ).fillna(0).round(4)
        return pivot[group_by + ["Detratores", "Inócuos", "Promotores", "nps_score"]]

    def contribution(
        self,
        data: pd.DataFrame,
        group_by: list[str],
        dimension: str,
        contribution_type: Literal["Total", "Promotor"] = "Total",
    ) -> pd.DataFrame:
        if dimension in group_by:
            raise DomainError("dimension cannot be a grouping column")
        self._require(data, group_by + [dimension, self.reach_column, self.impact_column])
        totals = self.nps(data, group_by)
        totals["denom_total"] = (
            totals["Detratores"] + totals["Inócuos"] + totals["Promotores"]
        )
        dimensions = self.nps(data, group_by + [dimension])
        dimensions["total_dimension"] = (
            dimensions["Detratores"] + dimensions["Inócuos"] + dimensions["Promotores"]
        )
        result = dimensions.merge(
            totals[group_by + ["denom_total", "nps_score"]],
            on=group_by,
            suffixes=("_dimension", ""),
            validate="many_to_one",
        )
        numerator = (
            result["Promotores"]
            if contribution_type == "Promotor"
            else result["Promotores"] - result["Detratores"]
        )
        result["nps_contribution"] = (
            numerator / result["denom_total"].where(result["denom_total"].ne(0))
        ).fillna(0).round(4)
        return result[
            group_by
            + [dimension, "nps_score", "nps_contribution", "total_dimension", "denom_total"]
        ]

    def protagonism(self, data: pd.DataFrame, group_by: list[str]) -> pd.DataFrame:
        self._require(data, group_by + [self.reach_column, self.protagonism_column])
        pivot = data.pivot_table(
            index=group_by,
            columns=self.protagonism_column,
            values=self.reach_column,
            aggfunc="sum",
            fill_value=0,
        ).reset_index()
        for category in PROTAGONISM_CATEGORIES:
            if category not in pivot:
                pivot[category] = 0
        total = pivot[list(PROTAGONISM_CATEGORIES)].sum(axis=1)
        pivot["protagonism_score"] = (
            (pivot["Protagonismo"] + pivot["Referência contextual / Setor"])
            / total.where(total.ne(0))
        ).fillna(0).round(4)
        pivot["total"] = total
        return pivot[group_by + list(PROTAGONISM_CATEGORIES) + ["protagonism_score", "total"]]
