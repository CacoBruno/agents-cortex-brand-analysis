import json
import hashlib
from datetime import timedelta
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import torch

from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")


from cortex_brand_analysis.nlp.models.summarize import resumo_extrativo

def closest_cluster_ids(df, n=10) -> Dict:
     
    if 'titulo_da_publicacao' in df.columns:
        title = 'titulo_da_publicacao'

    if "Título" in df.columns:
        title = "Título"

    if 'conteudo' in df.columns:
        content = 'conteudo'

    if "Conteúdo" in df.columns:
        content = "Conteúdo"


    top_texts_per_cluster = {}

    df['text'] = df[title] + df[content] 
    df['text'] = df['text'].apply(resumo_extrativo)
    for cluster_id in df['cluster_id'].unique():
            cluster_data = df[df['cluster_id'] == cluster_id]
            # Excluir outliers, se desejar
            # Ordenar por 'distance_to_centroid'
            closest_texts = cluster_data.nsmallest(n, 'distance_to_centroid')
            # Armazenar os textos ou outras informações relevantes
            top_texts_per_cluster[cluster_id] = closest_texts['text'].tolist()

    return top_texts_per_cluster


def get_embedding(text: str):
    return _model.encode(text)

# =========================================================
# UTILITÁRIOS
# =========================================================

def means_dict_values(dict_):
    return sum(dict_.values()) / len(dict_) if dict_ else 0


def _sanitize_nested(x):
    import numpy as np
    from datetime import date, datetime

    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if x is None:
        return None

    if isinstance(x, (pd.Timestamp, datetime)):
        return x.isoformat()
    if isinstance(x, date):
        return x.isoformat()

    if isinstance(x, dict):
        return {str(k): _sanitize_nested(v) for k, v in x.items()}

    if isinstance(x, (list, tuple, set)):
        return [_sanitize_nested(v) for v in x]

    try:
        json.dumps(x)
        return x
    except Exception:
        return str(x)


def _jsonify_nested(x):
    if isinstance(x, (dict, list, tuple, set)):
        return json.dumps(_sanitize_nested(x), ensure_ascii=False, sort_keys=True)
    return _sanitize_nested(x)


def _make_cluster_id(cluster_label: int, start_date=None, end_date=None, namespace: str = "clusters:v1") -> str:
    key = f"{namespace}|{start_date}|{end_date}|{cluster_label}".encode("utf-8")
    h = hashlib.blake2b(key, digest_size=8)
    return f"clu_{h.hexdigest()}"


# =========================================================
# EMBEDDING CACHE
# =========================================================

def build_embedding_cache(
    texts: List[str],
    get_embedding,
    max_workers: int = 8,
) -> Dict[str, np.ndarray]:
    """
    Gera embeddings uma única vez para textos únicos.
    """
    unique_texts = [t for t in pd.Series(texts, dtype="object").dropna().astype(str).str.strip().unique() if t]

    cache: Dict[str, np.ndarray] = {}

    def _embed_one(text):
        vec = get_embedding(text)
        vec = np.asarray(vec, dtype=np.float32)
        if vec.ndim != 1:
            raise ValueError(f"Embedding inválido para texto. Shape recebido: {vec.shape}")
        return text, vec

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_embed_one, txt) for txt in unique_texts]
        for fut in as_completed(futures):
            text, vec = fut.result()
            cache[text] = vec

    return cache


def _get_embeddings_from_cache(texts: List[str], embedding_cache: Dict[str, np.ndarray]) -> np.ndarray:
    vecs = []
    for t in texts:
        if t not in embedding_cache:
            raise KeyError("Texto não encontrado no cache de embeddings.")
        vecs.append(embedding_cache[t])

    if not vecs:
        return np.empty((0, 0), dtype=np.float32)

    return np.vstack(vecs).astype(np.float32)


# =========================================================
# CLUSTERING
# =========================================================

def clustering_classification_fast_cached(
    df: pd.DataFrame,
    column_to_cluster: str,
    *,
    embedding_cache: Dict[str, np.ndarray],
    max_k: int = 10,
    sample_for_k: int = 5000,
    pca_components: int = 50,
    use_cosine: bool = True,
    random_state: int = 0,
) -> pd.DataFrame:

    if column_to_cluster not in df.columns:
        raise KeyError(f"A coluna '{column_to_cluster}' não existe no DataFrame.")

    df = df.copy()

    mask_valid = (
        df[column_to_cluster].notna()
        & df[column_to_cluster].astype(str).str.strip().ne("")
    )
    df = df.loc[mask_valid].copy()

    if df.empty:
        return pd.DataFrame()

    textos = df[column_to_cluster].astype(str).tolist()
    embeddings_raw = _get_embeddings_from_cache(textos, embedding_cache)

    if embeddings_raw.ndim != 2:
        raise ValueError(f"Embeddings inválidos. Shape recebido: {embeddings_raw.shape}")

    df["embeddings"] = [row for row in embeddings_raw]

    # opcional: normalização para aproximar similaridade angular/cosseno
    X = embeddings_raw.copy()
    if use_cosine:
        X = normalize(X, norm="l2", axis=1)

    # PCA
    n_samples, n_features = X.shape
    max_valid_components = min(n_samples, n_features)

    if pca_components and max_valid_components > 1:
        n_comp = min(pca_components, max_valid_components)
        X_reduced = PCA(n_components=n_comp, random_state=random_state).fit_transform(X)
    else:
        X_reduced = X

    n = len(X_reduced)

    if n < 2:
        df["cluster"] = 0
        df["distance_to_centroid"] = 0.0
        df["reliability"] = "very reliable"

        if "data_da_publicacao" in df.columns:
            start_date = df["data_da_publicacao"].min()
            end_date = df["data_da_publicacao"].max()
        else:
            start_date = None
            end_date = None

        df["cluster_id"] = _make_cluster_id(0, start_date, end_date)
        return df.reset_index(drop=True)

    max_clusters = min(max_k, max(2, n // 2), n)

    if n > sample_for_k:
        rng = np.random.default_rng(random_state)
        idx = rng.choice(n, size=sample_for_k, replace=False)
        X_k = X_reduced[idx]
    else:
        X_k = X_reduced

    def mean_centroid_distance(centers: np.ndarray) -> float:
        if len(centers) < 2:
            return 0.0
        dists = np.linalg.norm(centers[:, None, :] - centers[None, :, :], axis=2)
        iu = np.triu_indices_from(dists, k=1)
        return float(dists[iu].mean())

    best_k = 2
    for k in range(2, max_clusters + 1):
        if k > len(X_k):
            break

        kmb = MiniBatchKMeans(
            n_clusters=k,
            random_state=random_state,
            n_init="auto",
            batch_size=min(2048, len(X_k)),
            max_iter=100,
        ).fit(X_k)

        mcd = mean_centroid_distance(kmb.cluster_centers_)
        best_k = k
        if 1.8 <= mcd <= 2.2:
            break

    kmeans = MiniBatchKMeans(
        n_clusters=best_k,
        random_state=random_state,
        n_init="auto",
        batch_size=min(2048, len(X_reduced)),
        max_iter=200,
    ).fit(X_reduced)

    labels = kmeans.labels_
    centers = kmeans.cluster_centers_

    df["cluster"] = labels

    distances = np.linalg.norm(X_reduced - centers[labels], axis=1)
    df["distance_to_centroid"] = np.round(distances, 3)

    bins = np.array([1.5, 2.5, 3.5], dtype=float)
    choices = np.array(
        ["very reliable", "reliable", "low reliable", "outlier"],
        dtype=object
    )
    df["reliability"] = choices[
        np.digitize(df["distance_to_centroid"].to_numpy(), bins, right=False)
    ]

    grp = df.groupby("cluster")["distance_to_centroid"]
    q1 = grp.transform(lambda s: s.quantile(0.25))
    q3 = grp.transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    lim_sup = q3 + 1.5 * iqr
    is_outlier = df["distance_to_centroid"] > lim_sup

    if is_outlier.any():
        idx_out = np.where(is_outlier.to_numpy())[0]
        XO = X_reduced[idx_out]
        dmat = np.linalg.norm(XO[:, None, :] - centers[None, :, :], axis=2)
        nearest = dmat.argmin(axis=1)
        new_dist = dmat[np.arange(len(idx_out)), nearest]

        df.loc[df.index[idx_out], "cluster"] = nearest
        df.loc[df.index[idx_out], "distance_to_centroid"] = np.round(new_dist, 3)

        grp2 = df.groupby("cluster")["distance_to_centroid"]
        q1b = grp2.transform(lambda s: s.quantile(0.25))
        q3b = grp2.transform(lambda s: s.quantile(0.75))
        iqrb = q3b - q1b
        lim_sup_b = q3b + 1.5 * iqrb
        still_out = df["distance_to_centroid"] > lim_sup_b
        df.loc[still_out, "reliability"] = "outlier"

    if "data_da_publicacao" in df.columns:
        start_date = df["data_da_publicacao"].min()
        end_date = df["data_da_publicacao"].max()
    else:
        start_date = None
        end_date = None

    cluster_to_id = {
        cl: _make_cluster_id(int(cl), start_date, end_date)
        for cl in df["cluster"].unique()
    }
    df["cluster_id"] = df["cluster"].map(cluster_to_id)

    cols_sort = [
        c for c in [
            "cluster",
            "cluster_id",
            "titulo_da_publicacao",
            "data_da_publicacao",
            "distance_to_centroid"
        ]
        if c in df.columns
    ]

    if cols_sort:
        df = df.sort_values(by=cols_sort)

    return df.reset_index(drop=True)


# =========================================================
# SIMILARIDADE
# =========================================================

def similaridade_cluster_fast(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Mesma lógica da sua função, mas com menos repetição.
    """
    df = dataframe.copy()

    if "cluster" not in df.columns:
        raise KeyError("A coluna 'cluster' não existe no DataFrame.")

    if "embeddings" not in df.columns:
        raise KeyError("A coluna 'embeddings' não existe no DataFrame.")

    # escolher coluna de alcance
    alcance = None
    if "Alcance orgânico" in df.columns:
        alcance = "Alcance orgânico"
    elif "alcance_organico_normalizado" in df.columns:
        alcance = "alcance_organico_normalizado"

    # escolher identificador
    id_col = None
    if "Chave Análise de Mídia Hash" in df.columns:
        id_col = "Chave Análise de Mídia Hash"
    elif "cortex_id" in df.columns:
        id_col = "cortex_id"
    elif "ID Cortex" in df.columns:
        id_col = "ID Cortex"

    if id_col is None:
        raise KeyError("Não encontrei coluna identificadora: 'Chave Análise de Mídia Hash', 'cortex_id' ou 'ID Cortex'.")

    sort_cols = [alcance] if alcance else None

    matriz_total = {}

    for cluster_value, cluster_df in df.groupby("cluster", sort=False):
        if sort_cols:
            cluster_df = cluster_df.sort_values(by=sort_cols, ascending=False)

        ids = cluster_df[id_col].tolist()
        vectors = np.vstack(cluster_df["embeddings"].to_list())
        matriz_sim = cosine_similarity(vectors)

        for i, id1 in enumerate(ids):
            sims = {
                ids[j]: float(matriz_sim[i, j])
                for j in range(len(ids))
                if i != j
            }
            matriz_total[id1] = dict(sorted(sims.items(), key=lambda item: item[1], reverse=True))

    df["similaridade_cluster"] = df[id_col].map(matriz_total)
    df["media_similaridade_cluster"] = df["similaridade_cluster"].map(means_dict_values)

    return df


# =========================================================
# JANELAS
# =========================================================

def _build_windows(sd: pd.Timestamp, ed: pd.Timestamp, time_delta: int) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    windows = []
    current_end = ed
    delta = timedelta(days=time_delta)

    while current_end >= sd:
        window_start = current_end - delta + timedelta(days=1)
        if window_start < sd:
            window_start = sd
        windows.append((window_start, current_end))
        current_end -= timedelta(days=1)

    return windows


def _process_single_window(
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
    df_base: pd.DataFrame,
    date_col: str,
    column_to_cluster: str,
    embedding_cache: Dict[str, np.ndarray],
    add_window_cols: bool,
    nested_as_json: bool,
) -> pd.DataFrame:
    mask = df_base["_date_only"].between(window_start, window_end, inclusive="both")
    df_filtrado = df_base.loc[mask].copy()

    if df_filtrado.empty:
        return pd.DataFrame()

    cluster_df = clustering_classification_fast_cached(
        df_filtrado,
        column_to_cluster=column_to_cluster,
        embedding_cache=embedding_cache,
    )

    if cluster_df.empty:
        return pd.DataFrame()

    similar_df = similaridade_cluster_fast(cluster_df)

    if add_window_cols:
        similar_df["window_start"] = window_start
        similar_df["window_end"] = window_end

    # sanitização
    for col in similar_df.columns:
        if similar_df[col].dtype == "object":
            has_nested = similar_df[col].map(
                lambda v: isinstance(v, (dict, list, tuple, set))
            ).any()

            if has_nested and nested_as_json:
                similar_df[col] = similar_df[col].map(_jsonify_nested)
            else:
                similar_df[col] = similar_df[col].map(_sanitize_nested)

    return similar_df


import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd


def daily_cluster_similaridade_parallel(
    df: pd.DataFrame,
    start_date: str,
    end_date: str,
    *,
    date_col: str = "Data",
    column_to_cluster: str = "Therms selected",
    time_delta: int = 1,
    add_window_cols: bool = True,
    verbose: bool = True,
    nested_as_json: bool = True,
    max_workers: int = 4,
    embedding_workers: int = 8,
    get_embedding=get_embedding,
) -> pd.DataFrame:
    """
    Executa clustering textual por janelas temporais em paralelo.

    Fluxo:
    1. valida colunas e datas
    2. filtra período
    3. limpa textos vazios
    4. gera cache de embeddings únicos
    5. processa cada janela em paralelo
    6. concatena os resultados finais

    Retorna um DataFrame com os dados originais enriquecidos com:
    - cluster: id local do cluster retornado por _process_single_window
    - cluster_local: versão string do cluster local
    - window_id: identificador da janela
    - cluster_id: identificador global único (window_id + cluster_local)
    - cluster_hash: hash estável do cluster_id
    - outras colunas produzidas por _process_single_window, como:
        - distance_to_centroid
        - window_start / window_end
        - etc.
    """

    def _stable_hash(value: str) -> str:
        return hashlib.sha1(str(value).encode("utf-8")).hexdigest()

    if get_embedding is None:
        raise ValueError("Você precisa passar a função get_embedding.")

    if date_col not in df.columns:
        raise KeyError(f"Coluna '{date_col}' não existe no DataFrame.")

    if column_to_cluster not in df.columns:
        raise KeyError(f"Coluna '{column_to_cluster}' não existe no DataFrame.")

    sd = pd.to_datetime(start_date).normalize()
    ed = pd.to_datetime(end_date).normalize()

    if sd > ed:
        raise ValueError("start_date não pode ser maior que end_date.")

    df = df.copy()

    # garante datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # remove datas inválidas
    df = df[df[date_col].notna()].copy()
    if df.empty:
        if verbose:
            print("Nenhum registro com data válida após conversão.")
        return pd.DataFrame()

    df["_date_only"] = df[date_col].dt.normalize()

    # filtra intervalo global
    df = df[df["_date_only"].between(sd, ed, inclusive="both")].copy()
    if df.empty:
        if verbose:
            print("Nenhum registro no intervalo informado.")
        return pd.DataFrame()

    # limpeza da coluna textual
    df[column_to_cluster] = df[column_to_cluster].fillna("").astype(str).str.strip()
    df = df[df[column_to_cluster].ne("")].copy()
    if df.empty:
        if verbose:
            print("Nenhum texto válido para clusterização.")
        return pd.DataFrame()

    # gera cache de embeddings apenas para textos únicos
    valid_texts = df[column_to_cluster].tolist()
    unique_texts_count = len(set(valid_texts))

    if verbose:
        print(f"Gerando cache de embeddings para {unique_texts_count} textos únicos...")

    embedding_cache = build_embedding_cache(
        valid_texts,
        get_embedding=get_embedding,
        max_workers=embedding_workers,
    )

    # constrói janelas
    windows = _build_windows(sd, ed, time_delta)

    if verbose:
        print(f"Total de janelas geradas: {len(windows)}")

    resultados = []
    erros = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _process_single_window,
                window_start,
                window_end,
                df,
                date_col,
                column_to_cluster,
                embedding_cache,
                add_window_cols,
                nested_as_json,
            ): (window_start, window_end)
            for window_start, window_end in windows
        }

        for future in as_completed(future_map):
            window_start, window_end = future_map[future]

            try:
                out = future.result()

                if out is None or out.empty:
                    if verbose:
                        print(
                            f"Janela {window_start.date()} -> {window_end.date()} vazia."
                        )
                    continue

                out = out.copy()

                if "cluster" not in out.columns:
                    raise KeyError(
                        "A saída de _process_single_window não contém a coluna 'cluster'."
                    )

                # cluster local original como string
                out["cluster_local"] = out["cluster"].astype(str)

                # id da janela
                out["window_id"] = (
                    pd.to_datetime(window_start).strftime("%Y-%m-%d")
                    + "_"
                    + pd.to_datetime(window_end).strftime("%Y-%m-%d")
                )

                # id global legível
                out["cluster_id"] = out["window_id"] + "_" + out["cluster_local"]

                # hash estável para banco / joins
                out["cluster_hash"] = out["cluster_id"].apply(_stable_hash)

                if verbose:
                    print(
                        f"Janela {window_start.date()} -> {window_end.date()} concluída | "
                        f"rows={len(out)} | "
                        f"clusters_local={out['cluster_local'].nunique()} | "
                        f"clusters_global_janela={out['cluster_id'].nunique()}"
                    )

                resultados.append(out)

            except Exception as e:
                erros.append((window_start, window_end, str(e)))
                if verbose:
                    print(
                        f"[AVISO] Falha na janela "
                        f"{window_start.date()}->{window_end.date()}: {e}"
                    )

    if not resultados:
        if verbose:
            print("Nenhum resultado de clustering foi gerado.")
        return pd.DataFrame()

    all_results = pd.concat(resultados, ignore_index=True)

    # ordenação final
    cols_sort = [
        c
        for c in [
            "window_end",
            "window_start",
            "cluster_id",
            "distance_to_centroid",
        ]
        if c in all_results.columns
    ]

    if cols_sort:
        all_results = all_results.sort_values(cols_sort).reset_index(drop=True)

    if verbose:
        print("\n===== RESUMO FINAL =====")
        print(f"Total de linhas: {len(all_results)}")

        if "cluster" in all_results.columns:
            print(f"Clusters locais (coluna 'cluster'): {all_results['cluster'].nunique()}")

        if "window_id" in all_results.columns:
            print(f"Total de janelas processadas: {all_results['window_id'].nunique()}")

        if "cluster_id" in all_results.columns:
            print(f"Clusters globais únicos (coluna 'cluster_id'): {all_results['cluster_id'].nunique()}")

        if "cluster_hash" in all_results.columns:
            print(f"Hashes únicos (coluna 'cluster_hash'): {all_results['cluster_hash'].nunique()}")

        if erros:
            print(f"Janelas com erro: {len(erros)}")

    return all_results