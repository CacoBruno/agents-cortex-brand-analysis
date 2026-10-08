from __future__ import annotations

import asyncio
from typing import Dict, List, Tuple
from typing import Callable, Dict, List, Any

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
# ESQUEMA DE SAÍDA
# =========================================================
class SaidaResumoTemaMacro(BaseModel):
    resumo: str = Field(
        ...,
        description="Resumo em exatamente 3 linhas, separado por quebras de linha."
    )
    tema: str = Field(
        ...,
        description="Tema curto, com no máximo 6 palavras."
    )
    macrotema: str = Field(
        ...,
        description="Escolha exatamente um macrotema da lista fornecida."
    )


# =========================================================
# PROMPT BASE
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
            "- Sempre classifique pelo tema PRINCIPAL da matéria."
            "- Se houver múltiplos temas, escolha o mais específico."
            "- Evite categorias genéricas se houver uma mais específica."
            "- 'Resultados financeiros' deve ser usado apenas quando nenhum outro tema for dominante."

        )
    ]
)


# =========================================================
# HELPERS
# =========================================================
def _normalize_text_for_cache(text: str) -> str:
    return " ".join((text or "").strip().split())


def _split_in_chunks(texts: List[str], max_chars: int = 18000) -> List[str]:
    """
    Divide a lista de textos em blocos concatenados, limitando o tamanho do bloco.
    Se um texto individual for maior que max_chars, ele também é quebrado.
    """
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
    """
    Quebra o dicionário de macrotemas em grupos menores.
    """
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


# =========================================================
# CHAMADA ASSÍNCRONA BÁSICA
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


# =========================================================
# CLASSIFICAÇÃO COM GRUPOS DE MACROTEMAS
# =========================================================
async def _classificar_com_grupos_de_macrotemas_async(
    corpus_final: str,
    chain,
    semaphore: asyncio.Semaphore,
    macrotemas_dict: Dict[str, str],
    macrotema_group_max_chars: int = 5000,
) -> SaidaResumoTemaMacro:
    """
    Se o dicionário de macrotemas estiver muito grande, roda uma pré-seleção
    por grupos e depois uma classificação final apenas com os candidatos.
    """
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

    # pré-seleção paralela por grupos
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


# =========================================================
# PROCESSAMENTO DE UM ID
# =========================================================
async def _processar_um_id_async(
    pair: Tuple[str, List[str]],
    chain,
    semaphore: asyncio.Semaphore,
    macrotemas_dict: Dict[str, str],
    text_chunk_max_chars: int = 18000,
    macrotema_group_max_chars: int = 5000,
) -> Tuple[str, Dict[str, str]]:
    """
    Processa um único ID -> lista de textos.
    Faz map-reduce dos textos e classificação com grupos de macrotemas.
    """
    id_, textos = pair
    chunks = _split_in_chunks(textos, max_chars=text_chunk_max_chars)

    # map step paralelo
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

    # reduce/final step
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
# FUNÇÃO ASYNC PRINCIPAL
# =========================================================
async def resumir_tematizar_macrotema_dict_async(
    dados: Dict[str, List[str]],
    *,
    macrotemas_dict: Dict[str, str],
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_concurrent: int = 8,
    text_chunk_max_chars: int = 18000,
    macrotema_group_max_chars: int = 5000,
) -> Dict[str, Dict[str, str]]:
    """
    Entrada:
        dados = {id: [lista_de_textos]}
        macrotemas_dict = {
            "Macrotema 1": "descrição ou exemplos",
            "Macrotema 2": "descrição ou exemplos"
        }

    Saída:
        {
            id: {
                "resumo": <3 linhas>,
                "tema": <string curta>,
                "macrotema": <rótulo fechado>
            }
        }
    """
    if not isinstance(dados, dict):
        raise TypeError("`dados` deve ser um dicionário no formato {id: [lista_de_textos]}.")

    if not isinstance(macrotemas_dict, dict) or not macrotemas_dict:
        raise ValueError("`macrotemas_dict` deve ser um dicionário não vazio.")

    chain = _make_chain(model=model, temperature=temperature)
    semaphore = asyncio.Semaphore(max_concurrent)

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
        id_ = item[0]

        if isinstance(result, Exception):
            resultados[id_] = {
                "resumo": "Não foi possível gerar o resumo para este ID.",
                "tema": f"Erro de processamento ({type(result).__name__})",
                "macrotema": "Não classificado",
            }
        else:
            k, v = result
            resultados[k] = v

    return resultados


# =========================================================
# WRAPPER SÍNCRONO
# =========================================================
def resumir_tematizar_macrotema_dict(
    dados: Dict[str, List[str]],
    *,
    macrotemas_dict: Dict[str, str],
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_concurrent: int = 8,
    text_chunk_max_chars: int = 18000,
    macrotema_group_max_chars: int = 5000,
) -> Dict[str, Dict[str, str]]:
    """
    Wrapper síncrono para uso em script normal.
    """
    return asyncio.run(
        resumir_tematizar_macrotema_dict_async(
            dados=dados,
            macrotemas_dict=macrotemas_dict,
            model=model,
            temperature=temperature,
            max_concurrent=max_concurrent,
            text_chunk_max_chars=text_chunk_max_chars,
            macrotema_group_max_chars=macrotema_group_max_chars,
        )
    )
# =========================================================
# FUNÇÃO CLASSIFICA: RECEBE DataFrame
# =========================================================
def classificar_macrotemas_no_dataframe(
    df: pd.DataFrame,
    *,
    macrotemas_dict: Dict[str, str],
    closest_cluster_ids_fn: Callable[[pd.DataFrame], Dict[str, List[str]]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_concurrent: int = 6,
    text_chunk_max_chars: int = 18000,
    macrotema_group_max_chars: int = 5000,
    return_dict_only: bool = False,
    id_col_resultado: str = "cluster_id"
) -> Any:
    """
    Pipeline completo:
      1) recebe df
      2) gera dict_thems = closest_cluster_ids_fn(df)
      3) gera dict_thems_tags = resumir_tematizar_macrotema_dict(dict_thems, ...)
      4) retorna dict ou DataFrame
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("`df` deve ser um pandas DataFrame.")

    dict_thems = closest_cluster_ids_fn(df)

    dict_thems_tags = resumir_tematizar_macrotema_dict(
        dados=dict_thems,
        macrotemas_dict=macrotemas_dict,
        model=model,
        temperature=temperature,
        max_concurrent=max_concurrent,
        text_chunk_max_chars=text_chunk_max_chars,
        macrotema_group_max_chars=macrotema_group_max_chars
    )

    if return_dict_only:
        return dict_thems_tags

    df_result = (
        pd.DataFrame.from_dict(dict_thems_tags, orient="index")
        .reset_index()
        .rename(columns={"index": id_col_resultado})
    )

    return df_result

# =========================================================
# FUNÇÃO FINAL: RECEBE DataFrame e Dicionário de Macrotemas
# =========================================================
from services.ia_funtions.clustering_functions import closest_cluster_ids
from services.ia_funtions.similarity_functions import normalizar_temas_similares
import pandas as pd


def thems_classification(
    dataframe: pd.DataFrame,
    macrotemas_dict: Dict[str, str]
) -> pd.DataFrame:
    """
    Pipeline completo:
    1) recebe df com o cluster id e o dicionário de macrotemas
    2) classifica os clusters
    3) normaliza temas similares
    4) insere resumo, tema e macrotema no dataframe
    5) retorna o dataframe
    """

    resultado = classificar_macrotemas_no_dataframe(
        df=dataframe,
        macrotemas_dict=macrotemas_dict,
        closest_cluster_ids_fn=closest_cluster_ids,
        model="gpt-4o-mini",
        temperature=0.2,
        max_concurrent=6,
        text_chunk_max_chars=18000,
        macrotema_group_max_chars=5000,
        return_dict_only=True
    )

    normalizando = normalizar_temas_similares(
        resultado=resultado,
        campo_tema="tema",
        similarity_threshold=0.72
    )

    norm_dict = normalizando["resultado_normalizado"]

    dataframe = dataframe.copy()

    dataframe["cluster_summary"] = dataframe["cluster_id"].apply(
        lambda x: norm_dict[x]["resumo"]
    )
    dataframe["specific_topic"] = dataframe["cluster_id"].apply(
        lambda x: norm_dict[x]["tema"]
    )
    dataframe["macro_topic"] = dataframe["cluster_id"].apply(
        lambda x: norm_dict[x]["macrotema"]
    )

    return dataframe