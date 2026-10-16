import re
import unicodedata
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd


TIER_WEIGHT = {
    "Tier 1": 1.0,
    "Tier 2": 0.7,
    "Tier 3": 0.4,
    "Outros" : 0.1
}

# =========================================================
# NORMALIZAÇÃO E SPLIT
# =========================================================
def normalize_text(text: str) -> str:
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"\s+", " ", text)
    return text


def split_sentences(text: str) -> List[str]:
    if pd.isna(text):
        return []
    text = str(text).strip()
    if not text:
        return []

    # split simples por final de frase
    frases = re.split(r"(?<=[\.\!\?\;\:])\s+", text)
    frases = [f.strip() for f in frases if f and f.strip()]
    return frases


def estimate_tokens(text: str) -> int:
    """
    Estimativa simples de tokens.
    Aproximação útil quando você não quer depender de tokenizer externo.
    """
    if not text:
        return 0
    return max(1, int(len(text) / 4))


# =========================================================
# EMBEDDINGS
# =========================================================
def get_sentence_transformer(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
    """
    Carrega um modelo multilingual bom para português.
    Requer:
        pip install sentence-transformers
    """
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


def cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    emb_norm = embeddings / norms
    return np.dot(emb_norm, emb_norm.T)


# =========================================================
# EXTRAÇÃO DE FRASES COM TERMOS
# =========================================================
def select_phrases_with_terms(text: str, list_search: List[str]) -> List[Dict[str, Any]]:
    phrases = split_sentences(text)
    search_terms = [(term, normalize_text(term)) for term in list_search]

    results = []

    for phrase in phrases:
        phrase_norm = normalize_text(phrase)
        found_terms = []

        for original_term, norm_term in search_terms:
            pattern = r"\b" + re.escape(norm_term) + r"\b"
            if re.search(pattern, phrase_norm):
                found_terms.append(original_term)

        if found_terms:
            results.append({
                "phrase": phrase,
                "terms_found": found_terms
            })

    return results


# =========================================================
# SCORE DE RELEVÂNCIA DA FRASE
# =========================================================
def score_phrase_relevance(
    phrase: str,
    terms_found: List[str],
    title: Optional[str] = None,
    source: Optional[str] = None,
) -> float:
    """
    Heurística de score:
    - quantidade de termos encontrados
    - tamanho razoável da frase
    - bônus se algum termo aparece no início
    - bônus se há números/dados
    - bônus se aproxima do título
    """
    phrase_norm = normalize_text(phrase)
    title_norm = normalize_text(title) if title else ""

    score = 0.0

    # 1. quantidade de termos encontrados
    unique_terms = list(set(terms_found))
    score += len(unique_terms) * 2.0

    # 2. tamanho ideal
    n_chars = len(phrase)
    if 60 <= n_chars <= 280:
        score += 2.0
    elif 30 <= n_chars < 60 or 280 < n_chars <= 400:
        score += 1.0

    # 3. termo aparece cedo na frase
    for term in unique_terms:
        term_norm = normalize_text(term)
        pos = phrase_norm.find(term_norm)
        if pos != -1:
            if pos <= 40:
                score += 1.0
            break

    # 4. presença de número / percentual / valor
    if re.search(r"\b\d+[\,\.\d]*\b", phrase):
        score += 0.8
    if "%" in phrase or "r$" in phrase.lower():
        score += 0.8

    # 5. aproximação com o título
    if title_norm:
        overlap = 0
        title_words = set(title_norm.split())
        phrase_words = set(phrase_norm.split())
        if title_words:
            overlap = len(title_words.intersection(phrase_words)) / max(1, len(title_words))
            score += overlap * 2.0

    # 6. penaliza frases muito curtas
    if n_chars < 25:
        score -= 1.5

    return round(score, 4)


# =========================================================
# REMOÇÃO DE FRASES SIMILARES COM EMBEDDINGS
# =========================================================
def remove_similares_embeddings(
    frases: List[str],
    model,
    similarity_threshold: float = 0.82,
    max_frases: int = 5,
    scores: Optional[List[float]] = None,
) -> List[str]:
    """
    Remove frases semanticamente muito próximas.
    Mantém preferencialmente as de maior score.
    """
    frases = [f for f in frases if isinstance(f, str) and f.strip()]
    if not frases:
        return []

    if len(frases) == 1:
        return frases

    if scores is None:
        scores = [0.0] * len(frases)

    # ordena por score desc para preservar as melhores
    idx_sorted = sorted(range(len(frases)), key=lambda i: scores[i], reverse=True)
    frases_sorted = [frases[i] for i in idx_sorted]

    embeddings = model.encode(frases_sorted, convert_to_numpy=True, normalize_embeddings=True)
    sim = np.dot(embeddings, embeddings.T)

    kept = []
    kept_idx = []

    for i, frase in enumerate(frases_sorted):
        is_similar = False
        for j in kept_idx:
            if sim[i, j] >= similarity_threshold:
                is_similar = True
                break

        if not is_similar:
            kept.append(frase)
            kept_idx.append(i)

        if len(kept) >= max_frases:
            break

    return kept


# =========================================================
# CLUSTER SEMÂNTICO DE FRASES
# =========================================================
def cluster_phrases_embeddings(
    frases: List[str],
    model,
    similarity_threshold: float = 0.72
) -> List[List[str]]:
    """
    Agrupamento simples por conectividade via threshold.
    """
    frases = [f for f in frases if isinstance(f, str) and f.strip()]
    if not frases:
        return []

    if len(frases) == 1:
        return [frases]

    embeddings = model.encode(frases, convert_to_numpy=True, normalize_embeddings=True)
    sim = np.dot(embeddings, embeddings.T)

    n = len(frases)
    visited = set()
    grupos = []

    for i in range(n):
        if i in visited:
            continue

        stack = [i]
        component = []

        while stack:
            node = stack.pop()
            if node in visited:
                continue

            visited.add(node)
            component.append(node)

            neighbors = np.where(sim[node] >= similarity_threshold)[0].tolist()
            for nb in neighbors:
                if nb not in visited:
                    stack.append(nb)

        grupos.append([frases[idx] for idx in component])

    return grupos


def choose_representative_phrase(cluster: List[str], all_scores_map: Dict[str, float]) -> str:
    """
    Pega a frase com maior score dentro do cluster.
    """
    return max(cluster, key=lambda x: all_scores_map.get(x, 0.0))


# =========================================================
# LIMITADOR AUTOMÁTICO DE TOKENS
# =========================================================

def ordenar_frases_por_encadeamento(frases: list[str], model) -> list[str]:
    if not frases:
        return []

    if len(frases) == 1:
        return frases

    embeddings = model.encode(
        frases,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    sim_matrix = np.dot(embeddings, embeddings.T)

    # começa pela frase mais central
    mean_sim = sim_matrix.mean(axis=1)
    atual = int(np.argmax(mean_sim))

    visitados = {atual}
    ordem = [atual]

    while len(visitados) < len(frases):
        candidatos = [
            (j, sim_matrix[atual, j])
            for j in range(len(frases))
            if j not in visitados
        ]

        proximo = max(candidatos, key=lambda x: x[1])[0]
        ordem.append(proximo)
        visitados.add(proximo)
        atual = proximo

    return [frases[i] for i in ordem]

def truncate_group_by_token_budget(
    items: List[Dict[str, Any]],
    max_tokens: int
) -> List[Dict[str, Any]]:
    """
    Mantém itens até bater o orçamento de tokens.
    Cada item deve ter campo 'estimated_tokens' e já estar ordenado.
    """
    selected = []
    total = 0

    for item in items:
        item_tokens = item.get("estimated_tokens", 0)
        if total + item_tokens > max_tokens:
            continue

        selected.append(item)
        total += item_tokens

    return selected

def construir_texto_narrativo(
    frases: list[dict],
    model,
    min_frases: int = 5,
    similarity_threshold: float = 0.7
) -> str:
    if not frases:
        return ""

    textos = [f["texto"] for f in frases]
    score_map = {f["texto"]: f["score_relevancia"] for f in frases}

    clusters = cluster_phrases_embeddings(
        frases=textos,
        model=model,
        similarity_threshold=similarity_threshold
    )

    clusters = sorted(
        clusters,
        key=lambda c: sum(score_map.get(f, 0) for f in c),
        reverse=True
    )
    melhor_cluster = clusters[0]

    if len(melhor_cluster) < min_frases:
        restantes = sorted(
            [f for f in textos if f not in melhor_cluster],
            key=lambda x: score_map.get(x, 0),
            reverse=True
        )
        for f in restantes:
            melhor_cluster.append(f)
            if len(melhor_cluster) >= min_frases:
                break

    frases_ordenadas = ordenar_frases_por_encadeamento(melhor_cluster, model)

    return " ".join(frases_ordenadas)


def safe_get(row, col):
    if col and col in row and pd.notna(row[col]):
        return row[col]
    return None


def safe_float(value):
    try:
        if pd.isna(value):
            return None
        return float(value)
    except:
        return None


def safe_str(value):
    if pd.isna(value) or value is None:
        return None
    return str(value).strip()

# =========================================================
# FUNÇÃO PRINCIPAL
# =========================================================

from collections import defaultdict
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from collections import defaultdict
from typing import List
import pandas as pd
import numpy as np

model = get_sentence_transformer()


def extrair_contexto_noticias(
    dataframe: pd.DataFrame,
    list_search: List[str],

    col_data: str = "data",
    col_titulo: str = "titulo",
    col_fonte: str = "fonte",
    col_conteudo: str = "conteudo",
    col_id: str = "Chave Análise de Mídia Hash",

    col_alcance: str | None = "alcance",
    col_tier: str | None = "tier",
    col_tipos_de_impactos: str | None = "tipos_de_impactos",
    col_sentimento: str | None = "sentimento",
    col_protagonismo: str | None = "protagonismo",

    col_empresa: str | None = "Empresa analisada",
    col_produto: str | None = "Produto analisado",
    col_jornalista: str | None = "Jornalista",

    col_url_noticia: str | None = "url da notícia",
    col_assuntos_especificos: str | None = "Assuntos específicos",
    col_midia: str | None = "Mídia",

    # novos parâmetros de performance
    model=model,
    max_frases_por_doc: int = 20,
    max_frases_saida: int = 5,
    usar_narrativa: bool = False,
):

    required_cols = [col_data, col_titulo, col_fonte, col_conteudo, col_id]
    missing = [c for c in required_cols if c not in dataframe.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")

    if model is None:
        model = get_sentence_transformer()

    df = dataframe.copy()

    # filtro inicial para reduzir processamento
    df = df[df[col_conteudo].notna()]
    df = df[df[col_conteudo].astype(str).str.len() > 20]

    registros_por_data = defaultdict(list)

    tier_weight_map = {
        "Tier 1": 1.0,
        "Tier 2": 0.7,
        "Tier 3": 0.4,
        "Outros": 0.1
    }

    tier_order = {
        "Tier 1": 3,
        "Tier 2": 2,
        "Tier 3": 1,
        "Outros": 0
    }

    for _, row in df.iterrows():

        data_raw = safe_get(row, col_data)
        try:
            data_val = pd.to_datetime(data_raw).strftime("%Y-%m-%d")
        except Exception:
            data_val = safe_str(data_raw)

        titulo_val = safe_str(safe_get(row, col_titulo))
        fonte_val = safe_str(safe_get(row, col_fonte))
        conteudo_val = safe_get(row, col_conteudo)
        id_val = safe_get(row, col_id)

        if not conteudo_val:
            continue

        extraidas = select_phrases_with_terms(conteudo_val, list_search)
        if not extraidas:
            continue

        alcance_val = safe_float(safe_get(row, col_alcance))
        tier_val = safe_str(safe_get(row, col_tier))

        alcance_score = np.log1p(alcance_val) if alcance_val else 0
        tier_weight = tier_weight_map.get(tier_val, 0.3)

        frases = []

        for item in extraidas:
            frase = item["phrase"]
            termos = item["terms_found"]

            base_score = score_phrase_relevance(
                phrase=frase,
                terms_found=termos,
                title=titulo_val,
                source=fonte_val,
            )

            final_score = base_score * (1 + 0.15 * alcance_score) * (1 + tier_weight)

            frases.append({
                "texto": frase,
                "score_relevancia": round(final_score, 4)
            })

        if not frases:
            continue

        # reduz custo dos embeddings
        frases = sorted(
            frases,
            key=lambda x: x["score_relevancia"],
            reverse=True
        )[:max_frases_por_doc]

        frases_texto = [f["texto"] for f in frases]
        scores = [f["score_relevancia"] for f in frases]

        frases_filtradas_texto = remove_similares_embeddings(
            frases_texto,
            model=model,
            scores=scores
        )

        frases_filtradas = [
            f for f in frases
            if f["texto"] in frases_filtradas_texto
        ]

        if not frases_filtradas:
            continue

        frases_filtradas = sorted(
            frases_filtradas,
            key=lambda x: x["score_relevancia"],
            reverse=True
        )

        if usar_narrativa:
            texto_narrativo = construir_texto_narrativo(
                frases=frases_filtradas,
                model=model
            )
        else:
            texto_narrativo = " ".join(
                f["texto"] for f in frases_filtradas[:max_frases_saida]
            )

        doc_score = sum(f["score_relevancia"] for f in frases_filtradas)

        registros_por_data[data_val].append({
            "fonte": fonte_val,
            "titulo": titulo_val,
            "id publicacao": id_val,
            "alcance": alcance_val,
            "tier": tier_val,
            "tipos_de_impactos": safe_get(row, col_tipos_de_impactos),
            "sentimento": safe_str(safe_get(row, col_sentimento)),
            "protagonismo": safe_str(safe_get(row, col_protagonismo)),
            "empresa": safe_get(row, col_empresa),
            "produto": safe_get(row, col_produto),
            "jornalista": safe_get(row, col_jornalista),
            "url da notícia": safe_str(safe_get(row, col_url_noticia)),
            "Assuntos específicos": safe_get(row, col_assuntos_especificos),
            "Mídia": safe_str(safe_get(row, col_midia)),
            "texto": texto_narrativo,
            "doc_score": doc_score
        })

    resultado_final = {}

    for data_val, docs in registros_por_data.items():

        docs = sorted(
            docs,
            key=lambda x: (
                x.get("alcance", 0) or 0,
                tier_order.get(x.get("tier"), 0),
                x.get("doc_score", 0)
            ),
            reverse=True
        )

        resultado_final[data_val] = {
            "tema_dominante": docs[0]["texto"] if docs else None,
            "documentos": docs
        }

    return resultado_final

from collections import defaultdict
from typing import List
import pandas as pd
import numpy as np


def deduplicar_frases_simples(frases, min_chars=30):
    vistas = set()
    resultado = []

    for f in frases:
        texto = f["texto"].strip()
        chave = texto.lower()[:120]

        if len(texto) < min_chars:
            continue

        if chave not in vistas:
            vistas.add(chave)
            resultado.append(f)

    return resultado


def extrair_contexto_noticias_fast(
    dataframe: pd.DataFrame,
    list_search: List[str],

    col_data: str = "data",
    col_titulo: str = "titulo",
    col_fonte: str = "fonte",
    col_conteudo: str = "conteudo",
    col_id: str = "Chave Análise de Mídia Hash",

    col_alcance: str | None = "alcance",
    col_tier: str | None = "tier",
    col_tipos_de_impactos: str | None = "tipos_de_impactos",
    col_sentimento: str | None = "sentimento",
    col_protagonismo: str | None = "protagonismo",

    col_empresa: str | None = "Empresa analisada",
    col_produto: str | None = "Produto analisado",
    col_jornalista: str | None = "Jornalista",

    col_url_noticia: str | None = "url da notícia",
    col_assuntos_especificos: str | None = "Assuntos específicos",
    col_midia: str | None = "Mídia",

    max_frases_por_doc: int = 8,
    max_frases_saida: int = 4,
    min_chars_frase: int = 30,
):

    required_cols = [col_data, col_titulo, col_fonte, col_conteudo, col_id]
    missing = [c for c in required_cols if c not in dataframe.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")

    df = dataframe.copy()

    df = df[df[col_conteudo].notna()]
    df = df[df[col_conteudo].astype(str).str.len() > 20]

    df[col_data] = pd.to_datetime(df[col_data], errors="coerce").dt.strftime("%Y-%m-%d")
    df[col_data] = df[col_data].fillna("sem_data")

    registros_por_data = defaultdict(list)

    tier_weight_map = {
        "Tier 1": 1.0,
        "Tier 2": 0.7,
        "Tier 3": 0.4,
        "Outros": 0.1
    }

    tier_order = {
        "Tier 1": 3,
        "Tier 2": 2,
        "Tier 3": 1,
        "Outros": 0
    }

    cols_necessarias = [
        col_data, col_titulo, col_fonte, col_conteudo, col_id,
        col_alcance, col_tier, col_tipos_de_impactos, col_sentimento,
        col_protagonismo, col_empresa, col_produto, col_jornalista,
        col_url_noticia, col_assuntos_especificos, col_midia
    ]

    cols_necessarias = [c for c in cols_necessarias if c and c in df.columns]
    df = df[cols_necessarias]

    for row in df.to_dict("records"):

        data_val = row.get(col_data)
        titulo_val = safe_str(row.get(col_titulo))
        fonte_val = safe_str(row.get(col_fonte))
        conteudo_val = row.get(col_conteudo)
        id_val = row.get(col_id)

        if not conteudo_val:
            continue

        extraidas = select_phrases_with_terms(conteudo_val, list_search)
        if not extraidas:
            continue

        alcance_val = safe_float(row.get(col_alcance)) if col_alcance else 0
        tier_val = safe_str(row.get(col_tier)) if col_tier else ""

        alcance_score = np.log1p(alcance_val) if alcance_val else 0
        tier_weight = tier_weight_map.get(tier_val, 0.3)

        frases = []

        for item in extraidas:
            frase = item["phrase"]
            termos = item["terms_found"]

            if not frase or len(frase) < min_chars_frase:
                continue

            base_score = score_phrase_relevance(
                phrase=frase,
                terms_found=termos,
                title=titulo_val,
                source=fonte_val,
            )

            final_score = base_score * (1 + 0.15 * alcance_score) * (1 + tier_weight)

            frases.append({
                "texto": frase,
                "score_relevancia": round(final_score, 4)
            })

        if not frases:
            continue

        frases = sorted(
            frases,
            key=lambda x: x["score_relevancia"],
            reverse=True
        )[:max_frases_por_doc]

        frases_filtradas = deduplicar_frases_simples(
            frases,
            min_chars=min_chars_frase
        )

        if not frases_filtradas:
            continue

        texto_narrativo = " ".join(
            f["texto"] for f in frases_filtradas[:max_frases_saida]
        )

        doc_score = sum(f["score_relevancia"] for f in frases_filtradas)

        registros_por_data[data_val].append({
            "fonte": fonte_val,
            "titulo": titulo_val,
            "id publicacao": id_val,
            "alcance": alcance_val,
            "tier": tier_val,
            "tipos_de_impactos": row.get(col_tipos_de_impactos),
            "sentimento": safe_str(row.get(col_sentimento)),
            "protagonismo": safe_str(row.get(col_protagonismo)),
            "empresa": row.get(col_empresa),
            "produto": row.get(col_produto),
            "jornalista": row.get(col_jornalista),
            "url da notícia": safe_str(row.get(col_url_noticia)),
            "Assuntos específicos": row.get(col_assuntos_especificos),
            "Mídia": safe_str(row.get(col_midia)),
            "texto": texto_narrativo,
            "doc_score": doc_score
        })

    resultado_final = {}

    for data_val, docs in registros_por_data.items():

        docs = sorted(
            docs,
            key=lambda x: (
                x.get("alcance", 0) or 0,
                tier_order.get(x.get("tier"), 0),
                x.get("doc_score", 0)
            ),
            reverse=True
        )

        resultado_final[data_val] = {
            "tema_dominante": docs[0]["texto"] if docs else None,
            "documentos": docs
        }

    return resultado_final



def filter_dataframe_by_date(
    df: pd.DataFrame,
    date_col: str,
    start_date: str | None = None,
    end_date: str | None = None,
    date_format: str | None = None
) -> pd.DataFrame:
    """
    Filtra um DataFrame por intervalo de datas.

    Parâmetros:
    - df: DataFrame
    - date_col: nome da coluna de data
    - start_date: data inicial (inclusive)
    - end_date: data final (inclusive)
    - date_format: opcional (ex: "%d/%m/%Y")

    Retorna:
    - DataFrame filtrado
    """

    df = df.copy()

    # 🔥 Garantir que a coluna é datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(
            df[date_col],
            format=date_format,
            errors="coerce"
        )

    # 🚨 Dropa datas inválidas
    df = df.dropna(subset=[date_col])

    # 🔽 Aplica filtros
    if start_date:
        start_date = pd.to_datetime(start_date)
        df = df[df[date_col] >= start_date]

    if end_date:
        end_date = pd.to_datetime(end_date)
        df = df[df[date_col] <= end_date]

    return df

##########################
##########################

import re
import unicodedata
import hashlib
import pandas as pd


# =========================
# NORMALIZAÇÃO
# =========================
def normalize_text(text):
    """
    Remove acentos e deixa em lowercase.
    """
    if pd.isna(text):
        return ""
    text = str(text)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ASCII", "ignore").decode("utf-8")
    return text.lower()


# =========================
# SPLIT DATAFRAME LIST
# =========================
def splitdataframelist(df, target_column, separator="|"):
    """
    Divide os valores de uma coluna em múltiplas linhas.
    """
    def splitListToRows(row, row_accumulator, target_column, separator):
        valor = row[target_column]

        if pd.isna(valor) or valor == "" or valor == "None":
            new_row = row.to_dict()
            row_accumulator.append(new_row)
            return

        split_row = str(valor).split(separator)

        for s in split_row:
            s = s.strip()
            if s:
                new_row = row.to_dict()
                new_row[target_column] = s
                row_accumulator.append(new_row)

    new_rows = []
    df.apply(splitListToRows, axis=1, args=(new_rows, target_column, separator))
    new_df = pd.DataFrame(new_rows)
    return new_df


# =========================
# HASH
# =========================
def generate_row_hash(
    df: pd.DataFrame,
    columns: list,
    hash_col: str = "Chave Análise de Mídia Hash",
    sep: str = "||"
) -> pd.DataFrame:
    """
    Gera um hash SHA-256 baseado em múltiplas colunas do DataFrame.
    """
    df = df.copy()

    def _hash_row(row):
        normalized = [
            str(row[col]).strip().lower() if col in row and pd.notna(row[col]) else ""
            for col in columns
        ]
        joined = sep.join(normalized)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    df[hash_col] = df.apply(_hash_row, axis=1)
    return df


# =========================
# BUSCA DOS TERMOS
# =========================
def find_dict_keys_in_text(texto, search_dict):
    """
    Procura no texto os termos presentes no dicionário e retorna
    as KEYS encontradas, separadas por '|'.

    Exemplo de input:
    {
        'Banco Master': ['Banco Master', 'Master'],
        'Itaú': ['Itaú', 'Itaú Unibanco']
    }

    Retorno:
    'Banco Master|Itaú'
    """
    texto_norm = normalize_text(texto)

    keys_found = []

    for chave, termos in search_dict.items():
        # ordena por tamanho para priorizar expressões maiores
        termos_sorted = sorted(termos, key=lambda x: len(str(x).split()), reverse=True)

        encontrou = False
        for termo in termos_sorted:
            termo_norm = normalize_text(termo)
            pattern = r'\b' + re.escape(termo_norm) + r'\b'

            if re.search(pattern, texto_norm):
                encontrou = True
                break

        if encontrou:
            keys_found.append(chave)

    return "|".join(keys_found) if keys_found else "None"


# =========================
# FUNÇÃO PRINCIPAL
# =========================
def identify_entities_in_dataframe(
    df: pd.DataFrame,
    search_dict: dict,
    title_col: str = "titulo",
    content_col: str = "conteudo",
    output_col: str = "entidade_encontrada",
    split_output: bool = True,
    hash_columns: list = None
) -> pd.DataFrame:
    """
    Procura termos nas colunas de título e conteúdo, retorna a KEY do dicionário,
    faz split em múltiplas linhas e gera nova 'Chave Análise de Mídia Hash'.

    Parâmetros
    ----------
    df : pd.DataFrame
    search_dict : dict
        Exemplo:
        {
            'Banco Master': ['Banco Master', 'Master'],
            'Itaú': ['Itaú', 'Itaú Unibanco']
        }
    title_col : str
        Nome da coluna de título
    content_col : str
        Nome da coluna de conteúdo
    output_col : str
        Nome da coluna com as entidades encontradas
    split_output : bool
        Se True, divide múltiplas entidades em várias linhas
    hash_columns : list
        Colunas usadas para gerar o hash final.
        Se None, usa automaticamente [title_col, content_col, output_col]

    Retorno
    -------
    pd.DataFrame
    """
    df = df.copy()

    # garante que as colunas existam
    if title_col not in df.columns:
        df[title_col] = ""
    if content_col not in df.columns:
        df[content_col] = ""

    # concatena título + conteúdo para busca
    df["_texto_busca"] = (
        df[title_col].fillna("").astype(str) + " " +
        df[content_col].fillna("").astype(str)
    )

    # identifica as keys encontradas
    df[output_col] = df["_texto_busca"].apply(
        lambda x: find_dict_keys_in_text(x, search_dict)
    )

    # remove coluna auxiliar
    df = df.drop(columns=["_texto_busca"])

    # faz split em linhas
    if split_output:
        df = splitdataframelist(df, target_column=output_col, separator="|")

    # define colunas do hash
    if hash_columns is None:
        hash_columns = [title_col, content_col, output_col]

    # gera hash
    df = generate_row_hash(
        df=df,
        columns=hash_columns,
        hash_col='Chave Análise de Mídia Hash'

    )

    return df