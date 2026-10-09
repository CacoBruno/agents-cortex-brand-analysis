from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class SentimentClassificationInput(BaseModel):
    dataframe_id: str = Field(
        ...,
        description=(
            "ID de um DataFrame previamente armazenado no dataframe_store. "
            "Esse ID deve vir de tools como export_media_analysis_database_tool, "
            "export_publications_database_tool ou get_prdata_dataframe_tool."
        )
    )

    def to_service_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True)


class SentimentClassificationMeta(BaseModel):
    source_dataframe_id: str
    result_rows: int
    result_columns_count: int
    result_columns: List[str]
    operation: str
    filters_applied: Dict[str, Any]


class SentimentClassificationOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: SentimentClassificationMeta
    preview: List[Dict[str, Any]]

class ToolErrorOutput(BaseModel):
    status: str = "error"
    message: str
    error_type: str
    details: Optional[str] = None


class ProtagonismClassificationInput(BaseModel):
    dataframe_id: str = Field(
        ...,
        description=(
            "ID de um DataFrame previamente armazenado no dataframe_store. "
            "Esse ID deve vir de tools como export_media_analysis_database_tool, "
            "export_publications_database_tool ou get_prdata_dataframe_tool."
        )
    )
    lista_marca: List[str] = Field(
        ...,
        description="Lista com os nomes das marcas para classificação de protagonismo."
    )

    @field_validator("lista_marca", mode="before")
    @classmethod
    def normalize_lista_marca(cls, v):
        if v is None:
            raise ValueError("lista_marca é obrigatória.")

        if isinstance(v, str):
            v = [v]

        if not isinstance(v, list):
            raise ValueError("lista_marca deve ser uma lista de strings.")

        cleaned = []
        for item in v:
            if item is None:
                continue
            if not isinstance(item, str):
                item = str(item)
            item = item.strip()
            if item:
                cleaned.append(item)

        if not cleaned:
            raise ValueError("lista_marca deve conter pelo menos uma marca válida.")

        return cleaned

    def to_service_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True)


class ProtagonismClassificationMeta(BaseModel):
    source_dataframe_id: str
    result_rows: int
    result_columns_count: int
    result_columns: List[str]
    operation: str
    filters_applied: Dict[str, Any]


class ProtagonismClassificationOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: ProtagonismClassificationMeta
    preview: List[Dict[str, Any]]

class ClusteringToClassificationInput(BaseModel):
    """
    Input para transformação de clustering/classificação
    a partir de um DataFrame salvo no DATAFRAME_STORE.
    """

    dataframe_id: str = Field(
        ...,
        description=(
            "ID de um DataFrame previamente armazenado no DATAFRAME_STORE. "
            "Esse ID deve vir de tools de download ou de outras tools de transformação."
        ),
    )

    focus_terms: Optional[List[str]] = Field(
        default=None,
        description=(
            "Lista opcional de termos para focar o texto antes do clustering. "
            "Exemplo: ['Itau', 'Itaú Unibanco']. "
            "Se None, o clustering usa o clean_text normal. "
            "Se os termos forem encontrados, a função usa apenas os trechos relacionados. "
            "Se não forem encontrados, mantém o texto original."
        ),
    )

    output_source: str = Field(
        default="clustering_to_classification",
        description="Nome da fonte para salvar o DataFrame processado no DATAFRAME_STORE.",
    )

    preview_rows: int = Field(
        default=10,
        description="Quantidade de linhas de preview a retornar no output.",
        ge=1,
        le=50,
    )

    def to_service_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True)


class ClusteringToClassificationMeta(BaseModel):
    """
    Metadados do processamento de clustering/classificação.
    """

    source_dataframe_id: str = Field(
        ...,
        description="ID do DataFrame original utilizado como entrada.",
    )
    result_rows: int = Field(
        ...,
        description="Número de linhas do DataFrame resultante.",
    )
    result_columns_count: int = Field(
        ...,
        description="Quantidade de colunas do DataFrame resultante.",
    )
    result_columns: List[str] = Field(
        ...,
        description="Lista de colunas presentes no DataFrame resultante.",
    )
    operation: str = Field(
        default="clustering_to_classification",
        description="Nome da operação executada.",
    )
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filtros e parâmetros aplicados durante o processamento.",
    )
    focus_terms_applied: bool = Field(
        default=False,
        description="Indica se termos de foco foram enviados para o processamento.",
    )
    focus_terms: Optional[List[str]] = Field(
        default=None,
        description="Lista de termos de foco efetivamente recebida.",
    )


class ClusteringToClassificationOutput(BaseModel):
    """
    Output de sucesso da transformação clustering/classificação.
    """

    status: str = Field(default="success")
    message: str = Field(
        ...,
        description="Mensagem de sucesso da operação.",
    )
    dataframe_id: str = Field(
        ...,
        description="ID do DataFrame salvo no DATAFRAME_STORE após o processamento.",
    )
    meta: ClusteringToClassificationMeta = Field(
        ...,
        description="Metadados da operação executada.",
    )
    preview: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Prévia das primeiras linhas do DataFrame resultante.",
    )


class ClusteringToClassificationErrorOutput(BaseModel):
    """
    Output de erro da transformação clustering/classificação.
    """

    status: str = Field(default="error")
    message: str = Field(
        ...,
        description="Mensagem resumida do erro.",
    )
    error_type: str = Field(
        ...,
        description="Tipo/classe do erro levantado.",
    )
    details: str = Field(
        ...,
        description="Detalhes técnicos do erro.",
    )

class ThemsClassificationInput(BaseModel):
    dataframe_id: str = Field(..., description="ID do DataFrame salvo no DATAFRAME_STORE.")
    macrotemas_dict: Dict[str, str] = Field(
        ...,
        description="Dicionário de macrotemas no formato {'Macrotema': 'descrição'}."
    )
    model: str = Field(default="gpt-4o-mini", description="Modelo LLM.")
    temperature: float = Field(default=0.2, description="Temperatura do modelo.")
    max_concurrent: Optional[int] = Field(
        default=None,
        description="Número máximo de chamadas concorrentes."
    )
    max_workers: Optional[int] = Field(
        default=None,
        description="Alias legado para concorrência."
    )
    text_chunk_max_chars: int = Field(
        default=18000,
        description="Tamanho máximo dos chunks de texto."
    )
    macrotema_group_max_chars: int = Field(
        default=5000,
        description="Tamanho máximo dos grupos de macrotemas."
    )
    similarity_threshold: float = Field(
        default=0.72,
        description="Threshold para normalização de temas similares."
    )
    cluster_id_col: str = Field(default="cluster_id", description="Nome da coluna de cluster.")
    summary_col: str = Field(default="cluster_summary", description="Nome da coluna de resumo.")
    topic_col: str = Field(default="specific_topic", description="Nome da coluna de tema específico.")
    macro_col: str = Field(default="macro_topic", description="Nome da coluna de macrotema.")
    output_source: str = Field(
        default="thems_classification",
        description="Nome da fonte para salvar no DATAFRAME_STORE."
    )


class ThemsClassificationMeta(BaseModel):
    input_dataframe_id: str = Field(..., description="ID do DataFrame de entrada.")
    output_dataframe_id: str = Field(..., description="ID do DataFrame salvo após processamento.")
    input_rows: int = Field(..., description="Número de linhas do DataFrame de entrada.")
    output_rows: int = Field(..., description="Número de linhas do DataFrame de saída.")
    added_columns: List[str] = Field(
        ...,
        description="Colunas adicionadas ao DataFrame."
    )
    cluster_id_col: str = Field(..., description="Coluna usada como identificador do cluster.")


class ThemsClassificationOutput(BaseModel):
    status: str = Field(default="success")
    message: str = Field(..., description="Mensagem de sucesso.")
    dataframe_id: str = Field(..., description="ID do DataFrame de saída.")
    meta: ThemsClassificationMeta


class ThemsClassificationErrorOutput(BaseModel):
    status: str = Field(default="error")
    message: str = Field(..., description="Mensagem de erro.")
    error_type: str = Field(..., description="Tipo do erro.")
    details: str = Field(..., description="Detalhes do erro.")


class IdentifyEntitiesInput(BaseModel):
    dataframe_id: str = Field(
        ...,
        description="ID do dataframe salvo no DATAFRAME_STORE."
    )
    search_dict: Dict[str, List[str]] = Field(
        ...,
        description=(
            "Dicionário de entidades e seus termos de busca. "
            "Exemplo: {'Banco Master': ['Banco Master', 'Master'], "
            "'Itaú': ['Itaú', 'Itaú Unibanco']}"
        )
    )
    title_col: str = Field(
        default="titulo",
        description="Nome da coluna de título."
    )
    content_col: str = Field(
        default="conteudo",
        description="Nome da coluna de conteúdo."
    )
    output_col: str = Field(
        default="entidade_encontrada",
        description="Nome da coluna de saída com as entidades identificadas."
    )
    split_output: bool = Field(
        default=True,
        description="Se True, divide múltiplas entidades em várias linhas."
    )
    hash_columns: Optional[List[str]] = Field(
        default=None,
        description=(
            "Lista de colunas usadas para gerar o hash. "
            "Se None, usa automaticamente [title_col, content_col, output_col]."
        )
    )


class IdentifyEntitiesMeta(BaseModel):
    input_rows: int = Field(..., description="Número de linhas do dataframe de entrada.")
    output_rows: int = Field(..., description="Número de linhas do dataframe de saída.")
    entities_found_count: int = Field(..., description="Número de linhas com alguma entidade encontrada.")
    unique_entities_found: List[str] = Field(..., description="Lista de entidades únicas encontradas.")
    output_dataframe_id: str = Field(..., description="ID do dataframe salvo após o processamento.")


class IdentifyEntitiesOutput(BaseModel):
    status: str = Field(default="success")
    message: str = Field(..., description="Mensagem de sucesso.")
    dataframe_id: str = Field(..., description="ID do dataframe gerado.")
    meta: IdentifyEntitiesMeta