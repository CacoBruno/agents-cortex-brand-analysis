from __future__ import annotations

from .labels import (
    _apply_labels,
    _merge_value_label_style,
)
from .styles import _apply_axes_style
from .utils import (
    _get_color_for_cat_from,
    _get_single_color_from,
    _get_main_cat_order,
    _norm_type,
    _reindex_series_to_main_order,
)


def _plot_secondary(
    ax,
    df,
    sec: dict | None,
    valor_x: str,
    colors,
    default_palette,
    orientation: str,
    chart_type_n: str,
    marker_style: dict,
    value_label_style: dict,
    show_labels: bool,
    font_family: str,
):
    """
    Plota eixo secundário com suporte a:
    - linha
    - barra

    Combinações suportadas:
    - gráfico principal vertical -> eixo secundário em y (ax.twinx)
    - gráfico principal horizontal de barra/barra empilhada -> eixo secundário em x (ax.twiny)

    Parâmetros esperados em sec:
    {
        "chart_type": "linha" | "barra",
        "valor_y": "nome_coluna",
        "agrupamento": None | "coluna_categoria",
        "colors": None | dict | list,
        "y_min": None | float,
        "y_max": None | float,
        "ylabel": None | str,
        "axis_style": None | dict,
        "value_label_style": None | dict,
        "marker_style": None | dict,
        "alpha": 0.9,
    }
    """
    if sec is None or chart_type_n == "pizza":
        return None

    sec_type = _norm_type(sec["chart_type"])
    sec_y = sec["valor_y"]
    sec_group = sec.get("agrupamento")
    sec_colors = sec.get("colors") if sec.get("colors") is not None else colors
    sec_alpha = float(sec.get("alpha", 0.9))

    is_horizontal_combo = (orientation == "horizontal") and (
        chart_type_n in {"barra", "barra_empilhada"}
    )

    if is_horizontal_combo:
        ax2 = ax.twiny()
        ax2.xaxis.set_label_position("top")
        ax2.xaxis.tick_top()
        ax2.set_ylim(ax.get_ylim())
        ax2.set_yticks(ax.get_yticks())
        ax2.set_yticklabels([t.get_text() for t in ax.get_yticklabels()])

        if sec.get("ylabel"):
            ax2.set_xlabel(str(sec["ylabel"]))
    else:
        ax2 = ax.twinx()
        if sec.get("ylabel"):
            ax2.set_ylabel(str(sec["ylabel"]))

    if sec.get("y_min") is not None or sec.get("y_max") is not None:
        if is_horizontal_combo:
            ax2.set_xlim(left=sec.get("y_min"), right=sec.get("y_max"))
        else:
            ax2.set_ylim(bottom=sec.get("y_min"), top=sec.get("y_max"))

    sec_vls = _merge_value_label_style(value_label_style, sec.get("value_label_style"))

    if not (
        isinstance(sec.get("value_label_style"), dict)
        and "unit" in sec["value_label_style"]
    ):
        sec_vls["unit"] = None

    if not (
        isinstance(sec.get("value_label_style"), dict)
        and "decimals" in sec["value_label_style"]
    ):
        sec_vls["decimals"] = 0

    if not (
        isinstance(sec.get("value_label_style"), dict)
        and "decimal_comma" in sec["value_label_style"]
    ):
        sec_vls["decimal_comma"] = False

    sec_mks = dict(marker_style)
    if isinstance(sec.get("marker_style"), dict):
        sec_mks.update({k: v for k, v in sec["marker_style"].items() if v is not None})

    main_order = _get_main_cat_order(ax, is_horizontal=is_horizontal_combo)

    def _plot_secondary_series(ax_sec, cat_axis, val_axis, label, color):
        if is_horizontal_combo:
            if sec_type == "linha":
                mk2 = str(sec_mks.get("marker", "o"))
                ax_sec.plot(
                    val_axis,
                    cat_axis,
                    label=str(label),
                    color=color,
                    alpha=sec_alpha,
                    linewidth=sec_mks.get("linewidth", 2),
                    marker=mk2,
                    markersize=sec_mks.get("markersize", 5),
                    markeredgecolor=sec_mks.get("markeredgecolor", None),
                    markeredgewidth=sec_mks.get("markeredgewidth", 0.8),
                    markerfacecolor=(
                        sec_mks.get("markerfacecolor")
                        if sec_mks.get("markerfacecolor") is not None
                        else color
                    ),
                    markevery=sec_mks.get("markevery", 1),
                )
            elif sec_type == "barra":
                ax_sec.barh(
                    cat_axis,
                    val_axis,
                    label=str(label),
                    color=color,
                    alpha=sec_alpha,
                    height=0.35,
                )
            else:
                raise ValueError(
                    "secondary_spec horizontal: suportado para 'linha' e 'barra'."
                )
        else:
            if sec_type == "linha":
                mk2 = str(sec_mks.get("marker", "o"))
                ax_sec.plot(
                    cat_axis,
                    val_axis,
                    label=str(label),
                    color=color,
                    alpha=sec_alpha,
                    linewidth=sec_mks.get("linewidth", 2),
                    marker=mk2,
                    markersize=sec_mks.get("markersize", 5),
                    markeredgecolor=sec_mks.get("markeredgecolor", None),
                    markeredgewidth=sec_mks.get("markeredgewidth", 0.8),
                    markerfacecolor=(
                        sec_mks.get("markerfacecolor")
                        if sec_mks.get("markerfacecolor") is not None
                        else color
                    ),
                    markevery=sec_mks.get("markevery", 1),
                )
            elif sec_type == "barra":
                ax_sec.bar(
                    cat_axis,
                    val_axis,
                    label=str(label),
                    color=color,
                    alpha=sec_alpha,
                )
            else:
                raise ValueError(
                    "secondary_spec: suportado para 'linha' e 'barra'."
                )

    if sec_group:
        cats2 = sorted(df[sec_group].dropna().unique().tolist(), key=lambda x: str(x))
        labels_ok2 = (
            all(len(df[df[sec_group] == cat2]) <= 12 for cat2 in cats2)
            if show_labels
            else False
        )

        for i2, cat2 in enumerate(cats2):
            c2 = _get_color_for_cat_from(cat2, i2, default_palette, sec_colors)

            tmp2 = df[df[sec_group] == cat2][[valor_x, sec_y]].copy()
            tmp2[sec_y] = tmp2[sec_y].apply(
                lambda x: 0.0 if x is None else x
            )
            s2 = tmp2.groupby(valor_x, dropna=False)[sec_y].sum()
            s2 = _reindex_series_to_main_order(s2, main_order).fillna(0.0)

            cat_axis = list(s2.index)
            val_axis = s2.values.astype(float).tolist()

            _plot_secondary_series(
                ax2,
                cat_axis,
                val_axis,
                (sec.get("ylabel") or cat2),
                c2,
            )

            if labels_ok2 and sec_type == "linha":
                if is_horizontal_combo:
                    _apply_labels(
                        ax2,
                        "line_h",
                        font_family,
                        sec_vls,
                        x=val_axis,
                        y_labels=cat_axis,
                    )
                else:
                    _apply_labels(
                        ax2,
                        "line",
                        font_family,
                        sec_vls,
                        x=cat_axis,
                        y=val_axis,
                    )
    else:
        sec_c = _get_single_color_from(sec_colors, default_palette)

        tmp = df[[valor_x, sec_y]].copy()
        tmp[sec_y] = tmp[sec_y].apply(lambda x: 0.0 if x is None else x)
        s = tmp.groupby(valor_x, dropna=False)[sec_y].sum()
        s = _reindex_series_to_main_order(s, main_order).fillna(0.0)

        cat_axis = list(s.index)
        val_axis = s.values.astype(float).tolist()

        _plot_secondary_series(
            ax2,
            cat_axis,
            val_axis,
            (sec.get("ylabel") or sec_y),
            sec_c,
        )

        if bool(show_labels) and len(cat_axis) <= 12 and sec_type == "linha":
            if is_horizontal_combo:
                _apply_labels(
                    ax2,
                    "line_h",
                    font_family,
                    sec_vls,
                    x=val_axis,
                    y_labels=cat_axis,
                )
            else:
                _apply_labels(
                    ax2,
                    "line",
                    font_family,
                    sec_vls,
                    x=cat_axis,
                    y=val_axis,
                )

    if isinstance(sec.get("axis_style"), dict):
        sec_axis_style = {
            "x": {
                "size": 10,
                "bold": False,
                "italic": False,
                "rotation": 0,
                "color": "#374151",
            },
            "y": {
                "size": 10,
                "bold": False,
                "italic": False,
                "rotation": 0,
                "color": "#374151",
            },
            "xlabel": {
                "size": 11,
                "bold": False,
                "italic": False,
                "color": "#111827",
            },
            "ylabel": {
                "size": 11,
                "bold": False,
                "italic": False,
                "color": "#111827",
            },
        }

        for k in sec_axis_style:
            if k in sec["axis_style"] and isinstance(sec["axis_style"][k], dict):
                sec_axis_style[k].update(
                    {kk: vv for kk, vv in sec["axis_style"][k].items() if vv is not None}
                )
    else:
        sec_axis_style = {
            "x": {
                "size": 10,
                "bold": False,
                "italic": False,
                "rotation": 0,
                "color": "#374151",
            },
            "y": {
                "size": 10,
                "bold": False,
                "italic": False,
                "rotation": 0,
                "color": "#374151",
            },
            "xlabel": {
                "size": 11,
                "bold": False,
                "italic": False,
                "color": "#111827",
            },
            "ylabel": {
                "size": 11,
                "bold": False,
                "italic": False,
                "color": "#111827",
            },
        }

    _apply_axes_style(
        ax2,
        sec_axis_style,
        {"horizontal": False, "vertical": False},
        font_family,
    )

    return ax2