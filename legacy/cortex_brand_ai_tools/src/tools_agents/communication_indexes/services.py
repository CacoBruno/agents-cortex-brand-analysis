from __future__ import annotations

import pandas as pd

from core.dataframe_store import get_dataframe
from services.index_function import (gen_dataviews, calc_nps_score, nps_total_and_contrib, 
                                     calc_protagonism_score, freq_score, valoration_score,
                                     jornalista_score, action_score)
from src.tools_agents.communication_indexes.schemas import (GenDataviewsInput, CalcNPSScoreInput, 
                                                            NPSTotalAndContribInput, ProtagonismScoreInput, 
                                                            FreqScoreInput, ValorationScoreInput, JornalistaScoreInput, 
                                                            ActionScoreInput)

def gen_dataviews_service(params: GenDataviewsInput) -> pd.DataFrame:
    """
    Recupera o DataFrame do store e gera o dataview a partir da função gen_dataviews.
    """
    try:
        df = get_dataframe(params.dataframe_id)

        if df is None:
            raise ValueError("DataFrame não encontrado no store.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O objeto recuperado não é um pandas DataFrame.")

        result_df = gen_dataviews(
            dataframe=df,
            data_ancora_semana=params.data_ancora_semana,
        )

        if result_df is None:
            raise ValueError("gen_dataviews retornou None.")

        if not isinstance(result_df, pd.DataFrame):
            raise TypeError("O retorno de gen_dataviews não é um pandas DataFrame.")

        return result_df

    except Exception as e:
        raise RuntimeError(f"Erro ao executar gen_dataviews: {str(e)}") from e
    

def calc_nps_score_service(params: CalcNPSScoreInput) -> pd.DataFrame:
    """
    Recupera o DataFrame do store e aplica o cálculo de NPS.
    """
    try:
        df = get_dataframe(params.dataframe_id)

        if df is None:
            raise ValueError("DataFrame não encontrado no store.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O objeto recuperado não é um pandas DataFrame.")

        result_df = calc_nps_score(
            df=df,
            value_col=params.value_col,
            impacto_col=params.impacto_col,
            group_cols=params.group_cols,
            sum_cols=params.sum_cols,
            dedupe_columns=params.dedupe_columns,
        )

        if result_df is None:
            raise ValueError("calc_nps_score retornou None.")

        if not isinstance(result_df, pd.DataFrame):
            raise TypeError("O retorno de calc_nps_score não é um pandas DataFrame.")

        return result_df

    except Exception as e:
        raise RuntimeError(f"Erro ao executar calc_nps_score: {str(e)}") from e
    

def nps_total_and_contrib_service(params: NPSTotalAndContribInput) -> pd.DataFrame:
    """
    Recupera o DataFrame do store e aplica o cálculo de NPS total e contribuição por dimensão.
    """
    try:
        df = get_dataframe(params.dataframe_id)

        if df is None:
            raise ValueError("DataFrame não encontrado no store.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O objeto recuperado não é um pandas DataFrame.")

        result_df = nps_total_and_contrib(
            df=df,
            dim_col=params.dim_col,
            value_col=params.value_col,
            impacto_col=params.impacto_col,
            group_cols=params.group_cols,
            impacts=params.impacts,
            contr_type=params.contr_type,
            round_total=params.round_total,
            round_contrib=params.round_contrib,
        )

        if result_df is None:
            raise ValueError("nps_total_and_contrib retornou None.")

        if not isinstance(result_df, pd.DataFrame):
            raise TypeError("O retorno de nps_total_and_contrib não é um pandas DataFrame.")

        return result_df

    except Exception as e:
        raise RuntimeError(f"Erro ao executar nps_total_and_contrib: {str(e)}") from e
    

def protagonism_score_service(params: ProtagonismScoreInput) -> pd.DataFrame:
    """
    Recupera o DataFrame do store e aplica o cálculo de protagonism_score.
    """
    try:
        df = get_dataframe(params.dataframe_id)

        if df is None:
            raise ValueError("DataFrame não encontrado no store.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O objeto recuperado não é um pandas DataFrame.")

        result_df = calc_protagonism_score(
            df=df,
            value_col=params.value_col,
            impacto_col=params.impacto_col,
            group_cols=params.group_cols,
            filter_column=params.filter_column,
            filter_value=params.filter_value,
        )

        if result_df is None:
            raise ValueError("protagonism_score retornou None.")

        if not isinstance(result_df, pd.DataFrame):
            raise TypeError("O retorno de protagonism_score não é um pandas DataFrame.")

        return result_df

    except Exception as e:
        raise RuntimeError(f"Erro ao executar protagonism_score: {str(e)}") from e  
    
def freq_score_service(params: FreqScoreInput) -> pd.DataFrame:
    """
    Recupera o DataFrame do store e aplica o cálculo de frequência.
    """
    try:
        df = get_dataframe(params.dataframe_id)

        if df is None:
            raise ValueError("DataFrame não encontrado no store.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O objeto recuperado não é um pandas DataFrame.")

        result_df = freq_score(
            df=df,
            value_col=params.value_col,
            impacto_col=params.impacto_col,
            group_cols=params.group_cols,
        )

        if result_df is None:
            raise ValueError("freq_score retornou None.")

        if not isinstance(result_df, pd.DataFrame):
            raise TypeError("O retorno de freq_score não é um pandas DataFrame.")

        return result_df

    except Exception as e:
        raise RuntimeError(f"Erro ao executar freq_score: {str(e)}") from e

def valoration_score_service(params: ValorationScoreInput) -> pd.DataFrame:
    """
    Recupera o DataFrame do store e aplica o cálculo de valoração agregada.
    """
    try:
        df = get_dataframe(params.dataframe_id)

        if df is None:
            raise ValueError("DataFrame não encontrado no store.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O objeto recuperado não é um pandas DataFrame.")

        result_df = valoration_score(
            df=df,
            value_col=params.value_col,
            group_cols=params.group_cols,
        )

        if result_df is None:
            raise ValueError("valoration_score retornou None.")

        if not isinstance(result_df, pd.DataFrame):
            raise TypeError("O retorno de valoration_score não é um pandas DataFrame.")

        return result_df

    except Exception as e:
        raise RuntimeError(f"Erro ao executar valoration_score: {str(e)}") from e
    

def jornalista_score_service(params: JornalistaScoreInput) -> pd.DataFrame:
    """
    Recupera o DataFrame do store e aplica o cálculo de jornalista_score.
    """
    try:
        df = get_dataframe(params.dataframe_id)

        if df is None:
            raise ValueError("DataFrame não encontrado no store.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O objeto recuperado não é um pandas DataFrame.")

        result_df = jornalista_score(
            df=df,
            value_cols=params.value_cols,
            group_cols=params.group_cols,
        )

        if result_df is None:
            raise ValueError("jornalista_score retornou None.")

        if not isinstance(result_df, pd.DataFrame):
            raise TypeError("O retorno de jornalista_score não é um pandas DataFrame.")

        return result_df

    except Exception as e:
        raise RuntimeError(f"Erro ao executar jornalista_score: {str(e)}") from e
    

def action_score_service(params: ActionScoreInput) -> pd.DataFrame:
    """
    Recupera o DataFrame do store e aplica o cálculo de action_score.
    """
    try:
        df = get_dataframe(params.dataframe_id)

        if df is None:
            raise ValueError("DataFrame não encontrado no store.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O objeto recuperado não é um pandas DataFrame.")

        result_df = action_score(
            df=df,
            value_cols=params.value_cols,
            group_cols=params.group_cols,
        )

        if result_df is None:
            raise ValueError("action_score retornou None.")

        if not isinstance(result_df, pd.DataFrame):
            raise TypeError("O retorno de action_score não é um pandas DataFrame.")

        return result_df

    except Exception as e:
        raise RuntimeError(f"Erro ao executar action_score: {str(e)}") from e