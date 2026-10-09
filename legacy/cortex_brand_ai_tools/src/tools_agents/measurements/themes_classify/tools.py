from __future__ import annotations

from typing import Any, Dict, Optional

from langchain_core.tools import tool

from src.tools_agents.measurements.themes_classify.schemas import (
    ThemeBatchFromStoreToolInputSchema,
    ThemeBatchFromStoreWithFocusByClusterInputSchema,
    ThemeBatchFromStoreWithFocusInputSchema,
    ThemeClassifierConfigSchema,
    ThemeDefinitionSchema,
    ThemeRuleSchema,
    ThemeSingleTextToolInputSchema,
    ThemeSingleTextWithFocusInputSchema,
    ThemeWithFocusConfigSchema,
    ThemeWithFocusDefinitionSchema,
    ThemeWithFocusRuleSchema,
)
from src.tools_agents.measurements.themes_classify.service import (
    ThemeClassifierService,
    ThemeClassifierWithFocusService,
)

from core.dataframe_store import (
    get_dataframe,
    get_dataframe_with_metadata,
    save_dataframe,
)

from services.ia_funtions.ai_factory import (
    get_default_embeddings,
    get_default_llm,
)


# =========================================================
# BASE PARSERS
# =========================================================
def _parse_macrotemas(
    macrotemas: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Optional[Dict[str, ThemeDefinitionSchema]]:
    """
    Converte o dicionário bruto de macrotemas em objetos tipados.
    """
    if not macrotemas:
        return None

    return {
        label: ThemeDefinitionSchema(**payload)
        for label, payload in macrotemas.items()
    }


def _parse_rules(
    rules: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Optional[Dict[str, ThemeRuleSchema]]:
    """
    Converte o dicionário bruto de regras em objetos tipados.
    """
    if not rules:
        return None

    return {
        label: ThemeRuleSchema(**payload)
        for label, payload in rules.items()
    }


def _parse_config(
    config: Optional[Dict[str, Any]] = None,
) -> Optional[ThemeClassifierConfigSchema]:
    """
    Converte a configuração bruta em schema tipado.
    """
    if not config:
        return None

    return ThemeClassifierConfigSchema(**config)


# =========================================================
# BASE TOOLS
# =========================================================
@tool(
    "classify_single_text_tool",
    args_schema=ThemeSingleTextToolInputSchema,
)
def classify_single_text_tool(
    titulo: str,
    conteudo: str,
    macrotemas: Optional[Dict[str, Dict[str, Any]]] = None,
    rules: Optional[Dict[str, Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classifica um único texto em temas com base em regras e similaridade semântica.

    Args:
        titulo: Título do texto.
        conteudo: Conteúdo principal do texto.
        macrotemas: Dicionário de definições de temas.
        rules: Dicionário de regras determinísticas por tema.
        config: Configuração do classificador.

    Returns:
        Resultado da classificação em formato serializável.
    """
    service = ThemeClassifierService(
        macrotemas=_parse_macrotemas(macrotemas),
        rules=_parse_rules(rules),
        config=_parse_config(config),
    )

    result = service.predict_one(
        titulo=titulo,
        conteudo=conteudo,
    )

    return result.model_dump()


@tool(
    "classify_themes_from_store_tool",
    args_schema=ThemeBatchFromStoreToolInputSchema,
)
def classify_themes_from_store_tool(
    df_id: str,
    title_col: str = "titulo",
    content_col: str = "conteudo",
    macrotemas: Optional[Dict[str, Dict[str, Any]]] = None,
    rules: Optional[Dict[str, Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    return_scores: bool = False,
    status_mode: str = "review",
    save_output: bool = True,
    output_source: str = "theme_classifier",
    output_filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classifica os textos de um DataFrame armazenado no DATAFRAME_STORE.

    Args:
        df_id: ID do DataFrame salvo no store.
        title_col: Nome da coluna de título.
        content_col: Nome da coluna de conteúdo.
        macrotemas: Dicionário de definições de temas.
        rules: Dicionário de regras determinísticas por tema.
        config: Configuração do classificador.
        return_scores: Se True, inclui scores no output.
        status_mode: Modo de status do classificador.
        save_output: Se True, salva o resultado no DATAFRAME_STORE.
        output_source: Nome da origem a ser salva no metadata.
        output_filters: Filtros adicionais para metadata do output.

    Returns:
        Metadados do processamento e, se aplicável, o novo df_id salvo.
    """
    stored = get_dataframe_with_metadata(df_id)
    df = stored["df"].copy()

    if title_col not in df.columns:
        raise ValueError(
            f"Coluna de título '{title_col}' não encontrada no DataFrame. "
            f"Colunas disponíveis: {list(df.columns)}"
        )

    if content_col not in df.columns:
        raise ValueError(
            f"Coluna de conteúdo '{content_col}' não encontrada no DataFrame. "
            f"Colunas disponíveis: {list(df.columns)}"
        )

    service = ThemeClassifierService(
        macrotemas=_parse_macrotemas(macrotemas),
        rules=_parse_rules(rules),
        config=_parse_config(config),
    )

    df_classificado = service.predict_dataframe(
        df=df,
        text_col_title=title_col,
        text_col_content=content_col,
        return_scores=return_scores,
        status_mode=status_mode,
    )

    if not save_output:
        return {
            "status": "success",
            "message": "Classificação concluída sem salvar no DATAFRAME_STORE.",
            "input_df_id": df_id,
            "output_preview": df_classificado.head(10).to_dict(orient="records"),
            "output_rows": len(df_classificado),
            "output_columns": list(df_classificado.columns),
        }

    merged_filters = {
        "parent_df_id": df_id,
        "step": "theme_classification",
        "classifier": "hybrid_rules_embeddings_prototypes",
        "title_col": title_col,
        "content_col": content_col,
        "return_scores": return_scores,
        "status_mode": status_mode,
        **(stored.get("filters", {}) or {}),
        **(output_filters or {}),
    }

    new_df_id = save_dataframe(
        df=df_classificado,
        source=output_source,
        filters=merged_filters,
    )

    return {
        "status": "success",
        "message": "Classificação concluída e DataFrame salvo no DATAFRAME_STORE.",
        "input_df_id": df_id,
        "output_df_id": new_df_id,
        "output_metadata": {
            "source": output_source,
            "rows": len(df_classificado),
            "columns": list(df_classificado.columns),
            "filters": merged_filters,
        },
    }


# =========================================================
# WITH FOCUS PARSERS
# =========================================================
def _build_macrotemas(
    macrotemas_raw: Optional[Dict[str, Dict[str, Any]]],
) -> Dict[str, ThemeWithFocusDefinitionSchema]:
    """
    Converte o dicionário bruto de macrotemas with-focus em objetos tipados.
    """
    if not macrotemas_raw:
        return {}

    return {
        label: (
            value
            if isinstance(value, ThemeWithFocusDefinitionSchema)
            else ThemeWithFocusDefinitionSchema(**value)
        )
        for label, value in macrotemas_raw.items()
    }


def _build_rules(
    rules_raw: Optional[Dict[str, Dict[str, Any]]],
) -> Dict[str, ThemeWithFocusRuleSchema]:
    """
    Converte o dicionário bruto de regras with-focus em objetos tipados.
    """
    if not rules_raw:
        return {}

    return {
        label: (
            value
            if isinstance(value, ThemeWithFocusRuleSchema)
            else ThemeWithFocusRuleSchema(**value)
        )
        for label, value in rules_raw.items()
    }


def _build_config(
    config_raw: Optional[Dict[str, Any]],
) -> ThemeWithFocusConfigSchema:
    """
    Converte a configuração bruta with-focus em schema tipado.
    """
    if not config_raw:
        return ThemeWithFocusConfigSchema()

    if isinstance(config_raw, ThemeWithFocusConfigSchema):
        return config_raw

    return ThemeWithFocusConfigSchema(**config_raw)


def _build_macro_groups(
    macro_groups_raw: Optional[Dict[str, Dict[str, Dict[str, Any]]]],
) -> Dict[str, Dict[str, ThemeWithFocusDefinitionSchema]]:
    """
    Converte a estrutura hierárquica macro -> subtemas em objetos tipados.
    """
    if not macro_groups_raw:
        return {}

    output: Dict[str, Dict[str, ThemeWithFocusDefinitionSchema]] = {}
    for macro_label, subthemes in macro_groups_raw.items():
        output[macro_label] = {}
        for sub_label, value in subthemes.items():
            output[macro_label][sub_label] = (
                value
                if isinstance(value, ThemeWithFocusDefinitionSchema)
                else ThemeWithFocusDefinitionSchema(**value)
            )
    return output


def _build_service(
    macrotemas: Optional[Dict[str, Dict[str, Any]]] = None,
    rules: Optional[Dict[str, Dict[str, Any]]] = None,
    macro_groups: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None,
    macro_rules: Optional[Dict[str, Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    llm: Any = None,
    embedding_backend: Any = None,
) -> ThemeClassifierWithFocusService:
    """
    Monta a instância do serviço with-focus com LLM e embeddings padrão.
    """
    macrotemas_obj = _build_macrotemas(macrotemas)
    rules_obj = _build_rules(rules)
    macro_groups_obj = _build_macro_groups(macro_groups)
    config_obj = _build_config(config)

    llm_instance = llm or get_default_llm()
    embedding_instance = embedding_backend or get_default_embeddings()

    return ThemeClassifierWithFocusService(
        macrotemas=macrotemas_obj,
        rules=rules_obj,
        config=config_obj,
        llm=llm_instance,
        embedding_backend=embedding_instance,
        macro_groups=macro_groups_obj,
        macro_rules=macro_rules or {},
    )


# =========================================================
# WITH FOCUS TOOLS
# =========================================================
@tool(
    "classify_theme_with_focus_single_tool",
    args_schema=ThemeSingleTextWithFocusInputSchema,
)
def classify_theme_with_focus_single_tool(
    titulo: str,
    conteudo: str,
    macrotemas: Optional[Dict[str, Dict[str, Any]]] = None,
    rules: Optional[Dict[str, Dict[str, Any]]] = None,
    macro_groups: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None,
    macro_rules: Optional[Dict[str, Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    focus_entity: Optional[str] = None,
    focus_aliases: Optional[list[str]] = None,
    threshold: float = 0.50,
    use_llm_validation: bool = False,
    neighbor_window: int = 1,
) -> Dict[str, Any]:
    """
    Classifica um único texto considerando uma entidade de foco.

    A classificação combina regras, embeddings e validação opcional com LLM,
    respeitando aliases e janelas de contexto para a entidade focal.

    Args:
        titulo: Título do texto.
        conteudo: Conteúdo principal do texto.
        macrotemas: Dicionário de macrotemas with-focus.
        rules: Dicionário de regras with-focus.
        macro_groups: Estrutura hierárquica macro -> subtemas.
        macro_rules: Regras adicionais por macrotema.
        config: Configuração do classificador.
        focus_entity: Entidade principal de foco.
        focus_aliases: Lista de aliases da entidade.
        threshold: Threshold mínimo de aceitação.
        use_llm_validation: Se True, ativa validação com LLM.
        neighbor_window: Janela de contexto vizinho.

    Returns:
        Resultado da classificação do texto.
    """
    service = _build_service(
        macrotemas=macrotemas,
        rules=rules,
        macro_groups=macro_groups,
        macro_rules=macro_rules,
        config=config,
    )

    result = service.predict_one_with_focus(
        titulo=titulo,
        conteudo=conteudo,
        focus_entity=focus_entity,
        focus_aliases=focus_aliases,
        threshold=threshold,
        use_llm_validation=use_llm_validation,
        neighbor_window=neighbor_window,
    )

    return result


@tool(
    "classify_theme_with_focus_from_store_tool",
    args_schema=ThemeBatchFromStoreWithFocusInputSchema,
)
def classify_theme_with_focus_from_store_tool(
    df_id: str,
    title_col: str = "titulo",
    content_col: str = "conteudo",
    focus_entity_col: Optional[str] = "Empresa analisada",
    focus_aliases_col: Optional[str] = None,
    macrotemas: Optional[Dict[str, Dict[str, Any]]] = None,
    rules: Optional[Dict[str, Dict[str, Any]]] = None,
    macro_groups: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None,
    macro_rules: Optional[Dict[str, Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    threshold: float = 0.50,
    use_llm_validation: bool = False,
    neighbor_window: int = 1,
    return_scores: bool = True,
    save_output: bool = True,
    output_source: str = "theme_classifier_with_focus_hierarchical",
    output_filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classifica um DataFrame do DATAFRAME_STORE considerando entidade de foco por linha.

    Args:
        df_id: ID do DataFrame salvo no store.
        title_col: Coluna com título do texto.
        content_col: Coluna com conteúdo do texto.
        focus_entity_col: Coluna com a entidade focal.
        focus_aliases_col: Coluna com aliases da entidade focal.
        macrotemas: Dicionário de macrotemas with-focus.
        rules: Dicionário de regras with-focus.
        macro_groups: Estrutura hierárquica macro -> subtemas.
        macro_rules: Regras adicionais por macrotema.
        config: Configuração do classificador.
        threshold: Threshold mínimo de aceitação.
        use_llm_validation: Se True, ativa validação com LLM.
        neighbor_window: Janela de contexto vizinho.
        return_scores: Se True, retorna scores no DataFrame final.
        save_output: Se True, salva o output no DATAFRAME_STORE.
        output_source: Nome da origem do output salvo.
        output_filters: Filtros adicionais para metadata.

    Returns:
        Metadados da classificação e preview do resultado.
    """
    df = get_dataframe(df_id)

    required_cols = [title_col, content_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return {
            "status": "error",
            "message": f"Colunas obrigatórias ausentes no DataFrame: {missing_cols}",
            "df_id": df_id,
            "available_columns": list(df.columns),
        }

    if focus_entity_col and focus_entity_col not in df.columns:
        return {
            "status": "error",
            "message": f"Coluna focus_entity_col '{focus_entity_col}' não encontrada no DataFrame.",
            "df_id": df_id,
            "available_columns": list(df.columns),
        }

    if focus_aliases_col and focus_aliases_col not in df.columns:
        return {
            "status": "error",
            "message": f"Coluna focus_aliases_col '{focus_aliases_col}' não encontrada no DataFrame.",
            "df_id": df_id,
            "available_columns": list(df.columns),
        }

    service = _build_service(
        macrotemas=macrotemas,
        rules=rules,
        macro_groups=macro_groups,
        macro_rules=macro_rules,
        config=config,
    )

    llm_batch_size = None
    if config and isinstance(config, dict):
        llm_batch_size = config.get("llm_batch_size")

    output_df = service.predict_dataframe_with_focus(
        df=df,
        text_col_title=title_col,
        text_col_content=content_col,
        focus_entity_col=focus_entity_col,
        focus_aliases_col=focus_aliases_col,
        threshold=threshold,
        use_llm_validation=use_llm_validation,
        neighbor_window=neighbor_window,
        return_scores=return_scores,
        llm_batch_size=llm_batch_size,
    )

    output_df_id = None
    if save_output:
        output_df_id = save_dataframe(
            df=output_df,
            source=output_source,
            filters={
                "parent_df_id": df_id,
                "title_col": title_col,
                "content_col": content_col,
                "focus_entity_col": focus_entity_col,
                "focus_aliases_col": focus_aliases_col,
                "threshold": threshold,
                "use_llm_validation": use_llm_validation,
                "neighbor_window": neighbor_window,
                **(output_filters or {}),
            },
        )

    preview_cols = [
        col
        for col in [
            title_col,
            content_col,
            focus_entity_col,
            "predicted_macro",
            "best_theme",
            "best_score",
            "focus_found",
            "fallback_reason",
            "llm_suggested_theme",
            "valid_themes",
        ]
        if col and col in output_df.columns
    ]

    return {
        "status": "success",
        "input_df_id": df_id,
        "output_df_id": output_df_id,
        "rows": len(output_df),
        "columns": list(output_df.columns),
        "preview": output_df[preview_cols].head(10).to_dict(orient="records"),
    }


@tool(
    "classify_theme_with_focus_from_store_by_cluster_tool",
    args_schema=ThemeBatchFromStoreWithFocusByClusterInputSchema,
)
def classify_theme_with_focus_from_store_by_cluster_tool(
    df_id: str,
    cluster_id_col: str = "cluster_id",
    title_col: str = "titulo",
    content_col: str = "conteudo",
    focus_entity_col: Optional[str] = "Empresa analisada",
    focus_aliases_col: Optional[str] = None,
    distance_col: str = "distance_to_centroid",
    closest_cluster_n: int = 10,
    macrotemas: Optional[Dict[str, Dict[str, Any]]] = None,
    rules: Optional[Dict[str, Dict[str, Any]]] = None,
    macro_groups: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None,
    macro_rules: Optional[Dict[str, Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    threshold: float = 0.50,
    use_llm_validation: bool = False,
    neighbor_window: int = 1,
    return_scores: bool = True,
    cluster_text_max_chars: int = 4000,
    run_ambiguous_llm_validation: bool = False,
    ambiguous_score_threshold: float = 0.72,
    ambiguous_margin_threshold: float = 0.12,
    save_output: bool = True,
    output_source: str = "theme_classifier_with_focus_by_cluster",
    output_filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classifica textos de um DataFrame agrupados por cluster, considerando entidade de foco.

    A tool utiliza o contexto dos textos mais próximos ao centróide do cluster
    para enriquecer a classificação temática, com suporte opcional a validação
    ambígua via LLM.

    Args:
        df_id: ID do DataFrame salvo no store.
        cluster_id_col: Coluna identificadora do cluster.
        title_col: Coluna de título.
        content_col: Coluna de conteúdo.
        focus_entity_col: Coluna com entidade focal.
        focus_aliases_col: Coluna com aliases da entidade focal.
        distance_col: Coluna de distância ao centróide.
        closest_cluster_n: Número de textos mais próximos por cluster.
        macrotemas: Dicionário de macrotemas with-focus.
        rules: Dicionário de regras with-focus.
        macro_groups: Estrutura hierárquica macro -> subtemas.
        macro_rules: Regras adicionais por macrotema.
        config: Configuração do classificador.
        threshold: Threshold mínimo de aceitação.
        use_llm_validation: Se True, ativa validação com LLM.
        neighbor_window: Janela de contexto vizinho.
        return_scores: Se True, mantém scores no output final.
        cluster_text_max_chars: Limite de caracteres do contexto por cluster.
        run_ambiguous_llm_validation: Se True, valida casos ambíguos com LLM.
        ambiguous_score_threshold: Threshold para identificar ambiguidade.
        ambiguous_margin_threshold: Margem entre scores para ambiguidade.
        save_output: Se True, salva o resultado no DATAFRAME_STORE.
        output_source: Nome da origem do output salvo.
        output_filters: Filtros adicionais para metadata.

    Returns:
        Metadados da classificação por cluster e preview do resultado.
    """
    df = get_dataframe(df_id).copy()

    required_cols = [cluster_id_col, title_col, content_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return {
            "status": "error",
            "message": f"Colunas obrigatórias ausentes no DataFrame: {missing_cols}",
            "df_id": df_id,
            "available_columns": list(df.columns),
        }

    if distance_col not in df.columns:
        return {
            "status": "error",
            "message": f"Coluna distance_col '{distance_col}' não encontrada no DataFrame.",
            "df_id": df_id,
            "available_columns": list(df.columns),
        }

    if focus_entity_col and focus_entity_col not in df.columns:
        return {
            "status": "error",
            "message": f"Coluna focus_entity_col '{focus_entity_col}' não encontrada no DataFrame.",
            "df_id": df_id,
            "available_columns": list(df.columns),
        }

    if focus_aliases_col and focus_aliases_col not in df.columns:
        return {
            "status": "error",
            "message": f"Coluna focus_aliases_col '{focus_aliases_col}' não encontrada no DataFrame.",
            "df_id": df_id,
            "available_columns": list(df.columns),
        }

    service = _build_service(
        macrotemas=macrotemas,
        rules=rules,
        macro_groups=macro_groups,
        macro_rules=macro_rules,
        config=config,
    )

    output_df = service.predict_dataframe_with_focus_by_cluster(
        df=df,
        cluster_id_col=cluster_id_col,
        text_col_title=title_col,
        text_col_content=content_col,
        distance_col=distance_col,
        closest_cluster_n=closest_cluster_n,
        focus_entity_col=focus_entity_col,
        focus_aliases_col=focus_aliases_col,
        threshold=threshold,
        use_llm_validation=use_llm_validation,
        neighbor_window=neighbor_window,
        return_scores=return_scores,
        cluster_text_max_chars=cluster_text_max_chars,
        run_ambiguous_llm_validation=run_ambiguous_llm_validation,
        ambiguous_score_threshold=ambiguous_score_threshold,
        ambiguous_margin_threshold=ambiguous_margin_threshold,
    )

    output_df_id = None
    if save_output:
        output_df_id = save_dataframe(
            df=output_df,
            source=output_source,
            filters={
                "parent_df_id": df_id,
                "cluster_id_col": cluster_id_col,
                "title_col": title_col,
                "content_col": content_col,
                "focus_entity_col": focus_entity_col,
                "focus_aliases_col": focus_aliases_col,
                "distance_col": distance_col,
                "closest_cluster_n": closest_cluster_n,
                "threshold": threshold,
                "use_llm_validation": use_llm_validation,
                "neighbor_window": neighbor_window,
                "cluster_text_max_chars": cluster_text_max_chars,
                "run_ambiguous_llm_validation": run_ambiguous_llm_validation,
                "ambiguous_score_threshold": ambiguous_score_threshold,
                "ambiguous_margin_threshold": ambiguous_margin_threshold,
                **(output_filters or {}),
            },
        )

    preview_cols = [
        col
        for col in [
            cluster_id_col,
            title_col,
            focus_entity_col,
            "predicted_macro",
            "best_theme",
            "best_score",
            "cluster_size",
            "focus_found",
            "fallback_reason",
            "llm_suggested_theme",
            "valid_themes",
        ]
        if col and col in output_df.columns
    ]

    return {
        "status": "success",
        "input_df_id": df_id,
        "output_df_id": output_df_id,
        "rows": len(output_df),
        "clusters": int(output_df[cluster_id_col].nunique(dropna=True)),
        "columns": list(output_df.columns),
        "preview": output_df[preview_cols].head(10).to_dict(orient="records"),
    }