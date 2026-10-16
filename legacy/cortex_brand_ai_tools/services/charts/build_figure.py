from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from .labels import _apply_labels, _labels_allowed
from .plotters import (
    _plot_area,
    _plot_bar,
    _plot_bubble,
    _plot_line,
    _plot_pie,
    _plot_scatter,
    _plot_stacked_bar,
)
from .secondary import _plot_secondary
from .styles import (
    _apply_axes_style,
    _apply_legend,
    _apply_title_style,
    _build_style_context,
)
from .utils import _norm_orientation, _norm_type, _require_cols


def build_chart_figure(
    df: pd.DataFrame,
    chart_type: str,
    valor_x: str,
    valor_y: str | None = None,
    valor_z: str | None = None,
    agrupamento: str | None = None,
    colors=None,
    figsize_w: float = 12.0,
    figsize_h: float = 6.0,
    transparent_bg: bool = True,
    background_color: str | None = None,
    title: str | None = None,
    x_min: float | None = None,
    x_max: float | None = None,
    y_min: float | None = None,
    y_max: float | None = None,
    font_family: str = "Arial",
    show_labels: bool = True,
    value_label_style: dict | None = None,
    title_style: dict | None = None,
    axis_style: dict | None = None,
    legend_style: dict | None = None,
    grid_style: dict | None = None,
    marker_style: dict | None = None,
    secondary_spec: dict | None = None,
    stack_by: str | None = None,
    stack_order=None,
    stack_colors=None,
    stack_labels: bool = True,
    stack_total_label: bool = False,
    orientation: str = "vertical",
):
    """
    Constrói e retorna a figure do gráfico sem exportar.

    Returns
    -------
    tuple
        (fig, ax, ax2)
    """
    if df.empty:
        raise ValueError("O DataFrame está vazio.")

    chart_type_n = _norm_type(chart_type)
    orient = _norm_orientation(orientation)

    required = [valor_x]

    if chart_type_n in {"linha", "barra", "dispersao", "area", "pizza"}:
        if not valor_y:
            raise ValueError(f"valor_y é obrigatório para chart_type='{chart_type_n}'.")
        required.append(valor_y)

    if chart_type_n == "bolha":
        if not (valor_y and valor_z):
            raise ValueError("Para 'bolha', valor_y e valor_z são obrigatórios.")
        required += [valor_y, valor_z]

    if chart_type_n == "barra_empilhada":
        if not valor_y:
            raise ValueError("Para 'barra_empilhada', valor_y é obrigatório.")
        if not stack_by:
            raise ValueError("Para 'barra_empilhada', stack_by é obrigatório.")
        required += [valor_y, stack_by]

    if agrupamento:
        required.append(agrupamento)

    sec = None
    if secondary_spec is not None:
        if not isinstance(secondary_spec, dict):
            raise TypeError("secondary_spec deve ser dict ou None.")
        if len(secondary_spec) > 0:
            sec = secondary_spec.copy()
            sec.setdefault("chart_type", "linha")
            sec.setdefault("valor_z", None)
            sec.setdefault("agrupamento", None)
            sec.setdefault("colors", None)
            sec.setdefault("y_min", None)
            sec.setdefault("y_max", None)
            sec.setdefault("ylabel", None)
            sec.setdefault("axis_style", None)
            sec.setdefault("value_label_style", None)
            sec.setdefault("marker_style", None)
            sec.setdefault("alpha", 0.9)

            if "valor_y" not in sec or not sec.get("valor_y"):
                raise ValueError("secondary_spec exige 'valor_y'.")

            required.append(sec["valor_y"])
            if sec.get("agrupamento"):
                required.append(sec["agrupamento"])

    _require_cols(df, required)

    ctx = _build_style_context(
        value_label_style=value_label_style,
        title_style=title_style,
        axis_style=axis_style,
        legend_style=legend_style,
        grid_style=grid_style,
        marker_style=marker_style,
    )

    plt.rcParams["font.family"] = font_family
    fig, ax = plt.subplots(figsize=(figsize_w, figsize_h))

    if not transparent_bg:
        bg = "white" if background_color is None else background_color
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)

    default_palette = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
    ax2 = None

    # =====================================================
    # PLOT PRINCIPAL
    # =====================================================
    if chart_type_n == "linha":
        _plot_line(
            ax=ax,
            df=df,
            valor_x=valor_x,
            valor_y=valor_y,
            colors=colors,
            default_palette=default_palette,
            marker_style=ctx["marker_style"],
            agrupamento=agrupamento,
        )

        if agrupamento:
            for cat in sorted(df[agrupamento].dropna().unique().tolist(), key=lambda x: str(x)):
                sub = df[df[agrupamento] == cat].sort_values(valor_x)
                if _labels_allowed(show_labels, len(sub), 12):
                    _apply_labels(
                        ax,
                        "line",
                        font_family,
                        ctx["value_label_style"],
                        x=sub[valor_x],
                        y=sub[valor_y],
                    )
        else:
            d0 = df.sort_values(valor_x)
            if _labels_allowed(show_labels, len(d0), 15):
                _apply_labels(
                            ax,
                                "scatter",
                                font_family,
                                {
                                    **ctx["value_label_style"],
                                    "label_values": sub[agrupamento].tolist() if agrupamento else None
                                },
                                x=sub[valor_x],
                                y=sub[valor_y],
                                z=sub[valor_z],
                            )
        ax.set_xlabel(valor_x)
        ax.set_ylabel(valor_y)

    elif chart_type_n == "barra":
        result = _plot_bar(
            ax=ax,
            df=df,
            valor_x=valor_x,
            valor_y=valor_y,
            colors=colors,
            default_palette=default_palette,
            orientation=orient,
            agrupamento=agrupamento,
        )

        if agrupamento:
            for _, sub, bars in result:
                if orient == "horizontal":
                    if _labels_allowed(show_labels, len(sub), 12):
                        _apply_labels(
                            ax,
                            "barh",
                            font_family,
                            ctx["value_label_style"],
                            bars=bars,
                            y_labels=sub[valor_x].tolist(),
                        )
                else:
                    if _labels_allowed(show_labels, len(sub), 12):
                        _apply_labels(
                            ax,
                            "bar",
                            font_family,
                            ctx["value_label_style"],
                            bars=bars,
                            x=sub[valor_x].tolist(),
                        )
            ax.set_xlabel(valor_x)
            ax.set_ylabel(valor_y)
        else:
            if orient == "horizontal":
                if _labels_allowed(show_labels, len(df), 15):
                    _apply_labels(
                        ax,
                        "barh",
                        font_family,
                        ctx["value_label_style"],
                        bars=result,
                        y_labels=df[valor_x].tolist(),
                    )
                ax.set_xlabel(valor_y)
                ax.set_ylabel(valor_x)
            else:
                if _labels_allowed(show_labels, len(df), 15):
                    _apply_labels(
                        ax,
                        "bar",
                        font_family,
                        ctx["value_label_style"],
                        bars=result,
                        x=df[valor_x].tolist(),
                    )
                ax.set_xlabel(valor_x)
                ax.set_ylabel(valor_y)

    elif chart_type_n == "barra_empilhada":
        pivot, cat_labels, plot_objects = _plot_stacked_bar(
            ax=ax,
            df=df,
            valor_x=valor_x,
            valor_y=valor_y,
            stack_by=stack_by,
            default_palette=default_palette,
            colors=colors,
            stack_colors=stack_colors,
            stack_order=stack_order,
            orientation=orient,
        )

        if orient == "horizontal":
            for _, vals, bars, lefts in plot_objects:
                if stack_labels and _labels_allowed(show_labels, len(cat_labels), 15):
                    for i_b, b in enumerate(bars):
                        v = float(vals[i_b])
                        if v == 0:
                            continue
                        x_mid = lefts[i_b] + v / 2.0
                        txt = f"{v:g}"
                        ax.annotate(
                            txt,
                            (x_mid, b.get_y() + b.get_height() / 2.0),
                            xytext=(0, 0),
                            textcoords="offset points",
                            ha="center",
                            va="center",
                            fontsize=ctx["value_label_style"]["size"],
                            fontfamily=font_family,
                            fontweight="bold" if ctx["value_label_style"].get("bold", True) else "normal",
                            fontstyle="italic" if ctx["value_label_style"].get("italic", False) else "normal",
                            color=ctx["value_label_style"].get("color", "#111827"),
                        )

            if stack_total_label and _labels_allowed(show_labels, len(cat_labels), 15):
                totals = pivot.sum(axis=1).values.astype(float).tolist()
                pad = float(ctx["value_label_style"].get("padding", 3))
                for i_y, total in enumerate(totals):
                    if total == 0:
                        continue
                    ax.annotate(
                        f"{total:g}",
                        (total, i_y),
                        xytext=(pad, 0),
                        textcoords="offset points",
                        ha="left",
                        va="center",
                        fontsize=ctx["value_label_style"]["size"],
                        fontfamily=font_family,
                        fontweight="bold" if ctx["value_label_style"].get("bold", True) else "normal",
                        fontstyle="italic" if ctx["value_label_style"].get("italic", False) else "normal",
                        color=ctx["value_label_style"].get("color", "#111827"),
                    )

            ax.set_xlabel(valor_y)
            ax.set_ylabel(valor_x)
        else:
            for _, vals, bars, bottoms in plot_objects:
                if stack_labels and _labels_allowed(show_labels, len(cat_labels), 15):
                    for i_b, b in enumerate(bars):
                        yv = float(vals[i_b])
                        if yv == 0:
                            continue
                        y_mid = bottoms[i_b] + yv / 2.0
                        txt = f"{yv:g}"
                        ax.annotate(
                            txt,
                            (b.get_x() + b.get_width() / 2.0, y_mid),
                            xytext=(0, 0),
                            textcoords="offset points",
                            ha="center",
                            va="center",
                            fontsize=ctx["value_label_style"]["size"],
                            fontfamily=font_family,
                            fontweight="bold" if ctx["value_label_style"].get("bold", True) else "normal",
                            fontstyle="italic" if ctx["value_label_style"].get("italic", False) else "normal",
                            color=ctx["value_label_style"].get("color", "#111827"),
                        )

            if stack_total_label and _labels_allowed(show_labels, len(cat_labels), 15):
                totals = pivot.sum(axis=1).values.astype(float).tolist()
                pad = float(ctx["value_label_style"].get("padding", 3))
                for i_x, total in enumerate(totals):
                    if total == 0:
                        continue
                    ax.annotate(
                        f"{total:g}",
                        (i_x, total),
                        xytext=(0, pad),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=ctx["value_label_style"]["size"],
                        fontfamily=font_family,
                        fontweight="bold" if ctx["value_label_style"].get("bold", True) else "normal",
                        fontstyle="italic" if ctx["value_label_style"].get("italic", False) else "normal",
                        color=ctx["value_label_style"].get("color", "#111827"),
                    )

            ax.set_xlabel(valor_x)
            ax.set_ylabel(valor_y)

    elif chart_type_n == "dispersao":
        _plot_scatter(
            ax=ax,
            df=df,
            valor_x=valor_x,
            valor_y=valor_y,
            colors=colors,
            default_palette=default_palette,
            agrupamento=agrupamento,
        )

        if agrupamento:
            for cat in sorted(df[agrupamento].dropna().unique().tolist(), key=lambda x: str(x)):
                sub = df[df[agrupamento] == cat]
                if _labels_allowed(show_labels, len(sub), 12):
                    _apply_labels(
                        ax,
                        "scatter",
                        font_family,
                        ctx["value_label_style"],
                        x=sub[valor_x],
                        y=sub[valor_y],
                    )
        else:
            if _labels_allowed(show_labels, len(df), 15):
                _apply_labels(
                    ax,
                    "scatter",
                    font_family,
                    ctx["value_label_style"],
                    x=df[valor_x],
                    y=df[valor_y],
                )

        ax.set_xlabel(valor_x)
        ax.set_ylabel(valor_y)

    elif chart_type_n == "pizza":
        _plot_pie(
            ax=ax,
            df=df,
            valor_x=valor_x,
            valor_y=valor_y,
            colors=colors,
            font_family=font_family,
            legend_style=ctx["legend_style"],
            value_label_style=ctx["value_label_style"],
        )

    elif chart_type_n == "area":
        _plot_area(
            ax=ax,
            df=df,
            valor_x=valor_x,
            valor_y=valor_y,
            colors=colors,
            default_palette=default_palette,
            agrupamento=agrupamento,
        )

        if agrupamento:
            for cat in sorted(df[agrupamento].dropna().unique().tolist(), key=lambda x: str(x)):
                sub = df[df[agrupamento] == cat].sort_values(valor_x)
                if _labels_allowed(show_labels, len(sub), 12):
                    _apply_labels(
                        ax,
                        "line",
                        font_family,
                        ctx["value_label_style"],
                        x=sub[valor_x],
                        y=sub[valor_y],
                    )
        else:
            d0 = df.sort_values(valor_x)
            if _labels_allowed(show_labels, len(d0), 15):
                _apply_labels(
                    ax,
                    "line",
                    font_family,
                    ctx["value_label_style"],
                    x=d0[valor_x],
                    y=d0[valor_y],
                )

        ax.set_xlabel(valor_x)
        ax.set_ylabel(valor_y)

    elif chart_type_n == "bolha":
        _plot_bubble(
            ax=ax,
            df=df,
            valor_x=valor_x,
            valor_y=valor_y,
            valor_z=valor_z,
            colors=colors,
            default_palette=default_palette,
            agrupamento=agrupamento,
        )

        if agrupamento:
            for cat in sorted(df[agrupamento].dropna().unique().tolist(), key=lambda x: str(x)):
                sub = df[df[agrupamento] == cat].sort_values(valor_x)
                if _labels_allowed(show_labels, len(sub), 12):
                    _apply_labels(
                        ax,
                        "scatter",
                        font_family,
                        ctx["value_label_style"],
                        x=sub[valor_x],
                        y=sub[valor_y],
                        z=sub[valor_z],
                    )
        else:
            d0 = df.sort_values(valor_x)
            if _labels_allowed(show_labels, len(d0), 15):
                _apply_labels(
                    ax,
                    "scatter",
                    font_family,
                    ctx["value_label_style"],
                    x=d0[valor_x],
                    y=d0[valor_y],
                    z=d0[valor_z],
                )

        ax.set_xlabel(valor_x)
        ax.set_ylabel(valor_y)

    else:
        raise ValueError(f"chart_type não suportado: '{chart_type}'.")

    # =====================================================
    # ESCALAS
    # =====================================================
    if chart_type_n != "pizza":
        if orient == "horizontal" and chart_type_n in {"barra", "barra_empilhada"}:
            if x_min is not None or x_max is not None:
                ax.set_xlim(left=x_min, right=x_max)
            if y_min is not None or y_max is not None:
                ax.set_ylim(bottom=y_min, top=y_max)
        else:
            if y_min is not None or y_max is not None:
                ax.set_ylim(bottom=y_min, top=y_max)
            if x_min is not None or x_max is not None:
                ax.set_xlim(left=x_min, right=x_max)

    # =====================================================
    # SECUNDÁRIO
    # =====================================================
    if sec is not None and chart_type_n != "pizza":
        ax2 = _plot_secondary(
            ax=ax,
            df=df,
            sec=sec,
            valor_x=valor_x,
            colors=colors,
            default_palette=default_palette,
            orientation=orient,
            chart_type_n=chart_type_n,
            marker_style=ctx["marker_style"],
            value_label_style=ctx["value_label_style"],
            show_labels=show_labels,
            font_family=font_family,
        )

    # =====================================================
    # ESTILO FINAL
    # =====================================================
    _apply_axes_style(ax, ctx["axis_style"], ctx["grid_style"], font_family)

    if ax2 is not None:
        for sp in ax2.spines.values():
            sp.set_color("#E6E6E6")
            sp.set_linewidth(1.0)

    if chart_type_n != "pizza":
        _apply_legend(ax, ctx["legend_style"], font_family, ax2=ax2)

    _apply_title_style(ax, title, ctx["title_style"], font_family)

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.25)

    return fig, ax, ax2