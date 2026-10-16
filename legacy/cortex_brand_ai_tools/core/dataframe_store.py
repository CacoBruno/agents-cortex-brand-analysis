from __future__ import annotations

import pandas as pd
import uuid
from datetime import datetime
from typing import Dict, Any
pd.options.display.float_format = '{:.0f}'.format


# =========================
# STORE GLOBAL
# =========================
DATAFRAME_STORE: Dict[str, Dict[str, Any]] = {}


# =========================
# SAVE
# =========================
def save_dataframe(
    df: pd.DataFrame,
    source: str,
    filters: dict | None = None,
) -> str:
    """
    Salva um DataFrame no store e retorna o ID.
    """

    df_id = str(uuid.uuid4())

    DATAFRAME_STORE[df_id] = {
        "df": df,
        "created_at": datetime.now(),
        "source": source,
        "filters": filters or {},
        "rows": len(df),
        "columns": list(df.columns),
    }

    return df_id


# =========================
# GET
# =========================
def get_dataframe(df_id: str) -> pd.DataFrame:
    """
    Retorna apenas o DataFrame.
    """
    if df_id not in DATAFRAME_STORE:
        raise ValueError(f"DataFrame {df_id} não encontrado.")

    return DATAFRAME_STORE[df_id]["df"]


# =========================
# GET FULL (metadata + df)
# =========================
def get_dataframe_with_metadata(df_id: str) -> Dict[str, Any]:
    """
    Retorna DataFrame + metadados.
    """
    if df_id not in DATAFRAME_STORE:
        raise ValueError(f"DataFrame {df_id} não encontrado.")

    return DATAFRAME_STORE[df_id]


# =========================
# DELETE (opcional)
# =========================
def delete_dataframe(df_id: str) -> None:
    if df_id in DATAFRAME_STORE:
        del DATAFRAME_STORE[df_id]


# =========================
# LIST (debug / inspeção)
# =========================
def list_dataframes() -> Dict[str, Dict[str, Any]]:
    """
    Lista todos os dataframes armazenados (sem o df completo).
    """
    return {
        df_id: {
            "created_at": v["created_at"],
            "source": v["source"],
            "rows": v["rows"],
            "columns": v["columns"],
        }
        for df_id, v in DATAFRAME_STORE.items()
    }