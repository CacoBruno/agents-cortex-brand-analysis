import pandas as pd
from newspaper import Article
from urllib.parse import urlparse
from typing import Optional


def extrair_dominio(url: str) -> Optional[str]:
    """
    Extrai o domínio principal de uma URL.
    Ex.: https://g1.globo.com/economia/... -> g1.globo.com
    """
    try:
        if pd.isna(url) or not str(url).strip():
            return None
        return urlparse(str(url)).netloc
    except Exception:
        return None


def extrair_info_url_newspaper(
    df: pd.DataFrame,
    url_col: str = "url",
    idioma: str = "pt",
    timeout: int = 15
) -> pd.DataFrame:
    """
    Extrai informações de páginas a partir de URLs em um DataFrame usando Newspaper3k.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame de entrada com a coluna de URLs.
    url_col : str
        Nome da coluna que contém as URLs.
    idioma : str
        Idioma esperado do conteúdo ('pt', 'en', etc.).
    timeout : int
        Timeout de requisição em segundos.

    Retorno
    -------
    pd.DataFrame
        DataFrame original com colunas adicionais:
        - dominio
        - titulo
        - texto
        - resumo
        - autores
        - data_publicacao
        - top_image
        - keywords
        - sucesso_extracao
        - erro
    """
    if url_col not in df.columns:
        raise ValueError(f"A coluna '{url_col}' não existe no DataFrame.")

    resultados = []

    for url in df[url_col]:
        row_result = {
            "dominio": extrair_dominio(url),
            "titulo": None,
            "texto": None,
            "resumo": None,
            "autores": None,
            "data_publicacao": None,
            "top_image": None,
            "keywords": None,
            "sucesso_extracao": False,
            "erro": None,
        }

        try:
            if pd.isna(url) or not str(url).strip():
                row_result["erro"] = "URL vazia"
                resultados.append(row_result)
                continue

            article = Article(
                url=str(url).strip(),
                language=idioma,
                fetch_images=True,
                request_timeout=timeout
            )

            article.download()
            article.parse()

            # NLP é opcional; às vezes falha dependendo do ambiente
            try:
                article.nlp()
                resumo = article.summary
                keywords = article.keywords
            except Exception:
                resumo = None
                keywords = None

            row_result.update({
                "titulo": article.title,
                "texto": article.text,
                "resumo": resumo,
                "autores": ", ".join(article.authors) if article.authors else None,
                "data_publicacao": article.publish_date,
                "top_image": article.top_image,
                "keywords": ", ".join(keywords) if keywords else None,
                "sucesso_extracao": True,
                "erro": None,
            })

        except Exception as e:
            row_result["erro"] = str(e)

        resultados.append(row_result)

    df_resultado = df.copy().reset_index(drop=True)
    df_extracao = pd.DataFrame(resultados)

    return pd.concat([df_resultado, df_extracao], axis=1)