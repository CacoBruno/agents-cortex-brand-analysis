import pandas as pd
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def stats_freq(dataframe: pd.DataFrame, column_value: str):
    
    serie = dataframe[column_value].dropna()

    n = len(serie)
    
    mean = serie.sum() / n
    
    std_dv = math.sqrt(
        sum((i - mean) ** 2 for i in serie) / n
    )
    
    coef_variation = std_dv / mean if mean != 0 else None

    return {
        'mean': mean,
        'std_dv': std_dv,
        'coef_variation': coef_variation
    }

def z_score(value, mean, std_dv):
    
    return ((value - mean) / std_dv)


def splitdataframelist(df,target_column,separator):
    ''' df = dataframe to split,
    target_column = the column containing the values to split
    separator = the symbol used to perform the split
    returns: a dataframe with each entry for the target column separated, with each element moved into a new row. 
    The values in the other columns are duplicated across the newly divided rows.
    '''
    def splitListToRows(row,row_accumulator,target_column,separator):
        split_row = row[target_column].split(separator)
        for s in split_row:
            new_row = row.to_dict()
            new_row[target_column] = s
            row_accumulator.append(new_row)
    new_rows = []
    df.apply(splitListToRows,axis=1,args = (new_rows,target_column,separator))
    new_df = pd.DataFrame(new_rows)
    return new_df

import re
import unicodedata


def normalize_text(text):
    # remove acento + lowercase
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ASCII", "ignore").decode("utf-8")
    return text.lower()



def is_in_text(texto, list_search):
    texto_norm = normalize_text(texto)

    # ordena por tamanho (trigram > bigram > unigram)
    list_search_sorted = sorted(list_search, key=lambda x: len(x.split()), reverse=True)

    palavras_encontradas = []

    for termo in list_search_sorted:
        termo_norm = normalize_text(termo)
        pattern = r'\b' + re.escape(termo_norm) + r'\b'

        if re.search(pattern, texto_norm):
            palavras_encontradas.append(termo)

    return '|'.join(palavras_encontradas) if palavras_encontradas else "None"


def split_sentences(text: str) -> list[str]:
    return re.split(r'(?<=[.!?])\s+', text.strip())


def select_phrases_with_terms(text: str, list_search: list[str]) -> list[dict]:
    phrases = split_sentences(text)
    search_terms = [(term, normalize_text(term)) for term in list_search]

    results = []

    for phrase in phrases:
        phrase_norm = normalize_text(phrase)
        found_terms = []

        for original_term, norm_term in search_terms:
            pattern = r'\b' + re.escape(norm_term) + r'\b'
            if re.search(pattern, phrase_norm):
                found_terms.append(original_term)

        if found_terms:
            results.append({
                "phrase": phrase,
                "terms_found": found_terms
            })

    return results


def remove_similares(frases_list):
        # Remove frases vazias ou inválidas
        frases_list = [frase for frase in frases_list if frase.strip()]

        # Verifica se há frases restantes após o filtro
        if not frases_list:
            return []  # Retorna lista vazia se não houver frases válidas

        # Cria uma matriz de similaridade de texto
        tfidf_vectorizer = TfidfVectorizer().fit_transform(frases_list)
        cosine_sim = cosine_similarity(tfidf_vectorizer)

        # Mantém apenas uma frase de cada grupo de frases similares
        unique_frases = []
        indices_to_remove = set()

        for i in range(len(frases_list)):
            if i not in indices_to_remove:
                unique_frases.append(frases_list[i])
                for j in range(i + 1, len(frases_list)):
                    if cosine_sim[i, j] > 0.8:  # Define o limite de similaridade
                        indices_to_remove.add(j)
            # Limita o número de frases a 5
            if len(unique_frases) >= 5:
                break
        return unique_frases



