from __future__ import annotations

import os
import re
import time
import logging
import datetime as dt
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence
from urllib.parse import urlparse

import pandas as pd
from newspaper import Article
import mediacloud.api


# =========================================================
# CONFIG
# =========================================================

@dataclass
class MediaCloudConfig:
    api_key: str | None = None
    platform: str = "online_news"
    page_size: int = 1000
    request_pause_seconds: float = 0.25
    article_language: str | None = "pt"

    # retry newspaper
    newspaper_retry_attempts: int = 3
    newspaper_retry_wait_seconds: float = 2.0

    # logging
    log_level: str = "INFO"
    log_file: str | None = None


# =========================================================
# LOGGER
# =========================================================

def build_logger(
    name: str = "mediacloud_news",
    level: str = "INFO",
    log_file: str | None = None,
) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


# =========================================================
# HELPERS
# =========================================================

def extract_domain_from_url(url: str | None) -> str | None:
    if not url or not isinstance(url, str):
        return None

    try:
        parsed = urlparse(url)
        domain = (parsed.netloc or "").lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or None
    except Exception:
        return None


# =========================================================
# CLIENTE
# =========================================================

class MediaCloudNewsClient:
    BRAZIL_KEYWORDS = (
        "brazil",
        "brasil",
        "brazilian",
        "brasileiro",
        "brasileira",
        "brasileiros",
        "brasileiras",
    )

    def __init__(self, config: MediaCloudConfig | None = None):
        self.config = config or MediaCloudConfig()
        api_key = self.config.api_key or os.getenv("MC_API_KEY")

        if not api_key:
            raise ValueError(
                "API key não encontrada. Passe MediaCloudConfig(api_key='...') "
                "ou defina a variável de ambiente MC_API_KEY."
            )

        self.search_api = mediacloud.api.SearchApi(api_key)
        self.directory_api = mediacloud.api.DirectoryApi(api_key)
        self.logger = build_logger(
            level=self.config.log_level,
            log_file=self.config.log_file,
        )

        self.logger.info("MediaCloudNewsClient inicializado com sucesso.")

    @staticmethod
    def _normalize_date(value: str | dt.date | dt.datetime) -> dt.date:
        if isinstance(value, dt.datetime):
            return value.date()
        if isinstance(value, dt.date):
            return value
        return dt.date.fromisoformat(value)

    @staticmethod
    def _quote_term(term: str) -> str:
        term = str(term).strip()
        if not term:
            return term
        if " " in term and not (term.startswith('"') and term.endswith('"')):
            return f'"{term}"'
        return term

    @staticmethod
    def _slugify_filename(value: str) -> str:
        """
        Normaliza um texto para uso seguro em nome de arquivo.
        """
        value = str(value or "").strip()
        if not value:
            return "busca"

        value = unicodedata.normalize("NFKD", value)
        value = value.encode("ascii", "ignore").decode("ascii")
        value = value.lower()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        value = re.sub(r"_+", "_", value).strip("_")
        return value or "busca"

    @staticmethod
    def _validate_search_config(search_name: str, config: dict) -> dict:
        """
        Valida e padroniza a configuração de uma busca individual.
        Estrutura esperada:
        {
            "termos": [...],
            "operador": "AND" | "OR",
            "not_terms": [...],   # opcional
            "extra_query": "...", # opcional
            "nome_arquivo": "...",# opcional
            "max_stories": 100,   # opcional
            "sort_order": "...",  # opcional
            "page_size": 500      # opcional
        }
        """
        if not isinstance(config, dict):
            raise ValueError(
                f"A configuração da busca '{search_name}' deve ser um dicionário."
            )

        termos = config.get("termos")
        not_terms = config.get("not_terms")
        operador = str(config.get("operador", "OR")).upper().strip()

        if operador not in {"AND", "OR"}:
            raise ValueError(
                f"Busca '{search_name}': 'operador' deve ser 'AND' ou 'OR'."
            )

        if not termos and not not_terms:
            raise ValueError(
                f"Busca '{search_name}': informe ao menos 'termos' ou 'not_terms'."
            )

        return {
            "termos": termos,
            "operador": operador,
            "not_terms": not_terms,
            "extra_query": config.get("extra_query"),
            "nome_arquivo": config.get("nome_arquivo"),
            "max_stories": config.get("max_stories"),
            "sort_order": config.get("sort_order"),
            "page_size": config.get("page_size"),
        }

    @classmethod
    def build_query_from_terms(
        cls,
        terms: str | Sequence[str] | None = None,
        operator: Literal["AND", "OR"] = "OR",
        not_terms: str | Sequence[str] | None = None,
        extra_query: str | None = None,
    ) -> str:
        positive_query = ""
        negative_query = ""

        if terms:
            if isinstance(terms, str):
                terms = [terms]
            positive_terms = [cls._quote_term(t) for t in terms if str(t).strip()]
            if positive_terms:
                joiner = f" {operator} "
                positive_query = "(" + joiner.join(positive_terms) + ")"

        if not_terms:
            if isinstance(not_terms, str):
                not_terms = [not_terms]
            negative_terms = [cls._quote_term(t) for t in not_terms if str(t).strip()]
            if negative_terms:
                negative_query = "(" + " OR ".join(negative_terms) + ")"

        if positive_query and negative_query:
            query = f"{positive_query} NOT {negative_query}"
        elif positive_query:
            query = positive_query
        elif negative_query:
            query = f"NOT {negative_query}"
        else:
            raise ValueError("Informe pelo menos um termo em 'terms' ou 'not_terms'.")

        if extra_query:
            query = f"({query}) AND ({extra_query})"

        return query

    @staticmethod
    def _safe_get_collection_id(collection: dict):
        return (
            collection.get("id")
            or collection.get("collection_id")
            or collection.get("pk")
        )

    @classmethod
    def _is_brazil_related_collection(cls, collection: dict) -> bool:
        text = " ".join(
            str(collection.get(k, ""))
            for k in ["name", "label", "title", "description"]
        ).lower()
        return any(keyword in text for keyword in cls.BRAZIL_KEYWORDS)

    def list_all_collections(
        self,
        name_filter: str | None = None,
        limit_per_page: int = 100,
        max_pages: int | None = None,
    ) -> list[dict]:
        self.logger.info("Listando coleções. Filtro nome=%s", name_filter)

        all_results: list[dict] = []
        offset = 0
        page = 0

        while True:
            response = self.directory_api.collection_list(
                platform=self.config.platform,
                name=name_filter,
                limit=limit_per_page,
                offset=offset,
            )

            results = response.get("results", [])
            all_results.extend(results)

            self.logger.info(
                "Página de coleções carregada | página=%s | itens=%s | acumulado=%s",
                page + 1,
                len(results),
                len(all_results),
            )

            page += 1
            if max_pages is not None and page >= max_pages:
                break

            if not response.get("next"):
                break

            offset += len(results)
            if not results:
                break

        self.logger.info("Total de coleções carregadas: %s", len(all_results))
        return all_results

    def get_brazil_collections_dict(self) -> dict[int, dict]:
        collections = self.list_all_collections()
        brazil = [c for c in collections if self._is_brazil_related_collection(c)]
        out: dict[int, dict] = {}

        for c in brazil:
            cid = self._safe_get_collection_id(c)
            if cid is not None:
                out[int(cid)] = c

        self.logger.info("Coleções relacionadas ao Brasil: %s", len(out))
        return out

    def search_stories(
        self,
        terms: str | Sequence[str] | None,
        start_date: str | dt.date | dt.datetime,
        end_date: str | dt.date | dt.datetime,
        collection_ids: Sequence[int] | None = None,
        only_brazil_collections: bool = False,
        operator: Literal["AND", "OR"] = "OR",
        not_terms: str | Sequence[str] | None = None,
        extra_query: str | None = None,
        sort_order: str | None = None,
        max_stories: int | None = None,
        page_size: int | None = None,
    ) -> pd.DataFrame:
        start = self._normalize_date(start_date)
        end = self._normalize_date(end_date)

        query = self.build_query_from_terms(
            terms=terms,
            operator=operator,
            not_terms=not_terms,
            extra_query=extra_query,
        )

        final_collection_ids: list[int] = []
        if collection_ids:
            final_collection_ids = [int(x) for x in collection_ids]
        elif only_brazil_collections:
            final_collection_ids = list(self.get_brazil_collections_dict().keys())

        page_size = page_size or self.config.page_size
        pagination_token = None
        stories: list[dict] = []

        self.logger.info(
            "Iniciando busca | query=%s | start=%s | end=%s | n_collections=%s",
            query,
            start,
            end,
            len(final_collection_ids),
        )

        while True:
            page, pagination_token = self.search_api.story_list(
                query=query,
                start_date=start,
                end_date=end,
                collection_ids=final_collection_ids,
                pagination_token=pagination_token,
                sort_order=sort_order,
                page_size=page_size,
            )

            stories.extend(page)

            self.logger.info(
                "Página de stories carregada | itens=%s | acumulado=%s",
                len(page),
                len(stories),
            )

            if max_stories is not None and len(stories) >= max_stories:
                stories = stories[:max_stories]
                self.logger.info("Limite max_stories atingido: %s", max_stories)
                break

            if not pagination_token:
                break

            time.sleep(self.config.request_pause_seconds)

        if not stories:
            self.logger.warning("Nenhum story encontrado para a busca.")
            return pd.DataFrame()

        df = pd.DataFrame(stories).copy()

        preferred_cols = [
            "id",
            "title",
            "url",
            "publish_date",
            "indexed_date",
            "language",
            "media_name",
            "media_url",
        ]
        ordered_cols = [c for c in preferred_cols if c in df.columns] + [
            c for c in df.columns if c not in preferred_cols
        ]
        df = df[ordered_cols]

        self.logger.info("Busca concluída com %s stories.", len(df))
        return df

    def extract_article(
        self,
        url: str,
        do_nlp: bool = False,
        retry_attempts: int | None = None,
        retry_wait_seconds: float | None = None,
    ) -> dict:
        retry_attempts = retry_attempts or self.config.newspaper_retry_attempts
        retry_wait_seconds = (
            retry_wait_seconds
            if retry_wait_seconds is not None
            else self.config.newspaper_retry_wait_seconds
        )

        last_error = None

        for attempt in range(1, retry_attempts + 1):
            try:
                self.logger.info(
                    "Baixando artigo | tentativa=%s/%s | url=%s",
                    attempt,
                    retry_attempts,
                    url,
                )

                article = Article(url=url, language=self.config.article_language)
                article.download()
                article.parse()

                if do_nlp:
                    try:
                        article.nlp()
                    except Exception as nlp_error:
                        self.logger.warning(
                            "Falha em article.nlp() | url=%s | erro=%s",
                            url,
                            nlp_error,
                        )

                return {
                    "article_title": article.title,
                    "article_text": article.text,
                    "article_summary": getattr(article, "summary", None),
                    "article_keywords": getattr(article, "keywords", None),
                    "article_authors": article.authors,
                    "article_publish_date": article.publish_date,
                    "article_top_image": article.top_image,
                    "article_movies": article.movies,
                    "article_success": True,
                    "article_error": None,
                    "article_attempts": attempt,
                }

            except Exception as e:
                last_error = str(e)
                self.logger.warning(
                    "Falha no download/parse | tentativa=%s/%s | url=%s | erro=%s",
                    attempt,
                    retry_attempts,
                    url,
                    e,
                )
                if attempt < retry_attempts:
                    time.sleep(retry_wait_seconds)

        self.logger.error("Falha final no artigo | url=%s | erro=%s", url, last_error)

        return {
            "article_title": None,
            "article_text": None,
            "article_summary": None,
            "article_keywords": None,
            "article_authors": None,
            "article_publish_date": None,
            "article_top_image": None,
            "article_movies": None,
            "article_success": False,
            "article_error": last_error,
            "article_attempts": retry_attempts,
        }

    # =====================================================
    # NOVO FLUXO 1: BAIXAR URLS E SALVAR
    # =====================================================

    def baixar_urls_e_salvar(
        self,
        terms: str | Sequence[str] | None,
        start_date: str | dt.date | dt.datetime,
        end_date: str | dt.date | dt.datetime,
        pasta_saida: str,
        nome_arquivo: str = "stories_urls",
        formato: Literal["csv", "parquet"] = "parquet",
        collection_ids: Sequence[int] | None = None,
        only_brazil_collections: bool = False,
        operator: Literal["AND", "OR"] = "OR",
        not_terms: str | Sequence[str] | None = None,
        extra_query: str | None = None,
        sort_order: str | None = None,
        max_stories: int | None = None,
        page_size: int | None = None,
    ) -> str:
        """
        Busca stories no Media Cloud e salva apenas a base de URLs/metadados
        em uma pasta.
        """
        df_urls = self.search_stories(
            terms=terms,
            start_date=start_date,
            end_date=end_date,
            collection_ids=collection_ids,
            only_brazil_collections=only_brazil_collections,
            operator=operator,
            not_terms=not_terms,
            extra_query=extra_query,
            sort_order=sort_order,
            max_stories=max_stories,
            page_size=page_size,
        )

        pasta = Path(pasta_saida)
        pasta.mkdir(parents=True, exist_ok=True)

        extensao = "parquet" if formato == "parquet" else "csv"
        caminho_saida = pasta / f"{nome_arquivo}.{extensao}"

        if formato == "parquet":
            df_urls.to_parquet(caminho_saida, index=False)
        else:
            df_urls.to_csv(caminho_saida, index=False, encoding="utf-8-sig")

        self.logger.info("Base de URLs salva em: %s", caminho_saida)
        return str(caminho_saida)

    def baixar_multiplas_buscas_e_salvar(
        self,
        searches: dict[str, dict],
        start_date: str | dt.date | dt.datetime,
        end_date: str | dt.date | dt.datetime,
        pasta_saida: str,
        formato: Literal["csv", "parquet"] = "parquet",
        collection_ids: Sequence[int] | None = None,
        only_brazil_collections: bool = False,
        default_max_stories: int | None = None,
        default_sort_order: str | None = None,
        default_page_size: int | None = None,
        salvar_manifesto: bool = True,
    ) -> dict[str, str]:
        """
        Executa múltiplas buscas no Media Cloud e salva cada uma em um arquivo separado.

        Parâmetro `searches`:
        {
            "nome_da_busca": {
                "termos": ["Nubank", "NuCel"],
                "operador": "AND",
                "not_terms": ["fintech"],        # opcional
                "extra_query": "...",            # opcional
                "nome_arquivo": "nubank_nucel", # opcional
                "max_stories": 100,              # opcional
                "sort_order": None,              # opcional
                "page_size": 500                 # opcional
            },
            ...
        }

        Retorna:
            {nome_da_busca: caminho_do_arquivo_salvo}
        """
        if not isinstance(searches, dict) or not searches:
            raise ValueError("'searches' deve ser um dicionário não vazio.")

        pasta = Path(pasta_saida)
        pasta.mkdir(parents=True, exist_ok=True)

        resultados: dict[str, str] = {}
        manifesto_rows: list[dict] = []

        for search_name, raw_config in searches.items():
            cfg = self._validate_search_config(search_name, raw_config)

            nome_arquivo = cfg["nome_arquivo"] or self._slugify_filename(search_name)

            self.logger.info(
                "Executando busca em lote | nome=%s | termos=%s | operador=%s | not_terms=%s",
                search_name,
                cfg["termos"],
                cfg["operador"],
                cfg["not_terms"],
            )

            caminho = self.baixar_urls_e_salvar(
                terms=cfg["termos"],
                start_date=start_date,
                end_date=end_date,
                pasta_saida=str(pasta),
                nome_arquivo=nome_arquivo,
                formato=formato,
                collection_ids=collection_ids,
                only_brazil_collections=only_brazil_collections,
                operator=cfg["operador"],
                not_terms=cfg["not_terms"],
                extra_query=cfg["extra_query"],
                sort_order=cfg["sort_order"] or default_sort_order,
                max_stories=(
                    cfg["max_stories"]
                    if cfg["max_stories"] is not None
                    else default_max_stories
                ),
                page_size=cfg["page_size"] or default_page_size,
            )

            resultados[search_name] = caminho

            manifesto_rows.append({
                "search_name": search_name,
                "file_path": caminho,
                "terms": cfg["termos"],
                "operator": cfg["operador"],
                "not_terms": cfg["not_terms"],
                "extra_query": cfg["extra_query"],
                "start_date": str(start_date),
                "end_date": str(end_date),
            })

        if salvar_manifesto and manifesto_rows:
            manifesto_df = pd.DataFrame(manifesto_rows)
            manifesto_path = pasta / "manifesto_buscas.parquet"
            manifesto_df.to_parquet(manifesto_path, index=False)
            self.logger.info("Manifesto de buscas salvo em: %s", manifesto_path)

        return resultados

    # =====================================================
    # NOVO FLUXO 2: LER URLS, BAIXAR COM NEWSPAPER E SALVAR
    # =====================================================

    def newspaper_from_urls_file_to_parquet(
        self,
        input_path: str,
        output_path: str,
        url_col: str = "url",
        do_nlp: bool = False,
        pause_seconds: float = 0.0,
        retry_attempts: int | None = None,
        retry_wait_seconds: float | None = None,
    ) -> str:
        """
        Lê uma base salva com URLs, baixa os textos via Newspaper3k,
        adiciona a coluna 'vehicle_domain' a partir da URL e salva em parquet.
        """
        input_path = str(input_path)
        output_path = str(output_path)

        if input_path.lower().endswith(".parquet"):
            stories_df = pd.read_parquet(input_path)
        elif input_path.lower().endswith(".csv"):
            stories_df = pd.read_csv(input_path)
        else:
            raise ValueError("input_path deve ser .csv ou .parquet")

        if stories_df.empty:
            self.logger.warning("Arquivo de entrada vazio: %s", input_path)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            stories_df.to_parquet(output_path, index=False)
            return output_path

        if url_col not in stories_df.columns:
            raise ValueError(f"Coluna '{url_col}' não encontrada no arquivo de entrada.")

        records = []
        total = len(stories_df)
        self.logger.info("Iniciando enriquecimento Newspaper3k | total=%s", total)

        for idx, (_, row) in enumerate(stories_df.iterrows(), start=1):
            url = row.get(url_col)
            self.logger.info("Processando artigo %s/%s | url=%s", idx, total, url)

            extracted = self.extract_article(
                url=url,
                do_nlp=do_nlp,
                retry_attempts=retry_attempts,
                retry_wait_seconds=retry_wait_seconds,
            )

            merged = row.to_dict()
            merged["vehicle_domain"] = extract_domain_from_url(url)
            merged.update(extracted)
            records.append(merged)

            if pause_seconds:
                time.sleep(pause_seconds)

        out_df = pd.DataFrame(records)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        out_df.to_parquet(output_path, index=False)

        success_rate = (
            out_df["article_success"].mean() if "article_success" in out_df.columns else 0
        )
        self.logger.info(
            "Parquet final salvo | path=%s | total=%s | taxa_sucesso=%.2f%%",
            output_path,
            len(out_df),
            success_rate * 100,
        )
        return output_path


# =========================================================
# EXEMPLO DE USO
# =========================================================

if __name__ == "__main__":
    client = MediaCloudNewsClient(
        MediaCloudConfig(
            api_key=os.getenv("MC_API_KEY"),
            log_file="logs/mediacloud_news.log",
        )
    )

    # Busca individual
    caminho_urls = client.baixar_urls_e_salvar(
        terms=["americanas", "varejo"],
        start_date="2026-03-01",
        end_date="2026-03-31",
        pasta_saida="outputs/media_cloud",
        nome_arquivo="stories_americanas_marco_2026",
        formato="parquet",
        only_brazil_collections=True,
        operator="OR",
        max_stories=500,
    )

    # Busca em lote
    searches = {
        "nubank_and_nucel": {
            "termos": ["Nubank", "NuCel"],
            "operador": "AND",
        },
        "somente_nucel": {
            "termos": ["NuCel"],
            "operador": "OR",
        },
        "inter_and_intercel": {
            "termos": ["Banco Inter", "Intercel"],
            "operador": "AND",
        },
        "tema_mvno_sem_bigtechs": {
            "termos": ["MVNO", "operadora virtual"],
            "operador": "OR",
            "not_terms": ["Google", "Amazon"],
        },
    }

    caminhos_lote = client.baixar_multiplas_buscas_e_salvar(
        searches=searches,
        start_date="2026-03-01",
        end_date="2026-03-31",
        pasta_saida="outputs/media_cloud/mvnos",
        formato="parquet",
        only_brazil_collections=True,
        default_max_stories=500,
    )

    caminho_final = client.newspaper_from_urls_file_to_parquet(
        input_path=caminho_urls,
        output_path="outputs/media_cloud/stories_americanas_marco_2026_newspaper.parquet",
        do_nlp=False,
        pause_seconds=0.2,
    )

    print("URLs salvas em:", caminho_urls)
    print("Buscas em lote salvas em:", caminhos_lote)
    print("Base final salva em:", caminho_final)
