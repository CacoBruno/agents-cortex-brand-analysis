from typing import Any, List, Dict ,Optional
from pydantic import BaseModel, Field, ConfigDict


class ExtrairContextoNoticiasInput(BaseModel):
    """
    Input para extração de contexto de notícias a partir de um DataFrame salvo.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid"
    )

    df_id: str = Field(
        ...,
        description="ID do DataFrame salvo no DATAFRAME_STORE."
    )

    list_search: List[str] = Field(
        ...,
        description="Lista de termos a serem buscados no conteúdo das notícias."
    )

    # filtro opcional de datas
    start_date: Optional[str] = Field(
        default=None,
        description="Data inicial do filtro (inclusive). Ex.: '2026-03-01'."
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Data final do filtro (inclusive). Ex.: '2026-03-31'."
    )
    date_format: Optional[str] = Field(
        default=None,
        description="Formato opcional da data de entrada, ex.: '%d/%m/%Y'."
    )

    # colunas principais
    col_data: str = Field(default="data", description="Nome da coluna de data.")
    col_titulo: str = Field(default="titulo", description="Nome da coluna de título.")
    col_fonte: str = Field(default="fonte", description="Nome da coluna de fonte.")
    col_conteudo: str = Field(default="conteudo", description="Nome da coluna de conteúdo.")
    col_id: str = Field(
        default="Chave Análise de Mídia Hash",
        description="Nome da coluna de identificador único."
    )

    # colunas opcionais de contexto
    col_alcance: Optional[str] = Field(default="alcance")
    col_tier: Optional[str] = Field(default="tier")
    col_tipos_de_impactos: Optional[str] = Field(default="tipos_de_impactos")
    col_sentimento: Optional[str] = Field(default="sentimento")
    col_protagonismo: Optional[str] = Field(default="protagonismo")

    col_empresa: Optional[str] = Field(default="Empresa analisada")
    col_produto: Optional[str] = Field(default="Produto analisado")
    col_jornalista: Optional[str] = Field(default="Jornalista")

    col_url_noticia: Optional[str] = Field(default="url da notícia")
    col_assuntos_especificos: Optional[str] = Field(default="Assuntos específicos")
    col_midia: Optional[str] = Field(default="Mídia")


class BuildMainDaysCoverageSchema(BaseModel):
    """
    Schema para construir o contexto dos principais dias do período
    com base na contribuição diária ao NPS e no dicionário de cobertura.
    """

    df_daily_contrib_id: str = Field(..., description="ID do dataframe diário salvo no DATAFRAME_STORE.")
    coverage_dict: Dict[str, Dict[str, Any]] = Field(
        ..., description="Dicionário de cobertura diária, indexado por data."
    )

    daily_date_col: str = Field("Data", description="Nome da coluna de data no dataframe diário.")
    contrib_col: str = Field("contr_nps_score", description="Coluna de contribuição para NPS.")
    promoter_col: str = Field("Promotores", description="Coluna de impacto promotor.")
    detractor_col: str = Field("Detratores", description="Coluna de impacto detrator.")
    zscore_col: str = Field("z_score_contr_nps", description="Coluna de z-score do alcance ou da métrica diária.")

    top_n_extra_positive: int = Field(
        0, description="Quantidade extra de dias positivos a adicionar além dos dias-base."
    )
    top_n_extra_negative: int = Field(
        0, description="Quantidade extra de dias negativos a adicionar além dos dias-base."
    )

    filter_col: str | None = Field(
        None, description="Coluna opcional para filtrar o dataframe antes da análise."
    )
    filter_values: list[Any] | None = Field(
        None, description="Valores aceitos para o filtro opcional."
    )


class BuildTopVehiclesCoverageSchema(BaseModel):
    """
    Schema para construir o contexto dos veículos mais relevantes.
    """

    df_vehicles_id: str = Field(..., description="ID do dataframe de veículos salvo no DATAFRAME_STORE.")
    coverage_dict: Dict[str, Dict[str, Any]] = Field(
        ..., description="Dicionário de cobertura diária com documentos."
    )

    source_col: str = Field("Fonte", description="Coluna com o nome da fonte/veículo.")
    promoter_col: str = Field("Promotores", description="Coluna de impacto promotor.")
    detractor_col: str = Field("Detratores", description="Coluna de impacto detrator.")
    top_n: int = Field(10, description="Quantidade de veículos a retornar.")

    filter_col: str | None = Field(
        None, description="Coluna opcional para filtrar o dataframe antes da análise."
    )
    filter_values: list[Any] | None = Field(
        None, description="Valores aceitos para o filtro opcional."
    )


class BuildSpecificTopicsReportsSchema(BaseModel):
    """
    Schema para construir o contexto dos assuntos promotores e detratores,
    cruzando métricas do período com reportagens do dicionário diário.
    """

    df_assunto_period_id: str = Field(..., description="ID do dataframe de assuntos por período salvo no DATAFRAME_STORE.")
    daily_top_news_dict: Dict[str, Dict[str, Any]] = Field(
        ..., description="Dicionário diário com reportagens."
    )

    empresa_col: str = Field("Empresa analisada", description="Coluna com a empresa analisada.")
    topic_col: str = Field("Assunto específico", description="Coluna com o assunto específico.")
    contrib_col: str = Field("nps_contrib_assunto_especifico", description="Coluna de contribuição do assunto ao NPS.")
    topic_nps_col: str = Field("nps_score_assunto_especifico", description="Coluna com NPS do assunto.")
    total_topic_col: str = Field("total_assunto_especifico", description="Coluna com volume total do assunto.")
    denom_total_col: str = Field("denom_total", description="Coluna com denominador total.")
    period_nps_col: str = Field("nps_score_periodo", description="Coluna com NPS do período.")

    period_filter_col: str = Field("mes_index", description="Coluna usada para filtrar o período.")
    period_filter_value: int = Field(0, description="Valor do filtro de período.")
    top_n_positive: int = Field(5, description="Top N assuntos promotores.")
    top_n_negative: int = Field(5, description="Top N assuntos detratores.")

    docs_key: str = Field("documentos", description="Chave dos documentos no dicionário diário.")
    doc_topic_key: str = Field("Assuntos específicos", description="Chave do assunto no documento.")
    doc_company_key: str = Field("empresa", description="Chave da empresa no documento.")
    sort_reports: bool = Field(True, description="Se True, ordena reportagens por alcance/tier/doc_score.")





class BuildCoverageSummarySchema(BaseModel):
    """
    Schema para construir o resumo consolidado da cobertura de mídia
    a partir dos contextos já processados de dias, veículos e assuntos.
    """

    contexto_dia: Dict[str, Any] = Field(
        ..., description="Dicionário de contexto dos principais dias."
    )
    context_veiculos: Dict[str, Any] = Field(
        ..., description="Dicionário de contexto dos principais veículos."
    )
    context_assuntos: Dict[str, Any] = Field(
        ..., description="Dicionário de contexto dos principais assuntos."
    )

    target_brand: str = Field(
        ..., description="Marca-alvo da análise, por exemplo 'americanas sa'."
    )

    model: str = Field(
        default="gpt-4.1-mini",
        description="Modelo OpenAI usado na geração do resumo."
    )
    temperature: float = Field(
        default=0.2,
        description="Temperatura do modelo."
    )

    top_n_vehicles: int = Field(
        default=10,
        description="Número máximo de veículos considerados."
    )
    top_n_docs_per_day: int = Field(
        default=10,
        description="Número máximo de documentos por dia."
    )
    top_n_docs_per_vehicle: int = Field(
        default=8,
        description="Número máximo de documentos por veículo."
    )
    top_n_docs_per_topic: int = Field(
        default=8,
        description="Número máximo de documentos por assunto."
    )
    max_chars_text: int = Field(
        default=2500,
        description="Máximo de caracteres do texto enviado ao LLM por documento."
    )
    include_only_target_brand: bool = Field(
        default=True,
        description="Se True, mantém apenas documentos da marca-alvo."
    )
    final_top_highlights: int = Field(
        default=8,
        description="Número máximo de highlights executivos finais."
    )