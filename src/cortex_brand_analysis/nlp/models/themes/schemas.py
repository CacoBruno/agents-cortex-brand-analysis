from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# =========================================================
# BASE CLASSIFIER
# =========================================================


class ThemeDefinitionSchema(BaseModel):
    descricao: str = Field(..., description="Descrição semântica do tema")
    exemplos: list[str] = Field(default_factory=list, description="Exemplos positivos do tema")
    exclusoes: list[str] = Field(
        default_factory=list, description="Termos/contextos que não pertencem ao tema"
    )
    prototipos: list[str] = Field(default_factory=list, description="Protótipos semânticos do tema")
    prioridade: int = Field(default=0, description="Prioridade para desempate")


class ThemeRuleSchema(BaseModel):
    include: list[str] = Field(
        default_factory=list, description="Termos que favorecem a classificação no tema"
    )
    exclude: list[str] = Field(
        default_factory=list, description="Termos que penalizam a classificação no tema"
    )
    weight: float = Field(default=1.0, description="Peso da regra")


class ThemeWeightsSchema(BaseModel):
    rules: float = Field(default=0.55, description="Peso do score de regras")
    title: float = Field(default=0.25, description="Peso do score do título")
    content: float = Field(default=0.10, description="Peso do score do conteúdo")
    prototypes: float = Field(default=0.10, description="Peso do score dos protótipos")


class ThemePredictionInputSchema(BaseModel):
    titulo: str | None = Field(default="", description="Título da matéria/texto")
    conteudo: str | None = Field(default="", description="Conteúdo da matéria/texto")


class ThemePredictionResultSchema(BaseModel):
    label: str = Field(..., description="Rótulo final predito")
    confidence: float = Field(..., description="Confiança do melhor rótulo")
    margin_top2: float = Field(..., description="Diferença entre top_1 e top_2")
    top_1: str = Field(..., description="Melhor rótulo antes da checagem de confidence")
    top_2: str = Field(..., description="Segundo melhor rótulo")
    rule_hits: list[str] = Field(
        default_factory=list, description="Termos de regra encontrados no tema vencedor"
    )
    rule_scores: dict[str, float] = Field(default_factory=dict)
    title_scores: dict[str, float] = Field(default_factory=dict)
    content_scores: dict[str, float] = Field(default_factory=dict)
    prototype_scores: dict[str, float] = Field(default_factory=dict)
    final_scores: dict[str, float] = Field(default_factory=dict)


class ThemeClassifierConfigSchema(BaseModel):
    embedding_model_name: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        description="Nome do modelo de embeddings",
    )
    min_confidence: float = Field(
        default=0.20, description="Confiança mínima para aceitar um rótulo"
    )
    review_threshold: float = Field(
        default=0.45, description="A partir deste valor, status vira 'review'"
    )
    accepted_threshold: float = Field(
        default=0.60, description="A partir deste valor, status vira 'accepted'"
    )
    weights: ThemeWeightsSchema = Field(default_factory=ThemeWeightsSchema)


class ThemeClassifierBatchInputSchema(BaseModel):
    text_col_title: str = Field(default="titulo")
    text_col_content: str = Field(default="conteudo")
    return_scores: bool = Field(default=False)
    status_mode: Literal["simple", "review"] = Field(default="review")


class ThemeSingleTextToolInputSchema(BaseModel):
    titulo: str = Field(..., description="Título do texto")
    conteudo: str = Field(..., description="Conteúdo do texto")

    macrotemas: dict[str, dict[str, Any]] | None = Field(
        default=None, description="Dicionário opcional de macrotemas customizados"
    )
    rules: dict[str, dict[str, Any]] | None = Field(
        default=None, description="Dicionário opcional de regras customizadas"
    )
    config: dict[str, Any] | None = Field(
        default=None, description="Configuração opcional do classificador"
    )


class ThemeBatchFromStoreToolInputSchema(BaseModel):
    df_id: str = Field(..., description="ID do DataFrame armazenado no DATAFRAME_STORE")
    title_col: str = Field(default="titulo", description="Nome da coluna de título")
    content_col: str = Field(default="conteudo", description="Nome da coluna de conteúdo")

    macrotemas: dict[str, dict[str, Any]] | None = Field(
        default=None, description="Dicionário opcional de macrotemas customizados"
    )
    rules: dict[str, dict[str, Any]] | None = Field(
        default=None, description="Dicionário opcional de regras customizadas"
    )
    config: dict[str, Any] | None = Field(
        default=None, description="Configuração opcional do classificador"
    )

    return_scores: bool = Field(default=False, description="Se True, adiciona colunas com scores")
    status_mode: Literal["simple", "review"] = Field(
        default="review", description="Modo de status da classificação"
    )

    save_output: bool = Field(
        default=True, description="Se True, salva o resultado classificado no DATAFRAME_STORE"
    )
    output_source: str = Field(
        default="theme_classifier",
        description="Valor do campo source ao salvar o DataFrame de saída",
    )
    output_filters: dict[str, Any] | None = Field(
        default=None, description="Filtros/metadados extras para salvar no DATAFRAME_STORE"
    )


# =========================================================
# WITH FOCUS
# =========================================================


class ThemeWithFocusDefinitionSchema(BaseModel):
    descricao: str = Field(..., description="Descrição do tema")
    exemplos: list[str] = Field(default_factory=list, description="Exemplos positivos")
    exclusoes: list[str] = Field(default_factory=list, description="Exclusões conceituais")
    prototipos: list[str] = Field(default_factory=list, description="Protótipos semânticos")
    prioridade: int = Field(default=0, description="Prioridade para desempate")


class ThemeWithFocusRuleSchema(BaseModel):
    include: list[str] = Field(default_factory=list, description="Termos que reforçam o tema")
    exclude: list[str] = Field(default_factory=list, description="Termos que enfraquecem o tema")
    weight: float = Field(default=1.0, description="Peso da regra")


class ThemeWithFocusConfigSchema(BaseModel):
    rule_weight: float = Field(default=0.55, description="Peso do score por regras")
    semantic_weight: float = Field(default=0.45, description="Peso do score semântico")
    threshold: float = Field(default=0.50, description="Threshold mínimo")
    neighbor_window: int = Field(default=1, description="Janela de sentenças vizinhas")

    require_lexical_gate: bool = Field(
        default=True, description="Se True, exige evidência lexical mínima antes de aceitar um tema"
    )
    lexical_gate_min_hits: int = Field(
        default=1, description="Quantidade mínima de hits include para liberar o tema"
    )
    lexical_gate_min_score: float = Field(
        default=0.05, description="Score mínimo de regra para liberar o tema"
    )
    semantic_cap_without_lexical: float = Field(
        default=0.20, description="Teto do score semântico quando não há gate lexical"
    )
    use_filtered_text_for_semantic: bool = Field(
        default=True, description="Se True, usa o texto filtrado no embedding semântico"
    )
    remove_focus_aliases_from_text: bool = Field(
        default=True,
        description="Se True, remove aliases da entidade foco antes de calcular o tema",
    )
    fallback_label: str = Field(
        default="Sem classificação",
        description="Rótulo usado quando nenhum tema passa nos critérios",
    )
    fallback_use_llm_suggestion: bool = Field(
        default=True, description="Se True, chama LLM para sugerir tema quando cair em fallback"
    )
    generic_financial_penalty: float = Field(
        default=0.15,
        description="Penalização aplicada a temas financeiros genéricos sem evidência lexical",
    )

    use_llm_validation: bool = Field(
        default=False, description="No primeiro passe, não usa LLM por padrão"
    )
    return_all_scores: bool = Field(default=True, description="Se retorna ranking completo")
    llm_batch_size: int = Field(default=20, description="Tamanho do batch para validação LLM")
    max_workers: int = Field(default=8, description="Workers para scoring paralelo")

    macro_prefilter_top_k: int = Field(default=3, description="Top-k macros no pré-filtro")
    theme_prefilter_top_k: int = Field(default=6, description="Top-k temas no pré-filtro")
    macro_rule_min_score: float = Field(default=0.05, description="Score mínimo para macro")
    theme_rule_min_score: float = Field(default=0.03, description="Score mínimo para tema")

    skip_llm_if_confident: bool = Field(default=True, description="Pula LLM se score muito claro")
    confidence_score_threshold: float = Field(default=0.85, description="Threshold para pular LLM")
    min_margin_for_skip_llm: float = Field(default=0.20, description="Margem mínima para pular LLM")

    distance_col: str = Field(
        default="distance_to_centroid", description="Coluna com a distância ao centróide"
    )
    closest_cluster_n: int = Field(
        default=10, description="Quantidade de textos mais centrais usados por cluster"
    )
    cluster_text_max_chars: int = Field(
        default=4000, description="Número máximo de caracteres do texto representativo do cluster"
    )

    run_ambiguous_llm_validation: bool = Field(
        default=False, description="Se True, roda LLM apenas para clusters ambíguos"
    )
    ambiguous_score_threshold: float = Field(
        default=0.72, description="Abaixo deste best_score o cluster é considerado ambíguo"
    )
    ambiguous_margin_threshold: float = Field(
        default=0.12, description="Abaixo desta margem top1-top2 o cluster é considerado ambíguo"
    )


class ThemeWithFocusPredictionItemSchema(BaseModel):
    label: str
    score: float
    rule_score: float | None = None
    embedding_score: float | None = None
    llm_valid: bool | None = None
    llm_reason: str | None = None
    llm_evidence_type: str | None = None
    llm_confidence: float | None = None


class ThemeWithFocusPredictionOutputSchema(BaseModel):
    best_theme: str | None = None
    best_score: float = 0.0
    valid_themes: list[ThemeWithFocusPredictionItemSchema] = Field(default_factory=list)
    focus_entity: str | None = None
    focus_aliases: list[str] = Field(default_factory=list)
    focus_found: bool = False
    filtered_text: str = ""
    scoring_text: str = ""
    all_scores: list[dict[str, Any]] = Field(default_factory=list)
    predicted_macro: str | None = None
    macro_candidates: list[str] = Field(default_factory=list)
    theme_candidates: list[str] = Field(default_factory=list)
    fallback_reason: str | None = None
    llm_suggested_theme: str | None = None
    llm_suggested_macro: str | None = None
    llm_suggestion_reason: str | None = None


class ThemeSingleTextWithFocusInputSchema(BaseModel):
    titulo: str = Field(..., description="Título do texto")
    conteudo: str = Field(..., description="Conteúdo do texto")
    macrotemas: dict[str, dict[str, Any]] | None = Field(default=None)
    rules: dict[str, dict[str, Any]] | None = Field(default=None)
    macro_groups: dict[str, dict[str, dict[str, Any]]] | None = Field(default=None)
    macro_rules: dict[str, dict[str, Any]] | None = Field(default=None)
    config: dict[str, Any] | None = Field(default=None)
    focus_entity: str | None = Field(default=None)
    focus_aliases: list[str] | None = Field(default=None)
    threshold: float = Field(default=0.50)
    use_llm_validation: bool = Field(default=False)
    neighbor_window: int = Field(default=1)


class ThemeBatchFromStoreWithFocusInputSchema(BaseModel):
    df_id: str = Field(..., description="ID do DataFrame salvo no DATAFRAME_STORE")
    title_col: str = Field(default="titulo", description="Coluna do título")
    content_col: str = Field(default="conteudo", description="Coluna do conteúdo")
    focus_entity_col: str | None = Field(
        default="Empresa analisada", description="Coluna da entidade foco"
    )
    focus_aliases_col: str | None = Field(default=None, description="Coluna opcional com aliases")
    macrotemas: dict[str, dict[str, Any]] | None = Field(default=None)
    rules: dict[str, dict[str, Any]] | None = Field(default=None)
    macro_groups: dict[str, dict[str, dict[str, Any]]] | None = Field(default=None)
    macro_rules: dict[str, dict[str, Any]] | None = Field(default=None)
    config: dict[str, Any] | None = Field(default=None)
    threshold: float = Field(default=0.50)
    use_llm_validation: bool = Field(default=False)
    neighbor_window: int = Field(default=1)
    return_scores: bool = Field(default=True)
    save_output: bool = Field(default=True)
    output_source: str = Field(default="theme_classifier_with_focus_hierarchical")
    output_filters: dict[str, Any] | None = Field(default=None)


class ThemeBatchFromStoreWithFocusByClusterInputSchema(BaseModel):
    df_id: str = Field(..., description="ID do DataFrame salvo no DATAFRAME_STORE")

    cluster_id_col: str = Field(
        default="cluster_id", description="Coluna de cluster já existente no dataframe principal"
    )

    title_col: str = Field(default="titulo", description="Coluna do título")
    content_col: str = Field(default="conteudo", description="Coluna do conteúdo")

    focus_entity_col: str | None = Field(
        default="Empresa analisada", description="Coluna da entidade foco"
    )
    focus_aliases_col: str | None = Field(default=None, description="Coluna opcional com aliases")

    distance_col: str = Field(
        default="distance_to_centroid", description="Coluna com a distância ao centróide do cluster"
    )
    closest_cluster_n: int = Field(
        default=10, description="Quantidade de textos mais centrais usados por cluster"
    )

    macrotemas: dict[str, dict[str, Any]] | None = Field(default=None)
    rules: dict[str, dict[str, Any]] | None = Field(default=None)
    macro_groups: dict[str, dict[str, dict[str, Any]]] | None = Field(default=None)
    macro_rules: dict[str, dict[str, Any]] | None = Field(default=None)
    config: dict[str, Any] | None = Field(default=None)

    threshold: float = Field(default=0.50)
    use_llm_validation: bool = Field(default=False)
    neighbor_window: int = Field(default=1)
    return_scores: bool = Field(default=True)

    cluster_text_max_chars: int = Field(
        default=4000, description="Número máximo de caracteres do texto representativo do cluster"
    )

    run_ambiguous_llm_validation: bool = Field(
        default=False, description="Se True, roda LLM apenas para clusters ambíguos"
    )
    ambiguous_score_threshold: float = Field(
        default=0.72, description="Abaixo deste score o cluster é considerado ambíguo"
    )
    ambiguous_margin_threshold: float = Field(
        default=0.12, description="Abaixo desta margem top1-top2 o cluster é considerado ambíguo"
    )

    save_output: bool = Field(default=True)
    output_source: str = Field(default="theme_classifier_with_focus_by_cluster")
    output_filters: dict[str, Any] | None = Field(default=None)
