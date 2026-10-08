from __future__ import annotations

from langchain_core.tools import tool
from typing import Optional, List

from core.dataframe_store import get_dataframe, save_dataframe
from src.tools_agents.measurements.schemas import (
    SentimentClassificationInput, SentimentClassificationMeta, SentimentClassificationOutput,
    ProtagonismClassificationInput, ProtagonismClassificationMeta, ProtagonismClassificationOutput,
    ClusteringToClassificationInput, ClusteringToClassificationMeta, ClusteringToClassificationOutput,
    ThemsClassificationInput,ThemsClassificationMeta, ThemsClassificationOutput, ClusteringToClassificationErrorOutput,
    ToolErrorOutput, IdentifyEntitiesInput, IdentifyEntitiesOutput, IdentifyEntitiesMeta)

from src.tools_agents.measurements.services import (sentiment_classification_service, protagonism_classification_service, 
                                                    clustering_to_classification_service, 
                                                    identify_entities_service)


@tool("sentiment_classification", args_schema=SentimentClassificationInput)
def sentiment_classification_tool(dataframe_id: str) -> dict:
    """
    Aplica classificação de sentimento em um DataFrame existente (via dataframe_id).
    """
    try:
        params = SentimentClassificationInput(dataframe_id=dataframe_id)

        result_df = sentiment_classification_service(params)

        result_dataframe_id = save_dataframe(
            df=result_df,
            source="sentiment_classification",
            filters={"source_dataframe_id": dataframe_id},
        )

        output = SentimentClassificationOutput(
            message="Classificação de sentimento executada com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=SentimentClassificationMeta(
                source_dataframe_id=dataframe_id,
                result_rows=int(len(result_df)),
                result_columns_count=int(len(result_df.columns)),
                result_columns=list(result_df.columns),
                operation="sentimentClassification",
                filters_applied={"source_dataframe_id": dataframe_id},
            ),
            preview=result_df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao executar classificação de sentimento.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    

@tool("protagonism_classification", args_schema=ProtagonismClassificationInput)
def protagonism_classification_tool(
    dataframe_id: str,
    lista_marca,
) -> dict:
    """
    previamente armazenado,
    usando uma lista de marcas de referência.
    """
    try:
        params = ProtagonismClassificationInput(
            dataframe_id=dataframe_id,
            lista_marca=lista_marca,
        )

        result_df = protagonism_classification_service(params)

        result_dataframe_id = save_dataframe(
            df=result_df,
            source="protagonism_classification",
            filters={
                "source_dataframe_id": dataframe_id,
                "lista_marca": params.lista_marca,
            },
        )

        output = ProtagonismClassificationOutput(
            message="Classificação de protagonismo executada com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=ProtagonismClassificationMeta(
                source_dataframe_id=dataframe_id,
                result_rows=int(len(result_df)),
                result_columns_count=int(len(result_df.columns)),
                result_columns=list(result_df.columns),
                operation="protagonismCclassification",
                filters_applied={
                    "source_dataframe_id": dataframe_id,
                    "lista_marca": params.lista_marca,
                },
            ),
            preview=result_df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao executar classificação de protagonismo.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    


@tool("clustering_to_classification", args_schema=ClusteringToClassificationInput)
def clustering_to_classification_tool(
    dataframe_id: str,
    focus_terms: Optional[List[str]] = None,
    output_source: str = "clustering_to_classification",
    preview_rows: int = 10,
) -> dict:
    """
    Aplica a transformação clustering_to_classification em um DataFrame
    previamente armazenado no DATAFRAME_STORE.

    Parâmetros
    ----------
    dataframe_id : str
        ID do DataFrame salvo no DATAFRAME_STORE.
    focus_terms : Optional[List[str]], default=None
        Lista opcional de termos para focar o texto antes do clustering.
        Se None, usa o clean_text normal.
        Se os termos forem encontrados, usa os trechos relacionados.
        Se não forem encontrados, mantém o texto original.
    output_source : str, default="clustering_to_classification"
        Nome da fonte para salvar o DataFrame processado no DATAFRAME_STORE.
    preview_rows : int, default=10
        Quantidade de linhas de preview retornadas no output.

    Retorna
    -------
    dict
        Dicionário estruturado com status, dataframe_id, metadados e preview.
    """
    try:
        params = ClusteringToClassificationInput(
            dataframe_id=dataframe_id,
            focus_terms=focus_terms,
            output_source=output_source,
            preview_rows=preview_rows,
        )

        result_df = clustering_to_classification_service(params)

        result_dataframe_id = save_dataframe(
            df=result_df,
            source=params.output_source,
            filters={
                "source_dataframe_id": dataframe_id,
                "focus_terms": focus_terms,
            },
        )

        output = ClusteringToClassificationOutput(
            message="Transformação clustering_to_classification executada com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=ClusteringToClassificationMeta(
                source_dataframe_id=dataframe_id,
                result_rows=int(len(result_df)),
                result_columns_count=int(len(result_df.columns)),
                result_columns=list(result_df.columns),
                operation="clustering_to_classification",
                filters_applied={
                    "source_dataframe_id": dataframe_id,
                    "focus_terms": focus_terms,
                    "output_source": output_source,
                    "preview_rows": preview_rows,
                },
                focus_terms_applied=bool(focus_terms),
                focus_terms=focus_terms,
            ),
            preview=result_df.head(preview_rows).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ClusteringToClassificationErrorOutput(
            message="Erro ao executar clustering_to_classification.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    
@tool("identify_entities_in_dataframe", args_schema=IdentifyEntitiesInput)
def identify_entities_in_dataframe_tool(
    dataframe_id: str,
    search_dict: dict,
    title_col: str = "titulo",
    content_col: str = "conteudo",
    output_col: str = "entidade_encontrada",
    split_output: bool = True,
    hash_columns: list | None = None,
) -> dict:
    """
    Identifica entidades em um DataFrame previamente armazenado,
    buscando termos nas colunas de título e conteúdo.
    """
    try:
        params = IdentifyEntitiesInput(
            dataframe_id=dataframe_id,
            search_dict=search_dict,
            title_col=title_col,
            content_col=content_col,
            output_col=output_col,
            split_output=split_output,
            hash_columns=hash_columns,
        )

        source_df = get_dataframe(dataframe_id)
        result_df = identify_entities_service(params)

        result_dataframe_id = save_dataframe(
            df=result_df,
            source="identify_entities_in_dataframe",
            filters={
                "source_dataframe_id": dataframe_id,
                "search_dict": params.search_dict,
                "title_col": params.title_col,
                "content_col": params.content_col,
                "output_col": params.output_col,
                "split_output": params.split_output,
                "hash_columns": params.hash_columns,
            },
        )

        unique_entities = []
        entities_found_count = 0

        if params.output_col in result_df.columns:
            non_null_entities = result_df[params.output_col].dropna()
            unique_entities = sorted(non_null_entities.astype(str).unique().tolist())
            entities_found_count = int(non_null_entities.shape[0])

        output = IdentifyEntitiesOutput(
            message="Identificação de entidades executada com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=IdentifyEntitiesMeta(
                input_rows=int(len(source_df)),
                output_rows=int(len(result_df)),
                entities_found_count=entities_found_count,
                unique_entities_found=unique_entities,
                output_dataframe_id=result_dataframe_id,
            ),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao executar identificação de entidades.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    

from langchain.tools import tool

from src.tools_agents.measurements.schemas import ThemsClassificationInput
from src.tools_agents.measurements.services import thems_classification_async

from core.dataframe_store import get_dataframe, save_dataframe

# ajuste os imports conforme seu projeto
from services.ia_funtions.clustering_functions import closest_cluster_ids
from services.ia_funtions.similarity_functions import normalizar_temas_similares


@tool("thems_classification", args_schema=ThemsClassificationInput)
async def thems_classification_tool(
    dataframe_id: str,
    macrotemas_dict: dict,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_concurrent: int | None = None,
    max_workers: int | None = None,
    text_chunk_max_chars: int = 18000,
    macrotema_group_max_chars: int = 5000,
    similarity_threshold: float = 0.72,
    cluster_id_col: str = "cluster_id",
    summary_col: str = "cluster_summary",
    topic_col: str = "specific_topic",
    macro_col: str = "macro_topic",
    output_source: str = "thems_classification",
) -> dict:
    """
    Classifica temas e macrotemas em um DataFrame salvo no DATAFRAME_STORE.
    """
    try:
        df = get_dataframe(dataframe_id)

        df_out = await thems_classification_async(
            dataframe=df,
            macrotemas_dict=macrotemas_dict,
            closest_cluster_ids_fn=closest_cluster_ids,
            normalizar_temas_similares_fn=normalizar_temas_similares,
            model=model,
            temperature=temperature,
            max_concurrent=max_concurrent,
            max_workers=max_workers,
            text_chunk_max_chars=text_chunk_max_chars,
            macrotema_group_max_chars=macrotema_group_max_chars,
            similarity_threshold=similarity_threshold,
            cluster_id_col=cluster_id_col,
            summary_col=summary_col,
            topic_col=topic_col,
            macro_col=macro_col,
        )

        output_dataframe_id = save_dataframe(
            df_out,
            source=output_source,
            filters={
                "input_dataframe_id": dataframe_id,
                "model": model,
                "temperature": temperature,
                "cluster_id_col": cluster_id_col,
                "summary_col": summary_col,
                "topic_col": topic_col,
                "macro_col": macro_col,
            },
        )

        return {
            "status": "success",
            "message": "Classificação de temas executada com sucesso.",
            "dataframe_id": output_dataframe_id,
            "meta": {
                "input_dataframe_id": dataframe_id,
                "output_dataframe_id": output_dataframe_id,
                "input_rows": len(df),
                "output_rows": len(df_out),
                "added_columns": [summary_col, topic_col, macro_col],
                "cluster_id_col": cluster_id_col,
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Erro ao executar classificação de temas.",
            "error_type": type(e).__name__,
            "details": f"Erro ao executar thems_classification: {str(e)}",
        }