from __future__ import annotations

import re
import unicodedata
from typing import Dict, Any, List, Tuple
from collections import defaultdict

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer


def _normalize_text(text: str) -> str:
    """
    Normalização leve para comparação.
    Mantém o sentido do texto, mas reduz variações superficiais.
    """
    if text is None:
        return ""

    text = str(text).strip().lower()

    # remove acentos
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # remove pontuação extra
    text = re.sub(r"[^\w\s]", " ", text)

    # espaços duplicados
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _choose_canonical_label(labels: List[str], sim_matrix: np.ndarray | None = None) -> str:
    """
    Escolhe o melhor rótulo canônico para um grupo de temas similares.

    Estratégia:
    - se houver matriz de similaridade do grupo, escolhe o label mais "central"
      (maior similaridade média com os demais)
    - em empate, escolhe o mais curto
    """
    if len(labels) == 1:
        return labels[0]

    if sim_matrix is not None and len(labels) == sim_matrix.shape[0]:
        mean_sim = sim_matrix.mean(axis=1)
        best_idx = np.argmax(mean_sim)
        candidates = np.where(mean_sim == mean_sim[best_idx])[0]
        if len(candidates) > 1:
            best_idx = min(candidates, key=lambda i: len(labels[i]))
        return labels[best_idx]

    return min(labels, key=len)


def _connected_components_from_similarity(
    similarity_matrix: np.ndarray,
    threshold: float
) -> List[List[int]]:
    """
    Cria grupos por componente conexa:
    se A~B e B~C, todos entram no mesmo grupo.
    """
    n = similarity_matrix.shape[0]
    visited = [False] * n
    groups = []

    for i in range(n):
        if visited[i]:
            continue

        stack = [i]
        component = []

        while stack:
            node = stack.pop()
            if visited[node]:
                continue

            visited[node] = True
            component.append(node)

            neighbors = np.where(similarity_matrix[node] >= threshold)[0]
            for nb in neighbors:
                if not visited[nb]:
                    stack.append(nb)

        groups.append(sorted(component))

    return groups


def normalizar_temas_similares(
    resultado: Dict[str, Dict[str, Any]],
    campo_tema: str = "tema",
    similarity_threshold: float = 0.72,
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    prefer_embedding: bool = True,
    atualizar_inplace: bool = False
) -> Dict[str, Any]:
    """
    Normaliza temas semanticamente similares dentro de um dicionário de clusters.

    Parâmetros
    ----------
    resultado : dict
        Ex:
        {
            "C33695845": {"resumo": "...", "tema": "Liquidação do Banco Master", "macrotema": "..."},
            "C27743667": {"resumo": "...", "tema": "Banco Master é liquidado", "macrotema": "..."},
        }

    campo_tema : str
        Nome da chave onde está o tema.

    similarity_threshold : float
        Limiar de similaridade para considerar dois temas equivalentes.
        Sugestões:
        - 0.68 a 0.74 -> mais sensível
        - 0.75 a 0.82 -> mais conservador

    model_name : str
        Modelo de embeddings, caso sentence-transformers esteja disponível.

    prefer_embedding : bool
        Se True, tenta usar embeddings primeiro.

    atualizar_inplace : bool
        Se True, altera o dicionário original.
        Se False, retorna uma cópia.

    Retorno
    -------
    dict com:
        - "resultado_normalizado": dicionário com os temas normalizados
        - "mapa_tema_original_para_canonico": dict
        - "grupos": lista com agrupamentos encontrados
        - "similarity_matrix": matriz de similaridade
        - "metodo_usado": "sentence_transformers" ou "tfidf_char_ngrams"
    """
    if not resultado:
        return {
            "resultado_normalizado": {},
            "mapa_tema_original_para_canonico": {},
            "grupos": [],
            "similarity_matrix": np.array([]),
            "metodo_usado": None,
        }

    cluster_ids = list(resultado.keys())
    temas_originais = [str(resultado[cid].get(campo_tema, "") or "") for cid in cluster_ids]
    temas_normalizados_texto = [_normalize_text(t) for t in temas_originais]

    # =========================
    # 1) Similaridade semântica
    # =========================
    metodo_usado = None
    emb = None

    if prefer_embedding:
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name)
            emb = model.encode(temas_originais, normalize_embeddings=True)
            similarity_matrix = cosine_similarity(emb)
            metodo_usado = "sentence_transformers"
        except Exception:
            emb = None

    if emb is None:
        # fallback: TF-IDF por n-grams de caracteres
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        X = vectorizer.fit_transform(temas_normalizados_texto)
        similarity_matrix = cosine_similarity(X)
        metodo_usado = "tfidf_char_ngrams"

    # garante diagonal 1
    np.fill_diagonal(similarity_matrix, 1.0)

    # =========================
    # 2) Agrupar temas similares
    # =========================
    groups_idx = _connected_components_from_similarity(similarity_matrix, similarity_threshold)

    # =========================
    # 3) Escolher rótulo canônico
    # =========================
    mapa_tema_original_para_canonico = {}
    grupos_saida = []

    for group in groups_idx:
        labels_group = [temas_originais[i] for i in group]
        sub_sim = similarity_matrix[np.ix_(group, group)]
        canonical = _choose_canonical_label(labels_group, sub_sim)

        grupos_saida.append({
            "indices": group,
            "cluster_ids": [cluster_ids[i] for i in group],
            "temas_originais": labels_group,
            "tema_canonico": canonical,
        })

        for i in group:
            mapa_tema_original_para_canonico[temas_originais[i]] = canonical

    # =========================
    # 4) Aplicar substituição
    # =========================
    if atualizar_inplace:
        resultado_normalizado = resultado
    else:
        resultado_normalizado = {
            cid: dict(payload) for cid, payload in resultado.items()
        }

    for cid in cluster_ids:
        tema_original = str(resultado_normalizado[cid].get(campo_tema, "") or "")
        resultado_normalizado[cid][campo_tema] = mapa_tema_original_para_canonico.get(
            tema_original, tema_original
        )

    return {
        "resultado_normalizado": resultado_normalizado,
        "mapa_tema_original_para_canonico": mapa_tema_original_para_canonico,
        "grupos": grupos_saida,
        "similarity_matrix": similarity_matrix,
        "metodo_usado": metodo_usado,
    }