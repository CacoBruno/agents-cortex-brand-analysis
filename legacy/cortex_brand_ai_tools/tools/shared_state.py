"""
Módulo compartilhado para gerenciar estado global
"""
import pandas as pd
from typing import Optional

# Variável global compartilhada
current_dataframe: Optional[pd.DataFrame] = None

def set_dataframe(df: pd.DataFrame) -> None:
    """Define o DataFrame global"""
    global current_dataframe
    current_dataframe = df.copy() if df is not None else None
    print(f"DataFrame definido globalmente - Shape: {current_dataframe.shape if current_dataframe is not None else 'None'}")

def get_dataframe() -> Optional[pd.DataFrame]:
    """Retorna o DataFrame global"""
    global current_dataframe
    return current_dataframe

def clear_dataframe() -> None:
    """Limpa o DataFrame global"""
    global current_dataframe
    current_dataframe = None
    print("DataFrame global limpo")

def has_dataframe() -> bool:
    """Verifica se existe um DataFrame global"""
    global current_dataframe
    return current_dataframe is not None
