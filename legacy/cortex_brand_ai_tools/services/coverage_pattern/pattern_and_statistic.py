from __future__ import annotations


from services.index_function import  calc_nps_score, calc_protagonism_score, nps_total_and_contrib, freq_score
import pandas as pd
from typing import List, Literal, Sequence
pd.options.display.float_format = '{:.2f}'.format

# ===========
# funções auxiliares
# ===========
def merge_nps_protagonismo(
    df_nps: pd.DataFrame,
    df_protagonismo: pd.DataFrame,
    keys: List[str] | None = None,
) -> pd.DataFrame:
    """
    Faz merge entre dataframe de NPS e dataframe de protagonismo.

    Chaves padrão:
        - dia_codmpleto
        - semana
        - semana_index
        - Empresa analisada

    Mantém a base de NPS como principal e retorna apenas os indicadores relevantes.
    """

    if keys is None:
        keys = ['dia', 'dia_index', 'semana', 'semana_index', 'mes', 'mes_index', 'Empresa analisada']

    # Seleciona apenas colunas necessárias
    df_nps_sel = df_nps[
        keys + ['Detratores', 'Inócuos', 'Promotores', 'alcance', 'nps_score']
    ].copy()

    df_prot_sel = df_protagonismo[
        keys + ['protagonism_score']
    ].copy()

    # Remove duplicatas com base nas chaves
    df_nps_sel = df_nps_sel.drop_duplicates(subset=keys)
    df_prot_sel = df_prot_sel.drop_duplicates(subset=keys)

    # Merge
    df_merged = pd.merge(
        df_nps_sel,
        df_prot_sel,
        on=keys,
        how='left',
        validate='one_to_one'
    )

    return df_merged

import pandas as pd

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

    # Garantir que a coluna é datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(
            df[date_col],
            format=date_format,
            errors="coerce"
        )

    # Dropa datas inválidas
    df = df.dropna(subset=[date_col])

    # 🔽 Aplica filtros
    if start_date:
        start_date = pd.to_datetime(start_date)
        df = df[df[date_col] >= start_date]

    if end_date:
        end_date = pd.to_datetime(end_date)
        df = df[df[date_col] <= end_date]

    return df


# ===========
# funções estatítica
# ===========

import math

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


# ===========
# criação dos dataframes com os indicadores
# ===========

PeriodType = Literal["dia", "semana", "mês", "mes", "ano"]
MetricType = Literal["nps", "protagonismo", "merged"]


def build_media_metrics_view(
    dataview_df: pd.DataFrame,
    client: str | Sequence[str] | None = None,
    contest: str | Sequence[str] | None = None,
    focus_analysis: str = "Empresa analisada",
    period: PeriodType = "dia",
    return_metric: MetricType = "merged",
) -> pd.DataFrame:
    """
    Constrói uma visão analítica agregada por período para métricas de mídia,
    com suporte ao cálculo de NPS, protagonismo, frequência e merge consolidado.

    Pipeline
    --------
    1. Define as colunas temporais conforme `period`.
    2. Agrupa por colunas temporais + `focus_analysis`.
    3. Calcula:
       - NPS (`calc_nps_score`)
       - Protagonismo (`protagonism_score`)
       - Frequência (`freq_score`)
    4. Renomeia as colunas de frequência para evitar colisão semântica:
       - Detratores -> Publicações Detratoras
       - Inócuos -> Publicações Inócuas
       - Promotores -> Publicações Promotoras
       - total -> frequencia
    5. Filtra `client` e `contest` na mesma coluna de foco analítico.
    6. Retorna uma métrica isolada ou o merge consolidado.

    Parâmetros
    ----------
    dataview_df : pd.DataFrame
        DataFrame base.

    client : str | Sequence[str] | None, default=None
        Entidade principal de análise.

    contest : str | Sequence[str] | None, default=None
        Concorrentes da análise. São filtrados na mesma coluna definida
        em `focus_analysis`.

    focus_analysis : str, default="Empresa analisada"
        Nome da coluna categórica de foco analítico.

    period : {"dia", "semana", "mês", "mes", "ano"}, default="dia"
        Granularidade temporal da análise.

    return_metric : {"nps", "protagonismo", "frequencia", "merged"}, default="merged"
        Define qual saída retornar.

    Retorno
    -------
    pd.DataFrame
        DataFrame agregado, filtrado e ordenado.

    Dependências esperadas no escopo
    --------------------------------
    - calc_nps_score
    - protagonism_score
    - freq_score
    - merge_nps_protagonismo
    """

    def _normalize_to_list(value: str | Sequence[str] | None) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return list(value)

    def _validate_required_columns(
        df: pd.DataFrame,
        required_cols: Sequence[str],
        context: str = "dataframe",
    ) -> None:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise KeyError(
                f"As seguintes colunas obrigatórias não existem em `{context}`: {missing}"
            )

    normalized_period = period.lower().strip()
    if normalized_period == "mes":
        normalized_period = "mês"

    period_analysis_map: dict[str, list[str]] = {
        "dia": ["dia", "dia_index", "semana", "semana_index", "mes", "mes_index", "ano", "ano_index"],
        "semana": ["semana", "semana_index"],
        "mês": ["mes", "mes_index", "ano", "ano_index"],
        "ano": ["ano", "ano_index"],
    }

    sort_col_map: dict[str, str] = {
        "dia": "dia_index",
        "semana": "semana_index",
        "mês": "mes_index",
        "ano": "ano_index",
    }

    valid_metrics = {"nps", "protagonismo", "frequencia", "merged"}

    if normalized_period not in period_analysis_map:
        raise ValueError(
            "`period` deve ser um destes valores: 'dia', 'semana', 'mês'/'mes', 'ano'."
        )

    if return_metric not in valid_metrics:
        raise ValueError(
            "`return_metric` deve ser um destes valores: "
            "'nps', 'protagonismo', 'frequencia', 'merged'."
        )

    time_cols = period_analysis_map[normalized_period]
    sort_col = sort_col_map[normalized_period]
    group_cols = [*time_cols, focus_analysis]

    _validate_required_columns(
        dataview_df,
        group_cols,
        context="dataview_df",
    )

    client_list = _normalize_to_list(client)
    contest_list = _normalize_to_list(contest)

    entity_filter: list[str] | None = None
    if client_list or contest_list:
        entity_filter = []
        if client_list:
            entity_filter.extend(client_list)
        if contest_list:
            entity_filter.extend(contest_list)
        entity_filter = list(dict.fromkeys(entity_filter))

    # ==========================================================
    # NPS
    # ==========================================================
    nps_df = calc_nps_score(
        dataview_df,
        group_cols=tuple(group_cols),
    )

    _validate_required_columns(
        nps_df,
        [*group_cols, sort_col],
        context="nps_df",
    )

    nps_df = nps_df.sort_values(by=sort_col).reset_index(drop=True)

    if "frequencia" in nps_df.columns:
        nps_df = nps_df.drop(columns=["frequencia"])

    if entity_filter is not None:
        nps_df = nps_df[nps_df[focus_analysis].isin(entity_filter)].reset_index(drop=True)

    if return_metric == "nps":
        return nps_df

    # ==========================================================
    # PROTAGONISMO
    # ==========================================================
    prot_df = calc_protagonism_score(
        dataview_df,
        group_cols=tuple(group_cols),
    )

    _validate_required_columns(
        prot_df,
        [*group_cols, sort_col],
        context="prot_df",
    )

    prot_df = prot_df.sort_values(by=sort_col).reset_index(drop=True)

    if entity_filter is not None:
        prot_df = prot_df[prot_df[focus_analysis].isin(entity_filter)].reset_index(drop=True)

    if return_metric == "protagonismo":
        return prot_df

    # ==========================================================
    # FREQUÊNCIA
    # ==========================================================
    freq_df = freq_score(
        dataview_df,
        group_cols=tuple(group_cols),
    )

    _validate_required_columns(
        freq_df,
        [*group_cols, sort_col, "Detratores", "Inócuos", "Promotores", "total"],
        context="freq_df",
    )

    freq_df = (
        freq_df
        .rename(
            columns={
                "Detratores": "Publicações Detratoras",
                "Inócuos": "Publicações Inócuas",
                "Promotores": "Publicações Promotoras",
                "total": "frequencia",
            }
        )
        .sort_values(by=sort_col)
        .reset_index(drop=True)
    )

    if entity_filter is not None:
        freq_df = freq_df[freq_df[focus_analysis].isin(entity_filter)].reset_index(drop=True)

    if return_metric == "frequencia":
        return freq_df

    # ==========================================================
    # MERGE NPS + PROTAGONISMO
    # ==========================================================
    merged_df = merge_nps_protagonismo(
        df_nps=nps_df,
        df_protagonismo=prot_df,
        keys=group_cols,
    )

    _validate_required_columns(
        merged_df,
        [*group_cols, sort_col],
        context="merged_df (nps + protagonismo)",
    )

    # ==========================================================
    # MERGE + FREQUÊNCIA
    # ==========================================================
    freq_cols_to_add = [
        *group_cols,
        "Publicações Detratoras",
        "Publicações Inócuas",
        "Publicações Promotoras",
        "frequencia",
    ]

    _validate_required_columns(
        freq_df,
        freq_cols_to_add,
        context="freq_df pós-rename",
    )

    final_df = pd.merge(
        merged_df,
        freq_df[freq_cols_to_add],
        on=group_cols,
        how="left",
        validate="one_to_one",
    )

    final_df = final_df.sort_values(by=sort_col).reset_index(drop=True)

    return final_df

def build_media_metrics_view_by_source(
    dataview_df: pd.DataFrame,
    client: str | Sequence[str] | None = None,
    contest: str | Sequence[str] | None = None,
    *,
    focus_analysis: str = "Empresa analisada",
    source_cols: Sequence[str] = ("Fonte", "Mídia"),
    period: PeriodType = "dia",
    return_metric: MetricType = "merged",
) -> pd.DataFrame:
    """
    Constrói uma visão analítica agregada por período e por fonte/mídia,
    calculando NPS, protagonismo, frequência e merge consolidado.

    Diferença em relação à versão base
    ----------------------------------
    Inclui, de forma fixa no agrupamento, colunas de origem editorial,
    por padrão:
    - Fonte
    - Mídia

    Pipeline
    --------
    1. Define colunas temporais conforme `period`.
    2. Acrescenta `source_cols` ao agrupamento.
    3. Acrescenta `focus_analysis` ao agrupamento.
    4. Calcula:
       - `calc_nps_score`
       - `protagonism_score`
       - `freq_score`
    5. Renomeia colunas de frequência:
       - Detratores -> Publicações Detratoras
       - Inócuos -> Publicações Inócuas
       - Promotores -> Publicações Promotoras
       - total -> frequencia
    6. Filtra cliente e concorrentes.
    7. Retorna métrica isolada ou merge consolidado.

    Parâmetros
    ----------
    dataview_df : pd.DataFrame
        DataFrame base.

    client : str | Sequence[str] | None, default=None
        Entidade principal da análise.

    contest : str | Sequence[str] | None, default=None
        Concorrentes da análise, filtrados na mesma coluna de foco.

    focus_analysis : str, default="Empresa analisada"
        Coluna de foco analítico.

    source_cols : Sequence[str], default=("Fonte", "Mídia")
        Colunas fixas de agrupamento editorial/distribuição.

    period : {"dia", "semana", "mês", "mes", "ano"}, default="dia"
        Granularidade temporal.

    return_metric : {"nps", "protagonismo", "frequencia", "merged"}, default="merged"
        Define qual saída retornar.

    Retorno
    -------
    pd.DataFrame
        DataFrame agregado e ordenado.

    Dependências esperadas no escopo
    --------------------------------
    - calc_nps_score
    - protagonism_score
    - freq_score
    - merge_nps_protagonismo
    """

    def _normalize_to_list(value: str | Sequence[str] | None) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return list(value)

    def _validate_required_columns(
        df: pd.DataFrame,
        required_cols: Sequence[str],
        context: str,
    ) -> None:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise KeyError(
                f"As seguintes colunas obrigatórias não existem em `{context}`: {missing}"
            )

    normalized_period = period.lower().strip()
    if normalized_period == "mes":
        normalized_period = "mês"

    period_analysis_map: dict[str, list[str]] = {
        "dia": ["dia", "dia_index", "semana", "semana_index", "mes", "mes_index", "ano", "ano_index"],
        "semana": ["semana", "semana_index"],
        "mês": ["mes", "mes_index", "ano", "ano_index"],
        "ano": ["ano", "ano_index"],
    }

    sort_col_map: dict[str, str] = {
        "dia": "dia_index",
        "semana": "semana_index",
        "mês": "mes_index",
        "ano": "ano_index",
    }

    valid_metrics = {"nps", "protagonismo", "frequencia", "merged"}

    if normalized_period not in period_analysis_map:
        raise ValueError(
            "`period` deve ser um destes valores: 'dia', 'semana', 'mês'/'mes', 'ano'."
        )

    if return_metric not in valid_metrics:
        raise ValueError(
            "`return_metric` deve ser um destes valores: "
            "'nps', 'protagonismo', 'frequencia', 'merged'."
        )

    source_cols = list(source_cols)
    time_cols = period_analysis_map[normalized_period]
    sort_col = sort_col_map[normalized_period]

    group_cols = [*time_cols, *source_cols, focus_analysis]

    _validate_required_columns(
        dataview_df,
        group_cols,
        context="dataview_df",
    )

    client_list = _normalize_to_list(client)
    contest_list = _normalize_to_list(contest)

    entity_filter: list[str] | None = None
    if client_list or contest_list:
        entity_filter = []
        if client_list:
            entity_filter.extend(client_list)
        if contest_list:
            entity_filter.extend(contest_list)
        entity_filter = list(dict.fromkeys(entity_filter))

    # ==========================================================
    # NPS
    # ==========================================================
    nps_df = calc_nps_score(
        dataview_df,
        group_cols=tuple(group_cols),
    )

    _validate_required_columns(
        nps_df,
        [*group_cols, sort_col],
        context="nps_df",
    )

    nps_df = nps_df.sort_values(by=sort_col).reset_index(drop=True)

    if "frequencia" in nps_df.columns:
        nps_df = nps_df.drop(columns=["frequencia"])

    if entity_filter is not None:
        nps_df = nps_df[nps_df[focus_analysis].isin(entity_filter)].reset_index(drop=True)

    if return_metric == "nps":
        return nps_df

    # ==========================================================
    # PROTAGONISMO
    # ==========================================================
    prot_df = calc_protagonism_score(
        dataview_df,
        group_cols=tuple(group_cols),
    )

    _validate_required_columns(
        prot_df,
        [*group_cols, sort_col],
        context="prot_df",
    )

    prot_df = prot_df.sort_values(by=sort_col).reset_index(drop=True)

    if entity_filter is not None:
        prot_df = prot_df[prot_df[focus_analysis].isin(entity_filter)].reset_index(drop=True)

    if return_metric == "protagonismo":
        return prot_df

    # ==========================================================
    # FREQUÊNCIA
    # ==========================================================
    freq_df = freq_score(
        dataview_df,
        group_cols=tuple(group_cols),
    )

    _validate_required_columns(
        freq_df,
        [*group_cols, sort_col, "Detratores", "Inócuos", "Promotores", "total"],
        context="freq_df",
    )

    freq_df = (
        freq_df
        .rename(
            columns={
                "Detratores": "Publicações Detratoras",
                "Inócuos": "Publicações Inócuas",
                "Promotores": "Publicações Promotoras",
                "total": "frequencia",
            }
        )
        .sort_values(by=sort_col)
        .reset_index(drop=True)
    )

    if entity_filter is not None:
        freq_df = freq_df[freq_df[focus_analysis].isin(entity_filter)].reset_index(drop=True)

    if return_metric == "frequencia":
        return freq_df

    # ==========================================================
    # MERGE NPS + PROTAGONISMO
    # ==========================================================
    merged_df = merge_nps_protagonismo(
        df_nps=nps_df,
        df_protagonismo=prot_df,
        keys=group_cols,
    )

    _validate_required_columns(
        merged_df,
        [*group_cols, sort_col],
        context="merged_df (nps + protagonismo)",
    )

    # ==========================================================
    # MERGE + FREQUÊNCIA
    # ==========================================================
    freq_cols_to_add = [
        *group_cols,
        "Publicações Detratoras",
        "Publicações Inócuas",
        "Publicações Promotoras",
        "frequencia",
    ]

    _validate_required_columns(
        freq_df,
        freq_cols_to_add,
        context="freq_df pós-rename",
    )

    final_df = pd.merge(
        merged_df,
        freq_df[freq_cols_to_add],
        on=group_cols,
        how="left",
        validate="one_to_one",
    )

    final_df = final_df.sort_values(by=sort_col).reset_index(drop=True)

    return final_df

def build_daily_media_metrics_with_nps_contrib(
    dataview_df: pd.DataFrame,
    client: str | Sequence[str] | None = None,
    contest: str | Sequence[str] | None = None,
    *,
    focus_analysis: str = "Empresa analisada",
    period: Literal["dia"] = "dia",
    contrib_dim_col: str = "dia",
    contrib_group_cols: Sequence[str] = ("mes", "mes_index", "Empresa analisada"),
    merge_how: str = "left",
    merge_validate: str = "one_to_one",
    rename_nps_daily: str = "nps_score_dia",
    rename_protagonism_daily: str = "protagonism_score_dia",
    rename_nps_contrib_base: str = "nps_score_mes",
) -> pd.DataFrame:
    """
    Constrói uma visão diária consolidada de métricas de mídia e a enriquece
    com a contribuição diária do NPS dentro de um agrupamento superior.

    Pipeline executado
    ------------------
    1. Gera a visão diária consolidada com `build_media_metrics_view`
       retornando NPS + protagonismo.
    2. Renomeia colunas diárias para evitar ambiguidade semântica.
    3. Calcula a decomposição de NPS com `nps_total_and_contrib`,
       usando `dim_col='dia'` e agrupamento superior configurável.
    4. Renomeia o score agregado retornado por `nps_total_and_contrib`.
    5. Realiza o merge entre as duas saídas.
    6. Ordena o resultado por `dia_index`, quando disponível.

    Parâmetros
    ----------
    dataview_df : pd.DataFrame
        DataFrame base contendo os dados de mídia e as colunas temporais
        necessárias para o cálculo das métricas.

    client : str | Sequence[str] | None, default=None
        Entidade principal da análise. Pode ser string única ou coleção de strings.

    contest : str | Sequence[str] | None, default=None
        Concorrentes da análise. Importante: são filtrados na mesma coluna
        definida em `focus_analysis`.

    focus_analysis : str, default="Empresa analisada"
        Coluna categórica usada como eixo da análise.

    period : Literal["dia"], default="dia"
        Granularidade da visão principal.
        Esta função foi desenhada para o fluxo diário, portanto aceita apenas `"dia"`.

    contrib_dim_col : str, default="dia"
        Dimensão interna usada em `nps_total_and_contrib`.

    contrib_group_cols : Sequence[str], default=("mes", "mes_index", "Empresa analisada")
        Colunas de agrupamento superior usadas em `nps_total_and_contrib`.

    merge_how : str, default="left"
        Estratégia de merge aplicada no `pd.merge`.

    merge_validate : str, default="one_to_one"
        Regra de validação estrutural do merge.

    rename_nps_daily : str, default="nps_score_dia"
        Novo nome da coluna de NPS da visão diária consolidada.

    rename_protagonism_daily : str, default="protagonism_score_dia"
        Novo nome da coluna de protagonismo da visão diária consolidada.

    rename_nps_contrib_base : str, default="nps_score_mes"
        Novo nome da coluna `nps_score` retornada por `nps_total_and_contrib`.

    Retorno
    -------
    pd.DataFrame
        DataFrame final contendo:
        - métricas diárias consolidadas
        - score agregado do agrupamento superior
        - contribuição diária do NPS
        - colunas auxiliares de totalização

    Exceções
    --------
    KeyError
        Se colunas obrigatórias não existirem no dataframe de entrada
        ou nos dataframes intermediários.

    ValueError
        Se houver inconsistência estrutural no merge ou parâmetros inválidos.

    Dependências esperadas no escopo
    --------------------------------
    - build_media_metrics_view
    - nps_total_and_contrib
    """

    def _normalize_to_list(value: str | Sequence[str] | None) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return list(value)

    def _validate_required_columns(
        df: pd.DataFrame,
        required_cols: Sequence[str],
        context: str,
    ) -> None:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise KeyError(
                f"As seguintes colunas obrigatórias não existem em `{context}`: {missing}"
            )

    if period != "dia":
        raise ValueError(
            "Esta função foi desenhada para visão diária; use `period='dia'`."
        )

    entity_filter = []
    client_list = _normalize_to_list(client)
    contest_list = _normalize_to_list(contest)

    if client_list:
        entity_filter.extend(client_list)
    if contest_list:
        entity_filter.extend(contest_list)

    entity_filter = list(dict.fromkeys(entity_filter)) if entity_filter else None

    required_input_cols = [
        "dia",
        "dia_index",
        "mes",
        "mes_index",
        focus_analysis,
    ]
    _validate_required_columns(dataview_df, required_input_cols, context="dataview_df")

    # ==========================================================
    # 1. VISÃO DIÁRIA CONSOLIDADA
    # ==========================================================
    df_daily = build_media_metrics_view(
        dataview_df=dataview_df,
        client=client,
        contest=contest,
        focus_analysis=focus_analysis,
        period="dia",
        return_metric="merged",
    )

    _validate_required_columns(
        df_daily,
        ["dia", "dia_index", "mes", "mes_index", focus_analysis, "nps_score", "protagonism_score"],
        context="df_daily (saída de build_media_metrics_view)",
    )

    df_daily = df_daily.rename(
        columns={
            "nps_score": rename_nps_daily,
            "protagonism_score": rename_protagonism_daily,
        }
    ).copy()

    # ==========================================================
    # 2. CONTRIBUIÇÃO DE NPS POR DIA
    # ==========================================================
    _validate_required_columns(
        dataview_df,
        list(contrib_group_cols) + [contrib_dim_col, focus_analysis],
        context="dataview_df para nps_total_and_contrib",
    )

    contr_dia_nps = nps_total_and_contrib(
        dataview_df,
        dim_col=contrib_dim_col,
        group_cols=tuple(contrib_group_cols),
    )

    _validate_required_columns(
        contr_dia_nps,
        list(contrib_group_cols) + [contrib_dim_col, "nps_score"],
        context="contr_dia_nps (saída de nps_total_and_contrib)",
    )

    if entity_filter is not None:
        contr_dia_nps = contr_dia_nps[
            contr_dia_nps[focus_analysis].isin(entity_filter)
        ].reset_index(drop=True)

    contr_dia_nps = contr_dia_nps.rename(
        columns={
            "nps_score": rename_nps_contrib_base,
        }
    ).copy()

    # ==========================================================
    # 3. MERGE FINAL
    # ==========================================================
    merge_keys = ["dia", "mes", "mes_index", focus_analysis]

    _validate_required_columns(df_daily, merge_keys, context="df_daily para merge")
    _validate_required_columns(contr_dia_nps, merge_keys, context="contr_dia_nps para merge")

    df_final = pd.merge(
        df_daily,
        contr_dia_nps,
        on=merge_keys,
        how=merge_how,
        validate=merge_validate,
    )

    # z-score de alcance
    dict_stats = stats_freq(df_final, 'alcance')
    df_final['z-score_alcance'] = df_final['alcance'].apply(
        lambda x: z_score(x, dict_stats['mean'], dict_stats['std_dv'])
    )


    if "dia_index" in df_final.columns:
        df_final = df_final.sort_values(by="dia_index").reset_index(drop=True)
    else:
        df_final = df_final.reset_index(drop=True)

    return df_final



from typing import Sequence
import pandas as pd

from typing import Sequence
import pandas as pd

period_analysis_map: dict[str, list[str]] = {
    "dia": ["dia", "dia_index", "semana", "semana_index", "mes", "mes_index", "ano", "ano_index"],
    "semana": ["semana", "semana_index"],
    "mes": ["mes", "mes_index", "ano", "ano_index"],
    "mês": ["mes", "mes_index", "ano", "ano_index"],
    "ano": ["ano", "ano_index"],
}

sort_col_map: dict[str, str] = {
    "dia": "dia_index",
    "semana": "semana_index",
    "mes": "mes_index",
    "mês": "mes_index",
    "ano": "ano_index",
}


def resolve_group_cols(
    period: str,
    focus_analysis: str = "Empresa analisada",
) -> list[str]:
    """
    Resolve automaticamente as colunas de agrupamento base a partir do período.
    """
    period_norm = period.lower().strip()

    if period_norm not in period_analysis_map:
        raise ValueError(
            f"Período inválido: {period}. Use um destes: {list(period_analysis_map.keys())}"
        )

    group_cols = period_analysis_map[period_norm].copy()

    if focus_analysis not in group_cols:
        group_cols.append(focus_analysis)

    return group_cols

def build_nps_contrib_by_specific_topic(
    dataview_df: pd.DataFrame,
    client: str | Sequence[str] | None = None,
    contest: str | Sequence[str] | None = None,
    *,
    period: str = "mes",
    focus_analysis: str = "Empresa analisada",
    topic_col: str = "Assunto específico",
    rename_nps_group: str = "nps_score_periodo",
    rename_nps_contrib: str = "nps_contrib_assunto_especifico",
    rename_total_topic: str = "total_assunto_especifico",
    rename_denom_total: str = "denom_total",
    sort_by: Sequence[str] | None = None,
    ascending: bool = False,
) -> pd.DataFrame:
    """
    Calcula a contribuição de `topic_col` para o NPS dentro de um agrupamento-base temporal.
    """

    def _normalize_to_list(value: str | Sequence[str] | None) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return list(value)

    def _validate_required_columns(
        df: pd.DataFrame,
        required_cols: Sequence[str],
        context: str,
    ) -> None:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise KeyError(
                f"As seguintes colunas obrigatórias não existem em `{context}`: {missing}"
            )

    period_norm = period.lower().strip()
    group_cols = resolve_group_cols(
        period=period_norm,
        focus_analysis=focus_analysis,
    )

    required_input_cols = list(dict.fromkeys([*group_cols, topic_col, focus_analysis]))
    _validate_required_columns(dataview_df, required_input_cols, context="dataview_df")

    client_list = _normalize_to_list(client)
    contest_list = _normalize_to_list(contest)

    entity_filter: list[str] | None = None
    if client_list or contest_list:
        entity_filter = []
        if client_list:
            entity_filter.extend(client_list)
        if contest_list:
            entity_filter.extend(contest_list)
        entity_filter = list(dict.fromkeys(entity_filter))

    base_df = dataview_df.copy()

    if entity_filter is not None:
        base_df = base_df[base_df[focus_analysis].isin(entity_filter)].copy()

    # 1. NPS DO GRUPO-BASE
    nps_group_df = calc_nps_score(
        base_df,
        group_cols=tuple(group_cols),
    )

    _validate_required_columns(
        nps_group_df,
        [*group_cols, "nps_score"],
        context="nps_group_df",
    )

    nps_group_df = nps_group_df[group_cols + ["nps_score"]].copy()
    nps_group_df = nps_group_df.rename(columns={"nps_score": rename_nps_group})

    # 2. NPS POR ASSUNTO ESPECÍFICO
    topic_group_cols = [*group_cols, topic_col]

    nps_topic_df = calc_nps_score(
        base_df,
        group_cols=tuple(topic_group_cols),
    )

    _validate_required_columns(
        nps_topic_df,
        [*topic_group_cols, "nps_score"],
        context="nps_topic_df",
    )

    nps_topic_df = nps_topic_df[topic_group_cols + ["nps_score"]].copy()
    nps_topic_df = nps_topic_df.rename(columns={"nps_score": "nps_score_assunto_especifico"})

    # 3. FREQUÊNCIA POR ASSUNTO ESPECÍFICO
    freq_topic_df = freq_score(
        base_df,
        group_cols=tuple(topic_group_cols),
    )

    _validate_required_columns(
        freq_topic_df,
        [*topic_group_cols, "total"],
        context="freq_topic_df",
    )

    freq_topic_df = freq_topic_df[topic_group_cols + ["total"]].copy()
    freq_topic_df = freq_topic_df.rename(columns={"total": rename_total_topic})

    # 4. DENOMINADOR TOTAL DO GRUPO-BASE
    denom_df = freq_score(
        base_df,
        group_cols=tuple(group_cols),
    )

    _validate_required_columns(
        denom_df,
        [*group_cols, "total"],
        context="denom_df",
    )

    denom_df = denom_df[group_cols + ["total"]].copy()
    denom_df = denom_df.rename(columns={"total": rename_denom_total})

    # 5. MERGES
    result_df = pd.merge(
        nps_topic_df,
        freq_topic_df,
        on=topic_group_cols,
        how="left",
        validate="one_to_one",
    )

    result_df = pd.merge(
        result_df,
        denom_df,
        on=group_cols,
        how="left",
        validate="many_to_one",
    )

    result_df = pd.merge(
        result_df,
        nps_group_df,
        on=group_cols,
        how="left",
        validate="many_to_one",
    )

    # 6. CONTRIBUIÇÃO
    result_df[rename_nps_contrib] = (
        result_df["nps_score_assunto_especifico"]
        * (result_df[rename_total_topic] / result_df[rename_denom_total])
    )

    # 7. ORDEM FINAL
    if sort_by is None:
        default_sort_col = sort_col_map.get(period_norm)
        if default_sort_col and default_sort_col in result_df.columns:
            result_df = result_df.sort_values(
                by=[focus_analysis, default_sort_col, rename_nps_contrib],
                ascending=[True, True, ascending],
            ).reset_index(drop=True)
        else:
            result_df = result_df.sort_values(
                by=[*group_cols, rename_nps_contrib],
                ascending=[*[True for _ in group_cols], ascending],
            ).reset_index(drop=True)
    else:
        result_df = result_df.sort_values(
            by=list(sort_by),
            ascending=ascending,
        ).reset_index(drop=True)

    return result_df

# =========================================================
# ESTATÍTICA
# =========================================================

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


from typing import Any, Dict, List, Optional

import pandas as pd


def _format_big_number_ptbr(value: float | int | None, decimals: int = 1) -> str:
    """
    Converte números para formato curto em pt-BR.

    Exemplos:
    1200 -> '1,2 mil'
    1250000 -> '1,2 M'
    2300000000 -> '2,3 bi'
    """
    if value is None or pd.isna(value):
        return "0"

    value = float(value)
    abs_value = abs(value)

    if abs_value >= 1_000_000_000:
        scaled = value / 1_000_000_000
        suffix = " bi"
    elif abs_value >= 1_000_000:
        scaled = value / 1_000_000
        suffix = " M"
    elif abs_value >= 1_000:
        scaled = value / 1_000
        suffix = " mil"
    else:
        if value.is_integer():
            return str(int(value))
        return f"{value:.{decimals}f}".replace(".", ",")

    return f"{scaled:.{decimals}f}".replace(".", ",") + suffix


def _safe_float(value: Any, decimals: int = 2) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value), decimals)


def _safe_int(value: Any) -> int:
    if value is None or pd.isna(value):
        return 0
    return int(round(float(value)))


def _safe_percent(value: Any, decimals: int = 2) -> float:
    """
    Multiplica por 100 e arredonda.
    Ex.: 0.4237 -> 42.37
    """
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value) * 100, decimals)


def _detect_period_col(df: pd.DataFrame) -> str:
    if "semana" in df.columns:
        return "semana"
    if "mes" in df.columns:
        return "mes"
    if "mês" in df.columns:
        return "mês"
    raise KeyError("Não foi possível detectar a coluna de período ('semana', 'mes' ou 'mês').")


def _detect_period_label(period_col: str) -> str:
    mapping = {
        "semana": "semana",
        "mes": "mês",
        "mês": "mês",
    }
    return mapping.get(period_col.lower(), period_col.lower())


def _sort_period_df(df: pd.DataFrame, period_col: str) -> pd.DataFrame:
    """
    Ordena priorizando coluna *_index se existir.
    Assume que 0 é o período de referência mais recente,
    1 e 2 são os anteriores.
    """
    index_col = f"{period_col}_index"

    if index_col in df.columns:
        return df.sort_values(index_col, ascending=True).copy()

    # fallback
    try:
        tmp = df.copy()
        tmp["_period_sort"] = pd.to_datetime(tmp[period_col], errors="coerce")
        if tmp["_period_sort"].notna().sum() > 0:
            return tmp.sort_values("_period_sort", ascending=False).drop(columns="_period_sort")
    except Exception:
        pass

    return df.sort_values(period_col, ascending=False).copy()


def _build_period_big_number_record(row: pd.Series, period_col: str) -> Dict[str, Any]:
    nps_num = _safe_percent(row.get("nps_score"), 2)
    protagonismo_num = _safe_percent(row.get("protagonism_score"), 2)

    return {
        "periodo": row.get(period_col),
        "indicadores": {
            "nps": {
                "label": "NPS",
                "numero": nps_num,
                "percentual": f"{nps_num}%"
            },
            "protagonismo": {
                "label": "Protagonismo",
                "numero": protagonismo_num,
                "percentual": f"{protagonismo_num}%"
            },
            "impacto_promotor": {
                "label": "Impacto Promotor",
                "numero": _safe_float(row.get("Promotores"), 2),
                "texto": _format_big_number_ptbr(row.get("Promotores"))
            },
            "impacto_detrator": {
                "label": "Impacto Detrator",
                "numero": _safe_float(row.get("Detratores"), 2),
                "texto": _format_big_number_ptbr(row.get("Detratores"))
            },
            "impacto_inocuo": {
                "label": "Impacto Inócuo",
                "numero": _safe_float(row.get("Inócuos"), 2),
                "texto": _format_big_number_ptbr(row.get("Inócuos"))
            },
            "impacto_total": {
                "label": "Impacto Total",
                "numero": _safe_float(row.get("alcance"), 2),
                "texto": _format_big_number_ptbr(row.get("alcance"))
            },
            "publicacoes_detratoras": {
                "label": "Publicações Detratoras",
                "numero": _safe_int(row.get("Publicações Detratoras"))
            },
            "publicacoes_inocuas": {
                "label": "Publicações Inócuas",
                "numero": _safe_int(row.get("Publicações Inócuas"))
            },
            "publicacoes_promotoras": {
                "label": "Publicações Promotoras",
                "numero": _safe_int(row.get("Publicações Promotoras"))
            },
            "publicacoes_totais": {
                "label": "Publicações Totais",
                "numero": _safe_int(row.get("frequencia"))
            },
        }
    }


def _build_company_output(
    df: pd.DataFrame,
    company_name: str,
    tipo_empresa: str,
    period_col: str,
    last_n_periods: int = 3
) -> Dict[str, Any]:
    company_df = df[
        df["Empresa analisada"].astype(str).str.lower().str.strip()
        == company_name.lower().strip()
    ].copy()

    if company_df.empty:
        return {
            "empresa_analisada": company_name,
            "tipo_empresa": tipo_empresa,
            "periodo": _detect_period_label(period_col),
            "big_numbers": []
        }

    company_df = _sort_period_df(company_df, period_col).head(last_n_periods)

    big_numbers = [
        _build_period_big_number_record(row=row, period_col=period_col)
        for _, row in company_df.iterrows()
    ]

    return {
        "empresa_analisada": company_name,
        "tipo_empresa": tipo_empresa,
        "periodo": _detect_period_label(period_col),
        "big_numbers": big_numbers
    }


def build_media_big_numbers_multi_company(
    index_df: pd.DataFrame,
    client: str,
    competitors: Optional[List[str]] = None,
    period_col: Optional[str] = None,
    last_n_periods: int = 3,
) -> Dict[str, Any]:
    """
    Retorna os big numbers do cliente e, opcionalmente, dos concorrentes,
    para os N períodos mais recentes.

    Parâmetros
    ----------
    index_df : pd.DataFrame
        DataFrame retornado pela build_media_metrics_view.
    client : str
        Nome do cliente.
    competitors : list[str] | None
        Lista de concorrentes.
    period_col : str | None
        Coluna de período ('semana', 'mes', 'mês'). Se None, detecta automaticamente.
    last_n_periods : int
        Quantidade de períodos mais recentes a retornar. Default = 3.

    Retorno
    -------
    dict
        Estrutura pronta para JSON/LLM/PPT.
    """
    if "Empresa analisada" not in index_df.columns:
        raise KeyError("A coluna 'Empresa analisada' não existe no DataFrame.")

    df = index_df.copy()

    if period_col is None:
        period_col = _detect_period_col(df)

    if period_col not in df.columns:
        raise KeyError(f"A coluna de período '{period_col}' não existe no DataFrame.")

    competitors = competitors or []

    empresas = [
        _build_company_output(
            df=df,
            company_name=client,
            tipo_empresa="cliente",
            period_col=period_col,
            last_n_periods=last_n_periods
        )
    ]

    for comp in competitors:
        empresas.append(
            _build_company_output(
                df=df,
                company_name=comp,
                tipo_empresa="concorrente",
                period_col=period_col,
                last_n_periods=last_n_periods
            )
        )

    return {
        "periodo": _detect_period_label(period_col),
        "empresas": empresas
    }


# =========================================================
# HELPERS
# =========================================================
def _detect_period_col(df: pd.DataFrame) -> str:
    if "semana" in df.columns:
        return "semana"
    if "mes" in df.columns:
        return "mes"
    if "mês" in df.columns:
        return "mês"
    raise KeyError("Não foi possível detectar a coluna de período ('semana', 'mes' ou 'mês').")


def _detect_period_label(period_col: str) -> str:
    mapping = {
        "semana": "semana",
        "mes": "mês",
        "mês": "mês",
    }
    return mapping.get(period_col.lower(), period_col.lower())


def _sort_period_df(df: pd.DataFrame, period_col: str) -> pd.DataFrame:
    """
    Ordena do mais recente para o mais antigo.
    Prioriza *_index se existir.
    Assume:
    0 = período mais recente
    1 = anterior
    2 = anterior ao anterior
    """
    df = df.copy()
    index_col = f"{period_col}_index"

    if index_col in df.columns:
        return df.sort_values(index_col, ascending=True).copy()

    tmp = df.copy()
    tmp["_period_sort"] = pd.to_datetime(tmp[period_col], errors="coerce")
    if tmp["_period_sort"].notna().sum() > 0:
        tmp = tmp.sort_values("_period_sort", ascending=False)
        return tmp.drop(columns="_period_sort")

    return df.sort_values(period_col, ascending=False).copy()


def _safe_float(value: Any, decimals: int = 2) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value), decimals)


def _safe_int(value: Any) -> int:
    if value is None or pd.isna(value):
        return 0
    return int(round(float(value)))


def _safe_percent_score(value: Any, decimals: int = 2) -> float:
    """
    Converte score proporcional para percentual.
    Ex.: 0.4231 -> 42.31
    """
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value) * 100, decimals)


def _format_big_number_ptbr(value: float | int | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "0"

    value = float(value)
    abs_value = abs(value)

    if abs_value >= 1_000_000_000:
        scaled = value / 1_000_000_000
        suffix = " bi"
    elif abs_value >= 1_000_000:
        scaled = value / 1_000_000
        suffix = " M"
    elif abs_value >= 1_000:
        scaled = value / 1_000
        suffix = " mil"
    else:
        if value.is_integer():
            return str(int(value))
        return f"{value:.{decimals}f}".replace(".", ",")

    return f"{scaled:.{decimals}f}".replace(".", ",") + suffix


def _pct_change(current: float, base: float, decimals: int = 2) -> float:
    """
    Variação percentual.
    """
    if pd.isna(base) or base == 0:
        return 0.0
    return round(((current - base) / abs(base)) * 100, decimals)


def _pp_change(current: float, base: float, decimals: int = 2) -> float:
    """
    Variação em pontos percentuais.
    """
    if pd.isna(base):
        return 0.0
    return round(current - base, decimals)


def _std_series(series: pd.Series) -> float:
    if len(series.dropna()) <= 1:
        return 0.0
    return float(series.std(ddof=1))


def _coef_var(mean_: float, std_: float, decimals: int = 2) -> float:
    if mean_ == 0 or pd.isna(mean_):
        return 0.0
    return round((std_ / abs(mean_)) * 100, decimals)


def _z_score(current: float, mean_: float, std_: float, decimals: int = 2) -> float:
    if std_ == 0 or pd.isna(std_):
        return 0.0
    return round((current - mean_) / std_, decimals)


# =========================================================
# CORE METRIC STATS
# =========================================================
def _build_metric_stats(
    company_df: pd.DataFrame,
    metric_col: str,
    period_col: str,
    label: str,
    variation_type: str = "percent",  # "percent" | "pp"
    formatter: str = "float",         # "float" | "int" | "big_number" | "score_percent"
) -> Dict[str, Any]:
    """
    Retorna as estatísticas de uma métrica para o último período.
    company_df já deve estar ordenado do mais recente para o mais antigo.
    """
    df = company_df[[period_col, metric_col]].copy()
    df = df.dropna(subset=[metric_col])

    if df.empty:
        return {
            "label": label,
            "periodo_atual": None,
            "valor_atual": 0,
            "variacao_vs_periodo_anterior": 0,
            "variacao_vs_media_historica": 0,
            "media": 0,
            "mediana": 0,
            "desvio_padrao": 0,
            "coeficiente_variacao": 0,
            "maximo": {"valor": 0, "periodo": None},
            "minimo": {"valor": 0, "periodo": None},
            "z_score_periodo": 0,
        }

    # normaliza valores conforme tipo do indicador
    if formatter == "score_percent":
        df["_value"] = df[metric_col].apply(_safe_percent_score)
    elif formatter == "int":
        df["_value"] = df[metric_col].apply(_safe_int)
    else:
        df["_value"] = df[metric_col].astype(float)

    current_period = df.iloc[0][period_col]
    current_value = float(df.iloc[0]["_value"])

    prev_value = float(df.iloc[1]["_value"]) if len(df) > 1 else np.nan

    hist_series = df["_value"].astype(float)
    mean_ = float(hist_series.mean()) if len(hist_series) > 0 else 0.0
    median_ = float(hist_series.median()) if len(hist_series) > 0 else 0.0
    std_ = _std_series(hist_series)
    cv_ = _coef_var(mean_, std_)
    z_ = _z_score(current_value, mean_, std_)

    idx_max = hist_series.idxmax()
    idx_min = hist_series.idxmin()

    max_value = float(df.loc[idx_max, "_value"])
    min_value = float(df.loc[idx_min, "_value"])
    max_period = df.loc[idx_max, period_col]
    min_period = df.loc[idx_min, period_col]

    if variation_type == "pp":
        var_prev = _pp_change(current_value, prev_value)
        var_hist = _pp_change(current_value, mean_)
        unidade_var = "p.p."
    else:
        var_prev = _pct_change(current_value, prev_value)
        var_hist = _pct_change(current_value, mean_)
        unidade_var = "%"

    # apresentação final
    if formatter == "int":
        current_value_out = _safe_int(current_value)
        mean_out = round(mean_, 2)
        median_out = round(median_, 2)
        std_out = round(std_, 2)
        max_out = _safe_int(max_value)
        min_out = _safe_int(min_value)
    elif formatter == "big_number":
        current_value_out = round(current_value, 2)
        mean_out = round(mean_, 2)
        median_out = round(median_, 2)
        std_out = round(std_, 2)
        max_out = round(max_value, 2)
        min_out = round(min_value, 2)
    elif formatter == "score_percent":
        current_value_out = round(current_value, 2)
        mean_out = round(mean_, 2)
        median_out = round(median_, 2)
        std_out = round(std_, 2)
        max_out = round(max_value, 2)
        min_out = round(min_value, 2)
    else:
        current_value_out = round(current_value, 2)
        mean_out = round(mean_, 2)
        median_out = round(median_, 2)
        std_out = round(std_, 2)
        max_out = round(max_value, 2)
        min_out = round(min_value, 2)

    result = {
        "label": label,
        "periodo_atual": current_period,
        "valor_atual": current_value_out,
        "variacao_vs_periodo_anterior": {
            "valor": var_prev,
            "unidade": unidade_var
        },
        "variacao_vs_media_historica": {
            "valor": var_hist,
            "unidade": unidade_var
        },
        "media": mean_out,
        "mediana": median_out,
        "desvio_padrao": std_out,
        "coeficiente_variacao": cv_,
        "maximo": {
            "valor": max_out,
            "periodo": max_period
        },
        "minimo": {
            "valor": min_out,
            "periodo": min_period
        },
        "z_score_periodo": z_
    }

    # campos extras úteis para big numbers
    if formatter == "big_number":
        result["valor_atual_texto"] = _format_big_number_ptbr(current_value_out)
        result["media_texto"] = _format_big_number_ptbr(mean_out)
        result["maximo"]["texto"] = _format_big_number_ptbr(max_out)
        result["minimo"]["texto"] = _format_big_number_ptbr(min_out)

    return result


# =========================================================
# COMPANY OUTPUT
# =========================================================
def _build_company_statistics_output(
    df: pd.DataFrame,
    company_name: str,
    tipo_empresa: str,
    period_col: str,
) -> Dict[str, Any]:
    company_df = df[
        df["Empresa analisada"].astype(str).str.lower().str.strip()
        == company_name.lower().strip()
    ].copy()

    if company_df.empty:
        return {
            "empresa_analisada": company_name,
            "tipo_empresa": tipo_empresa,
            "periodo": _detect_period_label(period_col),
            "estatisticas_ultimo_periodo": {}
        }

    company_df = _sort_period_df(company_df, period_col)

    stats = {
        "nps": _build_metric_stats(
            company_df=company_df,
            metric_col="nps_score",
            period_col=period_col,
            label="NPS",
            variation_type="pp",
            formatter="score_percent",
        ),
        "protagonismo": _build_metric_stats(
            company_df=company_df,
            metric_col="protagonism_score",
            period_col=period_col,
            label="Protagonismo",
            variation_type="pp",
            formatter="score_percent",
        ),
        "impacto_promotor": _build_metric_stats(
            company_df=company_df,
            metric_col="Promotores",
            period_col=period_col,
            label="Impacto Promotor",
            variation_type="percent",
            formatter="big_number",
        ),
        "impacto_detrator": _build_metric_stats(
            company_df=company_df,
            metric_col="Detratores",
            period_col=period_col,
            label="Impacto Detrator",
            variation_type="percent",
            formatter="big_number",
        ),
        "impacto_inocuo": _build_metric_stats(
            company_df=company_df,
            metric_col="Inócuos",
            period_col=period_col,
            label="Impacto Inócuo",
            variation_type="percent",
            formatter="big_number",
        ),
        "impacto_total": _build_metric_stats(
            company_df=company_df,
            metric_col="alcance",
            period_col=period_col,
            label="Impacto Total",
            variation_type="percent",
            formatter="big_number",
        ),
        "publicacoes_detratoras": _build_metric_stats(
            company_df=company_df,
            metric_col="Publicações Detratoras",
            period_col=period_col,
            label="Publicações Detratoras",
            variation_type="percent",
            formatter="int",
        ),
        "publicacoes_inocuas": _build_metric_stats(
            company_df=company_df,
            metric_col="Publicações Inócuas",
            period_col=period_col,
            label="Publicações Inócuas",
            variation_type="percent",
            formatter="int",
        ),
        "publicacoes_promotoras": _build_metric_stats(
            company_df=company_df,
            metric_col="Publicações Promotoras",
            period_col=period_col,
            label="Publicações Promotoras",
            variation_type="percent",
            formatter="int",
        ),
        "publicacoes_totais": _build_metric_stats(
            company_df=company_df,
            metric_col="frequencia",
            period_col=period_col,
            label="Publicações Totais",
            variation_type="percent",
            formatter="int",
        ),
    }

    ultimo_periodo = company_df.iloc[0][period_col]

    return {
        "empresa_analisada": company_name,
        "tipo_empresa": tipo_empresa,
        "periodo": _detect_period_label(period_col),
        "estatisticas_ultimo_periodo": {
            "periodo_referencia": ultimo_periodo,
            "indicadores": stats
        }
    }


# =========================================================
# MAIN
# =========================================================
def build_media_statistics_last_period(
    index_df: pd.DataFrame,
    client: str,
    competitors: Optional[List[str]] = None,
    period_col: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retorna um dicionário com as estatísticas do último período
    para cliente e concorrentes.

    Regras:
    - nps_score e protagonism_score:
        * convertidos para %
        * variação em p.p.
    - alcance, promotores, detratores, inócuos e publicações:
        * variação em %

    Estrutura:
    {
        "periodo": "semana" | "mês",
        "empresas": [
            {
                "empresa_analisada": "...",
                "tipo_empresa": "cliente" | "concorrente",
                "periodo": "...",
                "estatisticas_ultimo_periodo": {
                    "periodo_referencia": "...",
                    "indicadores": {...}
                }
            }
        ]
    }
    """
    if "Empresa analisada" not in index_df.columns:
        raise KeyError("A coluna 'Empresa analisada' não existe no DataFrame.")

    df = index_df.copy()

    if period_col is None:
        period_col = _detect_period_col(df)

    if period_col not in df.columns:
        raise KeyError(f"A coluna de período '{period_col}' não existe no DataFrame.")

    competitors = competitors or []

    empresas = [
        _build_company_statistics_output(
            df=df,
            company_name=client,
            tipo_empresa="cliente",
            period_col=period_col,
        )
    ]

    for comp in competitors:
        empresas.append(
            _build_company_statistics_output(
                df=df,
                company_name=comp,
                tipo_empresa="concorrente",
                period_col=period_col,
            )
        )

    return {
        "periodo": _detect_period_label(period_col),
        "empresas": empresas
    }


from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# =========================================================
# HELPERS
# =========================================================
def _detect_period_col(df: pd.DataFrame) -> str:
    if "semana" in df.columns:
        return "semana"
    if "mes" in df.columns:
        return "mes"
    if "mês" in df.columns:
        return "mês"
    raise KeyError("Não foi possível detectar a coluna de período.")


def _detect_period_label(period_col: str) -> str:
    if period_col == "semana":
        return "semana"
    if period_col in ["mes", "mês"]:
        return "mês"
    return period_col


def _safe_float(value: Any, decimals: int = 2) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value), decimals)


def _safe_int(value: Any) -> int:
    if value is None or pd.isna(value):
        return 0
    return int(round(float(value)))


def _safe_score_percent(value: Any, decimals: int = 2) -> float:
    """
    Para nps_score e protagonism_score em escala 0-1.
    Ex.: 0.42 -> 42.00
    """
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value) * 100, decimals)


def _format_big_number_ptbr(value: float | int | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "0"

    value = float(value)
    abs_value = abs(value)

    if abs_value >= 1_000_000_000:
        scaled = value / 1_000_000_000
        suffix = " bi"
    elif abs_value >= 1_000_000:
        scaled = value / 1_000_000
        suffix = " M"
    elif abs_value >= 1_000:
        scaled = value / 1_000
        suffix = " mil"
    else:
        if value.is_integer():
            return str(int(value))
        return f"{value:.{decimals}f}".replace(".", ",")

    return f"{scaled:.{decimals}f}".replace(".", ",") + suffix


def _pct_change(current: float, base: float, decimals: int = 2) -> Optional[float]:
    if pd.isna(base) or base == 0:
        return None
    return round(((current - base) / abs(base)) * 100, decimals)


def _pp_change(current: float, base: float, decimals: int = 2) -> Optional[float]:
    if pd.isna(base):
        return None
    return round(current - base, decimals)


def _std_series(series: pd.Series) -> float:
    s = series.dropna()
    if len(s) <= 1:
        return 0.0
    return float(s.std(ddof=1))


def _z_score(current: float, mean_: float, std_: float, decimals: int = 2) -> float:
    if std_ == 0 or pd.isna(std_):
        return 0.0
    return round((current - mean_) / std_, decimals)


def _sort_period_df(df: pd.DataFrame, period_col: str) -> pd.DataFrame:
    """
    Ordena do mais recente para o mais antigo.
    Prioriza *_index se existir.
    """
    df = df.copy()
    index_col = f"{period_col}_index"

    if index_col in df.columns:
        return df.sort_values(index_col, ascending=True).copy()

    tmp = df.copy()
    tmp["_period_dt"] = pd.to_datetime(tmp[period_col], errors="coerce")
    if tmp["_period_dt"].notna().sum() > 0:
        tmp = tmp.sort_values("_period_dt", ascending=False)
        return tmp.drop(columns="_period_dt")

    return df.sort_values(period_col, ascending=False).copy()


# =========================================================
# CORE
# =========================================================
def _build_source_metric_stats(
    source_history_df: pd.DataFrame,
    metric_col: str,
    period_col: str,
    label: str,
    variation_type: str = "percent",   # "percent" | "pp"
    formatter: str = "float",          # "float" | "int" | "big_number" | "score_percent"
) -> Dict[str, Any]:
    """
    Estatísticas da métrica para uma fonte específica.
    source_history_df deve conter apenas uma Fonte e uma Empresa analisada.
    Deve estar ordenado do mais recente para o mais antigo.
    """
    df = source_history_df[[period_col, metric_col]].copy()
    df = df.dropna(subset=[metric_col])

    if df.empty:
        return {
            "label": label,
            "valor_atual": 0,
            "variacao_vs_periodo_anterior": {"valor": None, "unidade": "p.p." if variation_type == "pp" else "%"},
            "variacao_vs_media_historica": {"valor": None, "unidade": "p.p." if variation_type == "pp" else "%"},
            "media_historica": 0,
            "mediana": 0,
            "desvio_padrao": 0,
            "z_score_periodo": 0,
        }

    if formatter == "score_percent":
        df["_value"] = df[metric_col].apply(_safe_score_percent)
    elif formatter == "int":
        df["_value"] = df[metric_col].apply(_safe_int)
    else:
        df["_value"] = df[metric_col].astype(float)

    current_value = float(df.iloc[0]["_value"])
    prev_value = float(df.iloc[1]["_value"]) if len(df) > 1 else np.nan

    hist_series = df["_value"].astype(float)
    mean_ = float(hist_series.mean()) if len(hist_series) > 0 else 0.0
    median_ = float(hist_series.median()) if len(hist_series) > 0 else 0.0
    std_ = _std_series(hist_series)
    z_ = _z_score(current_value, mean_, std_)

    if variation_type == "pp":
        var_prev = _pp_change(current_value, prev_value)
        var_hist = _pp_change(current_value, mean_)
        unit = "p.p."
    else:
        var_prev = _pct_change(current_value, prev_value)
        var_hist = _pct_change(current_value, mean_)
        unit = "%"

    result = {
        "label": label,
        "valor_atual": _safe_int(current_value) if formatter == "int" else round(current_value, 2),
        "variacao_vs_periodo_anterior": {
            "valor": var_prev,
            "unidade": unit,
        },
        "variacao_vs_media_historica": {
            "valor": var_hist,
            "unidade": unit,
        },
        "media_historica": round(mean_, 2),
        "mediana": round(median_, 2),
        "desvio_padrao": round(std_, 2),
        "z_score_periodo": z_,
    }

    if formatter == "big_number":
        result["valor_atual_texto"] = _format_big_number_ptbr(result["valor_atual"])
        result["media_historica_texto"] = _format_big_number_ptbr(result["media_historica"])

    return result



from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# =========================================================
# HELPERS
# =========================================================
def _detect_period_col(df: pd.DataFrame) -> str:
    if "semana" in df.columns:
        return "semana"
    if "mes" in df.columns:
        return "mes"
    if "mês" in df.columns:
        return "mês"
    raise KeyError("Não foi possível detectar a coluna de período.")


def _detect_period_label(period_col: str) -> str:
    if period_col == "semana":
        return "semana"
    if period_col in ["mes", "mês"]:
        return "mês"
    return period_col


def _safe_float(value: Any, decimals: int = 2) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value), decimals)


def _safe_int(value: Any) -> int:
    if value is None or pd.isna(value):
        return 0
    return int(round(float(value)))


def _safe_score_percent(value: Any, decimals: int = 2) -> float:
    """
    Para nps_score e protagonism_score em escala 0-1.
    Ex.: 0.42 -> 42.00
    """
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value) * 100, decimals)


def _format_big_number_ptbr(value: float | int | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "0"

    value = float(value)
    abs_value = abs(value)

    if abs_value >= 1_000_000_000:
        scaled = value / 1_000_000_000
        suffix = " bi"
    elif abs_value >= 1_000_000:
        scaled = value / 1_000_000
        suffix = " M"
    elif abs_value >= 1_000:
        scaled = value / 1_000
        suffix = " mil"
    else:
        if value.is_integer():
            return str(int(value))
        return f"{value:.{decimals}f}".replace(".", ",")

    return f"{scaled:.{decimals}f}".replace(".", ",") + suffix


def _pct_change(current: float, base: float, decimals: int = 2) -> Optional[float]:
    if pd.isna(base) or base == 0:
        return None
    return round(((current - base) / abs(base)) * 100, decimals)


def _pp_change(current: float, base: float, decimals: int = 2) -> Optional[float]:
    if pd.isna(base):
        return None
    return round(current - base, decimals)


def _std_series(series: pd.Series) -> float:
    s = series.dropna()
    if len(s) <= 1:
        return 0.0
    return float(s.std(ddof=1))


def _z_score(current: float, mean_: float, std_: float, decimals: int = 2) -> float:
    if std_ == 0 or pd.isna(std_):
        return 0.0
    return round((current - mean_) / std_, decimals)


def _sort_period_df(df: pd.DataFrame, period_col: str) -> pd.DataFrame:
    """
    Ordena do mais recente para o mais antigo.
    Prioriza *_index se existir.
    """
    df = df.copy()
    index_col = f"{period_col}_index"

    if index_col in df.columns:
        return df.sort_values(index_col, ascending=True).copy()

    tmp = df.copy()
    tmp["_period_dt"] = pd.to_datetime(tmp[period_col], errors="coerce")
    if tmp["_period_dt"].notna().sum() > 0:
        tmp = tmp.sort_values("_period_dt", ascending=False)
        return tmp.drop(columns="_period_dt")

    return df.sort_values(period_col, ascending=False).copy()


# =========================================================
# CORE MÉTRICA POR FONTE
# =========================================================
def _build_source_metric_stats(
    source_history_df: pd.DataFrame,
    metric_col: str,
    period_col: str,
    label: str,
    variation_type: str = "percent",   # "percent" | "pp"
    formatter: str = "float",          # "float" | "int" | "big_number" | "score_percent"
) -> Dict[str, Any]:
    """
    Estatísticas da métrica para uma fonte específica.
    source_history_df deve conter apenas uma Fonte e uma Empresa analisada.
    """
    df = source_history_df[[period_col, metric_col]].copy()
    df = df.dropna(subset=[metric_col])

    if df.empty:
        return {
            "label": label,
            "valor_atual": 0,
            "variacao_vs_periodo_anterior": {
                "valor": None,
                "unidade": "p.p." if variation_type == "pp" else "%"
            },
            "variacao_vs_media_historica": {
                "valor": None,
                "unidade": "p.p." if variation_type == "pp" else "%"
            },
            "media_historica": 0,
            "mediana": 0,
            "desvio_padrao": 0,
            "z_score_periodo": 0,
        }

    if formatter == "score_percent":
        df["_value"] = df[metric_col].apply(_safe_score_percent)
    elif formatter == "int":
        df["_value"] = df[metric_col].apply(_safe_int)
    else:
        df["_value"] = df[metric_col].astype(float)

    current_value = float(df.iloc[0]["_value"])
    prev_value = float(df.iloc[1]["_value"]) if len(df) > 1 else np.nan

    hist_series = df["_value"].astype(float)
    mean_ = float(hist_series.mean()) if len(hist_series) > 0 else 0.0
    median_ = float(hist_series.median()) if len(hist_series) > 0 else 0.0
    std_ = _std_series(hist_series)
    z_ = _z_score(current_value, mean_, std_)

    if variation_type == "pp":
        var_prev = _pp_change(current_value, prev_value)
        var_hist = _pp_change(current_value, mean_)
        unit = "p.p."
    else:
        var_prev = _pct_change(current_value, prev_value)
        var_hist = _pct_change(current_value, mean_)
        unit = "%"

    result = {
        "label": label,
        "valor_atual": _safe_int(current_value) if formatter == "int" else round(current_value, 2),
        "variacao_vs_periodo_anterior": {
            "valor": var_prev,
            "unidade": unit,
        },
        "variacao_vs_media_historica": {
            "valor": var_hist,
            "unidade": unit,
        },
        "media_historica": round(mean_, 2),
        "mediana": round(median_, 2),
        "desvio_padrao": round(std_, 2),
        "z_score_periodo": z_,
    }

    if formatter == "big_number":
        result["valor_atual_texto"] = _format_big_number_ptbr(result["valor_atual"])
        result["media_historica_texto"] = _format_big_number_ptbr(result["media_historica"])

    return result


# =========================================================
# EMPRESA
# =========================================================
def _build_company_sources_last_period(
    company_df: pd.DataFrame,
    company_name: str,
    tipo_empresa: str,
    period_col: str,
    include_metrics: Optional[List[str]] = None,
    sort_by: str = "alcance",
    ascending: bool = False,
) -> Dict[str, Any]:
    """
    Retorna as fontes do último período para uma empresa específica.
    """
    if company_df.empty:
        return {
            "empresa_analisada": company_name,
            "tipo_empresa": tipo_empresa,
            "fontes": []
        }

    company_df = _sort_period_df(company_df, period_col)

    last_period = company_df.iloc[0][period_col]
    current_period_df = company_df[company_df[period_col] == last_period].copy()

    if sort_by in current_period_df.columns:
        current_period_df = current_period_df.sort_values(sort_by, ascending=ascending)

    if include_metrics is None:
        include_metrics = [
            "nps",
            "protagonismo",
            "impacto_total",
            "impacto_promotor",
            "impacto_detrator",
            "impacto_inocuo",
            "publicacoes_totais",
            "publicacoes_promotoras",
            "publicacoes_detratoras",
            "publicacoes_inocuas",
        ]

    source_records = []

    for _, current_row in current_period_df.iterrows():
        fonte = current_row["Fonte"]
        midia = current_row["Mídia"] if "Mídia" in current_row.index else None

        source_history_df = company_df[company_df["Fonte"] == fonte].copy()
        source_history_df = _sort_period_df(source_history_df, period_col)

        indicadores = {}

        if "nps" in include_metrics:
            indicadores["nps"] = _build_source_metric_stats(
                source_history_df=source_history_df,
                metric_col="nps_score",
                period_col=period_col,
                label="NPS",
                variation_type="pp",
                formatter="score_percent",
            )

        if "protagonismo" in include_metrics:
            indicadores["protagonismo"] = _build_source_metric_stats(
                source_history_df=source_history_df,
                metric_col="protagonism_score",
                period_col=period_col,
                label="Protagonismo",
                variation_type="pp",
                formatter="score_percent",
            )

        if "impacto_total" in include_metrics:
            indicadores["impacto_total"] = _build_source_metric_stats(
                source_history_df=source_history_df,
                metric_col="alcance",
                period_col=period_col,
                label="Impacto Total",
                variation_type="percent",
                formatter="big_number",
            )

        if "impacto_promotor" in include_metrics:
            indicadores["impacto_promotor"] = _build_source_metric_stats(
                source_history_df=source_history_df,
                metric_col="Promotores",
                period_col=period_col,
                label="Impacto Promotor",
                variation_type="percent",
                formatter="big_number",
            )

        if "impacto_detrator" in include_metrics:
            indicadores["impacto_detrator"] = _build_source_metric_stats(
                source_history_df=source_history_df,
                metric_col="Detratores",
                period_col=period_col,
                label="Impacto Detrator",
                variation_type="percent",
                formatter="big_number",
            )

        if "impacto_inocuo" in include_metrics:
            indicadores["impacto_inocuo"] = _build_source_metric_stats(
                source_history_df=source_history_df,
                metric_col="Inócuos",
                period_col=period_col,
                label="Impacto Inócuo",
                variation_type="percent",
                formatter="big_number",
            )

        if "publicacoes_totais" in include_metrics:
            indicadores["publicacoes_totais"] = _build_source_metric_stats(
                source_history_df=source_history_df,
                metric_col="frequencia",
                period_col=period_col,
                label="Publicações Totais",
                variation_type="percent",
                formatter="int",
            )

        if "publicacoes_promotoras" in include_metrics:
            indicadores["publicacoes_promotoras"] = _build_source_metric_stats(
                source_history_df=source_history_df,
                metric_col="Publicações Promotoras",
                period_col=period_col,
                label="Publicações Promotoras",
                variation_type="percent",
                formatter="int",
            )

        if "publicacoes_detratoras" in include_metrics:
            indicadores["publicacoes_detratoras"] = _build_source_metric_stats(
                source_history_df=source_history_df,
                metric_col="Publicações Detratoras",
                period_col=period_col,
                label="Publicações Detratoras",
                variation_type="percent",
                formatter="int",
            )

        if "publicacoes_inocuas" in include_metrics:
            indicadores["publicacoes_inocuas"] = _build_source_metric_stats(
                source_history_df=source_history_df,
                metric_col="Publicações Inócuas",
                period_col=period_col,
                label="Publicações Inócuas",
                variation_type="percent",
                formatter="int",
            )

        source_records.append(
            {
                "fonte": fonte,
                "midia": midia,
                "indicadores": indicadores,
            }
        )

    return {
        "empresa_analisada": company_name,
        "tipo_empresa": tipo_empresa,
        "fontes": source_records,
    }


# =========================================================
# MAIN
# =========================================================
def build_sources_last_period_multi_company_dict(
    fonte_df: pd.DataFrame,
    client: str,
    competitors: Optional[List[str]] = None,
    period_col: Optional[str] = None,
    include_metrics: Optional[List[str]] = None,
    sort_by: str = "alcance",
    ascending: bool = False,
) -> Dict[str, Any]:
    """
    Retorna um dicionário com as fontes do último período
    para cliente e concorrentes.

    Estrutura:
    {
        "periodo": "mês" | "semana",
        "periodo_referencia": "...",
        "empresas": [
            {
                "empresa_analisada": "...",
                "tipo_empresa": "cliente" | "concorrente",
                "fontes": [...]
            }
        ]
    }
    """
    df = fonte_df.copy()

    if period_col is None:
        period_col = _detect_period_col(df)

    if "Empresa analisada" not in df.columns:
        raise KeyError("A coluna 'Empresa analisada' não existe no DataFrame.")

    if "Fonte" not in df.columns:
        raise KeyError("A coluna 'Fonte' não existe no DataFrame.")

    competitors = competitors or []

    all_companies = [(client, "cliente")] + [(c, "concorrente") for c in competitors]

    # define período de referência global a partir do cliente
    client_df = df[
        df["Empresa analisada"].astype(str).str.lower().str.strip()
        == client.lower().strip()
    ].copy()

    if client_df.empty:
        return {
            "periodo": _detect_period_label(period_col),
            "periodo_referencia": None,
            "empresas": []
        }

    client_df = _sort_period_df(client_df, period_col)
    periodo_referencia = client_df.iloc[0][period_col]

    empresas = []

    for company_name, tipo_empresa in all_companies:
        company_df = df[
            df["Empresa analisada"].astype(str).str.lower().str.strip()
            == company_name.lower().strip()
        ].copy()

        # opcionalmente, trava o output no mesmo período de referência do cliente
        if not company_df.empty:
            company_df = company_df[company_df[period_col] <= periodo_referencia].copy()
            company_df = _sort_period_df(company_df, period_col)

        empresas.append(
            _build_company_sources_last_period(
                company_df=company_df,
                company_name=company_name,
                tipo_empresa=tipo_empresa,
                period_col=period_col,
                include_metrics=include_metrics,
                sort_by=sort_by,
                ascending=ascending,
            )
        )

    return {
        "periodo": _detect_period_label(period_col),
        "periodo_referencia": periodo_referencia,
        "empresas": empresas,
    }

# =========================================================
# CAMADA DETERMINÍSTICA DE LEITURA DE PADRÃO DE MÍDIA
# =========================================================

from typing import Any, Dict, List, Optional, Sequence
import pandas as pd
import numpy as np


# =========================================================
# HELPERS GERAIS
# =========================================================
def _safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _normalize_tag(text: str) -> str:
    return (
        str(text)
        .strip()
        .lower()
        .replace("ç", "c")
        .replace("ã", "a")
        .replace("á", "a")
        .replace("à", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except Exception:
        return default


def _to_int(value: Any, default: int = 0) -> int:
    if value is None or pd.isna(value):
        return default
    try:
        return int(round(float(value)))
    except Exception:
        return default


# =========================================================
# RÉGUAS DETERMINÍSTICAS
# =========================================================
def classify_nps_band(nps_percent: float) -> Dict[str, Any]:
    """
    Régua:
    crise = -100 a -80
    atenção = -80 a 0
    regular = 0 a 35
    bom = 35 a 50
    ótimo = 50 a 80
    excelente = 80 a 100
    """
    nps_percent = _to_float(nps_percent)

    if nps_percent <= -80:
        return {
            "faixa": "crise",
            "tag": "nps_em_crise",
            "leitura": "qualidade reputacional em crise",
        }
    elif nps_percent < 0:
        return {
            "faixa": "atenção",
            "tag": "nps_em_atencao",
            "leitura": "qualidade reputacional sob atenção",
        }
    elif nps_percent < 35:
        return {
            "faixa": "regular",
            "tag": "nps_regular",
            "leitura": "qualidade reputacional regular",
        }
    elif nps_percent < 50:
        return {
            "faixa": "bom",
            "tag": "nps_bom",
            "leitura": "qualidade reputacional favorável",
        }
    elif nps_percent < 80:
        return {
            "faixa": "ótimo",
            "tag": "nps_otimo",
            "leitura": "qualidade reputacional muito favorável",
        }
    else:
        return {
            "faixa": "excelente",
            "tag": "nps_excelente",
            "leitura": "qualidade reputacional excelente",
        }


def classify_historical_position(z_score: float) -> Dict[str, Any]:
    z_score = _to_float(z_score)

    if z_score >= 2:
        return {
            "status": "muito acima da média histórica",
            "tag": "muito_acima_media_historica",
            "polaridade": "alta",
        }
    elif z_score >= 1:
        return {
            "status": "acima da média histórica",
            "tag": "acima_media_historica",
            "polaridade": "alta",
        }
    elif z_score > -1:
        return {
            "status": "dentro do padrão histórico",
            "tag": "dentro_padrao_historico",
            "polaridade": "normal",
        }
    elif z_score > -2:
        return {
            "status": "abaixo da média histórica",
            "tag": "abaixo_media_historica",
            "polaridade": "baixa",
        }
    else:
        return {
            "status": "muito abaixo da média histórica",
            "tag": "muito_abaixo_media_historica",
            "polaridade": "baixa",
        }


def classify_variation(value: Optional[float], unit: str) -> Dict[str, Any]:
    if value is None or pd.isna(value):
        return {
            "status": "sem base comparativa",
            "tag": "sem_base_comparativa",
            "valor": None,
            "unidade": unit,
        }

    value = _to_float(value)

    if unit == "p.p.":
        if value >= 5:
            return {"status": "melhora relevante", "tag": "melhora_relevante", "valor": value, "unidade": unit}
        elif value >= 1:
            return {"status": "melhora leve", "tag": "melhora_leve", "valor": value, "unidade": unit}
        elif value > -1:
            return {"status": "estabilidade", "tag": "estabilidade", "valor": value, "unidade": unit}
        elif value > -5:
            return {"status": "piora leve", "tag": "piora_leve", "valor": value, "unidade": unit}
        else:
            return {"status": "piora relevante", "tag": "piora_relevante", "valor": value, "unidade": unit}

    # %
    if value >= 20:
        return {"status": "alta relevante", "tag": "alta_relevante", "valor": value, "unidade": unit}
    elif value >= 5:
        return {"status": "leve alta", "tag": "leve_alta", "valor": value, "unidade": unit}
    elif value > -5:
        return {"status": "estabilidade", "tag": "estabilidade", "valor": value, "unidade": unit}
    elif value > -20:
        return {"status": "leve queda", "tag": "leve_queda", "valor": value, "unidade": unit}
    else:
        return {"status": "queda relevante", "tag": "queda_relevante", "valor": value, "unidade": unit}


def classify_stability(cv: Optional[float]) -> Dict[str, Any]:
    if cv is None or pd.isna(cv):
        return {
            "status": "indefinido",
            "tag": "estabilidade_indefinida",
        }

    cv = _to_float(cv)

    if cv <= 15:
        return {"status": "muito estável", "tag": "indicador_muito_estavel"}
    elif cv <= 30:
        return {"status": "estável", "tag": "indicador_estavel"}
    elif cv <= 60:
        return {"status": "volátil", "tag": "indicador_volatil"}
    else:
        return {"status": "muito volátil", "tag": "indicador_muito_volatil"}


def classify_protagonism_level(
    protagonism_percent: float,
    z_score: Optional[float] = None
) -> Dict[str, Any]:
    protagonism_percent = _to_float(protagonism_percent)
    hist = classify_historical_position(z_score if z_score is not None else 0.0)

    if protagonism_percent >= 70:
        base = {
            "faixa": "muito alto",
            "tag_base": "alta_chance_de_lembranca",
            "leitura": "alta chance de percepção e lembrança da marca",
        }
    elif protagonism_percent >= 40:
        base = {
            "faixa": "moderado",
            "tag_base": "chance_moderada_de_lembranca",
            "leitura": "chance moderada de percepção e lembrança da marca",
        }
    else:
        base = {
            "faixa": "baixo",
            "tag_base": "baixa_chance_de_lembranca",
            "leitura": "baixa chance de percepção e lembrança da marca",
        }

    return {
        **base,
        "status_historico": hist["status"],
        "tag_historico": hist["tag"],
    }


def classify_impact_balance(
    promotores: float,
    detratores: float,
    inocuos: float
) -> Dict[str, Any]:
    promotores = _to_float(promotores)
    detratores = _to_float(detratores)
    inocuos = _to_float(inocuos)

    values = {
        "promotores": promotores,
        "detratores": detratores,
        "inocuos": inocuos,
    }
    dominant = max(values, key=values.get)

    if dominant == "promotores":
        return {
            "dominancia": "promotores",
            "tag": "predominio_promotor",
            "leitura": "predomínio de exposição promotora",
        }
    elif dominant == "detratores":
        return {
            "dominancia": "detratores",
            "tag": "predominio_detrator",
            "leitura": "predomínio de exposição detratora",
        }
    else:
        return {
            "dominancia": "inocuos",
            "tag": "predominio_inocuo",
            "leitura": "predomínio de exposição inócua",
        }


# =========================================================
# LEITURA DETERMINÍSTICA POR INDICADOR
# =========================================================
def build_metric_deterministic_reading(metric_name: str, metric_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Espera a estrutura de cada indicador produzida pelas funções
    build_media_statistics_last_period / build_sources_last_period_multi_company_dict.
    """
    current_value = _safe_get(metric_payload, "valor_atual", default=0)
    var_prev = _safe_get(metric_payload, "variacao_vs_periodo_anterior", "valor", default=None)
    var_prev_unit = _safe_get(metric_payload, "variacao_vs_periodo_anterior", "unidade", default="%")
    var_hist = _safe_get(metric_payload, "variacao_vs_media_historica", "valor", default=None)
    var_hist_unit = _safe_get(metric_payload, "variacao_vs_media_historica", "unidade", default="%")
    cv = _safe_get(metric_payload, "coeficiente_variacao", default=None)
    z = _safe_get(metric_payload, "z_score_periodo", default=None)

    variation_prev = classify_variation(var_prev, var_prev_unit)
    variation_hist = classify_variation(var_hist, var_hist_unit)
    stability = classify_stability(cv)
    hist_pos = classify_historical_position(z if z is not None else 0.0)

    tags = [
        variation_prev["tag"],
        variation_hist["tag"],
        stability["tag"],
        hist_pos["tag"],
    ]

    reading: Dict[str, Any] = {
        "status_historico": hist_pos["status"],
        "status_variacao_vs_periodo_anterior": variation_prev["status"],
        "status_variacao_vs_media_historica": variation_hist["status"],
        "status_estabilidade": stability["status"],
        "tags": list(dict.fromkeys([t for t in tags if t])),
    }

    if metric_name == "nps":
        nps_band = classify_nps_band(current_value)
        reading.update(
            {
                "faixa_valor": nps_band["faixa"],
                "leitura_principal": nps_band["leitura"],
            }
        )
        reading["tags"] = list(dict.fromkeys(reading["tags"] + [nps_band["tag"]]))

    elif metric_name == "protagonismo":
        prot_band = classify_protagonism_level(current_value, z)
        reading.update(
            {
                "faixa_valor": prot_band["faixa"],
                "leitura_principal": prot_band["leitura"],
            }
        )
        reading["tags"] = list(
            dict.fromkeys(reading["tags"] + [prot_band["tag_base"], prot_band["tag_historico"]])
        )

    elif metric_name in {
        "impacto_total",
        "impacto_promotor",
        "impacto_detrator",
        "impacto_inocuo",
        "publicacoes_totais",
        "publicacoes_promotoras",
        "publicacoes_detratoras",
        "publicacoes_inocuas",
    }:
        reading.update(
            {
                "faixa_valor": None,
                "leitura_principal": "intensidade de exposição",
            }
        )

    return reading


# =========================================================
# PADRÃO COMPOSTO DO PERÍODO
# =========================================================
def build_period_media_pattern(indicadores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recebe o bloco `indicadores` do último período e devolve leitura consolidada.
    """
    nps = indicadores.get("nps", {})
    protagonismo = indicadores.get("protagonismo", {})
    impacto_total = indicadores.get("impacto_total", {})
    impacto_promotor = indicadores.get("impacto_promotor", {})
    impacto_detrator = indicadores.get("impacto_detrator", {})
    impacto_inocuo = indicadores.get("impacto_inocuo", {})

    nps_val = _to_float(nps.get("valor_atual", 0))
    prot_val = _to_float(protagonismo.get("valor_atual", 0))

    alcance_z = _to_float(impacto_total.get("z_score_periodo", 0))
    freq_var = _safe_get(indicadores, "publicacoes_totais", "variacao_vs_media_historica", "valor", default=0)
    freq_var = _to_float(freq_var, 0)

    prom = _to_float(impacto_promotor.get("valor_atual", 0))
    det = _to_float(impacto_detrator.get("valor_atual", 0))
    ino = _to_float(impacto_inocuo.get("valor_atual", 0))

    impact_balance = classify_impact_balance(prom, det, ino)

    tags_gerais: List[str] = []
    leituras_gerais: List[str] = []
    alertas: List[str] = []
    oportunidades: List[str] = []

    # regra 1: alta exposição sem qualidade
    if alcance_z >= 1 and nps_val < 35:
        tags_gerais.append("alta_exposicao_sem_qualidade_reputacional")
        leituras_gerais.append("O período teve intensidade de exposição acima do padrão histórico, mas sem qualidade reputacional proporcional.")
        alertas.append("Exposição alta não se converteu em percepção favorável.")

    # regra 2: presença inócua
    if impact_balance["dominancia"] == "inocuos":
        tags_gerais.append("presenca_midiatica_pouco_memoravel")
        leituras_gerais.append("A cobertura foi majoritariamente inócua, indicando presença midiática com baixa força de lembrança.")
        if prot_val < 40:
            tags_gerais.append("alto_volume_com_baixa_forca_de_lembranca")
            alertas.append("A marca apareceu, mas com baixa capacidade de fixação perceptiva.")

    # regra 3: cobertura eficiente
    if nps_val >= 35 and prot_val >= 40:
        tags_gerais.append("cobertura_fortalece_lembranca_favoravel")
        leituras_gerais.append("A cobertura combinou favorabilidade reputacional e capacidade de lembrança da marca.")
        oportunidades.append("Há espaço para amplificar narrativas já favoráveis.")

    # regra 4: pressão reputacional
    if impact_balance["dominancia"] == "detratores" and nps_val < 0:
        tags_gerais.append("pressao_reputacional_negativa")
        leituras_gerais.append("A composição dos impactos pressionou negativamente a leitura reputacional do período.")
        alertas.append("Predomínio detrator associado a NPS negativo.")

    # regra 5: boa qualidade em baixa escala
    if nps_val >= 35 and alcance_z <= -1:
        tags_gerais.append("boa_qualidade_com_baixa_escala")
        leituras_gerais.append("A reputação foi favorável, mas em escala abaixo do padrão histórico.")
        oportunidades.append("Narrativas favoráveis podem ser amplificadas para ganhar alcance.")

    # regra 6: intensidade forte
    if alcance_z >= 2 or freq_var >= 20:
        tags_gerais.append("intensidade_exposicao_muito_alta")
    elif alcance_z >= 1 or freq_var >= 5:
        tags_gerais.append("intensidade_exposicao_alta")
    elif alcance_z <= -2 or freq_var <= -20:
        tags_gerais.append("intensidade_exposicao_muito_baixa")
    elif alcance_z <= -1 or freq_var <= -5:
        tags_gerais.append("intensidade_exposicao_baixa")
    else:
        tags_gerais.append("intensidade_exposicao_normal")

    tags_gerais.append(impact_balance["tag"])
    leituras_gerais.append(impact_balance["leitura"])

    return {
        "tags_gerais": list(dict.fromkeys(tags_gerais)),
        "leituras_gerais": list(dict.fromkeys(leituras_gerais)),
        "alertas": list(dict.fromkeys(alertas)),
        "oportunidades": list(dict.fromkeys(oportunidades)),
    }


# =========================================================
# ENRIQUECIMENTO DO DICIONÁRIO DO ÚLTIMO PERÍODO
# =========================================================
def enrich_last_period_statistics_with_media_pattern(
    stats_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enriquecimento em cima da saída de build_media_statistics_last_period().
    """
    output = dict(stats_dict)
    empresas_out = []

    for empresa in output.get("empresas", []):
        empresa_cp = dict(empresa)
        est = empresa_cp.get("estatisticas_ultimo_periodo", {})
        indicadores = est.get("indicadores", {})

        indicadores_enriched = {}
        for metric_name, metric_payload in indicadores.items():
            metric_cp = dict(metric_payload)
            metric_cp["leitura_deterministica"] = build_metric_deterministic_reading(
                metric_name=metric_name,
                metric_payload=metric_cp,
            )
            indicadores_enriched[metric_name] = metric_cp

        est["indicadores"] = indicadores_enriched
        est["padrao_midia_periodo"] = build_period_media_pattern(indicadores_enriched)
        empresa_cp["estatisticas_ultimo_periodo"] = est
        empresas_out.append(empresa_cp)

    output["empresas"] = empresas_out
    return output


def build_media_statistics_last_period_enriched(
    index_df: pd.DataFrame,
    client: str,
    competitors: Optional[List[str]] = None,
    period_col: Optional[str] = None,
) -> Dict[str, Any]:
    base = build_media_statistics_last_period(
        index_df=index_df,
        client=client,
        competitors=competitors,
        period_col=period_col,
    )
    return enrich_last_period_statistics_with_media_pattern(base)


# =========================================================
# ENRIQUECIMENTO DAS FONTES DO ÚLTIMO PERÍODO
# =========================================================
def _build_source_pattern(indicadores: Dict[str, Any]) -> Dict[str, Any]:
    tags = []
    leituras = []
    alertas = []

    nps = indicadores.get("nps", {})
    prot = indicadores.get("protagonismo", {})
    impacto_total = indicadores.get("impacto_total", {})
    impacto_promotor = indicadores.get("impacto_promotor", {})
    impacto_detrator = indicadores.get("impacto_detrator", {})
    impacto_inocuo = indicadores.get("impacto_inocuo", {})

    nps_val = _to_float(nps.get("valor_atual", 0))
    prot_val = _to_float(prot.get("valor_atual", 0))
    alcance_z = _to_float(impacto_total.get("z_score_periodo", 0))

    prom = _to_float(impacto_promotor.get("valor_atual", 0))
    det = _to_float(impacto_detrator.get("valor_atual", 0))
    ino = _to_float(impacto_inocuo.get("valor_atual", 0))

    balance = classify_impact_balance(prom, det, ino)
    tags.append(balance["tag"])
    leituras.append(balance["leitura"])

    if nps_val >= 50:
        tags.append("fonte_com_nps_otimo")
        leituras.append("A fonte teve leitura reputacional muito favorável.")
    elif nps_val < 0:
        tags.append("fonte_com_pressao_reputacional")
        alertas.append("A fonte pressionou negativamente a percepção reputacional.")

    if prot_val >= 40:
        tags.append("fonte_com_boa_capacidade_de_lembranca")

    if alcance_z >= 1:
        tags.append("fonte_acima_da_media_historica_em_alcance")
    elif alcance_z <= -1:
        tags.append("fonte_abaixo_da_media_historica_em_alcance")

    if balance["dominancia"] == "inocuos":
        tags.append("fonte_com_presenca_inocua")

    return {
        "tags": list(dict.fromkeys(tags)),
        "leituras": list(dict.fromkeys(leituras)),
        "alertas": list(dict.fromkeys(alertas)),
    }


def enrich_sources_last_period_with_media_pattern(
    sources_dict: Dict[str, Any]
) -> Dict[str, Any]:
    output = dict(sources_dict)
    empresas_out = []

    for empresa in output.get("empresas", []):
        empresa_cp = dict(empresa)
        fontes_out = []

        for fonte in empresa_cp.get("fontes", []):
            fonte_cp = dict(fonte)
            indicadores = fonte_cp.get("indicadores", {})

            indicadores_enriched = {}
            for metric_name, metric_payload in indicadores.items():
                metric_cp = dict(metric_payload)
                metric_cp["leitura_deterministica"] = build_metric_deterministic_reading(
                    metric_name=metric_name,
                    metric_payload=metric_cp,
                )
                indicadores_enriched[metric_name] = metric_cp

            fonte_cp["indicadores"] = indicadores_enriched
            fonte_cp["padrao_fonte_periodo"] = _build_source_pattern(indicadores_enriched)
            fontes_out.append(fonte_cp)

        empresa_cp["fontes"] = fontes_out
        empresas_out.append(empresa_cp)

    output["empresas"] = empresas_out
    return output


def build_sources_last_period_multi_company_dict_enriched(
    fonte_df: pd.DataFrame,
    client: str,
    competitors: Optional[List[str]] = None,
    period_col: Optional[str] = None,
    include_metrics: Optional[List[str]] = None,
    sort_by: str = "alcance",
    ascending: bool = False,
) -> Dict[str, Any]:
    base = build_sources_last_period_multi_company_dict(
        fonte_df=fonte_df,
        client=client,
        competitors=competitors,
        period_col=period_col,
        include_metrics=include_metrics,
        sort_by=sort_by,
        ascending=ascending,
    )
    return enrich_sources_last_period_with_media_pattern(base)


# =========================================================
# DIÁRIO + CONTRIBUIÇÃO DE NPS
# =========================================================
def _build_daily_pattern_row(
    row: pd.Series,
    contrib_col: str = "nps_contrib_dia",
    zscore_col: str = "z-score_alcance",
    promoter_col: str = "Promotores",
    detractor_col: str = "Detratores",
    inocuous_col: str = "Inócuos",
    nps_daily_col: str = "nps_score_dia",
    protagonism_daily_col: str = "protagonism_score_dia",
) -> Dict[str, Any]:
    tags = []
    leituras = []
    alertas = []

    contrib = _to_float(row.get(contrib_col, 0))
    z_alcance = _to_float(row.get(zscore_col, 0))
    nps_daily = _to_float(row.get(nps_daily_col, 0)) * 100 if abs(_to_float(row.get(nps_daily_col, 0))) <= 1.0 else _to_float(row.get(nps_daily_col, 0))
    prot_daily = _to_float(row.get(protagonism_daily_col, 0)) * 100 if abs(_to_float(row.get(protagonism_daily_col, 0))) <= 1.0 else _to_float(row.get(protagonism_daily_col, 0))

    prom = _to_float(row.get(promoter_col, 0))
    det = _to_float(row.get(detractor_col, 0))
    ino = _to_float(row.get(inocuous_col, 0))

    balance = classify_impact_balance(prom, det, ino)
    tags.append(balance["tag"])

    if contrib >= 5:
        tags.append("dia_positivo_fora_da_curva")
        leituras.append("O dia teve contribuição positiva relevante para o NPS do período.")
    elif contrib <= -5:
        tags.append("dia_negativo_fora_da_curva")
        leituras.append("O dia teve contribuição negativa relevante para o NPS do período.")
        alertas.append("Dia com pressão negativa relevante sobre o resultado do período.")

    if z_alcance >= 2:
        tags.append("dia_com_exposicao_muito_acima_do_padrao")
    elif z_alcance >= 1:
        tags.append("dia_com_exposicao_acima_do_padrao")
    elif z_alcance <= -2:
        tags.append("dia_com_exposicao_muito_abaixo_do_padrao")
    elif z_alcance <= -1:
        tags.append("dia_com_exposicao_abaixo_do_padrao")

    nps_band = classify_nps_band(nps_daily)
    tags.append(nps_band["tag"])

    prot_band = classify_protagonism_level(prot_daily)
    tags.append(prot_band["tag_base"])

    if balance["dominancia"] == "detratores" and contrib < 0:
        tags.append("dia_com_alta_pressao_detratora")
        alertas.append("Predomínio detrator associado a contribuição negativa.")
    elif balance["dominancia"] == "promotores" and contrib > 0:
        tags.append("dia_com_predominio_promotor")
        leituras.append("O dia foi puxado por exposição promotora.")
    elif balance["dominancia"] == "inocuos":
        tags.append("dia_com_predominio_inocuo")
        leituras.append("O dia teve presença midiática mais inócua do que memorável.")

    return {
        "tags": list(dict.fromkeys(tags)),
        "leituras": list(dict.fromkeys(leituras)),
        "alertas": list(dict.fromkeys(alertas)),
    }


def build_daily_media_metrics_with_nps_contrib_enriched(
    dataview_df: pd.DataFrame,
    client: str | Sequence[str] | None = None,
    contest: str | Sequence[str] | None = None,
    *,
    focus_analysis: str = "Empresa analisada",
    period: str = "dia",
    contrib_dim_col: str = "dia",
    contrib_group_cols: Sequence[str] = ("mes", "mes_index", "Empresa analisada"),
    merge_how: str = "left",
    merge_validate: str = "one_to_one",
    rename_nps_daily: str = "nps_score_dia",
    rename_protagonism_daily: str = "protagonism_score_dia",
    rename_nps_contrib_base: str = "nps_score_mes",
    contrib_col_name: str = "nps_contrib_dia",
) -> pd.DataFrame:
    df = build_daily_media_metrics_with_nps_contrib(
        dataview_df=dataview_df,
        client=client,
        contest=contest,
        focus_analysis=focus_analysis,
        period=period,
        contrib_dim_col=contrib_dim_col,
        contrib_group_cols=contrib_group_cols,
        merge_how=merge_how,
        merge_validate=merge_validate,
        rename_nps_daily=rename_nps_daily,
        rename_protagonism_daily=rename_protagonism_daily,
        rename_nps_contrib_base=rename_nps_contrib_base,
    ).copy()

    # tenta identificar automaticamente a coluna de contribuição
    if contrib_col_name not in df.columns:
        possible_cols = [c for c in df.columns if "contrib" in c.lower() and "nps" in c.lower()]
        if possible_cols:
            contrib_col_name = possible_cols[0]

    df["padrao_midia_dia"] = df.apply(
        lambda row: _build_daily_pattern_row(
            row=row,
            contrib_col=contrib_col_name,
            zscore_col="z-score_alcance",
            promoter_col="Promotores",
            detractor_col="Detratores",
            inocuous_col="Inócuos",
            nps_daily_col=rename_nps_daily,
            protagonism_daily_col=rename_protagonism_daily,
        ),
        axis=1,
    )

    return df


# =========================================================
# DICIONÁRIO DIÁRIO PRONTO PARA LLM
# =========================================================
def build_daily_media_pattern_dict(
    contr_dia_df: pd.DataFrame,
    client: str,
    competitors: Optional[List[str]] = None,
    focus_analysis: str = "Empresa analisada",
    date_col: str = "dia",
    date_index_col: str = "dia_index",
    top_n_days: int = 10,
    contrib_col: str = "nps_contrib_dia",
) -> Dict[str, Any]:
    df = contr_dia_df.copy()
    competitors = competitors or []

    all_companies = [(client, "cliente")] + [(c, "concorrente") for c in competitors]

    empresas = []

    for company_name, tipo_empresa in all_companies:
        company_df = df[
            df[focus_analysis].astype(str).str.lower().str.strip()
            == company_name.lower().strip()
        ].copy()

        if company_df.empty:
            empresas.append(
                {
                    "empresa_analisada": company_name,
                    "tipo_empresa": tipo_empresa,
                    "dias": []
                }
            )
            continue

        if date_index_col in company_df.columns:
            company_df = company_df.sort_values(date_index_col, ascending=True).copy()
        else:
            company_df = company_df.sort_values(date_col, ascending=False).copy()

        # top dias por contribuição absoluta
        if contrib_col in company_df.columns:
            company_df["_abs_contrib"] = company_df[contrib_col].abs()
            top_days_df = company_df.sort_values("_abs_contrib", ascending=False).head(top_n_days).copy()
            top_days_df = top_days_df.drop(columns="_abs_contrib")
        else:
            top_days_df = company_df.head(top_n_days).copy()

        days = []
        for _, row in top_days_df.iterrows():
            padrao = row.get("padrao_midia_dia", {})
            days.append(
                {
                    "dia": row.get(date_col),
                    "nps_contrib_dia": row.get(contrib_col),
                    "nps_score_dia": row.get("nps_score_dia"),
                    "protagonism_score_dia": row.get("protagonism_score_dia"),
                    "alcance": row.get("alcance"),
                    "z_score_alcance": row.get("z-score_alcance"),
                    "Promotores": row.get("Promotores"),
                    "Detratores": row.get("Detratores"),
                    "Inócuos": row.get("Inócuos"),
                    "padrao_midia_dia": padrao,
                }
            )

        empresas.append(
            {
                "empresa_analisada": company_name,
                "tipo_empresa": tipo_empresa,
                "dias": days,
            }
        )

    return {
        "periodo": "dia",
        "empresas": empresas,
    }


####
## LLM assunto específico
####

from typing import Any, Dict, List, Optional
import pandas as pd


def _safe_percent_for_llm(value: Any, decimals: int = 2) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return round(float(value) * 100, decimals)


def _detect_topic_period_col(df: pd.DataFrame) -> str:
    for col in ["dia", "semana", "mes", "mês", "ano"]:
        if col in df.columns:
            return col
    raise KeyError("Não foi possível detectar a coluna de período.")


def _detect_topic_period_label(period_col: str) -> str:
    mapping = {
        "dia": "dia",
        "semana": "semana",
        "mes": "mês",
        "mês": "mês",
        "ano": "ano",
    }
    return mapping.get(period_col.lower(), period_col.lower())


def _sort_topic_period_df(df: pd.DataFrame, period_col: str) -> pd.DataFrame:
    df = df.copy()
    index_col = f"{period_col}_index"

    if index_col in df.columns:
        return df.sort_values(index_col, ascending=True).copy()

    tmp = df.copy()
    tmp["_period_sort"] = pd.to_datetime(tmp[period_col], errors="coerce")
    if tmp["_period_sort"].notna().sum() > 0:
        return tmp.sort_values("_period_sort", ascending=False).drop(columns="_period_sort")

    return df.sort_values(period_col, ascending=False).copy()


def _build_period_topics_block(
    company_period_df: pd.DataFrame,
    *,
    topic_col: str,
    period_col: str,
    contrib_col: str,
    total_topic_col: str,
    nps_period_col: str,
    denom_total_col: str,
    top_n_topics: Optional[int] = None,
) -> Dict[str, Any]:
    if company_period_df.empty:
        return {
            "periodo_referencia": None,
            "top_assuntos_periodo": [],
        }

    company_period_df = _sort_topic_period_df(company_period_df, period_col)
    periodo_referencia = company_period_df.iloc[0][period_col]
    current_df = company_period_df[company_period_df[period_col] == periodo_referencia].copy()

    current_df["_abs_contrib"] = current_df[contrib_col].abs()
    current_df = current_df.sort_values("_abs_contrib", ascending=False).drop(columns="_abs_contrib")

    if top_n_topics is not None:
        current_df = current_df.head(top_n_topics).copy()

    top_assuntos = []
    for _, row in current_df.iterrows():
        contrib_pp = _safe_percent_for_llm(row.get(contrib_col), 2)
        nps_period_percent = _safe_percent_for_llm(row.get(nps_period_col), 2)

        top_assuntos.append(
            {
                "assunto_especifico": row.get(topic_col),
                "contribuicao": {
                    "valor": contrib_pp,
                    "unidade": "p.p."
                },
                "nps_contrib_assunto_especifico": {
                    "valor": contrib_pp,
                    "unidade": "p.p."
                },
                "total_assunto_especifico": int(row.get(total_topic_col, 0) or 0),
                "nps_score_periodo": {
                    "valor": nps_period_percent,
                    "unidade": "%"
                },
                "denom_total": int(row.get(denom_total_col, 0) or 0),
            }
        )

    return {
        "periodo_referencia": periodo_referencia,
        "top_assuntos_periodo": top_assuntos,
    }


def _build_daily_topics_block(
    company_daily_df: pd.DataFrame,
    *,
    topic_col: str,
    period_col: str,
    contrib_col: str,
    total_topic_col: str,
    nps_period_col: str,
    denom_total_col: str,
    top_n_topics_per_day: Optional[int] = None,
) -> Dict[str, Any]:
    if company_daily_df.empty:
        return {
            "periodo_referencia": None,
            "dias": [],
        }

    company_daily_df = _sort_topic_period_df(company_daily_df, period_col)
    ultimo_periodo = company_daily_df.iloc[0][period_col]

    dias_out = []
    for dia, day_df in company_daily_df.groupby(period_col, sort=False):
        day_df = day_df.copy()
        day_df["_abs_contrib"] = day_df[contrib_col].abs()
        day_df = day_df.sort_values("_abs_contrib", ascending=False).drop(columns="_abs_contrib")

        if top_n_topics_per_day is not None:
            day_df = day_df.head(top_n_topics_per_day).copy()

        assuntos = []
        for _, row in day_df.iterrows():
            contrib_pp = _safe_percent_for_llm(row.get(contrib_col), 2)
            nps_period_percent = _safe_percent_for_llm(row.get(nps_period_col), 2)

            assuntos.append(
                {
                    "assunto_especifico": row.get(topic_col),
                    "contribuicao": {
                        "valor": contrib_pp,
                        "unidade": "p.p."
                    },
                    "nps_contrib_assunto_especifico": {
                        "valor": contrib_pp,
                        "unidade": "p.p."
                    },
                    "total_assunto_especifico": int(row.get(total_topic_col, 0) or 0),
                    "nps_score_periodo": {
                        "valor": nps_period_percent,
                        "unidade": "%"
                    },
                    "denom_total": int(row.get(denom_total_col, 0) or 0),
                }
            )

        dias_out.append(
            {
                "dia": dia,
                "assuntos": assuntos,
            }
        )

    dias_out = sorted(
        dias_out,
        key=lambda x: pd.to_datetime(x["dia"], errors="coerce"),
        reverse=True,
    )

    return {
        "periodo_referencia": ultimo_periodo,
        "dias": dias_out,
    }


def build_topic_contrib_llm_dict(
    assunto_df_daily: pd.DataFrame,
    assunto_df_period: pd.DataFrame,
    client: str,
    competitors: Optional[List[str]] = None,
    *,
    focus_analysis: str = "Empresa analisada",
    topic_col: str = "Assunto específico",
    daily_period_col: Optional[str] = "dia",
    period_period_col: Optional[str] = None,
    contrib_col: str = "nps_contrib_assunto_especifico",
    total_topic_col: str = "total_assunto_especifico",
    nps_period_col: str = "nps_score_periodo",
    denom_total_col: str = "denom_total",
    top_n_topics_period: Optional[int] = 10,
    top_n_topics_per_day: Optional[int] = 10,
) -> Dict[str, Any]:

    competitors = competitors or []

    if period_period_col is None:
        period_period_col = _detect_topic_period_col(assunto_df_period)

    empresas = []
    all_companies = [(client, "cliente")] + [(c, "concorrente") for c in competitors]

    for company_name, tipo_empresa in all_companies:
        daily_company_df = assunto_df_daily[
            assunto_df_daily[focus_analysis].astype(str).str.lower().str.strip()
            == company_name.lower().strip()
        ].copy()

        period_company_df = assunto_df_period[
            assunto_df_period[focus_analysis].astype(str).str.lower().str.strip()
            == company_name.lower().strip()
        ].copy()

        daily_block = _build_daily_topics_block(
            company_daily_df=daily_company_df,
            topic_col=topic_col,
            period_col=daily_period_col,
            contrib_col=contrib_col,
            total_topic_col=total_topic_col,
            nps_period_col=nps_period_col,
            denom_total_col=denom_total_col,
            top_n_topics_per_day=top_n_topics_per_day,
        )

        period_block = _build_period_topics_block(
            company_period_df=period_company_df,
            topic_col=topic_col,
            period_col=period_period_col,
            contrib_col=contrib_col,
            total_topic_col=total_topic_col,
            nps_period_col=nps_period_col,
            denom_total_col=denom_total_col,
            top_n_topics=top_n_topics_period,
        )

        empresas.append(
            {
                "empresa_analisada": company_name,
                "tipo_empresa": tipo_empresa,
                "periodo": _detect_topic_period_label(daily_period_col),
                "periodo_analitico": _detect_topic_period_label(period_period_col),
                "periodo_referencia": daily_block["periodo_referencia"],
                "periodo_analitico_referencia": period_block["periodo_referencia"],
                "top_assuntos_periodo": period_block["top_assuntos_periodo"],
                "dias": daily_block["dias"],
            }
        )

    return {
        "periodo": _detect_topic_period_label(daily_period_col),
        "periodo_analitico": _detect_topic_period_label(period_period_col),
        "empresas": empresas,
    }


from typing import Dict, Any
import pandas as pd


def build_company_big_number_dict(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Constrói um dicionário por empresa com evolução temporal,
    com métricas em formato executivo (texto + %).
    """

    # -------------------------------
    # 1. Detectar período automaticamente
    # -------------------------------
    if {"dia", "dia_index"}.issubset(df.columns):
        period_col = "dia"
        period_index_col = "dia_index"
        periodo_tipo = "dia"

    elif {"semana", "semana_index"}.issubset(df.columns):
        period_col = "semana"
        period_index_col = "semana_index"
        periodo_tipo = "semana"

    elif {"mes", "mes_index"}.issubset(df.columns):
        period_col = "mes"
        period_index_col = "mes_index"
        periodo_tipo = "mes"

    elif {"ano", "ano_index"}.issubset(df.columns):
        period_col = "ano"
        period_index_col = "ano_index"
        periodo_tipo = "ano"

    else:
        raise ValueError("Não foi possível identificar o período no DataFrame.")

    # -------------------------------
    # 2. Ordenação temporal
    # -------------------------------
    df = df.sort_values(by=period_index_col)

    # -------------------------------
    # 3. Mapeamento de métricas
    # -------------------------------
    metric_rename_map = {
        "nps_score": "NPS",
        "protagonism_score": "Protagonismo",
        "Detratores": "Impacto Detrator",
        "Inócuos": "Impacto Inócuo",
        "Promotores": "Impacto Promotor",
        "alcance": "Impacto Total",
        "frequencia": "Publicações Totais",
    }

    # -------------------------------
    # 4. Identificar métricas
    # -------------------------------
    dimension_cols = {
        "Empresa analisada",
        period_col,
        period_index_col,
        "ano", "ano_index",
        "mes", "mes_index",
        "semana", "semana_index",
        "dia", "dia_index",
    }

    metric_cols = [col for col in df.columns if col not in dimension_cols]

    # -------------------------------
    # 5. Função de transformação
    # -------------------------------
    def transform_value(col, value):
        if pd.isna(value):
            return None

        # Scores → string com %
        if col in ["nps_score", "protagonism_score"]:
            val = round(value * 100, 2)
            return f"{val:.2f}%"

        # Demais métricas → número arredondado
        if isinstance(value, (int, float)):
            return round(value, 2)

        return value

    # -------------------------------
    # 6. Construção do dicionário
    # -------------------------------
    output = {}

    for empresa, df_emp in df.groupby("Empresa analisada"):

        periodos = []

        for _, row in df_emp.iterrows():

            metricas = {}

            for col in metric_cols:
                new_key = metric_rename_map.get(col, col)
                metricas[new_key] = transform_value(col, row[col])

            periodo_dict = {
                "periodo": row[period_col],
                "periodo_index": int(row[period_index_col]),
                "metricas": metricas
            }

            periodos.append(periodo_dict)

        output[empresa] = {
            "periodo_tipo": periodo_tipo,
            "periodos": periodos
        }

    return output

