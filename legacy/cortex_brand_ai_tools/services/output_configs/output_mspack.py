import numpy as np
import pandas as pd
from datetime import date, datetime

def make_msgpack_safe(obj):
    if isinstance(obj, dict):
        return {
            str(make_msgpack_safe(k)): make_msgpack_safe(v)
            for k, v in obj.items()
        }

    if isinstance(obj, list):
        return [make_msgpack_safe(v) for v in obj]

    if isinstance(obj, tuple):
        return [make_msgpack_safe(v) for v in obj]

    if isinstance(obj, set):
        return [make_msgpack_safe(v) for v in obj]

    # NumPy scalars
    if isinstance(obj, np.generic):
        return obj.item()

    # NumPy arrays
    if isinstance(obj, np.ndarray):
        return make_msgpack_safe(obj.tolist())

    # Pandas Timestamp / datetime
    if isinstance(obj, (pd.Timestamp, datetime, date)):
        return obj.isoformat()

    # Pandas NA / NaN
    try:
        if pd.isna(obj):
            return None
    except Exception:
        pass

    # DataFrame / Series
    if isinstance(obj, pd.DataFrame):
        return make_msgpack_safe(obj.to_dict(orient="records"))

    if isinstance(obj, pd.Series):
        return make_msgpack_safe(obj.to_dict())

    return obj