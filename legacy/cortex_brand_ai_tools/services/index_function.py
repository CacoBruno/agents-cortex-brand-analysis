import pandas as pd
import hashlib
from datetime import date, timedelta
import math
pd.options.display.float_format = '{:.0f}'.format
### funções auxiliares

def generate_row_hash(
    df: pd.DataFrame,
    columns: list,
    hash_col: str = "hash_id",
    sep: str = "||"
) -> pd.DataFrame:
    """
    Gera um hash SHA-256 baseado em múltiplas colunas do DataFrame.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame de entrada
    columns : list
        Lista de colunas usadas para gerar o hash
    hash_col : str
        Nome da coluna de hash gerada
    sep : str
        Separador usado na concatenação

    Retorna
    -------
    pd.DataFrame
        DataFrame com a coluna de hash adicionada
    """

    def _hash_row(row):
        normalized = [
            str(row[col]).strip().lower() if pd.notna(row[col]) else ""
            for col in columns
        ]
        joined = sep.join(normalized)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    df[hash_col] = df.apply(_hash_row, axis=1)
    return df


map_mes = {
    1 : 'Jan',
    2 : 'Fev',
    3 : 'Mar',
    4 : 'Abr',
    5 : 'Mai',
    6 : 'Jun',
    7 : 'Jul',
    8 : 'Ago',
    9 : 'Set',
    10 : 'Out',
    11 : 'Nov', 
    12 : 'Dez'
}

map_mes_low = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr",
    5: "mai", 6: "jun", 7: "jul", 8: "ago",
    9: "set", 10: "out", 11: "nov", 12: "dez"
}

map_mes_days = {
    1 : 31,
    2 : 28,
    3 : 31,
    4 : 30,
    5 : 31,
    6 : 30,
    7 : 31,
    8 : 31,
    9 : 30,
    10 : 31,
    11 : 30, 
    12 : 31
}

import pandas as pd

def marcar_semanas_retroativas(
    df: pd.DataFrame,
    col_data: str = "Data",
    data_ancora: str = "2026-01-04"
):
    """
    Marca todas as datas em semanas retroativas de 7 dias
    ancoradas em uma data final.

    Ex:
      Âncora: 2026-01-06
      Semanas:
        31/12-06/01
        24/12-30/12
        17/12-23/12
        ...

    Retorna:
      - semana_index (0, 1, 2, ...)
      - semana_label (DD/MM-DD/MM)
    """
    out = df.copy()

    out[col_data] = pd.to_datetime(out[col_data], errors="coerce")
    ancora = pd.to_datetime(data_ancora)

    # diferença em dias (datas futuras ficam negativas)
    delta_dias = (ancora - out[col_data]).dt.days

    # índice da semana retroativa
    out["semana_index"] = delta_dias // 7

    # início e fim da semana correspondente
    out["semana_fim"] = ancora - pd.to_timedelta(out["semana_index"] * 7, unit="D")
    out["semana_inicio"] = out["semana_fim"] - pd.Timedelta(days=6)

    # label final
    out["semana"] = (
        out["semana_inicio"].dt.strftime("%d/%m")
        + " a "
        + out["semana_fim"].dt.strftime("%d/%m")
    )

    # opcional: remover colunas auxiliares
    out = out.drop(columns=["semana_inicio", "semana_fim"])

    return out



def is_jornalist(jornalista):
    list_not_jornalista = ['não mapeado', '-', 'redação']
    jornalista_lower = jornalista.lower()

    if any(l.lower() in jornalista_lower for l in list_not_jornalista):
        return None
    else: 
        return 'é jornalista'
    
def is_action_count(action):
    list_not_action = ['outros', '-']
    action_lower = action.lower()

    if any(l.lower() in action_lower for l in list_not_action):
        return None
    else: 
        return 'é ação'
    


def is_action(action):
    list_not_action = ['outros', '-']
    action_lower = action.lower()

    if any(l.lower() in action_lower for l in list_not_action):
        return 'sem ação'
    else: 
        return 'ação'  


def impact_types(sentiment: str, protagonism:str ):
    '''
    retorna "Promotores" "Inócuos" "Detratores"
    '''

    if sentiment == "Positivo" and (protagonism == "Protagonismo" or protagonism == "Citação relevante"):
        return "Promotores" 
    
    elif sentiment == "Negativo" and (protagonism == "Protagonismo" or protagonism == "Citação relevante"):
        return "Detratores" 

    if sentiment == "Positivo" and protagonism == "Figurante":
        return "Inócuos" 
    
    elif sentiment == "Negativo" and protagonism == "Figurante":
        return "Inócuos" 

    elif sentiment == "Neutro":
        return "Inócuos" 
    
    else:
        return 'Outros'    

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

from datetime import datetime

# =========================
# MES INDEX
# =========================

import pandas as pd
from datetime import date, timedelta

import pandas as pd
from datetime import date, timedelta


def add_semestre_index(
    df: pd.DataFrame,
    date_col: str
) -> pd.DataFrame:
    """
    Cria:
    - semestre (label: S1/2026)
    - semestre_index (0 = semestre mais recente)
    - semestre_corrente_flag
    - semestre_fechado_flag
    - semestre_status
    """

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    if df[date_col].dropna().empty:
        df["semestre"] = pd.NA
        df["semestre_index"] = pd.NA
        df["semestre_corrente_flag"] = pd.NA
        df["semestre_fechado_flag"] = pd.NA
        df["semestre_status"] = pd.NA
        return df

    # -------------------------
    # definição do semestre
    # -------------------------
    df["ano"] = df[date_col].dt.year
    df["mes_num"] = df[date_col].dt.month

    df["semestre_num"] = df["mes_num"].apply(lambda x: 1 if x <= 6 else 2)
    df["semestre"] = "S" + df["semestre_num"].astype(str) + "/" + df["ano"].astype(str)

    # -------------------------
    # referência (último semestre do DF)
    # -------------------------
    last_date = df[date_col].max()
    last_year = last_date.year
    last_sem = 1 if last_date.month <= 6 else 2

    # -------------------------
    # cálculo do índice
    # -------------------------
    df["semestre_index"] = (
        (last_year - df["ano"]) * 2 +
        (last_sem - df["semestre_num"])
    )

    # -------------------------
    # flags de status
    # -------------------------
    hoje = pd.Timestamp.today()
    ano_atual = hoje.year
    sem_atual = 1 if hoje.month <= 6 else 2

    df["semestre_corrente_flag"] = (
        (df["ano"] == ano_atual) &
        (df["semestre_num"] == sem_atual)
    )

    df["semestre_fechado_flag"] = (
        (df["ano"] < ano_atual) |
        (
            (df["ano"] == ano_atual) &
            (df["semestre_num"] < sem_atual)
        )
    )

    df["semestre_status"] = "semestre_aberto"
    df.loc[df["semestre_corrente_flag"], "semestre_status"] = "semestre_corrente"
    df.loc[df["semestre_fechado_flag"], "semestre_status"] = "semestre_fechado"

    return df

def add_mes_index(
    df: pd.DataFrame,
    col_mes: str = "_mes_ordem"
) -> pd.DataFrame:
    """
    Cria coluna mes_index usando como referência o ÚLTIMO mês presente no dataframe.

    Regras:
        0 = último mês existente no dataframe
        1, 2, ... = meses anteriores
        -1, -2, ... = meses posteriores

    Também adiciona:
        - mes_status
        - mes_corrente_flag
        - mes_fechado_flag
    """
    df = df.copy()

    df[col_mes] = pd.to_datetime(df[col_mes], errors="coerce")
    df[col_mes] = df[col_mes].dt.to_period("M").dt.to_timestamp()

    if df[col_mes].dropna().empty:
        df["mes_index"] = pd.NA
        df["mes_status"] = pd.NA
        df["mes_corrente_flag"] = pd.NA
        df["mes_fechado_flag"] = pd.NA
        return df

    ref_date = df[col_mes].max()

    df["mes_index"] = (
        (ref_date.year - df[col_mes].dt.year) * 12 +
        (ref_date.month - df[col_mes].dt.month)
    )

    hoje = pd.Timestamp.today().normalize()
    mes_corrente_real = hoje.to_period("M").to_timestamp()

    df["mes_corrente_flag"] = df[col_mes].eq(mes_corrente_real)
    df["mes_fechado_flag"] = df[col_mes] < mes_corrente_real

    df["mes_status"] = df["mes_corrente_flag"].map(
        {True: "mes_corrente", False: "mes_fechado"}
    )

    return df


def add_day_year_index(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Cria:
    - dia_index: último dia do dataframe = 0
    - ano_index: último ano do dataframe = 0
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    if df[date_col].dropna().empty:
        df["dia_index"] = pd.NA
        df["ano_index"] = pd.NA
        return df

    last_date = df[date_col].max().normalize()
    current_dates = df[date_col].dt.normalize()
    df["dia_index"] = (last_date - current_dates).dt.days

    last_year = last_date.year
    df["ano_index"] = last_year - df[date_col].dt.year

    return df


def _get_week_start(dt_series: pd.Series) -> pd.Series:
    """
    Retorna o início da semana (segunda-feira) para uma série de datas.
    """
    return dt_series - pd.to_timedelta(dt_series.dt.weekday, unit="D")


def add_week_index_and_status(
    df: pd.DataFrame,
    date_col: str,
    data_ancora_semana: str | None = None
) -> pd.DataFrame:
    """
    Cria semana_index.

    Regra da referência:
    - se data_ancora_semana for informada, ela SOBREPÕE a referência automática
      e passa a ser o ÚLTIMO dia da semana
    - se data_ancora_semana for None, usa a última data presente no dataframe
      como ÚLTIMO dia da semana de referência

    Adiciona:
        - semana_inicio
        - semana_fim
        - semana
        - semana_index
        - semana_corrente_flag
        - semana_fechada_flag
        - semana_status

    Formato da coluna semana:
        03/04 a 09/04/26
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    if df[date_col].dropna().empty:
        cols = [
            "semana_inicio", "semana_fim", "semana",
            "semana_index", "semana_corrente_flag",
            "semana_fechada_flag", "semana_status"
        ]
        for c in cols:
            df[c] = pd.NA
        return df

    datas = df[date_col].dt.normalize()

    # =========================
    # referência da semana (fim da semana)
    # =========================
    if data_ancora_semana is not None:
        ref_week_end = pd.to_datetime(data_ancora_semana, errors="coerce")
        if pd.isna(ref_week_end):
            raise ValueError("data_ancora_semana inválida.")
        ref_week_end = ref_week_end.normalize()
    else:
        ref_week_end = datas.max()

    # =========================
    # semana_index baseado no fim da semana
    # cada bloco de 7 dias pertence à mesma semana
    # =========================
    diff_days = (ref_week_end - datas).dt.days
    df["semana_index"] = (diff_days // 7).astype("Int64")

    # =========================
    # início/fim da semana de cada linha
    # =========================
    df["semana_fim"] = ref_week_end - pd.to_timedelta(df["semana_index"] * 7, unit="D")
    df["semana_inicio"] = df["semana_fim"] - pd.Timedelta(days=6)

    df["semana"] = (
        df["semana_inicio"].dt.strftime("%d/%m")
        + " a "
        + df["semana_fim"].dt.strftime("%d/%m/%y")
    )

    # =========================
    # semana corrente real
    # usa a mesma lógica: janela de 7 dias terminando hoje
    # =========================
    hoje = pd.Timestamp.today().normalize()
    semana_corrente_fim = hoje
    semana_corrente_inicio = hoje - pd.Timedelta(days=6)

    df["semana_corrente_flag"] = (
        df["semana_inicio"].eq(semana_corrente_inicio)
        & df["semana_fim"].eq(semana_corrente_fim)
    )

    df["semana_fechada_flag"] = df["semana_fim"] < hoje

    df["semana_status"] = "semana_aberta"
    df.loc[df["semana_corrente_flag"], "semana_status"] = "semana_corrente"
    df.loc[df["semana_fechada_flag"], "semana_status"] = "semana_fechada"

    return df


def add_trimestre_index(
    df: pd.DataFrame,
    date_col: str
) -> pd.DataFrame:
    """
    Cria:
    - trimestre: T1/2026
    - trimestre_num
    - trimestre_index: 0 = trimestre mais recente do dataframe
    - trimestre_corrente_flag
    - trimestre_fechado_flag
    - trimestre_status
    """

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    if df[date_col].dropna().empty:
        df["trimestre"] = pd.NA
        df["trimestre_num"] = pd.NA
        df["trimestre_index"] = pd.NA
        df["trimestre_corrente_flag"] = pd.NA
        df["trimestre_fechado_flag"] = pd.NA
        df["trimestre_status"] = pd.NA
        return df

    df["ano"] = df[date_col].dt.year
    df["mes_num"] = df[date_col].dt.month

    # T1 = Jan-Mar | T2 = Abr-Jun | T3 = Jul-Set | T4 = Out-Dez
    df["trimestre_num"] = ((df["mes_num"] - 1) // 3) + 1
    df["trimestre"] = "T" + df["trimestre_num"].astype(str) + "/" + df["ano"].astype(str)

    # referência: último trimestre presente no dataframe
    last_date = df[date_col].max()
    last_year = last_date.year
    last_tri = ((last_date.month - 1) // 3) + 1

    df["trimestre_index"] = (
        (last_year - df["ano"]) * 4 +
        (last_tri - df["trimestre_num"])
    ).astype("Int64")

    # status em relação ao trimestre real atual
    hoje = pd.Timestamp.today()
    ano_atual = hoje.year
    tri_atual = ((hoje.month - 1) // 3) + 1

    df["trimestre_corrente_flag"] = (
        (df["ano"] == ano_atual) &
        (df["trimestre_num"] == tri_atual)
    )

    df["trimestre_fechado_flag"] = (
        (df["ano"] < ano_atual) |
        (
            (df["ano"] == ano_atual) &
            (df["trimestre_num"] < tri_atual)
        )
    )

    df["trimestre_status"] = "trimestre_aberto"
    df.loc[df["trimestre_corrente_flag"], "trimestre_status"] = "trimestre_corrente"
    df.loc[df["trimestre_fechado_flag"], "trimestre_status"] = "trimestre_fechado"

    return df

import numpy as np

def add_tipos_de_impactos_vectorized(df):
    if "Tipos de impactos" in df.columns:
        return df

    required = ["Sentimento", "Nível de Protagonismo final"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise TypeError(f"Precisa ser uma base classificada! Colunas ausentes: {missing}")

    sent = df["Sentimento"].astype(str).str.lower().str.strip()
    prot = df["Nível de Protagonismo final"].astype(str).str.lower().str.strip()

    cond_promotor = (
        sent.isin(["positivo", "positiva", "promotor", "promotores"])
        & prot.ne("não representa")
    )

    cond_detrator = (
        sent.isin(["negativo", "negativa", "detrator", "detratores"])
        & prot.ne("não representa")
    )

    df["Tipos de impactos"] = np.select(
        [cond_promotor, cond_detrator],
        ["Promotores", "Detratores"],
        default="Inócuos"
    )

    return df


############ funções principais

### gerando as dataviews

def gen_dataviews(
    dataframe: pd.DataFrame,
    data_ancora_semana: str | None = None,
) -> pd.DataFrame:
    """
    input: pd.DataFrame
    data_ancora_semana:
        - se informada, sobrepõe a referência automática do semana_index
        - se None, usa a última semana do dataframe
    output: Dataview (dataframe)
    """

    dataframe = dataframe.copy()

    # =========================
    # checagens iniciais
    # =========================
    if {'cortex_id', 'Chave Análise de Mídia Hash'}.issubset(dataframe.columns):
        dataframe = dataframe.drop(columns=['Chave Análise de Mídia Hash'], errors='ignore')

    if {'ID Cortex', 'Chave Análise de Mídia Hash'}.issubset(dataframe.columns):
        dataframe = dataframe.drop(columns=['Chave Análise de Mídia Hash'], errors='ignore')

    dataframe = add_tipos_de_impactos_vectorized(dataframe)

    # =========================
    # coluna de data
    # =========================
    date_columns = None
    if "data_da_publicacao" in dataframe.columns:
        date_columns = "data_da_publicacao"
    if "Data" in dataframe.columns:
        date_columns = "Data"

    if date_columns is None:
        raise ValueError("Nenhuma coluna de data encontrada. Esperado: 'Data' ou 'data_da_publicacao'.")

    # =========================
    # checagem de IDs
    # =========================
    id_columns = None
    if 'Chave Análise de Mídia Hash' in dataframe.columns:
        id_columns = 'Chave Análise de Mídia Hash'
    if 'ID Cortex' in dataframe.columns:
        id_columns = 'ID Cortex'
    if 'cortex_id' in dataframe.columns:
        id_columns = 'cortex_id'

    if id_columns is None:
        raise ValueError("Nenhuma coluna de ID encontrada.")

    # =========================
    # checagem de alcance
    # =========================
    alcance_columns = None
    if "alcance_organico_normalizado" in dataframe.columns:
        alcance_columns = "alcance_organico_normalizado"
    if "Alcance orgânico" in dataframe.columns:
        alcance_columns = "Alcance orgânico"

    if alcance_columns is None:
        raise ValueError("Nenhuma coluna de alcance encontrada.")

    if not pd.api.types.is_numeric_dtype(dataframe[alcance_columns]):
        dataframe[alcance_columns] = dataframe[alcance_columns].apply(
            lambda x: float(str(x).replace('-', '0').replace(',', '.'))
        )

    # =========================
    # checagem de valoração
    # =========================
    valoracao_columns = None
    if "Valoração" in dataframe.columns:
        valoracao_columns = "Valoração"
    if "valoracao" in dataframe.columns:
        valoracao_columns = "valoracao"

    if valoracao_columns is None:
        dataframe['valoracao'] = 0
        valoracao_columns = "valoracao"

    if not pd.api.types.is_numeric_dtype(dataframe[valoracao_columns]):
        dataframe[valoracao_columns] = dataframe[valoracao_columns].apply(
            lambda x: float(str(x).replace('-', '0').replace(',', '.'))
        )

    # =========================
    # colunas auxiliares
    # =========================

    if "Jornalista" in dataframe.columns:
        jornalista = dataframe["Jornalista"].fillna("").astype(str).str.lower().str.strip()

        mask_not_jornalista = (
            jornalista.eq("")
            | jornalista.str.contains("não mapeado", regex=False)
            | jornalista.str.contains("-", regex=False)
            | jornalista.str.contains("redação", regex=False)
        )

        dataframe["Jornalista count"] = np.where(mask_not_jornalista, None, 1)
    else:
        dataframe["Jornalista count"] = 0


    if 'Ação' in dataframe.columns:
        dataframe['Ação total'] = dataframe['Ação'].apply(lambda x: is_action_count(x))
        dataframe['É ação'] = dataframe['Ação'].apply(lambda x: is_action(x))
    else:
        dataframe['Ação total'] = 0
        dataframe['É ação'] = 'sem ação'

    # =========================
    # colunas fixas por tipo de base
    # =========================
    columns_fix = []
    columns_themes = []

    if 'Chave Análise de Mídia Hash' in dataframe.columns:
        columns_fix = [
            'Data', 'Tipos de impactos', 'Sentimento', 'Empresa analisada',
            'Produto analisado', 'Nível de Protagonismo final', 'Tier',
            "Cidade (MSS)", "Estado (MSS)", "País (MSS)",
            'Jornalista', 'Fonte', 'Mídia', 'Ação', 'Tipo da ação',
            'É ação', 'Status classificação'
        ]

        columns_themes = [
            "Macro assunto", "Macro-assunto", "Temas", "Mensagem-chave", "Tags",
            "Pilar", "Sub-pilar", "Subpilar (Crise)", "Subpilar (Geral)",
            "Tópicos", "Pilares", "Assuntos monitorados", "Assunto específico", 'specific_topic',
       'macro_topic'
        ]

    if 'ID Cortex' in dataframe.columns:
        columns_fix = [
            'Data', 'Empresas citadas', 'Produtos citados', 'Tipos de impactos',
            "Cidade (MSS)", "Estado (MSS)", "País (MSS)",
            'Sentimento', 'Nível de Protagonismo final', 'Tier',
            'Fonte', 'Mídia', 'É ação'
        ]

        columns_themes = [
            'specific_topic',
            'macro_topic'
        ]

    if 'cortex_id' in dataframe.columns:
        columns_fix = [
            "data_da_publicacao", "nome_fonte_normalizado", "midia_publicada",
            "Empresa analisada", "tipo_de_publico", "cidade_do_publicador",
            "estado_do_publicador", "pais_do_publicador", 'tier_cortex',
            'Tipos de impactos', 'Sentimento', 'Nível de Protagonismo final',
            'É ação'
        ]

        columns_themes = [
            'specific_topic',
            'macro_topic'
        ]

    columns_themes_valid = [c for c in columns_themes if c in dataframe.columns]
    columns_fix_valid = [c for c in columns_fix if c in dataframe.columns]
    columns_valid = columns_fix_valid + columns_themes_valid

    if not columns_valid:
        raise ValueError("Nenhuma coluna válida para agrupamento foi encontrada.")

    # =========================
    # agrupamento
    # =========================
    dataview = (
        dataframe
        .groupby(columns_valid, dropna=False)
        .agg(
            alcance=(alcance_columns, 'sum'),
            valoracao=(valoracao_columns, 'sum'),
            frequencia=(id_columns, 'count'),
            jornalista_count=('Jornalista count', 'count'),
            acao_count=('Ação total', 'count')
        )
        .reset_index()
    )

    # =========================
    # enriquecimento temporal
    # =========================
    dataview[date_columns] = pd.to_datetime(dataview[date_columns], errors="coerce")
    dataview["dia"] = dataview[date_columns]

    dataview["dia_completo"] = (
        dataview[date_columns].dt.day.astype(str).str.zfill(2)
        + "-" + dataview[date_columns].dt.month.map(map_mes_low)
        + "-" + dataview[date_columns].dt.strftime("%y")
    )

    dataview["data_ext"] = dataview[date_columns].dt.strftime("%d-%b-%y")
    dataview["ano"] = dataview[date_columns].dt.year
    dataview["mes_num"] = dataview[date_columns].dt.month
    dataview["mes"] = dataview[date_columns].dt.strftime("%m/%Y")
    dataview["_mes_ordem"] = dataview[date_columns].dt.to_period("M").dt.to_timestamp()

    dataview = dataview.sort_values(by=[date_columns]).reset_index(drop=True)

    # z-score de alcance
    dict_stats = stats_freq(dataview, 'alcance')
    dataview['z-scorre'] = dataview['alcance'].apply(
        lambda x: z_score(x, dict_stats['mean'], dict_stats['std_dv'])
    )

    # =========================
    # semana_index e status de semana
    # =========================
    dataview = add_week_index_and_status(
        dataview,
        date_col=date_columns,
        data_ancora_semana=data_ancora_semana
    )

    # =========================
    # mes_index e status de mês
    # =========================
    dataview = add_mes_index(dataview)


    # =========================
    # trimestre
    # =========================

    dataview = add_trimestre_index(dataview, date_columns)

    # =========================
    # semestre
    # =========================

    dataview = add_semestre_index(dataview, date_columns)

    # =========================
    # dia_index e ano_index
    # =========================
    dataview = add_day_year_index(dataview, date_columns)

    return dataview

################## Gerando indicadores
import pandas as pd
from typing import Tuple

import pandas as pd
from typing import Tuple

from typing import Union, Tuple, List
import pandas as pd

def calc_nps_score(
    df: pd.DataFrame,
    value_col: str = "alcance",
    impacto_col: str = "Tipos de impactos",
    group_cols: Union[str, List[str], Tuple[str, ...]] = ("Data", "Empresa analisada"),
    sum_cols: Union[str, List[str], Tuple[str, ...]] = ("alcance", "valoracao", "frequencia"),
    dedupe_columns: bool = True,
) -> pd.DataFrame:
    """
    Calcula o NPS:
    (Promotores - Detratores) / (Promotores + Detratores + Inócuos)
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df deve ser um pandas.DataFrame")

    # ✅ NORMALIZAÇÃO (ESSENCIAL)
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    else:
        group_cols = list(group_cols)

    if isinstance(sum_cols, str):
        sum_cols = [sum_cols]
    else:
        sum_cols = list(sum_cols)

    # 0) Sanidade: colunas duplicadas
    if df.columns.duplicated().any():
        dup_names = df.columns[df.columns.duplicated()].tolist()
        if dedupe_columns:
            df = df.loc[:, ~df.columns.duplicated()].copy()
        else:
            raise ValueError(
                f"Há colunas duplicadas no DataFrame (ex: {dup_names}). "
                "Isso faz df['col'] virar 2D e quebra groupby/pivot."
            )

    long_mode = impacto_col in group_cols
    group_cols_wo_impact = [c for c in group_cols if c != impacto_col]

    needed = set(group_cols_wo_impact) | {impacto_col, value_col} | set(sum_cols)
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"Colunas ausentes no DataFrame: {missing}")

    # 1) Pivot para cálculo do NPS
    pivot = (
        df.pivot_table(
            index=group_cols_wo_impact,
            columns=impacto_col,
            values=value_col,
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    for col in ["Promotores", "Detratores", "Inócuos"]:
        if col not in pivot.columns:
            pivot[col] = 0

    denom = pivot["Promotores"] + pivot["Detratores"] + pivot["Inócuos"]
    pivot["nps_score"] = (
        (pivot["Promotores"] - pivot["Detratores"]) /
        denom.replace(0, pd.NA)
    ).fillna(0).round(4)

    # 2) Somas adicionais
    if long_mode:
        sums_by_impact = (
            df.groupby(group_cols_wo_impact + [impacto_col], as_index=False)[sum_cols]
            .sum()
        )
    else:
        sums = (
            df.groupby(group_cols_wo_impact, as_index=False)[sum_cols]
            .sum()
        )

    # 3) Merge base
    if long_mode:
        result = pivot

        long_df = result.melt(
            id_vars=group_cols_wo_impact + ["nps_score"],
            value_vars=["Detratores", "Inócuos", "Promotores"],
            var_name="Tipos de impacto",
            value_name="Impactos",
        )

        long_df = long_df.merge(
            sums_by_impact,
            left_on=group_cols_wo_impact + ["Tipos de impacto"],
            right_on=group_cols_wo_impact + [impacto_col],
            how="left",
        ).drop(columns=[impacto_col])

        for c in sum_cols:
            long_df[c] = long_df[c].fillna(0)

        return long_df

    result = pivot.merge(sums, on=group_cols_wo_impact, how="left")
    return result


def nps_color(nps_score):

    if nps_score >= 80.0:

        return "0b877d"
    
    elif nps_score >= 50.0 and nps_score < 80.0:

        return "308cf6"
    

    elif nps_score >= 35.0 and nps_score < 50.0:

        return "0bc2b4"


    elif nps_score >= 0.0 and nps_score < 35.0:

        return "ffd278"


    elif nps_score >= -80.0 and nps_score < 0.0:

        return "fb991e"

    elif nps_score < -80.0:

        return "ef2b56"

from typing import Union, List, Tuple
import pandas as pd

def nps_total_and_contrib(
    df: pd.DataFrame,
    dim_col: str,  # ex: "Temas"
    value_col: str = "alcance",
    impacto_col: str = "Tipos de impactos",
    group_cols: Union[str, List[str], Tuple[str, ...]] = ("Data", "Empresa analisada"),
    impacts=("Promotores", "Detratores", "Inócuos"),
    contr_type: str = "Total",  # "Total" ou "Promotor"
    round_total: int = 2,
    round_contrib: int = 4,
) -> pd.DataFrame:
    """
    Output:
      group_cols + [dim_col] + ["nps_score", f"nps_contrib_{dim_col}", "denom_total", f"total_{dim_col}"]

    Onde:
      nps_score = (Promotores - Detratores) / (Promotores + Detratores + Inócuos)
                  no nível de group_cols

      nps_contrib_dim =
          - se contr_type == "Total":
                (Promotores_dim - Detratores_dim) / denom_total
          - se contr_type == "Promotor":
                Promotores_dim / denom_total

      total_dim_col =
          soma total de value_col para aquela dimensão dentro do grupo
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df deve ser um pandas.DataFrame")

    df = df.copy()
    dim_contrib_col = f"nps_contrib_{dim_col}"
    dim_total_col = f"total_{dim_col}"

    # Normalização de group_cols
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    else:
        group_cols = list(group_cols)

    # Validação de colunas
    needed = set(group_cols) | {dim_col, value_col, impacto_col}
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"Colunas ausentes no DataFrame: {missing}")

    if contr_type not in {"Total", "Promotor"}:
        raise ValueError("contr_type deve ser 'Total' ou 'Promotor'")

    # -------------------------
    # 1) NPS TOTAL (por group_cols)
    # -------------------------
    total = (
        df.pivot_table(
            index=group_cols,
            columns=impacto_col,
            values=value_col,
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    for c in impacts:
        if c not in total.columns:
            total[c] = 0

    total["denom_total"] = total[list(impacts)].sum(axis=1)

    total["nps_score"] = (
        (total["Promotores"] - total["Detratores"])
        / total["denom_total"].replace(0, pd.NA)
    ).fillna(0).round(round_total)

    total_keep = total[group_cols + ["denom_total", "nps_score"]]

    # -------------------------
    # 2) CONTRIBUIÇÃO (por group_cols + dim_col)
    # -------------------------
    dim_pivot = (
        df.pivot_table(
            index=group_cols + [dim_col],
            columns=impacto_col,
            values=value_col,
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    for c in impacts:
        if c not in dim_pivot.columns:
            dim_pivot[c] = 0

    # total da própria dimensão
    dim_pivot[dim_total_col] = dim_pivot[list(impacts)].sum(axis=1)

    out = dim_pivot.merge(total_keep, on=group_cols, how="left")

    if contr_type == "Total":
        out[dim_contrib_col] = (
            (out["Promotores"] - out["Detratores"])
            / out["denom_total"].replace(0, pd.NA)
        ).fillna(0).round(round_contrib)

    elif contr_type == "Promotor":
        out[dim_contrib_col] = (
            out["Promotores"]
            / out["denom_total"].replace(0, pd.NA)
        ).fillna(0).round(round_contrib)

    out = out[
        group_cols + [dim_col, "nps_score", dim_contrib_col, dim_total_col, "denom_total"]
    ]

    return out.sort_values(group_cols + [dim_col]).reset_index(drop=True)
def calc_protagonism_score(
    df: pd.DataFrame,
    value_col: str = "alcance",
    impacto_col: str = "Nível de Protagonismo final",
    group_cols: Union[str, List[str], Tuple[str, ...]] = ("Data", "Empresa analisada"),
    filter_column: str = None,
    filter_value=None
) -> pd.DataFrame:
    """
    Calcula o protagonism_score por agrupamento.

    Fórmula:
        (Protagonismo + Referência contextual / Setor) / total

    Onde total =
        Citação relevante
        + Figurante
        + Referência contextual / Setor
        + Protagonismo
        + Referência em matéria de concorrente

    Também retorna a coluna 'total'.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df deve ser um pandas.DataFrame")

    # Normaliza group_cols
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    else:
        group_cols = list(group_cols)

    # Aplica filtro opcional
    if filter_column is not None and filter_value is not None:
        if filter_column not in df.columns:
            raise KeyError(f"Coluna de filtro ausente no DataFrame: '{filter_column}'")

        if isinstance(filter_value, (list, tuple, set)):
            df = df[df[filter_column].isin(filter_value)]
        else:
            df = df[df[filter_column].eq(filter_value)]

    # Validação de colunas necessárias
    needed = set(group_cols) | {impacto_col, value_col}
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"Colunas ausentes no DataFrame: {missing}")

    # Pivot
    pivot = (
        df.pivot_table(
            index=group_cols,
            columns=impacto_col,
            values=value_col,
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    # Garantir colunas obrigatórias
    required_cols = [
        "Citação relevante",
        "Figurante",
        "Referência contextual / Setor",
        "Protagonismo",
        "Referência em matéria de concorrente"
    ]

    for col in required_cols:
        if col not in pivot.columns:
            pivot[col] = 0

    # Cálculo
    denom = (
        pivot["Citação relevante"]
        + pivot["Figurante"]
        + pivot["Referência contextual / Setor"]
        + pivot["Protagonismo"]
        + pivot["Referência em matéria de concorrente"]
    ).astype(float)

    pivot["protagonism_score"] = (
        (
            pivot["Protagonismo"] + pivot["Referência contextual / Setor"]
        ) / denom.where(denom != 0)
    ).fillna(0).round(4)

    pivot["total"] = denom

    return pivot


def freq_score(
    df: pd.DataFrame,
    value_col: str = "frequencia",
    impacto_col: str = "Tipos de impactos",
    group_cols: Union[str, List[str], Tuple[str, ...]] = ("Data", "Empresa analisada")
) -> pd.DataFrame:
    """
    Cálculo da frequência por agrupamento.

    - Usa value_col como valor
    - Faz pivot por impacto_col
    - Calcula total e percentuais quando encontrar grupos de classes compatíveis
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df deve ser um pandas.DataFrame")

    # Normaliza group_cols
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    else:
        group_cols = list(group_cols)

    # Validação de colunas
    needed = set(group_cols) | {impacto_col, value_col}
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"Colunas ausentes no DataFrame: {missing}")

    # Pivot
    pivot = (
        df.pivot_table(
            index=group_cols,
            columns=impacto_col,
            values=value_col,
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    # Caso 1: Promotores / Detratores / Inócuos
    impact_nps = ["Promotores", "Detratores", "Inócuos"]
    if any(col in pivot.columns for col in impact_nps):
        for col in impact_nps:
            if col not in pivot.columns:
                pivot[col] = 0

        pivot["total"] = pivot["Promotores"] + pivot["Detratores"] + pivot["Inócuos"]

        total_safe = pivot["total"].replace(0, pd.NA)

        pivot["% Promotores"] = (pivot["Promotores"] / total_safe).fillna(0)
        pivot["% Detratores"] = (pivot["Detratores"] / total_safe).fillna(0)
        pivot["% Inócuos"] = (pivot["Inócuos"] / total_safe).fillna(0)

    # Caso 2: Positivo / Negativo / Neutro / -
    impact_sent = ["Positivo", "Negativo", "Neutro", "-"]
    if any(col in pivot.columns for col in impact_sent):
        for col in impact_sent:
            if col not in pivot.columns:
                pivot[col] = 0

        pivot["total"] = (
            pivot["Positivo"] + pivot["Negativo"] + pivot["Neutro"] + pivot["-"]
        )

        total_safe = pivot["total"].replace(0, pd.NA)

        pivot["% Positivo"] = (pivot["Positivo"] / total_safe).fillna(0)
        pivot["% Negativo"] = (pivot["Negativo"] / total_safe).fillna(0)
        pivot["% Neutro"] = (pivot["Neutro"] / total_safe).fillna(0)
        pivot["% -"] = (pivot["-"] / total_safe).fillna(0)

    return pivot

def valoration_score(
    df: pd.DataFrame,
    value_col: str = "valoracao",
    group_cols: Union[str, List[str], Tuple[str, ...]] = ("Data", "Empresa analisada")
) -> pd.DataFrame:
    """
    Calcula a valoração agregada por agrupamento.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df deve ser um pandas.DataFrame")

    # Normaliza group_cols
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    else:
        group_cols = list(group_cols)

    # Validação de colunas
    needed = set(group_cols) | {value_col}
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"Colunas ausentes no DataFrame: {missing}")

    pivot = (
        df.pivot_table(
            index=group_cols,
            values=value_col,
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    pivot[value_col] = pivot[value_col].round(2)

    return pivot

def jornalista_score(
    df: pd.DataFrame,
    value_cols: Union[str, List[str], Tuple[str, ...]] = ("jornalista_count", "count"),
    group_cols: Union[str, List[str], Tuple[str, ...]] = ("Data", "Empresa analisada")
) -> pd.DataFrame:
    """
    Soma métricas de jornalista.

    - Usa múltiplas colunas de valor
    - Agrupa por group_cols
    - Trata valores ausentes como 0
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df deve ser um pandas.DataFrame")

    # Normaliza inputs
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    else:
        group_cols = list(group_cols)

    if isinstance(value_cols, str):
        value_cols = [value_cols]
    else:
        value_cols = list(value_cols)

    # Validação de colunas
    needed = set(group_cols) | set(value_cols)
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"Colunas ausentes no DataFrame: {missing}")

    pivot = (
        df.pivot_table(
            index=group_cols,
            values=value_cols,
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    return pivot


def action_score(
    df: pd.DataFrame,
    value_cols: Union[str, List[str], Tuple[str, ...]] = ("acao_count", "count"),
    group_cols: Union[str, List[str], Tuple[str, ...]] = ("Data", "Empresa analisada")
) -> pd.DataFrame:
    """
    Count de ação

    - Soma value_cols
    - Agrupa por group_cols
    - Trata valores ausentes como 0
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df deve ser um pandas.DataFrame")

    # Normalização
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    else:
        group_cols = list(group_cols)

    if isinstance(value_cols, str):
        value_cols = [value_cols]
    else:
        value_cols = list(value_cols)

    # Validação
    needed = set(group_cols) | set(value_cols)
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"Colunas ausentes no DataFrame: {missing}")

    pivot = (
        df.pivot_table(
            index=group_cols,
            values=value_cols,
            aggfunc="sum",
            fill_value=0
        )  )

    return pivot

