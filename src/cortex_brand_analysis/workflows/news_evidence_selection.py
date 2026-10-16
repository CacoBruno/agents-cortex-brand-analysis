from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from cortex_brand_analysis.domain.errors import DomainError


@dataclass(frozen=True)
class NewsEvidenceSelectionV1:
    """Deterministic legacy-compatible ranking primitives, no article generation."""

    @staticmethod
    def _validate(df: pd.DataFrame, columns: list[str]) -> None:
        missing = [name for name in columns if name not in df.columns]
        if missing:
            raise DomainError(f"missing evidence columns: {missing}")

    def key_days(
        self,
        daily: pd.DataFrame,
        *,
        date_col: str = "Data",
        contribution_col: str = "contr_nps_score",
        promoter_col: str = "Promotores",
        detractor_col: str = "Detratores",
        zscore_col: str = "z_score_contr_nps",
        extra_positive: int = 0,
        extra_negative: int = 0,
    ) -> dict[str, object]:
        """Legacy default mode: extrema from five metrics plus optional extras."""
        columns = [date_col, contribution_col, promoter_col, detractor_col, zscore_col]
        self._validate(daily, columns)
        if min(extra_positive, extra_negative) < 0:
            raise DomainError("extra day counts must not be negative")
        frame = daily[columns].copy()
        frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce").dt.strftime(
            "%Y-%m-%d"
        )
        frame = frame.dropna(subset=[date_col])
        for column in columns[1:]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        specs = {
            "dia_maior_contribuicao_nps": (contribution_col, "max"),
            "dia_maior_detracao_nps": (contribution_col, "min"),
            "dia_maior_promotor": (promoter_col, "max"),
            "dia_maior_detrator": (detractor_col, "max"),
            "dia_maior_zscore": (zscore_col, "max"),
        }
        rules: dict[str, str | None] = {}
        for name, (column, method) in specs.items():
            valid = frame.dropna(subset=[column])
            if valid.empty:
                rules[name] = None
            else:
                index = valid[column].idxmax() if method == "max" else valid[column].idxmin()
                rules[name] = str(valid.loc[index, date_col])
        selected = [value for value in rules.values() if value is not None]
        for positive, count in ((True, extra_positive), (False, extra_negative)):
            valid = frame.dropna(subset=[contribution_col])
            valid = valid[
                valid[contribution_col].gt(0)
                if positive
                else valid[contribution_col].lt(0)
            ]
            selected.extend(
                valid.sort_values(contribution_col, ascending=not positive)
                .head(count)[date_col]
                .tolist()
            )
        days = list(dict.fromkeys(selected))
        reverse: dict[str, list[str]] = {}
        for rule, day in rules.items():
            if day is not None:
                reverse.setdefault(day, []).append(rule)
        summary = {}
        for _, row in frame[frame[date_col].isin(days)].drop_duplicates(date_col).iterrows():
            summary[row[date_col]] = {
                "contribuicao_nps": row[contribution_col],
                "promotores": row[promoter_col],
                "detratores": row[detractor_col],
                "z_score": row[zscore_col],
            }
        return {
            "selected_days": days,
            "rules": rules,
            "summary": summary,
            "reverse_rules": reverse,
        }

    def top_vehicles(
        self,
        vehicles: pd.DataFrame,
        *,
        source_col: str = "Fonte",
        promoter_col: str = "Promotores",
        detractor_col: str = "Detratores",
        top_n: int = 10,
    ) -> pd.DataFrame:
        """Legacy composite score, including the same tie-break ordering."""
        self._validate(vehicles, [source_col, promoter_col, detractor_col])
        if top_n < 0:
            raise DomainError("top_n must be nonnegative")
        frame = vehicles[[source_col, promoter_col, detractor_col]].copy()
        for column in (promoter_col, detractor_col):
            frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)
        frame["composite_score"] = frame[promoter_col] - frame[detractor_col]
        return (
            frame.sort_values(
                ["composite_score", promoter_col, detractor_col],
                ascending=[False, False, True],
            )
            .dropna(subset=[source_col])
            .drop_duplicates(subset=[source_col])
            .head(top_n)
            .reset_index(drop=True)
        )

    def top_topics(
        self,
        topics: pd.DataFrame,
        *,
        topic_col: str = "Assunto específico",
        contribution_col: str = "nps_contrib_assunto_especifico",
        total_col: str = "total_assunto_especifico",
        score_col: str = "nps_score_assunto_especifico",
        top_n: int = 5,
    ) -> dict[str, list[dict]]:
        """Legacy topic rankings; callers must apply period/company filters first."""
        cols = [topic_col, contribution_col, total_col, score_col]
        self._validate(topics, cols)
        if top_n < 0:
            raise DomainError("top_n must be nonnegative")
        frame = topics[cols].copy()
        for column in cols[1:]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=[topic_col])
        positive = (
            frame[frame[contribution_col] > 0]
            .sort_values(cols[1:], ascending=[False, False, False])
            .drop_duplicates(topic_col)
            .head(top_n)
        )
        negative = (
            frame[frame[contribution_col] < 0]
            .sort_values(cols[1:], ascending=[True, False, True])
            .drop_duplicates(topic_col)
            .head(top_n)
        )
        return {
            "assuntos_promotores": positive.to_dict(orient="records"),
            "assuntos_detratores": negative.to_dict(orient="records"),
        }
