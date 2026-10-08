from __future__ import annotations

from typing import Any, Mapping, Sequence, Tuple, Union
import pandas as pd

ColorLike = Union[str, Tuple[int, int, int], Tuple[float, float, float], Sequence[int], Sequence[float]]
ColorsDict = Mapping[Any, ColorLike]


def _norm_type(t: str) -> str:
    t = (t or "").strip().lower()
    mapping = {
        "linha": "linha", "line": "linha",
        "barra": "barra", "bar": "barra",
        "barra_empilhada": "barra_empilhada", "stacked_bar": "barra_empilhada",
        "dispersao": "dispersao", "dispersão": "dispersao", "scatter": "dispersao",
        "pizza": "pizza", "pie": "pizza",
        "area": "area", "área": "area",
        "bolha": "bolha", "bubble": "bolha",
    }
    return mapping.get(t, t)


def _norm_orientation(o: str) -> str:
    o = (o or "").strip().lower()
    if o in {"h", "hor", "horizontal", "horiz"}:
        return "horizontal"
    return "vertical"


def _safe_filename(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-=" else "_" for ch in text)


def _normalize_rgb(c: ColorLike) -> ColorLike:
    if isinstance(c, (list, tuple)) and len(c) == 3:
        try:
            vals = [float(v) for v in c]
            if any(v > 1.0 for v in vals):
                return tuple(max(0.0, min(1.0, v / 255.0)) for v in vals)
            return tuple(vals)
        except Exception:
            return c
    return c


def _get_color_for_cat_from(cat, i, palette, color_source):
    if isinstance(color_source, dict):
        if cat in color_source and color_source[cat] is not None:
            return _normalize_rgb(color_source[cat])
        return palette[i % len(palette)] if palette else "#1f77b4"

    if isinstance(color_source, (list, tuple)) and len(color_source) > 0:
        return _normalize_rgb(color_source[i % len(color_source)])

    return palette[i % len(palette)] if palette else "#1f77b4"


def _get_single_color_from(color_source, palette):
    if isinstance(color_source, (list, tuple)) and len(color_source) > 0:
        return _normalize_rgb(color_source[0])
    if isinstance(color_source, dict) and len(color_source) > 0:
        try:
            return _normalize_rgb(next(iter(color_source.values())))
        except Exception:
            pass
    return palette[0] if palette else "#1f77b4"


def _require_cols(df: pd.DataFrame, cols):
    missing = [c for c in cols if c and c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes no dataframe: {missing}")


def _is_number(x) -> bool:
    try:
        float(x)
        return True
    except Exception:
        return False


def _get_main_cat_order(ax, is_horizontal=False):
    labels = [t.get_text() for t in (ax.get_yticklabels() if is_horizontal else ax.get_xticklabels())]
    labels = [l for l in labels if l is not None and str(l).strip() != ""]
    if labels:
        return labels

    try:
        return list(ax.get_yticks() if is_horizontal else ax.get_xticks())
    except Exception:
        return None


def _reindex_series_to_main_order(series: pd.Series, main_order):
    if main_order is None or len(main_order) == 0:
        return series

    if isinstance(main_order[0], str):
        try:
            s = series.copy()
            s.index = [str(i) for i in s.index.tolist()]
            return s.reindex([str(x) for x in main_order])
        except Exception:
            return series

    try:
        return series.reindex(main_order)
    except Exception:
        return series