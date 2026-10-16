from __future__ import annotations

import pandas as pd

from core.dataframe_store import get_dataframe
from services.classifications_functions import sentimentClassification, protagonismClassification, clusteringClassification 
from src.tools_agents.measurements.schemas import (SentimentClassificationInput, ProtagonismClassificationInput, 
                                                   ClusteringToClassificationInput, ThemsClassificationInput, IdentifyEntitiesInput)
from services.texts_treatments import identify_entities_in_dataframe

def sentiment_classification_service(params: SentimentClassificationInput) -> pd.DataFrame:
    """
    Recupera o DataFrame do store e aplica a classificação de sentimento.
    """
    try:
        df = get_dataframe(params.dataframe_id)

        if df is None:
            raise ValueError("DataFrame não encontrado no store.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Objeto recuperado não é um pandas DataFrame.")

        # 👇 aqui mudou
        result_df = sentimentClassification(df)

        if result_df is None:
            raise ValueError("sentimentClassification retornou None.")

        if not isinstance(result_df, pd.DataFrame):
            raise TypeError("Retorno não é um pandas DataFrame.")

        return result_df

    except Exception as e:
        raise RuntimeError(f"Erro no sentiment_classification_service: {str(e)}") from e
    

def protagonism_classification_service(
    params: ProtagonismClassificationInput,
) -> pd.DataFrame:
    """
    Recupera o DataFrame do store e aplica a classificação de protagonismo.
    """
    try:
        df = get_dataframe(params.dataframe_id)

        if df is None:
            raise ValueError("DataFrame não encontrado no store.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O objeto recuperado não é um pandas DataFrame.")

        result_df = protagonismClassification(
            dataframe=df,
            lista_marca=params.lista_marca,
        )

        if result_df is None:
            raise ValueError("protagonismCclassification retornou None.")

        if not isinstance(result_df, pd.DataFrame):
            raise TypeError("O retorno de protagonismCclassification não é um pandas DataFrame.")

        return result_df

    except Exception as e:
        raise RuntimeError(f"Erro ao executar protagonism classification: {str(e)}") from e
    

def clustering_to_classification_service(
    params: ClusteringToClassificationInput,
) -> pd.DataFrame:
    """
    Recupera um DataFrame do DATAFRAME_STORE e aplica a transformação
    clusteringClassification.

    Regras:
    - usa o dataframe_id informado no input
    - passa focus_terms para a função de clustering, se informado
    - valida o tipo de entrada e saída
    """

    try:
        df = get_dataframe(params.dataframe_id)

        if df is None:
            raise ValueError(
                f"DataFrame não encontrado no DATAFRAME_STORE para o id='{params.dataframe_id}'."
            )

        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                f"O objeto recuperado do store não é um pandas DataFrame. Tipo recebido: {type(df).__name__}."
            )

        result_df = clusteringClassification(
            dataframe=df,
            focus_terms=params.focus_terms,
        )

        if result_df is None:
            raise ValueError("clusteringClassification retornou None.")

        if not isinstance(result_df, pd.DataFrame):
            raise TypeError(
                "O retorno de clusteringClassification não é um pandas DataFrame."
            )

        return result_df

    except Exception as e:
        raise RuntimeError(
            f"Erro ao executar clustering_to_classification_service: {str(e)}"
        ) from e

def identify_entities_service(
    params: IdentifyEntitiesInput,
) -> pd.DataFrame:
    """
    Recupera o DataFrame do store e aplica a identificação de entidades
    com base no dicionário de busca.
    """
    try:
        df = get_dataframe(params.dataframe_id)

        result_df = identify_entities_in_dataframe(
            df=df,
            search_dict=params.search_dict,
            title_col=params.title_col,
            content_col=params.content_col,
            output_col=params.output_col,
            split_output=params.split_output,
            hash_columns=params.hash_columns,
        )

        return result_df

    except Exception as e:
        raise RuntimeError(
            f"Erro ao executar identify_entities_service: {str(e)}"
        ) from e
    



import asyncio
from typing import Any, Callable, Dict, List, Tuple

import pandas as pd
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache


# =========================================================
# CACHE GLOBAL
# =========================================================
set_llm_cache(InMemoryCache())


# =========================================================
# ESQUEMA INTERNO DE SAÍDA DO LLM
# =========================================================
class SaidaResumoTemaMacro(BaseModel):
    resumo: str = Field(..., description="Resumo em exatamente 3 linhas.")
    tema: str = Field(..., description="Tema curto, com no máximo 6 palavras.")
    macrotema: str = Field(..., description="Macrotema escolhido da lista.")


# =========================================================
# PROMPT
# =========================================================
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Você é um assistente de comunicação especializado em resumir e classificar notícias "
            "em português, de forma fiel, concisa, neutra e estruturada.\n\n"
            "Sua tarefa é gerar 3 saídas:\n"
            "1) Um resumo em exatamente 3 linhas.\n"
            "2) Um tema curto, de no máximo 6 palavras.\n"
            "3) Um macrotema, escolhido EXATAMENTE da lista fornecida.\n\n"
            "Regras:\n"
            "- Não invente macrotemas fora da lista.\n"
            "- O resumo deve ser factual e claro.\n"
            "- O tema deve ser curto e sem ponto final.\n"
            "- O macrotema deve refletir o eixo predominante da cobertura.\n"
            "- Considere também a descrição e os exemplos de cada macrotema.\n"
            "- Se houver múltiplos assuntos, escolha o mais central."
        ),
        (
            "human",
            "Tarefa:\n"
            "1) Produzir um resumo em 3 linhas (use exatamente 2 quebras de linha \\n).\n"
            "2) Criar um tema curto, máximo 6 palavras, sem ponto final.\n"
            "3) Escolher um único macrotema da lista abaixo.\n\n"
            "Macrotemas válidos e contexto:\n"
            "{macrotemas_formatados}\n\n"
            "Regras adicionais:\n"
            "- Linguagem clara e factual; evite floreios.\n"
            "- Preserve números, datas e atores relevantes quando forem centrais.\n"
            "- Não crie rótulos fora da lista.\n\n"
            "# TEXTOS\n{corpus}"
        )
    ]
)


# =========================================================
# HELPERS
# =========================================================
def _normalize_text_for_cache(text: str) -> str:
    return " ".join((text or "").strip().split())


def _split_in_chunks(texts: List[str], max_chars: int = 18000) -> List[str]:
    blocks: List[str] = []
    current = ""

    for t in texts:
        t = _normalize_text_for_cache(t)
        if not t:
            continue

        if len(t) > max_chars:
            partes = [t[i:i + max_chars] for i in range(0, len(t), max_chars)]
        else:
            partes = [t]

        for parte in partes:
            if len(current) + len(parte) + 2 > max_chars:
                if current:
                    blocks.append(current)
                current = parte
            else:
                current = f"{current}\n{parte}" if current else parte

    if current:
        blocks.append(current)

    return blocks or [""]


def _chunk_macrotemas_dict(
    macrotemas_dict: Dict[str, str],
    max_chars: int = 5000
) -> List[Dict[str, str]]:
    items = list(macrotemas_dict.items())
    grupos: List[Dict[str, str]] = []
    grupo_atual: Dict[str, str] = {}
    tamanho_atual = 0

    for nome, descricao in items:
        trecho = f"{nome}: {descricao}\n"
        if tamanho_atual + len(trecho) > max_chars and grupo_atual:
            grupos.append(grupo_atual)
            grupo_atual = {}
            tamanho_atual = 0

        grupo_atual[nome] = descricao
        tamanho_atual += len(trecho)

    if grupo_atual:
        grupos.append(grupo_atual)

    return grupos


def _formatar_macrotemas(macrotemas_dict: Dict[str, str]) -> str:
    linhas = []
    for nome, descricao in macrotemas_dict.items():
        descricao = (descricao or "").strip()
        if descricao:
            linhas.append(f"- {nome}: {descricao}")
        else:
            linhas.append(f"- {nome}")
    return "\n".join(linhas)


def _normalize_resumo(resumo: str) -> str:
    linhas = [l.strip() for l in (resumo or "").splitlines() if l.strip()]
    if len(linhas) < 3:
        linhas = (linhas + [""] * 3)[:3]
    elif len(linhas) > 3:
        linhas = [linhas[0], linhas[1], " ".join(linhas[2:])]
    return "\n".join(linhas)


def _shorten_tema(tema: str, max_palavras: int = 6) -> str:
    palavras = (tema or "").strip().split()
    return " ".join(palavras[:max_palavras])


def _validar_macrotema(macrotema: str, macrotemas_validos: List[str]) -> str:
    macrotema = (macrotema or "").strip()

    if macrotema in macrotemas_validos:
        return macrotema

    mapa_lower = {m.lower(): m for m in macrotemas_validos}
    return mapa_lower.get(macrotema.lower(), "Não classificado")


def _make_chain(model: str = "gpt-4o-mini", temperature: float = 0.2):
    llm = ChatOpenAI(model=model, temperature=temperature)
    structured = llm.with_structured_output(SaidaResumoTemaMacro)
    return prompt | structured


def _resolve_concurrency(
    max_concurrent: int | None = None,
    max_workers: int | None = None,
    default: int = 6,
) -> int:
    if max_concurrent is not None:
        return max_concurrent
    if max_workers is not None:
        return max_workers
    return default


# =========================================================
# CORE ASYNC
# =========================================================
async def _ainvoke_chain(
    chain,
    *,
    corpus: str,
    macrotemas_formatados: str,
    semaphore: asyncio.Semaphore,
) -> SaidaResumoTemaMacro:
    corpus = _normalize_text_for_cache(corpus)
    macrotemas_formatados = _normalize_text_for_cache(macrotemas_formatados)

    async with semaphore:
        return await chain.ainvoke({
            "corpus": corpus,
            "macrotemas_formatados": macrotemas_formatados,
        })


async def _classificar_com_grupos_de_macrotemas_async(
    corpus_final: str,
    chain,
    semaphore: asyncio.Semaphore,
    macrotemas_dict: Dict[str, str],
    macrotema_group_max_chars: int = 5000,
) -> SaidaResumoTemaMacro:
    grupos = _chunk_macrotemas_dict(
        macrotemas_dict,
        max_chars=macrotema_group_max_chars
    )

    if len(grupos) == 1:
        return await _ainvoke_chain(
            chain,
            corpus=corpus_final,
            macrotemas_formatados=_formatar_macrotemas(grupos[0]),
            semaphore=semaphore,
        )

    tarefas = [
        _ainvoke_chain(
            chain,
            corpus=corpus_final,
            macrotemas_formatados=_formatar_macrotemas(grupo),
            semaphore=semaphore,
        )
        for grupo in grupos
    ]

    saidas_parciais = await asyncio.gather(*tarefas, return_exceptions=True)

    candidatos: Dict[str, str] = {}

    for grupo, saida_parcial in zip(grupos, saidas_parciais):
        if isinstance(saida_parcial, Exception):
            continue

        macro = _validar_macrotema(saida_parcial.macrotema, list(grupo.keys()))
        if macro != "Não classificado":
            candidatos[macro] = grupo[macro]

    if not candidatos:
        candidatos = macrotemas_dict

    return await _ainvoke_chain(
        chain,
        corpus=corpus_final,
        macrotemas_formatados=_formatar_macrotemas(candidatos),
        semaphore=semaphore,
    )


async def _processar_um_id_async(
    pair: Tuple[str, List[str]],
    chain,
    semaphore: asyncio.Semaphore,
    macrotemas_dict: Dict[str, str],
    text_chunk_max_chars: int = 18000,
    macrotema_group_max_chars: int = 5000,
) -> Tuple[str, Dict[str, str]]:
    id_, textos = pair
    chunks = _split_in_chunks(textos, max_chars=text_chunk_max_chars)

    if len(chunks) > 1:
        tarefas_chunks = [
            _classificar_com_grupos_de_macrotemas_async(
                corpus_final=ch,
                chain=chain,
                semaphore=semaphore,
                macrotemas_dict=macrotemas_dict,
                macrotema_group_max_chars=macrotema_group_max_chars,
            )
            for ch in chunks
        ]

        resultados_chunks = await asyncio.gather(*tarefas_chunks)

        parciais = [
            (
                f"Resumo parcial:\n{_normalize_resumo(parcial.resumo)}\n"
                f"Tema parcial: {_shorten_tema(parcial.tema, 6)}\n"
                f"Macrotema parcial: {parcial.macrotema}"
            )
            for parcial in resultados_chunks
        ]

        corpus_final = "\n\n".join(parciais)
    else:
        corpus_final = chunks[0]

    saida_final = await _classificar_com_grupos_de_macrotemas_async(
        corpus_final=corpus_final,
        chain=chain,
        semaphore=semaphore,
        macrotemas_dict=macrotemas_dict,
        macrotema_group_max_chars=macrotema_group_max_chars,
    )

    return id_, {
        "resumo": _normalize_resumo(saida_final.resumo),
        "tema": _shorten_tema(saida_final.tema, 6),
        "macrotema": _validar_macrotema(
            saida_final.macrotema,
            list(macrotemas_dict.keys())
        ),
    }


# =========================================================
# API PÚBLICA
# =========================================================
async def resumir_tematizar_macrotema_dict_async(
    dados: Dict[str, List[str]],
    *,
    macrotemas_dict: Dict[str, str],
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_concurrent: int | None = None,
    max_workers: int | None = None,
    text_chunk_max_chars: int = 18000,
    macrotema_group_max_chars: int = 5000,
) -> Dict[str, Dict[str, str]]:
    if not isinstance(dados, dict):
        raise TypeError("`dados` deve ser um dicionário no formato {id: [lista_de_textos]}.")

    if not isinstance(macrotemas_dict, dict) or not macrotemas_dict:
        raise ValueError("`macrotemas_dict` deve ser um dicionário não vazio.")

    concorrencia = _resolve_concurrency(max_concurrent, max_workers, default=6)

    chain = _make_chain(model=model, temperature=temperature)
    semaphore = asyncio.Semaphore(concorrencia)

    tarefas = [
        _processar_um_id_async(
            pair=item,
            chain=chain,
            semaphore=semaphore,
            macrotemas_dict=macrotemas_dict,
            text_chunk_max_chars=text_chunk_max_chars,
            macrotema_group_max_chars=macrotema_group_max_chars,
        )
        for item in dados.items()
    ]

    resultados: Dict[str, Dict[str, str]] = {}
    outputs = await asyncio.gather(*tarefas, return_exceptions=True)

    for item, result in zip(dados.items(), outputs):
        id_ = str(item[0])

        if isinstance(result, Exception):
            resultados[id_] = {
                "resumo": "Não foi possível gerar o resumo para este ID.",
                "tema": f"Erro de processamento ({type(result).__name__})",
                "macrotema": "Não classificado",
            }
        else:
            k, v = result
            resultados[str(k)] = v

    return resultados


def resumir_tematizar_macrotema_dict(
    dados: Dict[str, List[str]],
    *,
    macrotemas_dict: Dict[str, str],
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_concurrent: int | None = None,
    max_workers: int | None = None,
    text_chunk_max_chars: int = 18000,
    macrotema_group_max_chars: int = 5000,
) -> Dict[str, Dict[str, str]]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            resumir_tematizar_macrotema_dict_async(
                dados=dados,
                macrotemas_dict=macrotemas_dict,
                model=model,
                temperature=temperature,
                max_concurrent=max_concurrent,
                max_workers=max_workers,
                text_chunk_max_chars=text_chunk_max_chars,
                macrotema_group_max_chars=macrotema_group_max_chars,
            )
        )

    raise RuntimeError(
        "resumir_tematizar_macrotema_dict() foi chamada dentro de um event loop já ativo. "
        "Use `await resumir_tematizar_macrotema_dict_async(...)`."
    )


async def classificar_macrotemas_no_dataframe_async(
    df: pd.DataFrame,
    *,
    macrotemas_dict: Dict[str, str],
    closest_cluster_ids_fn: Callable[[pd.DataFrame], Dict[str, List[str]]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_concurrent: int | None = None,
    max_workers: int | None = None,
    text_chunk_max_chars: int = 18000,
    macrotema_group_max_chars: int = 5000,
    return_dict_only: bool = False,
    id_col_resultado: str = "cluster_id",
) -> Any:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("`df` deve ser um pandas DataFrame.")

    dict_thems = closest_cluster_ids_fn(df)
    dict_thems = {str(k): v for k, v in dict_thems.items()}

    dict_thems_tags = await resumir_tematizar_macrotema_dict_async(
        dados=dict_thems,
        macrotemas_dict=macrotemas_dict,
        model=model,
        temperature=temperature,
        max_concurrent=max_concurrent,
        max_workers=max_workers,
        text_chunk_max_chars=text_chunk_max_chars,
        macrotema_group_max_chars=macrotema_group_max_chars,
    )

    if return_dict_only:
        return dict_thems_tags

    df_result = (
        pd.DataFrame.from_dict(dict_thems_tags, orient="index")
        .reset_index()
        .rename(columns={"index": id_col_resultado})
    )

    return df_result


def classificar_macrotemas_no_dataframe(
    df: pd.DataFrame,
    *,
    macrotemas_dict: Dict[str, str],
    closest_cluster_ids_fn: Callable[[pd.DataFrame], Dict[str, List[str]]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_concurrent: int | None = None,
    max_workers: int | None = None,
    text_chunk_max_chars: int = 18000,
    macrotema_group_max_chars: int = 5000,
    return_dict_only: bool = False,
    id_col_resultado: str = "cluster_id",
) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            classificar_macrotemas_no_dataframe_async(
                df=df,
                macrotemas_dict=macrotemas_dict,
                closest_cluster_ids_fn=closest_cluster_ids_fn,
                model=model,
                temperature=temperature,
                max_concurrent=max_concurrent,
                max_workers=max_workers,
                text_chunk_max_chars=text_chunk_max_chars,
                macrotema_group_max_chars=macrotema_group_max_chars,
                return_dict_only=return_dict_only,
                id_col_resultado=id_col_resultado,
            )
        )

    raise RuntimeError(
        "classificar_macrotemas_no_dataframe() foi chamada dentro de um event loop já ativo. "
        "Use `await classificar_macrotemas_no_dataframe_async(...)`."
    )


async def thems_classification_async(
    dataframe: pd.DataFrame,
    macrotemas_dict: Dict[str, str],
    *,
    closest_cluster_ids_fn: Callable[[pd.DataFrame], Dict[str, List[str]]],
    normalizar_temas_similares_fn: Callable[..., Dict[str, Any]],
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
) -> pd.DataFrame:
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("`dataframe` deve ser um pandas DataFrame.")

    if cluster_id_col not in dataframe.columns:
        raise KeyError(f"Coluna `{cluster_id_col}` não encontrada no dataframe.")

    resultado = await classificar_macrotemas_no_dataframe_async(
        df=dataframe,
        macrotemas_dict=macrotemas_dict,
        closest_cluster_ids_fn=closest_cluster_ids_fn,
        model=model,
        temperature=temperature,
        max_concurrent=max_concurrent,
        max_workers=max_workers,
        text_chunk_max_chars=text_chunk_max_chars,
        macrotema_group_max_chars=macrotema_group_max_chars,
        return_dict_only=True,
        id_col_resultado=cluster_id_col,
    )

    normalizando = normalizar_temas_similares_fn(
        resultado=resultado,
        campo_tema="tema",
        similarity_threshold=similarity_threshold
    )

    norm_dict = normalizando["resultado_normalizado"]
    norm_dict = {str(k): v for k, v in norm_dict.items()}

    df_out = dataframe.copy()
    cluster_keys = df_out[cluster_id_col].astype(str)

    df_out[summary_col] = cluster_keys.apply(
        lambda x: norm_dict.get(x, {}).get("resumo", "")
    )
    df_out[topic_col] = cluster_keys.apply(
        lambda x: norm_dict.get(x, {}).get("tema", "")
    )
    df_out[macro_col] = cluster_keys.apply(
        lambda x: norm_dict.get(x, {}).get("macrotema", "Não classificado")
    )

    return df_out


def thems_classification(
    dataframe: pd.DataFrame,
    macrotemas_dict: Dict[str, str],
    *,
    closest_cluster_ids_fn: Callable[[pd.DataFrame], Dict[str, List[str]]],
    normalizar_temas_similares_fn: Callable[..., Dict[str, Any]],
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
) -> pd.DataFrame:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            thems_classification_async(
                dataframe=dataframe,
                macrotemas_dict=macrotemas_dict,
                closest_cluster_ids_fn=closest_cluster_ids_fn,
                normalizar_temas_similares_fn=normalizar_temas_similares_fn,
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
        )

    raise RuntimeError(
        "thems_classification() foi chamada dentro de um event loop já ativo. "
        "Use `await thems_classification_async(...)`."
    )
