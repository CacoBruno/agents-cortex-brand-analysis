import re
from typing import List, Union
from summa import summarizer

def resumo_extrativo(
    texto: str,
    proporcao: float = 0.30,
    min_sentencas: int = 3,
    max_sentencas: int = 20,
    retorno_lista: bool = False,
    linguagem: str = "portuguese",
) -> Union[str, List[str]]:
    """
    Gera um resumo extrativo em PT-BR usando TextRank (summa.summarizer).

    Melhorias:
    - Limita a proporção entre 0.05 e 0.9.
    - Garante um mínimo e máximo de sentenças (fallback).
    - Limpa espaços e lida com textos curtos.
    - Pode retornar lista de sentenças ou string única.

    Parâmetros:
    - texto: conteúdo original.
    - proporcao: fração das sentenças do texto (0.05–0.9).
    - min_sentencas: nº mínimo de sentenças no resumo.
    - max_sentencas: nº máximo de sentenças no resumo.
    - retorno_lista: se True, retorna List[str]; senão, str.
    - linguagem: idioma para o Summa (default: "portuguese").

    Retorna:
    - str ou List[str] com o resumo.
    """
    if not isinstance(texto, str):
        raise TypeError("`texto` deve ser string.")
    texto = re.sub(r"\s+", " ", texto).strip()

    # Split simples de sentenças para regras de fallback
    def _split_sentencas(t: str) -> List[str]:
        # separa em ., !, ?, … e mantém pontuação
        sent = re.split(r"(?<=[\.\?\!…])\s+", t)
        # remove vazias e tira espaços extras
        return [s.strip() for s in sent if s and s.strip()]

    sentencas = _split_sentencas(texto)
    if not sentencas:
        return [] if retorno_lista else ""

    # Textos muito curtos: devolve como está
    if len(texto) < 280 or len(sentencas) <= min_sentencas:
        resumo_list = sentencas[: min(len(sentencas), max(min_sentencas, 1))]
        return resumo_list if retorno_lista else " ".join(resumo_list)

    # Boundaries
    proporcao = max(0.05, min(0.9, float(proporcao)))
    min_sentencas = max(1, int(min_sentencas))
    max_sentencas = max(min_sentencas, int(max_sentencas))


    # Primeiro, deixa o Summa escolher por ratio
    try:
        resumo_str = summarizer.summarize(texto, language=linguagem, ratio=proporcao) or ""
    except Exception:
        resumo_str = ""

    resumo_list = _split_sentencas(resumo_str)

    # Fallback se o Summa não retornou nada ou retornou muito pouco
    if len(resumo_list) < min_sentencas:
        alvo = int(round(len(sentencas) * proporcao))
        alvo = max(min_sentencas, min(max_sentencas, alvo))
        resumo_list = sentencas[:alvo]

    # Limita ao máximo permitido, mantendo a ordem
    if len(resumo_list) > max_sentencas:
        resumo_list = resumo_list[:max_sentencas]

    return resumo_list if retorno_lista else " ".join(resumo_list)
