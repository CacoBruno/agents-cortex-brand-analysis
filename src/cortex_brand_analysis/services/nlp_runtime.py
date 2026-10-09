from __future__ import annotations

from typing import Any

import pandas as pd

from cortex_brand_analysis.domain.nlp import NlpRequest, NlpResult


def _records(df: pd.DataFrame) -> list[dict]:
    return df.where(pd.notna(df), None).to_dict(orient="records")


def _resolve_column(df: pd.DataFrame, preferred: str, alternatives: list[str]) -> str:
    if preferred in df.columns:
        return preferred
    for column in alternatives:
        if column in df.columns:
            return column
    raise ValueError(f"column '{preferred}' not found")


class NativeNlpRuntime:
    def run(self, request: NlpRequest) -> NlpResult:
        frame = pd.DataFrame(request.data).copy()
        handler = getattr(self, f"_run_{request.operation}")
        result, metadata = handler(frame, request)
        return NlpResult(
            operation=request.operation,
            rows=len(result),
            columns=list(result.columns),
            data=_records(result),
            metadata={"runtime": "native", **metadata},
        )

    @staticmethod
    def _run_sentiment(
        df: pd.DataFrame, request: NlpRequest
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        from cortex_brand_analysis.nlp.models.sentiment_analysis.CortexLexicon import (
            CortexLexicon,
        )
        from cortex_brand_analysis.nlp.models.text_treatment.text_processing import (
            clean_text,
        )

        title = _resolve_column(df, request.title_column, ["Título", "titulo_da_publicacao"])
        content = _resolve_column(df, request.content_column, ["Conteúdo", "conteudo"])
        out = df.copy()
        out[title] = out[title].fillna("").astype(str)
        out[content] = out[content].fillna("").astype(str)
        out["aggregated_text"] = out[[title, content]].agg(" - ".join, axis=1)
        tasks = ["lower", "html", "punctuation", "length_1", "digits"]
        out["clean_text"] = out["aggregated_text"].map(
            lambda text: clean_text(text, "pt", cleaning_tasks=tasks)
        )
        analyser = CortexLexicon(extra_terms=[])
        scores = out["clean_text"].map(analyser)
        out["perc_negative"] = scores.map(lambda value: round(float(value[0]), 2))
        out["perc_positive"] = scores.map(lambda value: round(float(value[1]), 2))
        out["Sentimento"] = out["perc_positive"].map(
            lambda value: "Positivo"
            if value > 0.55
            else ("Neutro" if value >= 0.45 else "Negativo")
        )
        return out, {"model": "CortexLexicon"}

    @staticmethod
    def _run_protagonism(
        df: pd.DataFrame, request: NlpRequest
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        from cortex_brand_analysis.nlp.models.protagonism.Protagonism import Protagonism

        title = _resolve_column(df, request.title_column, ["Título", "titulo_da_publicacao"])
        content = _resolve_column(df, request.content_column, ["Conteúdo", "conteudo"])
        brands = [item.strip() for item in request.brands if item.strip()]
        primary = brands[0]
        variants = {brand for item in brands for brand in (item, item.split()[0])}
        classifier = Protagonism({primary: {value: primary for value in variants}}, [])

        out = df.copy()
        out["protagonism_code"] = out.apply(
            lambda row: classifier.run_protagonism(
                primary,
                str(row.get(title, "") or ""),
                str(row.get(content, "") or ""),
            ),
            axis=1,
        )
        mapping = {
            "A": "Protagonismo", "B": "Protagonismo", "C": "Citação relevante",
            "D": "Figurante", "E": "Protagonismo", "F": "Citação relevante",
            "G": "Citação relevante", "H": "Figurante", "I": "Protagonismo",
            "J": "Citação relevante", "K": "Citação relevante", "L": "Figurante",
            "M": "Protagonismo", "Revisar": "Revisar", "-": "-",
        }
        out["Nível de Protagonismo final"] = out["protagonism_code"].map(
            lambda value: mapping.get(str(value), "Revisar")
        )
        return out, {"model": "CortexProtagonism"}

    @staticmethod
    def _run_entities(
        df: pd.DataFrame, request: NlpRequest
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        from cortex_brand_analysis.nlp.models.entities import identify_entities_in_dataframe

        title = _resolve_column(df, request.title_column, ["Título", "titulo_da_publicacao"])
        content = _resolve_column(df, request.content_column, ["Conteúdo", "conteudo"])
        out = identify_entities_in_dataframe(
            df=df,
            search_dict=request.entity_search,
            title_col=title,
            content_col=content,
            output_col="entidade_encontrada",
            split_output=True,
            hash_columns=None,
        )
        return out, {"model": "deterministic_entity_matcher"}

    @staticmethod
    def _run_clustering(
        df: pd.DataFrame, request: NlpRequest
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        from cortex_brand_analysis.nlp.models.clustering import (
            daily_cluster_similaridade_parallel,
        )

        date_col = _resolve_column(df, request.date_column, ["Data", "data_da_publicacao"])
        out = df.copy()
        text_col = request.text_column
        if not text_col:
            title = _resolve_column(out, request.title_column, ["Título", "titulo_da_publicacao"])
            content = _resolve_column(out, request.content_column, ["Conteúdo", "conteudo"])
            text_col = "_nlp_cluster_text"
            out[text_col] = (
                out[title].fillna("").astype(str)
                + " - "
                + out[content].fillna("").astype(str)
            )

        dates = pd.to_datetime(out[date_col], errors="coerce")
        if not dates.notna().any():
            raise ValueError("no valid dates available for clustering")

        start = request.start_date or str(dates.min().date())
        end = request.end_date or str(dates.max().date())
        result = daily_cluster_similaridade_parallel(
            df=out,
            start_date=start,
            end_date=end,
            date_col=date_col,
            column_to_cluster=text_col,
            time_delta=request.time_delta,
            add_window_cols=True,
            verbose=False,
            nested_as_json=True,
            max_workers=4,
            embedding_workers=8,
        )
        return result, {"model": "all-MiniLM-L6-v2"}

    @staticmethod
    def _run_themes(
        df: pd.DataFrame, request: NlpRequest
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        from cortex_brand_analysis.nlp.models.themes.schemas import (
            ThemeClassifierConfigSchema,
            ThemeDefinitionSchema,
            ThemeRuleSchema,
        )
        from cortex_brand_analysis.nlp.models.themes.service import ThemeClassifierService

        title = _resolve_column(df, request.title_column, ["Título", "titulo_da_publicacao"])
        content = _resolve_column(df, request.content_column, ["Conteúdo", "conteudo"])
        definitions = {
            label: ThemeDefinitionSchema(**payload)
            for label, payload in request.macrothemes.items()
        }
        rules = {
            label: ThemeRuleSchema(**payload)
            for label, payload in request.theme_rules.items()
        }
        config = ThemeClassifierConfigSchema(**request.theme_config)
        classifier: Any = ThemeClassifierService(
            macrotemas=definitions,
            rules=rules,
            config=config,
        )
        out = classifier.predict_dataframe(
            df,
            text_col_title=title,
            text_col_content=content,
            return_scores=request.return_scores,
            status_mode="review",
        )
        return out, {"model": config.embedding_model_name}
