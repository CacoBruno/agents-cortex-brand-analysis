from __future__ import annotations

import pandas as pd

from services.cortex_platform import (export_database_ma, export_action_database, export_databate_publ, 
                                      get_infos_brand, get_prdata_dataframe, get_prdata_open_source, get_mss_dataframe)

from src.tools_agents.platform.schemas import (ExportDatabaseMAInput, ExportActionDatabaseInput, ExportDatabasePublInput,
                                                GetInfosBrandInput, GetPRDataDataFrameInput, GetMSSDataFrameInput, GetPRDataOpenSourceDataFrameInput)


def export_media_analysis_database(params: ExportDatabaseMAInput) -> pd.DataFrame:
    """
    Executa a exportação da base de análise de mídia.
    """

    try:
        df = export_database_ma(**params.to_service_kwargs())

        if df is None:
            raise ValueError("A função retornou None.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O retorno não é um pandas DataFrame.")

        if df.empty:
            # decisão de design: isso NÃO é erro crítico
            return df

        return df

    except Exception as e:
        # aqui você pode plugar logging depois
        raise RuntimeError(f"Erro ao exportar base: {str(e)}") from e
    

def export_action_database_service(params: ExportActionDatabaseInput) -> pd.DataFrame:
    """
    Executa a exportação da base de ações de comunicação da plataforma Cortex.
    """
    try:
        df = export_action_database(**params.to_service_kwargs())

        if df is None:
            raise ValueError("A função retornou None.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O retorno não é um pandas DataFrame.")

        return df

    except Exception as e:
        raise RuntimeError(f"Erro ao exportar action database: {str(e)}") from e
    

def export_publications_database_service(params: ExportDatabasePublInput) -> pd.DataFrame:
    """
    Executa a exportação da base de publicações da plataforma Cortex.
    """
    try:
        df = export_databate_publ(**params.to_service_kwargs())

        if df is None:
            raise ValueError("A função retornou None.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O retorno não é um pandas DataFrame.")

        return df

    except Exception as e:
        raise RuntimeError(f"Erro ao exportar publications database: {str(e)}") from e


def get_infos_brand_service(params: GetInfosBrandInput) -> pd.DataFrame:
    """
    Obtém as informações da marca na plataforma Cortex.
    """
    try:
        df = get_infos_brand(**params.to_service_kwargs())

        if df is None:
            raise ValueError("A função retornou None.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O retorno não é um pandas DataFrame.")

        return df

    except Exception as e:
        raise RuntimeError(f"Erro ao obter informações da marca: {str(e)}") from e
    
def get_prdata_dataframe_service(params: GetPRDataDataFrameInput) -> pd.DataFrame:
    """
    Obtém um DataFrame do PRData com base em período, termos e veículos.
    """
    try:
        df = get_prdata_dataframe(**params.to_service_kwargs())

        if df is None:
            raise ValueError("A função retornou None.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O retorno não é um pandas DataFrame.")

        return df

    except Exception as e:
        raise RuntimeError(f"Erro ao obter DataFrame do PRData: {str(e)}") from e
    

def get_prdata_open_source_service(params: GetPRDataOpenSourceDataFrameInput) -> pd.DataFrame:
    """
    Obtém um DataFrame do PRData com base no período, termos e veículos informados.
    
    """
    try:
        df = get_prdata_open_source(**params.to_service_kwargs())

        if df is None:
            raise ValueError("A função retornou None.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O retorno não é um pandas DataFrame.")

        return df

    except Exception as e:
        raise RuntimeError(f"Erro ao obter DataFrame do PRData: {str(e)}") from e
    

def get_mss_dataframe_service(params: GetMSSDataFrameInput) -> pd.DataFrame:
    """
    Obtém um DataFrame MSS com base nos filtros informados.

    """
    try:
        df = get_mss_dataframe(**params.to_service_kwargs())

        if df is None:
            raise ValueError("A função retornou None.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("O retorno não é um pandas DataFrame.")

        return df

    except Exception as e:
        raise RuntimeError(f"Erro ao obter DataFrame MSS: {str(e)}") from e