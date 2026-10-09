from __future__ import annotations

from typing import Any, Sequence

import pandas as pd

from services.charts.labels import _labels_allowed
from services.charts.utils import (
    _get_color_for_cat_from,
    _get_single_color_from,
    _normalize_rgb,
)


# =========================================================
# HELPERS INTERNOS DE PLOT
# =========================================================
def _coerce_numeric_series(series: pd.Series) -> pd.Series:
    """
    Converte uma Series para numérico e preenche NaN com 0.
    """
    return pd.to_numeric(series, errors="coerce").fillna(0)


def _get_group_categories(df: pd.DataFrame, agrupamento: str) -> list:
    """
    Retorna as categorias do agrupamento ordenadas alfabeticamente.
    """
    return sorted(df[agrupamento].dropna().unique().tolist(), key=lambda x: str(x))


def _compute_bubble_sizes(
    z: pd.Series,
    min_size: float = 80.0,
    max_size: float = 700.0,
    default_size: float = 200.0,
):
    """
    Normaliza a variável z para tamanhos de bolha.
    """
    z = _coerce_numeric_series(z).astype(float)

    if len(z) == 0:
        return []

    z_min_v, z_max_v = float(z.min()), float(z.max())

    if z_max_v == z_min_v:
        return [default_size] * len(z)

    return min_size + (z - z_min_v) / (z_max_v - z_min_v) * (max_size - min_size)


def _prepare_pivot_stacked_bar(
    df: pd.DataFrame,
    valor_x: str,
    valor_y: str,
    stack_by: str,
    stack_order: Sequence[Any] | None = None,
) -> pd.DataFrame:
    """
    Prepara a tabela pivot para gráfico de barra empilhada.
    """
    d = df[[valor_x, stack_by, valor_y]].copy()
    d[valor_y] = _coerce_numeric_series(d[valor_y])

    pivot = (
        d.pivot_table(
            index=valor_x,
            columns=stack_by,
            values=valor_y,
            aggfunc="sum",
            fill_value=0,
        )
        .sort_index()
    )

    if stack_order is not None:
        cols = [c for c in stack_order if c in pivot.columns] + [
            c for c in pivot.columns if c not in stack_order
        ]
        pivot = pivot[cols]

    return pivot


# =========================================================
# PLOTS
# =========================================================
def _plot_line(
    ax,
    df: pd.DataFrame,
    valor_x: str,
    valor_y: str,
    colors,
    default_palette,
    marker_style: dict,
    agrupamento: str | None = None,
):
    if agrupamento:
        cats = _get_group_categories(df, agrupamento)

        for i, cat in enumerate(cats):
            sub = df[df[agrupamento] == cat].sort_values(valor_x)
            c = _get_color_for_cat_from(cat, i, default_palette, colors)
            mk = (
                marker_style.get("by_cat", {}).get(cat, marker_style.get("marker", "o"))
                if isinstance(marker_style.get("by_cat"), dict)
                else marker_style.get("marker", "o")
            )

            ax.plot(
                sub[valor_x],
                sub[valor_y],
                label=str(cat),
                color=c,
                linewidth=marker_style.get("linewidth", 2),
                marker=str(mk),
                markersize=marker_style.get("markersize", 5),
                markeredgecolor=marker_style.get("markeredgecolor", None),
                markeredgewidth=marker_style.get("markeredgewidth", 0.8),
                markerfacecolor=(
                    marker_style.get("markerfacecolor")
                    if marker_style.get("markerfacecolor") is not None
                    else c
                ),
                markevery=marker_style.get("markevery", 1),
            )
    else:
        d0 = df.sort_values(valor_x)
        c0 = _get_single_color_from(colors, default_palette)
        mk = str(marker_style.get("marker", "o"))

        ax.plot(
            d0[valor_x],
            d0[valor_y],
            color=c0,
            linewidth=marker_style.get("linewidth", 2),
            marker=mk,
            markersize=marker_style.get("markersize", 5),
            markeredgecolor=marker_style.get("markeredgecolor", None),
            markeredgewidth=marker_style.get("markeredgewidth", 0.8),
            markerfacecolor=(
                marker_style.get("markerfacecolor")
                if marker_style.get("markerfacecolor") is not None
                else c0
            ),
            markevery=marker_style.get("markevery", 1),
        )


def _plot_bar(
    ax,
    df: pd.DataFrame,
    valor_x: str,
    valor_y: str,
    colors,
    default_palette,
    orientation: str = "vertical",
    agrupamento: str | None = None,
):
    if agrupamento:
        cats = _get_group_categories(df, agrupamento)
        all_bars = []

        for i, cat in enumerate(cats):
            sub = df[df[agrupamento] == cat]
            c = _get_color_for_cat_from(cat, i, default_palette, colors)
            vals = _coerce_numeric_series(sub[valor_y])

            if orientation == "horizontal":
                bars = ax.barh(
                    sub[valor_x],
                    vals,
                    label=str(cat),
                    color=c,
                    alpha=0.9,
                )
            else:
                bars = ax.bar(
                    sub[valor_x],
                    vals,
                    label=str(cat),
                    color=c,
                    alpha=0.9,
                )

            all_bars.append((cat, sub, bars))

        return all_bars

    c0 = _get_single_color_from(colors, default_palette)
    vals = _coerce_numeric_series(df[valor_y])

    if orientation == "horizontal":
        return ax.barh(df[valor_x], vals, alpha=0.9, color=c0)

    return ax.bar(df[valor_x], vals, alpha=0.9, color=c0)


def _plot_stacked_bar(
    ax,
    df: pd.DataFrame,
    valor_x: str,
    valor_y: str,
    stack_by: str,
    default_palette,
    colors=None,
    stack_colors=None,
    stack_order: Sequence[Any] | None = None,
    orientation: str = "vertical",
):
    pivot = _prepare_pivot_stacked_bar(
        df=df,
        valor_x=valor_x,
        valor_y=valor_y,
        stack_by=stack_by,
        stack_order=stack_order,
    )

    cat_labels = pivot.index.tolist()
    color_src = stack_colors if stack_colors is not None else colors
    plot_objects = []

    if orientation == "horizontal":
        lefts = [0.0] * len(pivot)

        for j, seg in enumerate(pivot.columns):
            vals = pivot[seg].values.astype(float).tolist()
            cseg = _get_color_for_cat_from(seg, j, default_palette, color_src)

            bars = ax.barh(
                cat_labels,
                vals,
                left=lefts,
                label=str(seg),
                color=cseg,
                alpha=0.9,
            )

            plot_objects.append((seg, vals, bars, lefts.copy()))
            lefts = [lefts[k] + vals[k] for k in range(len(vals))]
    else:
        bottoms = [0.0] * len(pivot)

        for j, seg in enumerate(pivot.columns):
            vals = pivot[seg].values.astype(float).tolist()
            cseg = _get_color_for_cat_from(seg, j, default_palette, color_src)

            bars = ax.bar(
                cat_labels,
                vals,
                bottom=bottoms,
                label=str(seg),
                color=cseg,
                alpha=0.9,
            )

            plot_objects.append((seg, vals, bars, bottoms.copy()))
            bottoms = [bottoms[k] + vals[k] for k in range(len(vals))]

    return pivot, cat_labels, plot_objects


def _plot_scatter(
    ax,
    df: pd.DataFrame,
    valor_x: str,
    valor_y: str,
    colors,
    default_palette,
    agrupamento: str | None = None,
):
    if agrupamento:
        cats = _get_group_categories(df, agrupamento)
        for i, cat in enumerate(cats):
            sub = df[df[agrupamento] == cat]
            c = _get_color_for_cat_from(cat, i, default_palette, colors)
            ax.scatter(sub[valor_x], sub[valor_y], label=str(cat), color=c, alpha=0.9)
    else:
        c0 = _get_single_color_from(colors, default_palette)
        ax.scatter(df[valor_x], df[valor_y], alpha=0.9, color=c0)


def _plot_pie(
    ax,
    df: pd.DataFrame,
    valor_x: str,
    valor_y: str,
    colors,
    font_family: str,
    legend_style: dict,
    value_label_style: dict,
):
    data_pie = df[[valor_x, valor_y]].copy()
    data_pie[valor_y] = _coerce_numeric_series(data_pie[valor_y])

    pie_agg = (
        data_pie.groupby(valor_x, dropna=False)[valor_y]
        .sum()
        .sort_values(ascending=False)
    )

    labels = [str(i) for i in pie_agg.index.tolist()]
    vals = pie_agg.values.tolist()

    pie_colors = None
    if isinstance(colors, dict):
        pie_colors = [_normalize_rgb(colors.get(cat, None)) for cat in pie_agg.index]
    elif isinstance(colors, (list, tuple)) and len(colors) > 0:
        pie_colors = [_normalize_rgb(colors[i % len(colors)]) for i in range(len(labels))]

    wedges, _texts, autotexts = ax.pie(
        vals,
        labels=None,
        colors=pie_colors,
        autopct="%1.1f%%" if _labels_allowed(True, len(vals)) else None,
        startangle=90,
    )
    ax.axis("equal")

    if legend_style.get("show", True):
        x_map = {"left": 0.0, "center": 0.5, "right": 1.0}
        x = x_map.get(str(legend_style.get("position", "center")).lower(), 0.5)
        y = float(legend_style.get("offset", -0.12))
        ncol = legend_style.get("ncol", None) or min(4, len(labels))

        ax.legend(
            wedges,
            labels,
            loc="upper center",
            bbox_to_anchor=(x, y),
            ncol=ncol,
            frameon=bool(legend_style.get("frameon", False)),
            prop={"family": font_family, "size": legend_style.get("font_size", 9)},
            labelcolor=legend_style.get("font_color", "#374151"),
        )

    if autotexts:
        for t in autotexts:
            t.set_fontfamily(font_family)
            t.set_fontsize(value_label_style["size"])
            t.set_fontweight("bold" if value_label_style["bold"] else "normal")
            t.set_fontstyle("italic" if value_label_style["italic"] else "normal")
            t.set_color(value_label_style.get("color", "#111827"))


def _plot_area(
    ax,
    df: pd.DataFrame,
    valor_x: str,
    valor_y: str,
    colors,
    default_palette,
    agrupamento: str | None = None,
):
    if agrupamento:
        cats = _get_group_categories(df, agrupamento)
        for i, cat in enumerate(cats):
            sub = df[df[agrupamento] == cat].sort_values(valor_x)
            c = _get_color_for_cat_from(cat, i, default_palette, colors)
            ax.fill_between(
                sub[valor_x],
                _coerce_numeric_series(sub[valor_y]),
                label=str(cat),
                alpha=0.35,
                color=c,
            )
    else:
        d0 = df.sort_values(valor_x)
        c0 = _get_single_color_from(colors, default_palette)
        ax.fill_between(
            d0[valor_x],
            _coerce_numeric_series(d0[valor_y]),
            alpha=0.35,
            color=c0,
        )


def _plot_bubble(
    ax,
    df: pd.DataFrame,
    valor_x: str,
    valor_y: str,
    valor_z: str,
    colors,
    default_palette,
    agrupamento: str | None = None,
):
    if agrupamento:
        cats = _get_group_categories(df, agrupamento)
        for i, cat in enumerate(cats):
            sub = df[df[agrupamento] == cat].sort_values(valor_x)
            sizes = _compute_bubble_sizes(sub[valor_z])
            c = _get_color_for_cat_from(cat, i, default_palette, colors)
            ax.scatter(
                sub[valor_x],
                sub[valor_y],
                s=sizes,
                label=str(cat),
                color=c,
                alpha=0.6,
            )
    else:
        d0 = df.sort_values(valor_x)
        sizes = _compute_bubble_sizes(d0[valor_z])
        c0 = _get_single_color_from(colors, default_palette)
        ax.scatter(
            d0[valor_x],
            d0[valor_y],
            s=sizes,
            alpha=0.6,
            color=c0,
        )