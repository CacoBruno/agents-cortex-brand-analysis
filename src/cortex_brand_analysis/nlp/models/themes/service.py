from __future__ import annotations

import json
import math
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from cortex_brand_analysis.nlp.models.themes.schemas import (
    ThemeDefinitionSchema,
    ThemeRuleSchema,
    ThemeWeightsSchema,
    ThemePredictionInputSchema,
    ThemePredictionResultSchema,
    ThemeClassifierConfigSchema,
    ThemeWithFocusConfigSchema,
    ThemeWithFocusDefinitionSchema,
    ThemeWithFocusPredictionOutputSchema,
    ThemeWithFocusRuleSchema,
)


# =========================================================
# BASE CLASSIFIER
# =========================================================

DEFAULT_MACROTEMAS: Dict[str, ThemeDefinitionSchema] = {}
DEFAULT_RULES: Dict[str, ThemeRuleSchema] = {}


class ThemeClassifierService:
    def __init__(
        self,
        macrotemas: Optional[Dict[str, ThemeDefinitionSchema]] = None,
        rules: Optional[Dict[str, ThemeRuleSchema]] = None,
        config: Optional[ThemeClassifierConfigSchema] = None,
    ) -> None:
        self.macrotemas = macrotemas or DEFAULT_MACROTEMAS
        self.rules = rules or DEFAULT_RULES
        self.config = config or ThemeClassifierConfigSchema()
        self.weights: ThemeWeightsSchema = self.config.weights

        self.labels: List[str] = list(self.macrotemas.keys())
        self.model = SentenceTransformer(self.config.embedding_model_name)

        self.label_texts: List[str] = [
            self._build_label_text(label, self.macrotemas[label])
            for label in self.labels
        ]
        self.label_embeddings = self.model.encode(
            self.label_texts,
            normalize_embeddings=True,
        )

        self.prototype_embeddings: Dict[str, Optional[np.ndarray]] = {}
        for label in self.labels:
            prototipos = self.macrotemas[label].prototipos
            if prototipos:
                self.prototype_embeddings[label] = self.model.encode(
                    prototipos,
                    normalize_embeddings=True,
                )
            else:
                self.prototype_embeddings[label] = None

    @staticmethod
    def _normalize_text(text: Any) -> str:
        if text is None:
            return ""
        text = str(text).lower().strip()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _safe_round_dict(d: Dict[str, float], ndigits: int = 4) -> Dict[str, float]:
        return {k: round(float(v), ndigits) for k, v in d.items()}

    def _build_label_text(self, label: str, payload: ThemeDefinitionSchema) -> str:
        exemplos = "; ".join(payload.exemplos)
        exclusoes = "; ".join(payload.exclusoes)
        return (
            f"Tema: {label}. "
            f"Descrição: {payload.descricao}. "
            f"Exemplos: {exemplos}. "
            f"Não classificar aqui se houver: {exclusoes}."
        )

    def score_rules(self, text: str) -> Tuple[Dict[str, float], Dict[str, List[str]]]:
        text_norm = self._normalize_text(text)
        scores = {label: 0.0 for label in self.labels}
        hits = {label: [] for label in self.labels}

        for label, rule in self.rules.items():
            include_count = 0
            exclude_count = 0

            for term in rule.include:
                term_norm = self._normalize_text(term)
                if term_norm and term_norm in text_norm:
                    include_count += 1
                    hits[label].append(f"+{term_norm}")

            for term in rule.exclude:
                term_norm = self._normalize_text(term)
                if term_norm and term_norm in text_norm:
                    exclude_count += 1
                    hits[label].append(f"-{term_norm}")

            raw_score = (include_count * rule.weight) - (exclude_count * rule.weight * 0.9)
            scores[label] = max(raw_score, 0.0)

        max_score = max(scores.values()) if scores else 0.0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}

        return scores, hits

    @staticmethod
    def _minmax_scale(score_map: Dict[str, float]) -> Dict[str, float]:
        values = np.array(list(score_map.values()), dtype=float)
        min_v = float(np.min(values))
        max_v = float(np.max(values))

        if max_v - min_v <= 1e-12:
            return {k: 0.0 for k in score_map.keys()}

        return {
            k: float((v - min_v) / (max_v - min_v))
            for k, v in score_map.items()
        }

    def score_embeddings_split(
        self,
        titulo: str,
        conteudo: str,
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
        titulo_norm = self._normalize_text(titulo)
        conteudo_norm = self._normalize_text(conteudo)

        title_emb = self.model.encode([titulo_norm], normalize_embeddings=True)[0]
        content_emb = self.model.encode([conteudo_norm], normalize_embeddings=True)[0]

        title_scores_raw: Dict[str, float] = {}
        content_scores_raw: Dict[str, float] = {}
        prototype_scores_raw: Dict[str, float] = {}

        for i, label in enumerate(self.labels):
            label_emb = self.label_embeddings[i]

            title_scores_raw[label] = float(
                cosine_similarity([title_emb], [label_emb])[0][0]
            )

            content_scores_raw[label] = float(
                cosine_similarity([content_emb], [label_emb])[0][0]
            )

            proto_embs = self.prototype_embeddings.get(label)
            if proto_embs is None:
                prototype_scores_raw[label] = 0.0
            else:
                proto_title = cosine_similarity([title_emb], proto_embs)[0]
                proto_content = cosine_similarity([content_emb], proto_embs)[0]
                combined_proto = 0.7 * proto_title + 0.3 * proto_content
                prototype_scores_raw[label] = float(np.max(combined_proto))

        title_scores = self._minmax_scale(title_scores_raw)
        content_scores = self._minmax_scale(content_scores_raw)
        prototype_scores = self._minmax_scale(prototype_scores_raw)

        return title_scores, content_scores, prototype_scores

    def combine_scores(
        self,
        rule_scores: Dict[str, float],
        title_scores: Dict[str, float],
        content_scores: Dict[str, float],
        prototype_scores: Dict[str, float],
    ) -> Dict[str, float]:
        final_scores: Dict[str, float] = {}

        for label in self.labels:
            prioridade_bonus = self.macrotemas[label].prioridade * 0.01

            final_scores[label] = (
                self.weights.rules * rule_scores.get(label, 0.0)
                + self.weights.title * title_scores.get(label, 0.0)
                + self.weights.content * content_scores.get(label, 0.0)
                + self.weights.prototypes * prototype_scores.get(label, 0.0)
                + prioridade_bonus
            )

        return final_scores

    def get_status(self, confidence: float, mode: str = "review") -> str:
        if mode == "simple":
            return "accepted" if confidence >= self.config.min_confidence else "undefined"

        if confidence >= self.config.accepted_threshold:
            return "accepted"
        if confidence >= self.config.review_threshold:
            return "review"
        return "undefined"

    def predict_one(
        self,
        titulo: str = "",
        conteudo: str = "",
    ) -> ThemePredictionResultSchema:
        payload = ThemePredictionInputSchema(
            titulo=titulo or "",
            conteudo=conteudo or "",
        )

        combined_text = f"{payload.titulo}. {payload.conteudo}".strip()

        rule_scores, hits = self.score_rules(combined_text)
        title_scores, content_scores, prototype_scores = self.score_embeddings_split(
            titulo=payload.titulo,
            conteudo=payload.conteudo,
        )

        final_scores = self.combine_scores(
            rule_scores=rule_scores,
            title_scores=title_scores,
            content_scores=content_scores,
            prototype_scores=prototype_scores,
        )

        ranking = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        best_label, best_score = ranking[0]
        second_label, second_score = ranking[1] if len(ranking) > 1 else ("", 0.0)

        final_label = best_label if best_score >= self.config.min_confidence else "Indefinido"

        return ThemePredictionResultSchema(
            label=final_label,
            confidence=round(float(best_score), 4),
            margin_top2=round(float(best_score - second_score), 4),
            top_1=best_label,
            top_2=second_label,
            rule_hits=hits.get(best_label, []),
            rule_scores=self._safe_round_dict(rule_scores),
            title_scores=self._safe_round_dict(title_scores),
            content_scores=self._safe_round_dict(content_scores),
            prototype_scores=self._safe_round_dict(prototype_scores),
            final_scores=self._safe_round_dict(final_scores),
        )

    def predict_dataframe(
        self,
        df: pd.DataFrame,
        text_col_title: str = "titulo",
        text_col_content: str = "conteudo",
        return_scores: bool = False,
        status_mode: str = "review",
    ) -> pd.DataFrame:
        out = df.copy()

        if text_col_title not in out.columns:
            raise ValueError(
                f"Coluna de título '{text_col_title}' não encontrada. "
                f"Colunas disponíveis: {list(out.columns)}"
            )

        if text_col_content not in out.columns:
            raise ValueError(
                f"Coluna de conteúdo '{text_col_content}' não encontrada. "
                f"Colunas disponíveis: {list(out.columns)}"
            )

        out[text_col_title] = out[text_col_title].fillna("").astype(str)
        out[text_col_content] = out[text_col_content].fillna("").astype(str)

        predictions = out.apply(
            lambda row: self.predict_one(
                titulo=row.get(text_col_title, ""),
                conteudo=row.get(text_col_content, ""),
            ),
            axis=1,
        )

        out["macrotema"] = predictions.apply(lambda x: x.label)
        out["macrotema_confidence"] = predictions.apply(lambda x: x.confidence)
        out["macrotema_top_1"] = predictions.apply(lambda x: x.top_1)
        out["macrotema_top_2"] = predictions.apply(lambda x: x.top_2)
        out["macrotema_margin_top2"] = predictions.apply(lambda x: x.margin_top2)
        out["macrotema_rule_hits"] = predictions.apply(lambda x: ", ".join(x.rule_hits))
        out["macrotema_status"] = predictions.apply(
            lambda x: self.get_status(x.confidence, mode=status_mode)
        )

        if return_scores:
            for label in self.labels:
                out[f"score_rule::{label}"] = predictions.apply(
                    lambda x: x.rule_scores.get(label, 0.0)
                )
                out[f"score_title::{label}"] = predictions.apply(
                    lambda x: x.title_scores.get(label, 0.0)
                )
                out[f"score_content::{label}"] = predictions.apply(
                    lambda x: x.content_scores.get(label, 0.0)
                )
                out[f"score_proto::{label}"] = predictions.apply(
                    lambda x: x.prototype_scores.get(label, 0.0)
                )
                out[f"score_final::{label}"] = predictions.apply(
                    lambda x: x.final_scores.get(label, 0.0)
                )

        return out


# =========================================================
# WITH FOCUS
# =========================================================

class ThemeClassifierWithFocusService:
    def __init__(
        self,
        macrotemas: Optional[Dict[str, ThemeWithFocusDefinitionSchema]] = None,
        rules: Optional[Dict[str, ThemeWithFocusRuleSchema]] = None,
        config: Optional[ThemeWithFocusConfigSchema] = None,
        llm: Any = None,
        embedding_backend: Any = None,
        macro_groups: Optional[Dict[str, Dict[str, ThemeWithFocusDefinitionSchema]]] = None,
        macro_rules: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        self.macrotemas = macrotemas or {}
        self.rules = rules or {}
        self.config = config or ThemeWithFocusConfigSchema()
        self.llm = llm
        self.embedding_backend = embedding_backend
        self.macro_groups = macro_groups or {}
        self.macro_rules = macro_rules or {}

        self._theme_embedding_cache: Dict[str, List[float]] = {}
        self._text_embedding_cache: Dict[str, List[float]] = {}

    # =========================================================
    # PUBLIC API
    # =========================================================
    def predict_one_with_focus(
        self,
        titulo: str,
        conteudo: str,
        focus_entity: Optional[str] = None,
        focus_aliases: Optional[List[str]] = None,
        threshold: Optional[float] = None,
        use_llm_validation: Optional[bool] = None,
        neighbor_window: Optional[int] = None,
    ) -> Dict[str, Any]:
        titulo = (titulo or "").strip()
        conteudo = (conteudo or "").strip()
        full_text = " ".join([p for p in [titulo, conteudo] if p]).strip()

        threshold = threshold if threshold is not None else self.config.threshold
        use_llm_validation = (
            use_llm_validation
            if use_llm_validation is not None
            else self.config.use_llm_validation
        )
        neighbor_window = (
            neighbor_window
            if neighbor_window is not None
            else self.config.neighbor_window
        )

        self._prepare_theme_embeddings()

        aliases = focus_aliases or self._build_entity_aliases(focus_entity)
        filtered_text = full_text
        focus_found = True

        if focus_entity:
            extracted_text = self._extract_focus_context(
                text=full_text,
                aliases=aliases,
                window=neighbor_window,
            )
            focus_found = bool(extracted_text.strip())
            filtered_text = extracted_text if focus_found else full_text

        scoring_text = filtered_text
        if self.config.remove_focus_aliases_from_text and aliases:
            scoring_text = self._remove_aliases_from_text(filtered_text, aliases)
            if not scoring_text.strip():
                scoring_text = filtered_text

        if not filtered_text.strip():
            return self._build_fallback_output(
                full_text=full_text,
                filtered_text="",
                scoring_text="",
                focus_entity=focus_entity,
                aliases=aliases,
                focus_found=False,
                predicted_macro=None,
                macro_candidates=[],
                theme_candidates=[],
                all_scores=[],
                reason="texto_vazio",
            )

        semantic_source_text = scoring_text if self.config.use_filtered_text_for_semantic else full_text
        text_emb = self._embed_text(semantic_source_text)

        macro_candidates = self._prefilter_macros(
            scoring_text,
            min_rule_score=self.config.macro_rule_min_score,
            top_k=self.config.macro_prefilter_top_k,
        )
        predicted_macro = self._predict_macro(
            text_emb=text_emb,
            filtered_text=scoring_text,
            candidate_macros=macro_candidates,
        )

        if predicted_macro and predicted_macro in self.macro_groups:
            candidate_themes = list(self.macro_groups[predicted_macro].keys())
        else:
            candidate_themes = list(self.macrotemas.keys())

        candidate_themes = self._prefilter_themes(
            scoring_text,
            candidate_themes,
            min_rule_score=self.config.theme_rule_min_score,
            top_k=self.config.theme_prefilter_top_k,
        )

        predictions = self._score_themes_parallel(
            candidate_theme_labels=candidate_themes,
            scoring_text=scoring_text,
            semantic_text_emb=text_emb,
            threshold=threshold,
        )

        if not predictions:
            return self._build_fallback_output(
                full_text=full_text,
                filtered_text=scoring_text,
                scoring_text=scoring_text,
                focus_entity=focus_entity,
                aliases=aliases,
                focus_found=focus_found,
                predicted_macro=predicted_macro,
                macro_candidates=macro_candidates,
                theme_candidates=candidate_themes,
                all_scores=[],
                reason="sem_candidatos",
            )

        best = predictions[0]
        second_score = predictions[1]["score"] if len(predictions) > 1 else 0.0

        if not best.get("passed_threshold", False):
            return self._build_fallback_output(
                full_text=full_text,
                filtered_text=scoring_text,
                scoring_text=scoring_text,
                focus_entity=focus_entity,
                aliases=aliases,
                focus_found=focus_found,
                predicted_macro=predicted_macro,
                macro_candidates=macro_candidates,
                theme_candidates=candidate_themes,
                all_scores=predictions if self.config.return_all_scores else [],
                reason=best.get("fallback_reason") or "threshold_ou_gate",
            )

        should_skip_llm = (
            (not use_llm_validation)
            or (
                self.config.skip_llm_if_confident
                and best["score"] >= self.config.confidence_score_threshold
                and (best["score"] - second_score) >= self.config.min_margin_for_skip_llm
            )
        )

        valid_themes = []
        fallback_reason = None

        if should_skip_llm:
            valid_themes.append({
                "label": best["label"],
                "score": best["score"],
                "rule_score": best["rule_score"],
                "embedding_score": best["embedding_score"],
                "llm_valid": None,
                "llm_reason": "LLM pulado por alta confiança." if use_llm_validation else None,
                "llm_evidence_type": None,
                "llm_confidence": None,
            })
        else:
            theme_definition = self.macrotemas.get(best["label"])
            theme_rule = self.rules.get(best["label"])

            llm_result = self._llm_validate_theme_with_focus(
                titulo=titulo,
                conteudo=scoring_text,
                conteudo_completo=full_text,
                focus_entity=focus_entity,
                focus_aliases=aliases,
                theme_label=best["label"],
                theme_definition=theme_definition,
                theme_rule=theme_rule,
                rule_score=best["rule_score"],
                semantic_score=best["embedding_score"],
                top_candidates=predictions[:3],
            )

            if llm_result.get("is_valid"):
                valid_themes.append({
                    "label": best["label"],
                    "score": best["score"],
                    "rule_score": best["rule_score"],
                    "embedding_score": best["embedding_score"],
                    "llm_valid": True,
                    "llm_reason": llm_result.get("reason"),
                    "llm_evidence_type": llm_result.get("evidence_type"),
                    "llm_confidence": llm_result.get("confidence"),
                })
            else:
                fallback_reason = llm_result.get("evidence_type") or "llm_invalidou"

        if not valid_themes:
            return self._build_fallback_output(
                full_text=full_text,
                filtered_text=scoring_text,
                scoring_text=scoring_text,
                focus_entity=focus_entity,
                aliases=aliases,
                focus_found=focus_found,
                predicted_macro=predicted_macro,
                macro_candidates=macro_candidates,
                theme_candidates=candidate_themes,
                all_scores=predictions if self.config.return_all_scores else [],
                reason=fallback_reason or "sem_tema_valido",
            )

        output = ThemeWithFocusPredictionOutputSchema(
            best_theme=best["label"],
            best_score=best["score"],
            valid_themes=valid_themes,
            focus_entity=focus_entity,
            focus_aliases=aliases,
            focus_found=focus_found,
            filtered_text=scoring_text,
            scoring_text=scoring_text,
            all_scores=predictions if self.config.return_all_scores else [],
            predicted_macro=predicted_macro,
            macro_candidates=macro_candidates,
            theme_candidates=candidate_themes,
            fallback_reason=None,
        )
        return output.model_dump()

    def predict_dataframe_with_focus(
        self,
        df: pd.DataFrame,
        text_col_title: str,
        text_col_content: str,
        focus_entity_col: Optional[str] = None,
        focus_aliases_col: Optional[str] = None,
        threshold: Optional[float] = None,
        use_llm_validation: Optional[bool] = None,
        neighbor_window: Optional[int] = None,
        return_scores: bool = True,
        llm_batch_size: Optional[int] = None,
    ) -> pd.DataFrame:
        df = df.copy()

        threshold = threshold if threshold is not None else self.config.threshold
        use_llm_validation = (
            use_llm_validation
            if use_llm_validation is not None
            else self.config.use_llm_validation
        )
        neighbor_window = (
            neighbor_window
            if neighbor_window is not None
            else self.config.neighbor_window
        )
        llm_batch_size = llm_batch_size or self.config.llm_batch_size

        self._prepare_theme_embeddings()

        titles = df[text_col_title].fillna("").astype(str).tolist()
        contents = df[text_col_content].fillna("").astype(str).tolist()

        full_texts = [
            self._truncate_text(f"{t} {c}", max_chars=2000)
            for t, c in zip(titles, contents)
        ]

        rows_results: List[Dict[str, Any]] = []
        llm_queue: List[Dict[str, Any]] = []

        for i, row in enumerate(df.itertuples(index=False)):
            row_dict = row._asdict()

            titulo = titles[i]
            conteudo = contents[i]
            full_text = full_texts[i]

            focus_entity = row_dict.get(focus_entity_col) if focus_entity_col and focus_entity_col in df.columns else None
            raw_aliases = row_dict.get(focus_aliases_col) if focus_aliases_col and focus_aliases_col in df.columns else None
            focus_aliases = self._coerce_aliases(raw_aliases) if raw_aliases is not None else None
            aliases = focus_aliases or self._build_entity_aliases(focus_entity)

            filtered_text = full_text
            focus_found = True

            if focus_entity:
                filtered_text = self._extract_focus_context(
                    text=full_text,
                    aliases=aliases,
                    window=neighbor_window,
                )
                focus_found = bool(filtered_text.strip())

            scoring_text = filtered_text
            if self.config.remove_focus_aliases_from_text and aliases:
                scoring_text = self._remove_aliases_from_text(filtered_text, aliases)
                if not scoring_text.strip():
                    scoring_text = filtered_text

            if not filtered_text.strip():
                rows_results.append(self._build_fallback_row_result(
                    full_text=full_text,
                    filtered_text="",
                    scoring_text="",
                    focus_entity=focus_entity,
                    aliases=aliases,
                    focus_found=False,
                    predicted_macro=None,
                    macro_candidates=[],
                    theme_candidates=[],
                    all_scores=[],
                    reason="texto_vazio",
                ))
                continue

            semantic_source_text = scoring_text if self.config.use_filtered_text_for_semantic else full_text
            text_emb = self._embed_text(semantic_source_text)

            macro_candidates = self._prefilter_macros(
                scoring_text,
                min_rule_score=self.config.macro_rule_min_score,
                top_k=self.config.macro_prefilter_top_k,
            )

            predicted_macro = self._predict_macro(
                text_emb=text_emb,
                filtered_text=scoring_text,
                candidate_macros=macro_candidates,
            )

            if predicted_macro and predicted_macro in self.macro_groups:
                candidate_themes = list(self.macro_groups[predicted_macro].keys())
            else:
                candidate_themes = list(self.macrotemas.keys())

            candidate_themes = self._prefilter_themes(
                scoring_text,
                candidate_themes,
                min_rule_score=self.config.theme_rule_min_score,
                top_k=self.config.theme_prefilter_top_k,
            )

            predictions = self._score_themes_parallel(
                candidate_theme_labels=candidate_themes,
                scoring_text=scoring_text,
                semantic_text_emb=text_emb,
                threshold=threshold,
            )

            best = predictions[0] if predictions else None
            second_score = predictions[1]["score"] if len(predictions) > 1 else 0.0

            if (not best) or (not best.get("passed_threshold", False)):
                rows_results.append(self._build_fallback_row_result(
                    full_text=full_text,
                    filtered_text=filtered_text,
                    scoring_text=scoring_text,
                    focus_entity=focus_entity,
                    aliases=aliases,
                    focus_found=focus_found,
                    predicted_macro=predicted_macro,
                    macro_candidates=macro_candidates,
                    theme_candidates=candidate_themes,
                    all_scores=predictions if return_scores else [],
                    reason=(best or {}).get("fallback_reason") if best else "sem_candidatos",
                ))
                continue

            should_skip_llm = (
                (not use_llm_validation)
                or (
                    self.config.skip_llm_if_confident
                    and best["score"] >= self.config.confidence_score_threshold
                    and (best["score"] - second_score) >= self.config.min_margin_for_skip_llm
                )
            )

            base_result = {
                "best_theme": best["label"],
                "best_score": best["score"],
                "valid_themes": [],
                "focus_entity": focus_entity,
                "focus_aliases": aliases,
                "focus_found": focus_found,
                "filtered_text": filtered_text,
                "scoring_text": scoring_text,
                "all_scores": predictions if return_scores else [],
                "predicted_macro": predicted_macro,
                "macro_candidates": macro_candidates,
                "theme_candidates": candidate_themes,
                "fallback_reason": None,
                "llm_suggested_theme": None,
                "llm_suggested_macro": None,
                "llm_suggestion_reason": None,
            }

            if should_skip_llm:
                base_result["valid_themes"] = [{
                    "label": best["label"],
                    "score": best["score"],
                    "rule_score": best["rule_score"],
                    "embedding_score": best["embedding_score"],
                    "llm_valid": None,
                    "llm_reason": "LLM pulado por alta confiança." if use_llm_validation else None,
                    "llm_evidence_type": None,
                    "llm_confidence": None,
                }]
            else:
                theme_definition = self.macrotemas.get(best["label"])
                theme_rule = self.rules.get(best["label"])

                llm_queue.append({
                    "row_id": i,
                    "titulo": titulo,
                    "conteudo": filtered_text,
                    "scoring_text": scoring_text,
                    "conteudo_completo": full_text,
                    "focus_entity": focus_entity,
                    "focus_aliases": aliases,
                    "theme_label": best["label"],
                    "theme_definition": {
                        "descricao": getattr(theme_definition, "descricao", ""),
                        "exemplos": getattr(theme_definition, "exemplos", []),
                        "exclusoes": getattr(theme_definition, "exclusoes", []),
                        "prototipos": getattr(theme_definition, "prototipos", []),
                    },
                    "theme_rule": {
                        "include": getattr(theme_rule, "include", []) if theme_rule else [],
                        "exclude": getattr(theme_rule, "exclude", []) if theme_rule else [],
                        "weight": getattr(theme_rule, "weight", 1.0) if theme_rule else 1.0,
                    },
                    "rule_score": best["rule_score"],
                    "semantic_score": best["embedding_score"],
                    "top_candidates": predictions[:3],
                })

            rows_results.append(base_result)

        for start in range(0, len(llm_queue), llm_batch_size):
            batch = llm_queue[start:start + llm_batch_size]
            llm_results = self._llm_validate_theme_batch(batch)

            for item in batch:
                row_id = item["row_id"]
                llm_result = llm_results.get(row_id, {
                    "is_valid": True,
                    "reason": "Fallback.",
                    "evidence_type": "fallback",
                    "confidence": 0.0,
                })

                if llm_result.get("is_valid"):
                    best_theme = rows_results[row_id]["best_theme"]
                    all_scores = rows_results[row_id]["all_scores"]
                    best_pred = next((x for x in all_scores if x["label"] == best_theme), None)

                    rows_results[row_id]["valid_themes"] = [{
                        "label": best_theme,
                        "score": rows_results[row_id]["best_score"],
                        "rule_score": best_pred["rule_score"] if best_pred else None,
                        "embedding_score": best_pred["embedding_score"] if best_pred else None,
                        "llm_valid": True,
                        "llm_reason": llm_result.get("reason"),
                        "llm_evidence_type": llm_result.get("evidence_type"),
                        "llm_confidence": llm_result.get("confidence"),
                    }]
                else:
                    fallback = self._build_fallback_row_result(
                        full_text=item["conteudo_completo"],
                        filtered_text=item["conteudo"],
                        scoring_text=item.get("scoring_text") or item["conteudo"],
                        focus_entity=rows_results[row_id].get("focus_entity"),
                        aliases=rows_results[row_id].get("focus_aliases", []),
                        focus_found=rows_results[row_id].get("focus_found", False),
                        predicted_macro=rows_results[row_id].get("predicted_macro"),
                        macro_candidates=rows_results[row_id].get("macro_candidates", []),
                        theme_candidates=rows_results[row_id].get("theme_candidates", []),
                        all_scores=rows_results[row_id].get("all_scores", []),
                        reason=llm_result.get("evidence_type") or "llm_invalidou",
                    )
                    rows_results[row_id].update(fallback)

        df["best_theme"] = [r["best_theme"] for r in rows_results]
        df["best_score"] = [r["best_score"] for r in rows_results]
        df["valid_themes"] = [r["valid_themes"] for r in rows_results]
        df["focus_entity"] = [r["focus_entity"] for r in rows_results]
        df["focus_aliases"] = [r["focus_aliases"] for r in rows_results]
        df["focus_found"] = [r["focus_found"] for r in rows_results]
        df["filtered_text"] = [r["filtered_text"] for r in rows_results]
        df["scoring_text"] = [r.get("scoring_text", "") for r in rows_results]
        df["predicted_macro"] = [r["predicted_macro"] for r in rows_results]
        df["macro_candidates"] = [r["macro_candidates"] for r in rows_results]
        df["theme_candidates"] = [r["theme_candidates"] for r in rows_results]
        df["fallback_reason"] = [r.get("fallback_reason") for r in rows_results]
        df["llm_suggested_theme"] = [r.get("llm_suggested_theme") for r in rows_results]
        df["llm_suggested_macro"] = [r.get("llm_suggested_macro") for r in rows_results]
        df["llm_suggestion_reason"] = [r.get("llm_suggestion_reason") for r in rows_results]

        if return_scores:
            df["all_scores"] = [r["all_scores"] for r in rows_results]

        return df

    def build_cluster_text_dict(
        self,
        df: pd.DataFrame,
        cluster_id_col: str,
        text_col_title: str,
        text_col_content: str,
        distance_col: str = "distance_to_centroid",
        closest_cluster_n: int = 10,
        focus_entity_col: Optional[str] = None,
        focus_aliases_col: Optional[str] = None,
        cluster_text_max_chars: int = 4000,
    ) -> Dict[Any, Dict[str, Any]]:
        cluster_dict: Dict[Any, Dict[str, Any]] = {}

        if cluster_id_col not in df.columns:
            raise ValueError(
                f"Coluna de cluster '{cluster_id_col}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        if text_col_title not in df.columns:
            raise ValueError(
                f"Coluna de título '{text_col_title}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        if text_col_content not in df.columns:
            raise ValueError(
                f"Coluna de conteúdo '{text_col_content}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        if distance_col not in df.columns:
            raise ValueError(
                f"Coluna de distância '{distance_col}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        if focus_entity_col and focus_entity_col not in df.columns:
            raise ValueError(
                f"Coluna focus_entity_col '{focus_entity_col}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        if focus_aliases_col and focus_aliases_col not in df.columns:
            raise ValueError(
                f"Coluna focus_aliases_col '{focus_aliases_col}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        for cluster_id, group in df.groupby(cluster_id_col, dropna=False):
            group = group.copy()
            original_size = len(group)

            group[text_col_title] = group[text_col_title].fillna("").astype(str)
            group[text_col_content] = group[text_col_content].fillna("").astype(str)
            group[distance_col] = pd.to_numeric(group[distance_col], errors="coerce")

            group["_text_len"] = (
                group[text_col_title].str.len() +
                group[text_col_content].str.len()
            )

            valid_distance_group = group[group[distance_col].notna()].copy()

            if not valid_distance_group.empty:
                selected = (
                    valid_distance_group
                    .sort_values(
                        by=[distance_col, "_text_len"],
                        ascending=[True, False],
                    )
                    .head(closest_cluster_n)
                )
            else:
                selected = (
                    group
                    .sort_values("_text_len", ascending=False)
                    .head(closest_cluster_n)
                )

            snippets: List[str] = []
            current_chars = 0

            for _, row in selected.iterrows():
                titulo = str(row.get(text_col_title, "") or "").strip()
                conteudo = str(row.get(text_col_content, "") or "").strip()

                bloco = " ".join([x for x in [titulo, conteudo] if x]).strip()
                if not bloco:
                    continue

                bloco = re.sub(r"\s+", " ", bloco).strip()

                if current_chars + len(bloco) > cluster_text_max_chars:
                    remaining = cluster_text_max_chars - current_chars
                    if remaining > 0:
                        snippets.append(bloco[:remaining].strip())
                    break

                snippets.append(bloco)
                current_chars += len(bloco) + 2

            representative_text = "\n\n".join(snippets).strip()

            first_row = selected.iloc[0] if not selected.empty else group.iloc[0]

            cluster_dict[cluster_id] = {
                "cluster_id": cluster_id,
                "titulo": f"Cluster {cluster_id}",
                "conteudo": representative_text,
                "focus_entity": first_row.get(focus_entity_col) if focus_entity_col else None,
                "focus_aliases": first_row.get(focus_aliases_col) if focus_aliases_col else None,
                "cluster_size": original_size,
                "selected_rows": int(len(selected)),
                "min_distance": (
                    float(selected[distance_col].min())
                    if distance_col in selected.columns and selected[distance_col].notna().any()
                    else None
                ),
                "mean_distance": (
                    float(selected[distance_col].mean())
                    if distance_col in selected.columns and selected[distance_col].notna().any()
                    else None
                ),
            }

        return cluster_dict

    def _is_ambiguous_cluster_prediction(
        self,
        prediction: Dict[str, Any],
        ambiguous_score_threshold: float = 0.72,
        ambiguous_margin_threshold: float = 0.12,
    ) -> bool:
        all_scores = prediction.get("all_scores", []) or []
        best_score = float(prediction.get("best_score", 0.0) or 0.0)

        second_score = 0.0
        if len(all_scores) > 1:
            second_score = float(all_scores[1].get("score", 0.0) or 0.0)

        margin = best_score - second_score

        return (
            best_score < ambiguous_score_threshold
            or margin < ambiguous_margin_threshold
        )

    def predict_dataframe_with_focus_by_cluster(
        self,
        df: pd.DataFrame,
        cluster_id_col: str,
        text_col_title: str,
        text_col_content: str,
        distance_col: str = "distance_to_centroid",
        closest_cluster_n: int = 10,
        focus_entity_col: Optional[str] = None,
        focus_aliases_col: Optional[str] = None,
        threshold: Optional[float] = None,
        use_llm_validation: Optional[bool] = False,
        neighbor_window: Optional[int] = None,
        return_scores: bool = True,
        llm_batch_size: Optional[int] = None,
        cluster_text_max_chars: int = 4000,
        run_ambiguous_llm_validation: bool = False,
        ambiguous_score_threshold: float = 0.72,
        ambiguous_margin_threshold: float = 0.12,
    ) -> pd.DataFrame:
        df = df.copy()

        if cluster_id_col not in df.columns:
            raise ValueError(
                f"Coluna de cluster '{cluster_id_col}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        if text_col_title not in df.columns:
            raise ValueError(
                f"Coluna de título '{text_col_title}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        if text_col_content not in df.columns:
            raise ValueError(
                f"Coluna de conteúdo '{text_col_content}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        if distance_col not in df.columns:
            raise ValueError(
                f"Coluna de distância '{distance_col}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        if focus_entity_col and focus_entity_col not in df.columns:
            raise ValueError(
                f"Coluna focus_entity_col '{focus_entity_col}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        if focus_aliases_col and focus_aliases_col not in df.columns:
            raise ValueError(
                f"Coluna focus_aliases_col '{focus_aliases_col}' não encontrada. "
                f"Colunas disponíveis: {list(df.columns)}"
            )

        threshold = threshold if threshold is not None else self.config.threshold

        neighbor_window = (
            neighbor_window
            if neighbor_window is not None
            else self.config.neighbor_window
        )

        use_llm_validation = (
            use_llm_validation
            if use_llm_validation is not None
            else self.config.use_llm_validation
        )

        llm_batch_size = (
            llm_batch_size
            if llm_batch_size is not None
            else self.config.llm_batch_size
        )

        cluster_dict = self.build_cluster_text_dict(
            df=df,
            cluster_id_col=cluster_id_col,
            text_col_title=text_col_title,
            text_col_content=text_col_content,
            distance_col=distance_col,
            closest_cluster_n=closest_cluster_n,
            focus_entity_col=focus_entity_col,
            focus_aliases_col=focus_aliases_col,
            cluster_text_max_chars=cluster_text_max_chars,
        )

        cluster_predictions: Dict[Any, Dict[str, Any]] = {}

        # Primeiro passe: classificação por cluster
        # Se run_ambiguous_llm_validation=True, o primeiro passe roda sem LLM
        # e o segundo passe refina apenas os ambíguos.
        # Caso contrário, respeita use_llm_validation diretamente.
        first_pass_use_llm = use_llm_validation and (not run_ambiguous_llm_validation)

        for cluster_id, payload in cluster_dict.items():
            result = self.predict_one_with_focus(
                titulo=payload["titulo"],
                conteudo=payload["conteudo"],
                focus_entity=payload.get("focus_entity"),
                focus_aliases=self._coerce_aliases(payload.get("focus_aliases")),
                threshold=threshold,
                use_llm_validation=first_pass_use_llm,
                neighbor_window=neighbor_window,
            )
            result["cluster_size"] = payload.get("cluster_size", 0)
            result["selected_rows"] = payload.get("selected_rows", 0)
            result["min_distance"] = payload.get("min_distance")
            result["mean_distance"] = payload.get("mean_distance")
            cluster_predictions[cluster_id] = result

        # Refinamento opcional apenas para clusters ambíguos
        if run_ambiguous_llm_validation and use_llm_validation:
            ambiguous_cluster_ids: List[Any] = []

            for cluster_id, prediction in cluster_predictions.items():
                if self._is_ambiguous_cluster_prediction(
                    prediction=prediction,
                    ambiguous_score_threshold=ambiguous_score_threshold,
                    ambiguous_margin_threshold=ambiguous_margin_threshold,
                ):
                    ambiguous_cluster_ids.append(cluster_id)

            # Mantido em loop simples para preservar sua API atual.
            # llm_batch_size é resolvido acima para futura otimização em batch.
            for cluster_id in ambiguous_cluster_ids:
                payload = cluster_dict[cluster_id]

                refined = self.predict_one_with_focus(
                    titulo=payload["titulo"],
                    conteudo=payload["conteudo"],
                    focus_entity=payload.get("focus_entity"),
                    focus_aliases=self._coerce_aliases(payload.get("focus_aliases")),
                    threshold=threshold,
                    use_llm_validation=True,
                    neighbor_window=neighbor_window,
                )
                refined["cluster_size"] = payload.get("cluster_size", 0)
                refined["selected_rows"] = payload.get("selected_rows", 0)
                refined["min_distance"] = payload.get("min_distance")
                refined["mean_distance"] = payload.get("mean_distance")
                cluster_predictions[cluster_id] = refined

        df["best_theme"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("best_theme")
        )
        df["best_score"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("best_score")
        )
        df["valid_themes"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("valid_themes", [])
        )
        df["focus_entity"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("focus_entity")
        )
        df["focus_aliases"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("focus_aliases", [])
        )
        df["focus_found"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("focus_found", False)
        )
        df["filtered_text"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("filtered_text", "")
        )
        df["scoring_text"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("scoring_text", "")
        )
        df["predicted_macro"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("predicted_macro")
        )
        df["macro_candidates"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("macro_candidates", [])
        )
        df["theme_candidates"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("theme_candidates", [])
        )
        df["fallback_reason"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("fallback_reason")
        )
        df["llm_suggested_theme"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("llm_suggested_theme")
        )
        df["llm_suggested_macro"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("llm_suggested_macro")
        )
        df["llm_suggestion_reason"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("llm_suggestion_reason")
        )
        df["cluster_size"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("cluster_size", 0)
        )
        df["cluster_selected_rows"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("selected_rows", 0)
        )
        df["cluster_min_distance"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("min_distance")
        )
        df["cluster_mean_distance"] = df[cluster_id_col].map(
            lambda x: cluster_predictions.get(x, {}).get("mean_distance")
        )

        if return_scores:
            df["all_scores"] = df[cluster_id_col].map(
                lambda x: cluster_predictions.get(x, {}).get("all_scores", [])
            )

        return df

    def _build_fallback_row_result(
        self,
        full_text: str,
        filtered_text: str,
        scoring_text: str,
        focus_entity: Optional[str],
        aliases: List[str],
        focus_found: bool,
        predicted_macro: Optional[str],
        macro_candidates: List[str],
        theme_candidates: List[str],
        all_scores: List[Dict[str, Any]],
        reason: Optional[str],
    ) -> Dict[str, Any]:
        suggestion = self._llm_suggest_theme_on_fallback(
            full_text=full_text,
            filtered_text=filtered_text,
            scoring_text=scoring_text,
            focus_entity=focus_entity,
            aliases=aliases,
            candidate_themes=theme_candidates,
            predicted_macro=predicted_macro,
            all_scores=all_scores,
        )
        return {
            "best_theme": self.config.fallback_label,
            "best_score": 0.0,
            "valid_themes": [],
            "focus_entity": focus_entity,
            "focus_aliases": aliases,
            "focus_found": focus_found,
            "filtered_text": filtered_text,
            "scoring_text": scoring_text,
            "all_scores": all_scores,
            "predicted_macro": predicted_macro,
            "macro_candidates": macro_candidates,
            "theme_candidates": theme_candidates,
            "fallback_reason": reason,
            "llm_suggested_theme": suggestion.get("suggested_theme"),
            "llm_suggested_macro": suggestion.get("suggested_macro"),
            "llm_suggestion_reason": suggestion.get("reason"),
        }

    def _build_fallback_output(
        self,
        full_text: str,
        filtered_text: str,
        scoring_text: str,
        focus_entity: Optional[str],
        aliases: List[str],
        focus_found: bool,
        predicted_macro: Optional[str],
        macro_candidates: List[str],
        theme_candidates: List[str],
        all_scores: List[Dict[str, Any]],
        reason: Optional[str],
    ) -> Dict[str, Any]:
        row = self._build_fallback_row_result(
            full_text=full_text,
            filtered_text=filtered_text,
            scoring_text=scoring_text,
            focus_entity=focus_entity,
            aliases=aliases,
            focus_found=focus_found,
            predicted_macro=predicted_macro,
            macro_candidates=macro_candidates,
            theme_candidates=theme_candidates,
            all_scores=all_scores,
            reason=reason,
        )
        return ThemeWithFocusPredictionOutputSchema(**row).model_dump()

    def _llm_suggest_theme_on_fallback(
        self,
        full_text: str,
        filtered_text: str,
        scoring_text: str,
        focus_entity: Optional[str],
        aliases: List[str],
        candidate_themes: List[str],
        predicted_macro: Optional[str],
        all_scores: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not self.config.fallback_use_llm_suggestion:
            return {}
        if self.llm is None:
            return {}

        prompt = f"""
Você receberá um texto que caiu em fallback de classificação.
Sua tarefa NÃO é forçar um tema do catálogo. Em vez disso:
1. Sugira um tema descritivo livre e curto.
2. Sugira a macro, se existir, senão null.
3. Explique rapidamente por que o texto não encaixa bem nos temas atuais.
4. Não use a entidade foco como tema.
5. Se o texto parecer claramente fora do domínio do catálogo, diga isso.

Responda apenas JSON válido:
{{
  "suggested_theme": "...",
  "suggested_macro": null,
  "reason": "..."
}}

Entidade foco: {focus_entity or 'não informada'}
Aliases: {aliases}
Macro prevista: {predicted_macro}
Temas candidatos: {candidate_themes}
Scores candidatos: {all_scores[:5]}
Texto completo: {full_text[:2500]}
Trecho focado: {filtered_text[:1800]}
Texto para scoring: {scoring_text[:1800]}
""".strip()
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            parsed = self._safe_parse_json(content)
            if isinstance(parsed, dict):
                return {
                    "suggested_theme": parsed.get("suggested_theme"),
                    "suggested_macro": parsed.get("suggested_macro"),
                    "reason": parsed.get("reason"),
                }
        except Exception:
            return {}
        return {}

    # =========================================================
    # HIERARCHY / PREFILTER
    # =========================================================
    def _prefilter_macros(
        self,
        text: str,
        min_rule_score: float = 0.05,
        top_k: int = 3,
    ) -> List[str]:
        scored = []

        for macro_label, rule_dict in self.macro_rules.items():
            score = self._score_rule_dict(text, rule_dict)
            if score >= min_rule_score:
                scored.append((macro_label, score))

        scored = sorted(scored, key=lambda x: x[1], reverse=True)

        if scored:
            return [label for label, _ in scored[:top_k]]

        return list(self.macro_groups.keys())[:top_k] if self.macro_groups else []

    def _prefilter_themes(
        self,
        text: str,
        candidate_labels: List[str],
        min_rule_score: float = 0.03,
        top_k: int = 6,
    ) -> List[str]:
        scored = []

        for theme_label in candidate_labels:
            rule = self.rules.get(theme_label)
            score = self._score_rule_dict(text, {
                "include": getattr(rule, "include", []) if rule else [],
                "exclude": getattr(rule, "exclude", []) if rule else [],
                "weight": getattr(rule, "weight", 1.0) if rule else 1.0,
            })
            if score >= min_rule_score:
                scored.append((theme_label, score))

        scored = sorted(scored, key=lambda x: x[1], reverse=True)

        if scored:
            return [label for label, _ in scored[:top_k]]

        return candidate_labels[:top_k]

    def _predict_macro(
        self,
        text_emb: List[float],
        filtered_text: str,
        candidate_macros: List[str],
    ) -> Optional[str]:
        scored = []

        for macro_label in candidate_macros:
            subthemes = self.macro_groups.get(macro_label, {})
            if not subthemes:
                continue

            sub_embs = []
            for sub_label in subthemes.keys():
                emb = self._theme_embedding_cache.get(sub_label)
                if emb:
                    sub_embs.append(emb)

            if not sub_embs:
                continue

            centroid = [
                sum(values) / len(values)
                for values in zip(*sub_embs)
            ]

            semantic_score = self._cosine_similarity(text_emb, centroid)
            rule_score = self._score_rule_dict(filtered_text, self.macro_rules.get(macro_label))
            final_score = (0.35 * rule_score) + (0.65 * semantic_score)
            scored.append((macro_label, final_score))

        scored = sorted(scored, key=lambda x: x[1], reverse=True)
        return scored[0][0] if scored else None

    # =========================================================
    # PARALLEL SCORING
    # =========================================================
    def _score_single_theme(
        self,
        theme_label: str,
        scoring_text: str,
        semantic_text_emb: List[float],
        threshold: float,
    ) -> Dict[str, Any]:
        rule = self.rules.get(theme_label)
        theme_emb = self._theme_embedding_cache.get(theme_label, [])

        rule_dict = {
            "include": getattr(rule, "include", []) if rule else [],
            "exclude": getattr(rule, "exclude", []) if rule else [],
            "weight": getattr(rule, "weight", 1.0) if rule else 1.0,
        }
        rule_score = self._score_rule_dict(scoring_text, rule_dict)
        include_hits, exclude_hits = self._count_rule_hits(scoring_text, rule_dict)
        lexical_gate_ok = (
            include_hits >= self.config.lexical_gate_min_hits
            and rule_score >= self.config.lexical_gate_min_score
        )

        semantic_score = self._cosine_similarity(semantic_text_emb, theme_emb)
        if self.config.require_lexical_gate and not lexical_gate_ok:
            semantic_score = min(semantic_score, self.config.semantic_cap_without_lexical)

        final_score = (
            self.config.rule_weight * rule_score
            + self.config.semantic_weight * semantic_score
        )

        fallback_reason = None
        if self.config.require_lexical_gate and not lexical_gate_ok:
            fallback_reason = "lexical_gate"

        if self._looks_like_generic_financial_theme(theme_label) and not lexical_gate_ok:
            final_score = max(final_score - self.config.generic_financial_penalty, 0.0)
            if fallback_reason is None:
                fallback_reason = "generic_financial_bias"

        passed_threshold = final_score >= threshold
        if self.config.require_lexical_gate and not lexical_gate_ok:
            passed_threshold = False

        return {
            "label": theme_label,
            "score": round(final_score, 4),
            "rule_score": round(rule_score, 4),
            "embedding_score": round(semantic_score, 4),
            "include_hits": include_hits,
            "exclude_hits": exclude_hits,
            "lexical_gate_ok": lexical_gate_ok,
            "passed_threshold": passed_threshold,
            "fallback_reason": fallback_reason,
        }

    def _score_themes_parallel(
        self,
        candidate_theme_labels: List[str],
        scoring_text: str,
        semantic_text_emb: List[float],
        threshold: float,
    ) -> List[Dict[str, Any]]:
        if not candidate_theme_labels:
            return []

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = [
                executor.submit(
                    self._score_single_theme,
                    theme_label,
                    scoring_text,
                    semantic_text_emb,
                    threshold,
                )
                for theme_label in candidate_theme_labels
            ]
            results = [f.result() for f in futures]

        results = sorted(results, key=lambda x: x["score"], reverse=True)

        for item in results:
            theme_def = self.macrotemas.get(item["label"])
            prioridade = getattr(theme_def, "prioridade", 0) if theme_def else 0
            item["prioridade"] = prioridade

        results = sorted(results, key=lambda x: (x["score"], x["prioridade"]), reverse=True)

        for item in results:
            item.pop("prioridade", None)

        return results

    # =========================================================
    # LLM BATCH
    # =========================================================
    def _llm_validate_theme_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> Dict[int, Dict[str, Any]]:
        if not items:
            return {}

        if self.llm is None:
            return {
                item["row_id"]: {
                    "is_valid": True,
                    "reason": "LLM não configurado.",
                    "evidence_type": "fallback",
                    "confidence": 0.0,
                }
                for item in items
            }

        payload = json.dumps(items, ensure_ascii=False, indent=2)

        prompt = f"""
Você é um verificador de classificação temática com foco em precisão.

Receberá uma lista de casos.
Para cada caso, decida se o tema candidato é válido.

Regras:
1. O tema deve ser central, não lateral.
2. Se houver empresa foco, o tema deve se referir à empresa foco.
3. Se falar do tema mas sobre outra empresa, retorne false.
4. Considere definição, exemplos, exclusões, protótipos, regras e scores.
5. Responda apenas JSON válido.
6. A saída deve ser uma lista, com um item por row_id.

Formato:
[
  {{
    "row_id": 0,
    "is_valid": true,
    "reason": "curto",
    "evidence_type": "central|lateral|other_company|excluded|insufficient",
    "confidence": 0.0
  }}
]

Casos:
{payload}
""".strip()

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            parsed = self._safe_parse_json_list(content)

            result = {}
            for item in parsed:
                row_id = int(item["row_id"])
                result[row_id] = {
                    "is_valid": bool(item.get("is_valid")),
                    "reason": str(item.get("reason", "")),
                    "evidence_type": str(item.get("evidence_type", "")),
                    "confidence": float(item.get("confidence", 0.0) or 0.0),
                }
            return result

        except Exception as e:
            return {
                item["row_id"]: {
                    "is_valid": True,
                    "reason": f"Fallback por erro LLM batch: {e}",
                    "evidence_type": "fallback",
                    "confidence": 0.0,
                }
                for item in items
            }

    def _llm_validate_theme_with_focus(
        self,
        titulo: str,
        conteudo: str,
        conteudo_completo: str,
        focus_entity: Optional[str],
        focus_aliases: Optional[List[str]],
        theme_label: str,
        theme_definition: Optional[ThemeWithFocusDefinitionSchema] = None,
        theme_rule: Optional[ThemeWithFocusRuleSchema] = None,
        rule_score: Optional[float] = None,
        semantic_score: Optional[float] = None,
        top_candidates: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if self.llm is None:
            return {
                "is_valid": True,
                "reason": "LLM não configurado; validação assumida como verdadeira.",
                "evidence_type": "fallback",
                "confidence": 0.0,
            }

        descricao = theme_definition.descricao if theme_definition else ""
        exemplos = theme_definition.exemplos if theme_definition else []
        exclusoes = theme_definition.exclusoes if theme_definition else []
        prototipos = theme_definition.prototipos if theme_definition else []

        include_terms = theme_rule.include if theme_rule else []
        exclude_terms = theme_rule.exclude if theme_rule else []

        prompt = f"""
Você é um verificador de classificação temática com foco em precisão.

## Entidade foco
- Empresa: {focus_entity or "não informada"}
- Aliases: {focus_aliases or []}

## Macrotema candidato
- Nome: {theme_label}
- Descrição: {descricao}
- Exemplos: {exemplos}
- Exclusões: {exclusoes}
- Protótipos: {prototipos}

## Regras heurísticas
- Include: {include_terms}
- Exclude: {exclude_terms}

## Scores prévios
- rule_score: {rule_score}
- semantic_score: {semantic_score}

## Principais candidatos
{top_candidates}

## Texto completo
{conteudo_completo}

## Trecho focado
{conteudo}

## Critérios
1. O tema deve ser central, não lateral.
2. Se houver empresa foco, o tema deve se referir a ela.
3. Se falar do tema mas sobre outra empresa, retorne false.
4. Exclusões devem invalidar o tema.
5. Seja rigoroso.

Responda apenas JSON:

{{
  "is_valid": true,
  "reason": "curto",
  "evidence_type": "central|lateral|other_company|excluded|insufficient",
  "confidence": 0.0
}}
""".strip()

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            parsed = self._safe_parse_json(content)

            if isinstance(parsed, dict) and "is_valid" in parsed:
                return {
                    "is_valid": bool(parsed.get("is_valid")),
                    "reason": str(parsed.get("reason", "")),
                    "evidence_type": parsed.get("evidence_type"),
                    "confidence": float(parsed.get("confidence", 0.0) or 0.0),
                }

        except Exception as e:
            return {
                "is_valid": True,
                "reason": f"Fallback por erro LLM: {e}",
                "evidence_type": "fallback",
                "confidence": 0.0,
            }

        return {
            "is_valid": True,
            "reason": "Fallback por parsing inválido",
            "evidence_type": "fallback",
            "confidence": 0.0,
        }

    # =========================================================
    # EMBEDDINGS
    # =========================================================
    def _get_theme_text(
        self,
        theme_definition: ThemeWithFocusDefinitionSchema,
    ) -> str:
        parts = [
            theme_definition.descricao,
            *theme_definition.exemplos,
            *theme_definition.prototipos,
        ]
        return " ".join([str(x).strip() for x in parts if x and str(x).strip()]).strip()

    def _prepare_theme_embeddings(self) -> None:
        missing_labels = []
        missing_texts = []

        for theme_label, theme_definition in self.macrotemas.items():
            if theme_label not in self._theme_embedding_cache:
                missing_labels.append(theme_label)
                missing_texts.append(self._get_theme_text(theme_definition))

        if missing_texts:
            embs = self._embed_batch(missing_texts)
            for label, emb in zip(missing_labels, embs):
                self._theme_embedding_cache[label] = emb

    def _embed_batch(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        clean_texts = [str(t).strip() for t in texts if str(t).strip()]

        if not clean_texts:
            return []

        all_embeddings: List[List[float]] = []

        for i in range(0, len(clean_texts), batch_size):
            chunk = clean_texts[i:i + batch_size]

            if hasattr(self.embedding_backend, "embed_documents"):
                embs = self.embedding_backend.embed_documents(chunk)
            else:
                embs = [self.embedding_backend.embed_query(t) for t in chunk]

            all_embeddings.extend(embs)

        return all_embeddings

    def _truncate_text(self, text: str, max_chars: int = 2000) -> str:
        text = (text or "").strip()
        return text[:max_chars] if text else ""

    def _embed_text(self, text: str) -> List[float]:
        clean_text = (text or "").strip()
        if not clean_text:
            return []

        if clean_text in self._text_embedding_cache:
            return self._text_embedding_cache[clean_text]

        if hasattr(self.embedding_backend, "embed_query"):
            emb = self.embedding_backend.embed_query(clean_text)
        elif hasattr(self.embedding_backend, "embed_documents"):
            result = self.embedding_backend.embed_documents([clean_text])
            emb = result[0] if result else []
        else:
            raise ValueError("embedding_backend não possui embed_query nem embed_documents.")

        self._text_embedding_cache[clean_text] = emb
        return emb

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return min(max((dot / (norm_a * norm_b) + 1.0) / 2.0, 0.0), 1.0)

    # =========================================================
    # RULES / FOCUS
    # =========================================================
    def _score_rule_dict(self, text: str, rule_dict: Optional[Dict[str, Any]]) -> float:
        if not rule_dict:
            return 0.0

        include_hits, exclude_hits = self._count_rule_hits(text, rule_dict)
        include_terms = rule_dict.get("include", []) or []
        weight = float(rule_dict.get("weight", 1.0))

        if not include_terms:
            return 0.0

        base = include_hits / max(len(include_terms), 1)
        penalty = min(exclude_hits * 0.20, 0.7)
        score = max(base - penalty, 0.0) * weight
        return min(score, 1.0)

    def _count_rule_hits(self, text: str, rule_dict: Optional[Dict[str, Any]]) -> Tuple[int, int]:
        if not rule_dict:
            return 0, 0
        include_terms = rule_dict.get("include", []) or []
        exclude_terms = rule_dict.get("exclude", []) or []
        include_hits = sum(1 for term in include_terms if self._term_in_text(text, term))
        exclude_hits = sum(1 for term in exclude_terms if self._term_in_text(text, term))
        return include_hits, exclude_hits

    def _term_in_text(self, text: str, term: str) -> bool:
        text_norm = self._normalize_text(text)
        term_norm = self._normalize_text(term)
        if not text_norm or not term_norm:
            return False

        if re.search(r"[\(\)\[\]\|]", term_norm):
            try:
                return bool(re.search(term_norm, text_norm, flags=re.IGNORECASE))
            except re.error:
                pass

        pattern = rf"(?<!\w){re.escape(term_norm)}(?!\w)"
        if re.search(pattern, text_norm, flags=re.IGNORECASE):
            return True

        return term_norm in text_norm

    def _remove_aliases_from_text(self, text: str, aliases: List[str]) -> str:
        cleaned = text or ""
        ordered_aliases = sorted({self._normalize_text(a) for a in aliases if a}, key=len, reverse=True)
        for alias in ordered_aliases:
            if not alias:
                continue
            cleaned = re.sub(rf"(?<!\w){re.escape(alias)}(?!\w)", " ", self._normalize_text(cleaned), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _looks_like_generic_financial_theme(self, theme_label: str) -> bool:
        label_norm = self._normalize_text(theme_label)
        return any(token in label_norm for token in ["financeir", "resultado financeiro", "balanco", "balanço"])

    def _build_entity_aliases(
        self,
        entity: Optional[str],
        extra_aliases: Optional[List[str]] = None,
    ) -> List[str]:
        entity = (entity or "").strip()
        if not entity:
            return []

        raw = re.sub(r"\s+", " ", entity.strip())
        raw_lower = raw.lower()
        raw_norm = self._normalize_text(raw)

        aliases = {raw_lower, raw_norm}

        cleaned = re.sub(r"[^\w\s&/-]", " ", raw_lower)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned_norm = self._normalize_text(cleaned)

        if cleaned:
            aliases.add(cleaned)
        if cleaned_norm:
            aliases.add(cleaned_norm)

        corporate_suffixes = [
            "s a", "sa", "s.a", "s.a.", "ltda", "ltda.", "me", "eireli",
            "holding", "holdings", "participacoes", "participações",
            "group", "grupo", "inc", "inc.", "corp", "corp.",
            "corporation", "companhia", "cia", "cia.",
        ]

        base_variants = {cleaned, cleaned_norm, raw_lower, raw_norm}
        reduced_variants = set()

        for variant in list(base_variants):
            if not variant:
                continue

            reduced = variant
            for suffix in corporate_suffixes:
                pattern = rf"\b{re.escape(suffix)}\b"
                reduced = re.sub(pattern, " ", reduced)

            reduced = re.sub(r"\s+", " ", reduced).strip()
            if reduced and reduced != variant:
                reduced_variants.add(reduced)

        aliases.update(reduced_variants)

        token_blacklist = {
            "sa", "s", "a", "ltda", "me", "eireli", "group", "grupo",
            "holdings", "holding", "inc", "corp", "corporation",
            "companhia", "cia"
        }

        for variant in list(aliases):
            parts = [p.strip() for p in variant.split() if p.strip()]
            meaningful_parts = [p for p in parts if p not in token_blacklist and len(p) > 2]

            if meaningful_parts:
                aliases.add(" ".join(meaningful_parts))

            if len(meaningful_parts) >= 1:
                aliases.add(meaningful_parts[0])

        if extra_aliases:
            for alias in extra_aliases:
                if alias and str(alias).strip():
                    alias_raw = str(alias).strip().lower()
                    alias_norm = self._normalize_text(alias_raw)
                    aliases.add(alias_raw)
                    aliases.add(alias_norm)

        aliases = {
            re.sub(r"\s+", " ", a).strip()
            for a in aliases
            if a and re.sub(r"\s+", " ", a).strip()
        }

        return sorted(aliases)

    def _coerce_aliases(self, raw_aliases: Any) -> Optional[List[str]]:
        if raw_aliases is None:
            return None

        if isinstance(raw_aliases, list):
            cleaned = [str(x).strip() for x in raw_aliases if str(x).strip()]
            return cleaned or None

        if isinstance(raw_aliases, str):
            raw_aliases = raw_aliases.strip()
            if not raw_aliases:
                return None

            if "|" in raw_aliases:
                cleaned = [x.strip() for x in raw_aliases.split("|") if x.strip()]
                return cleaned or None

            if "," in raw_aliases:
                cleaned = [x.strip() for x in raw_aliases.split(",") if x.strip()]
                return cleaned or None

            return [raw_aliases]

        return None

    def _extract_focus_context(
        self,
        text: str,
        aliases: List[str],
        window: int = 1,
    ) -> str:
        if not text or not aliases:
            return ""

        sentences = self._split_sentences(text)
        if not sentences:
            return ""

        patterns = [
            re.compile(rf"\b{re.escape(alias)}\b", flags=re.IGNORECASE)
            for alias in aliases
            if alias.strip()
        ]

        selected_idxs = set()

        for i, sent in enumerate(sentences):
            if any(p.search(sent) for p in patterns):
                start = max(0, i - window)
                end = min(len(sentences), i + window + 1)
                selected_idxs.update(range(start, end))

        selected_sentences = [sentences[i] for i in sorted(selected_idxs)]
        return " ".join(selected_sentences).strip()

    def _split_sentences(self, text: str) -> List[str]:
        parts = re.split(r"(?<=[\.\!\?\;\:])\s+", text.strip())
        return [p.strip() for p in parts if p.strip()]

    # =========================================================
    # UTILS
    # =========================================================
    def _normalize_text(self, text: str) -> str:
        text = (text or "").lower().strip()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"\s+", " ", text)
        return text

    def _safe_parse_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        return {}

    def _safe_parse_json_list(self, text: str) -> List[Dict[str, Any]]:
        text = text.strip()

        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            pass

        match = re.search(r"\[.*\]", text, flags=re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                return parsed if isinstance(parsed, list) else []
            except Exception:
                pass

        return []