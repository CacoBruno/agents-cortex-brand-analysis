import pandas as pd
from services.pr.text_treatment import text_processing
from services.pr.sentiment_analysis import CortexLexicon as SentimentAnalysis
from services.pr.protagonism.Protagonism import Protagonism
from services.ia_funtions.clustering_functions import daily_cluster_similaridade_parallel


import warnings
from tqdm import tqdm
tqdm.pandas()

#### Options ####
pd.options.display.max_rows = 999
pd.set_option('max_colwidth', 1000)
warnings.filterwarnings("ignore")

#####################################
# SENTIMENT
#####################################

def sentimentTag(positive_score):
    if positive_score > 0.55:
        return 'Positivo'
    
    elif positive_score >= 0.45 and positive_score <=0.55:
        return 'Neutro'
    
    elif positive_score < 0.45:
        return 'Negativo'

def sentimentClassification(dataframe: pd.DataFrame) -> pd.DataFrame:
   
    """
   dataframe_id : é o id do dataframe retornado das tools 
   que fazem download da plataforma: export_media_analysis_database_tool, export_publications_database_tool, get_prdata_dataframe_tool

    """
        
    if 'Título' in dataframe.columns:
        column_title_name = 'Título'

    if 'Conteúdo' in dataframe.columns:     
        column_content_name = 'Conteúdo'

    if 'titulo_da_publicacao' in dataframe.columns:
       column_title_name = 'titulo_da_publicacao'

    if 'conteudo' in dataframe.columns:
      column_content_name = 'conteudo'    

    sentiment_cleaning_tasks = ['lower', 'html', 'punctuation', 'length_1', 'digits']
    dataframe[column_title_name] = dataframe[column_title_name].fillna(' ')
    dataframe[column_content_name] = dataframe[column_content_name].fillna(' ')

    dataframe[column_title_name] = dataframe[column_title_name].apply(str)
    dataframe[column_content_name] = dataframe[column_content_name].apply(str)

    dataframe['aggregated_text'] = dataframe[[column_title_name, column_content_name]].agg('-'.join, axis=1)
    dataframe['aggregated_text'] = dataframe['aggregated_text'].apply(str)
    dataframe.loc[:, 'clean_text'] = dataframe['aggregated_text'].apply(lambda x:text_processing.clean_text(x, 'pt', cleaning_tasks=sentiment_cleaning_tasks))

    sentiment_analyser = SentimentAnalysis.CortexLexicon(extra_terms=[])
    positivo_list = []
    negativo_list = []  
    for sentence in tqdm(dataframe['clean_text']):    
        try:
            negativo, positivo = sentiment_analyser(sentence)     
            positivo_list.append(positivo)
            negativo_list.append(negativo)
        except:
            positivo_list.append(0)
            negativo_list.append(0)    

    dataframe.loc[:, 'perc_positive'] = positivo_list
    dataframe.loc[:, 'perc_negative'] = negativo_list

    # Formatt Percentual
    dataframe["perc_positive"] = dataframe["perc_positive"].round(2)
    dataframe["perc_negative"] = dataframe["perc_negative"].round(2)
    dataframe['Sentimento'] = dataframe["perc_positive"].progress_apply(sentimentTag)

    
    return dataframe


#################################
# PROTAGONISM
#################################

def _to_list(x):
    """Garante que x seja lista; None → [], escalar → [esc], lista → lista."""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def mapping_names(code_protagonism):
    """ Maps names and description according to generated protagonism code

    Args:
        am_df (Pandas dataframe]): Dataframe with classified data

    Returns:
        [Pandas dataframe]: Dataframe with new columns:Descrição do Protagonismo and Protagonismo Automático
    """
    protagonism_map = {
        'A': 'Protagonismo',
        'B': 'Protagonismo',
        'C': 'Citação relevante',
        'D': 'Figurante',
        'E': 'Protagonismo',
        'F': 'Citação relevante',
        'G': 'Citação relevante',
        'H': 'Figurante',
        'I': 'Protagonismo',
        'J': 'Citação relevante',
        'K': 'Citação relevante',
        'L': 'Figurante',
        'M': 'Protagonismo',
        'Revisar': 'Revisar',
        '-': '-'
    }

    return protagonism_map[code_protagonism]


def criar_protagonismo(brand):
    return {
        brand: {
            brand: brand,
            brand.split()[0]: brand
        }
    }

# Usando compreensão de lista para aplicar a função em cada item da lista

def transformar_lista_para_dicionario(lista_de_dicionarios):
    resultado = {}
    for item in lista_de_dicionarios:
        for chave, valor in item.items():
            resultado[chave] = valor
    return resultado

def protagonism_to_dict(list_search):
    resultados = [criar_protagonismo(brand) for brand in list_search]

    return transformar_lista_para_dicionario(resultados)
protagonism_cleaning_tasks = ['lower', 'html', 'punctuation']

def protagonismClassification(dataframe: pd.DataFrame, lista_marca: list) -> pd.DataFrame: 

    """
   dataframe_id : é o id do dataframe retornado das tools 
   que fazem download da plataforma: export_media_analysis_database_tool, export_publications_database_tool, get_prdata_dataframe_tool
   lista_marca: é a lista de nome das marcas para serem ['Americanas', 'Lojas Americanas'] 

    """
    lista_marca = _to_list(lista_marca)
        
    if 'Título' in dataframe.columns:
        column_title_name = 'Título'

    if 'Conteúdo' in dataframe.columns:     
        column_content_name = 'Conteúdo'

    if 'titulo_da_publicacao' in dataframe.columns:
      column_title_name = 'titulo_da_publicacao'

    if 'conteudo' in dataframe.columns:
      column_content_name = 'conteudo'    

    brand = lista_marca[0]
    print('list search:', lista_marca)
    protagonism = protagonism_to_dict(lista_marca)
    print(protagonism)

    pt = Protagonism(protagonism, [])

    dataframe['protagonism_code'] = dataframe.apply(lambda x : pt.run_protagonism(brand, x[column_title_name], x[column_content_name]), axis=1)
    dataframe['Nível de Protagonismo final'] = dataframe['protagonism_code'].apply(lambda x : mapping_names(x) )

    return dataframe


#################################
# CLUSTERING
#################################

import re
import unicodedata
import pandas as pd


def clusteringClassification(
    dataframe: pd.DataFrame,
    focus_terms: list[str] | None = None,
) -> pd.DataFrame:
    """
    Faz o pré-processamento textual e executa o clustering.

    Parâmetros
    ----------
    dataframe : pd.DataFrame
        DataFrame de entrada com colunas de título, conteúdo e data.
    focus_terms : list[str] | None, default=None
        Lista opcional de termos de foco para selecionar apenas os trechos
        do texto que mencionam esses termos dentro de `clean_text`.

        Exemplo:
        ["Itau", "Itaú Unibanco"]

        Regras:
        - se for None, usa o clean_text completo
        - se os termos forem encontrados, usa apenas os trechos/frases com esses termos
        - se os termos não forem encontrados, retorna o clean_text normal
    """

    df = dataframe.copy()

    # =========================
    # Helpers
    # =========================
    def _normalize_text(text: str) -> str:
        """Normaliza texto para comparação: lower + remoção de acentos + strip."""
        if pd.isna(text):
            return ""
        text = str(text).lower().strip()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        return text

    def _extract_focus_context(clean_text: str, terms: list[str] | None) -> str:
        """
        Retorna apenas os trechos do texto que contenham os termos de foco.
        Se não encontrar nada, retorna o texto original.
        """
        if not clean_text or not terms:
            return clean_text

        normalized_text = _normalize_text(clean_text)
        normalized_terms = [
            _normalize_text(term) for term in terms
            if term is not None and str(term).strip()
        ]

        if not normalized_terms:
            return clean_text

        # Divide em sentenças / blocos simples
        raw_parts = re.split(r"[.!?;\n]+", str(clean_text))
        selected_parts = []

        for part in raw_parts:
            part_strip = part.strip()
            if not part_strip:
                continue

            normalized_part = _normalize_text(part_strip)

            if any(term in normalized_part for term in normalized_terms):
                selected_parts.append(part_strip)

        # Se encontrou trechos com os termos, retorna só eles
        if selected_parts:
            return " . ".join(selected_parts)

        # Se não encontrou nada, retorna o texto original
        return clean_text

    # =========================
    # Detecta coluna de data
    # =========================
    date_columns = None

    if "Data" in df.columns:
        date_columns = "Data"
    elif "data_da_publicacao" in df.columns:
        date_columns = "data_da_publicacao"
    else:
        raise ValueError("Nenhuma coluna de data encontrada. Esperado: 'Data' ou 'data_da_publicacao'.")

    start_date = df[date_columns].min()
    end_date = df[date_columns].max()

    # =========================
    # Ajusta colunas numéricas
    # =========================
    if "Alcance orgânico" in df.columns:
        if df["Alcance orgânico"].dtype != "float64":
            df["Alcance orgânico"] = df["Alcance orgânico"].apply(
                lambda x: float(str(x).replace("-", "0").replace(",", "."))
            )

    if "alcance_organico_normalizado" in df.columns:
        if df["alcance_organico_normalizado"].dtype != "float64":
            df["alcance_organico_normalizado"] = df["alcance_organico_normalizado"].apply(
                lambda x: float(str(x).replace("-", "0").replace(",", "."))
            )

    # =========================
    # Detecta colunas de texto
    # =========================
    column_title_name = None
    column_content_name = None

    if "Título" in df.columns:
        column_title_name = "Título"
    elif "titulo_da_publicacao" in df.columns:
        column_title_name = "titulo_da_publicacao"
    else:
        raise ValueError("Nenhuma coluna de título encontrada. Esperado: 'Título' ou 'titulo_da_publicacao'.")

    if "Conteúdo" in df.columns:
        column_content_name = "Conteúdo"
    elif "conteudo" in df.columns:
        column_content_name = "conteudo"
    else:
        raise ValueError("Nenhuma coluna de conteúdo encontrada. Esperado: 'Conteúdo' ou 'conteudo'.")

    # =========================
    # Gera clean_text se não existir
    # =========================
    if "clean_text" not in df.columns:
        sentiment_cleaning_tasks = ["lower", "html", "punctuation", "length_1", "digits"]

        df["aggregated_text"] = (
            df[[column_title_name, column_content_name]]
            .fillna("")
            .astype(str)
            .agg(" - ".join, axis=1)
        )

        df.loc[:, "clean_text"] = df["aggregated_text"].apply(
            lambda x: text_processing.clean_text(
                x,
                "pt",
                cleaning_tasks=sentiment_cleaning_tasks
            )
        )

    # =========================
    # Aplica filtro por termos de foco
    # =========================
    # Se focus_terms=None -> usa clean_text normal
    # Se houver termos e encontrar no texto -> usa apenas trechos focados
    # Se não encontrar -> mantém clean_text normal
    if focus_terms is not None:
        df["clean_text_focus"] = df["clean_text"].apply(
            lambda x: _extract_focus_context(x, focus_terms)
        )
        column_to_cluster = "clean_text_focus"
    else:
        column_to_cluster = "clean_text"

    # =========================
    # Clustering
    # =========================
    df_clustering = daily_cluster_similaridade_parallel(
        df=df,
        start_date=start_date,
        end_date=end_date,
        date_col=date_columns,
        column_to_cluster=column_to_cluster,
        time_delta=1,
        add_window_cols=True,
        nested_as_json=True,
        max_workers=4,
        embedding_workers=8,
    )

    return df_clustering