from __future__ import annotations


def _build_style_context(
    value_label_style=None,
    title_style=None,
    axis_style=None,
    legend_style=None,
    grid_style=None,
    marker_style=None,
):
    vls = {
        "size": 9,
        "bold": True,
        "italic": False,
        "color": "#111827",
        "offset_xy": (0, 6),
        "padding": 3,
        "fields": ["y"],
        "prefix": False,
        "unit": None,
        "decimals": 2,
        "decimal_comma": True,
        "thousands_sep": False,
    }
    if isinstance(value_label_style, dict):
        vls.update({k: v for k, v in value_label_style.items() if v is not None})

    ts = {
        "size": 14,
        "pad": 10,
        "bold": False,
        "italic": False,
        "color": "#111827",
    }
    if isinstance(title_style, dict):
        ts.update({k: v for k, v in title_style.items() if v is not None})

    axst = {
        "x": {"size": 10, "bold": False, "italic": False, "rotation": 0, "color": "#374151"},
        "y": {"size": 10, "bold": False, "italic": False, "rotation": 0, "color": "#374151"},
        "xlabel": {"size": 11, "bold": False, "italic": False, "color": "#111827"},
        "ylabel": {"size": 11, "bold": False, "italic": False, "color": "#111827"},
    }
    if isinstance(axis_style, dict):
        for k in axst:
            if k in axis_style and isinstance(axis_style[k], dict):
                axst[k].update({kk: vv for kk, vv in axis_style[k].items() if vv is not None})

    lgs = {
        "show": True,
        "position": "center",
        "offset": -0.18,
        "font_size": 9,
        "font_color": "#374151",
        "ncol": None,
        "frameon": False,
    }
    if isinstance(legend_style, dict):
        lgs.update({k: v for k, v in legend_style.items() if v is not None})

    gds = {
        "horizontal": True,
        "vertical": True,
        "color": "#DADADA",
        "linewidth": 0.8,
        "linestyle": "-",
    }
    if isinstance(grid_style, dict):
        gds.update({k: v for k, v in grid_style.items() if v is not None})

    mks = {
        "marker": "o",
        "markersize": 5,
        "markeredgecolor": None,
        "markeredgewidth": 0.8,
        "markerfacecolor": None,
        "markevery": 1,
        "by_cat": None,
        "linewidth": 2,
    }
    if isinstance(marker_style, dict):
        mks.update({k: v for k, v in marker_style.items() if v is not None})

    return {
        "value_label_style": vls,
        "title_style": ts,
        "axis_style": axst,
        "legend_style": lgs,
        "grid_style": gds,
        "marker_style": mks,
    }


def _apply_axes_style(ax, axis_style_dict, grid_style_dict, font_family: str):
    for sp in ax.spines.values():
        sp.set_color("#E6E6E6")
        sp.set_linewidth(1.0)

    ax.set_axisbelow(True)

    ax.yaxis.grid(
        bool(grid_style_dict.get("horizontal", True)),
        color=grid_style_dict.get("color", "#DADADA"),
        linewidth=grid_style_dict.get("linewidth", 0.8),
        linestyle=grid_style_dict.get("linestyle", "-"),
    )
    ax.xaxis.grid(
        bool(grid_style_dict.get("vertical", True)),
        color=grid_style_dict.get("color", "#DADADA"),
        linewidth=grid_style_dict.get("linewidth", 0.8),
        linestyle=grid_style_dict.get("linestyle", "-"),
    )

    for lab in ax.get_xticklabels():
        lab.set_fontfamily(font_family)
        lab.set_fontsize(axis_style_dict["x"]["size"])
        lab.set_fontweight("bold" if axis_style_dict["x"]["bold"] else "normal")
        lab.set_fontstyle("italic" if axis_style_dict["x"]["italic"] else "normal")
        lab.set_rotation(axis_style_dict["x"]["rotation"])
        lab.set_color(axis_style_dict["x"]["color"])

    for lab in ax.get_yticklabels():
        lab.set_fontfamily(font_family)
        lab.set_fontsize(axis_style_dict["y"]["size"])
        lab.set_fontweight("bold" if axis_style_dict["y"]["bold"] else "normal")
        lab.set_fontstyle("italic" if axis_style_dict["y"]["italic"] else "normal")
        lab.set_rotation(axis_style_dict["y"]["rotation"])
        lab.set_color(axis_style_dict["y"]["color"])

    ax.xaxis.label.set_fontfamily(font_family)
    ax.xaxis.label.set_fontsize(axis_style_dict["xlabel"]["size"])
    ax.xaxis.label.set_fontweight("bold" if axis_style_dict["xlabel"]["bold"] else "normal")
    ax.xaxis.label.set_fontstyle("italic" if axis_style_dict["xlabel"]["italic"] else "normal")
    ax.xaxis.label.set_color(axis_style_dict["xlabel"]["color"])

    ax.yaxis.label.set_fontfamily(font_family)
    ax.yaxis.label.set_fontsize(axis_style_dict["ylabel"]["size"])
    ax.yaxis.label.set_fontweight("bold" if axis_style_dict["ylabel"]["bold"] else "normal")
    ax.yaxis.label.set_fontstyle("italic" if axis_style_dict["ylabel"]["italic"] else "normal")
    ax.yaxis.label.set_color(axis_style_dict["ylabel"]["color"])


def _apply_title_style(ax, title: str | None, title_style_dict: dict, font_family: str):
    if title is None:
        return

    ax.set_title(
        title,
        fontfamily=font_family,
        fontsize=title_style_dict["size"],
        fontweight="bold" if title_style_dict["bold"] else "normal",
        fontstyle="italic" if title_style_dict["italic"] else "normal",
        color=title_style_dict.get("color", "#111827"),
        pad=title_style_dict["pad"],
    )


def _apply_legend(ax, legend_style_dict, font_family: str, ax2=None):
    if not legend_style_dict.get("show", True):
        return

    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ([], [])
    if ax2 is not None:
        handles2, labels2 = ax2.get_legend_handles_labels()

    handles = handles1 + handles2
    labels = labels1 + labels2

    if not labels:
        return

    x_map = {"left": 0.0, "center": 0.5, "right": 1.0}
    x = x_map.get(str(legend_style_dict.get("position", "center")).lower(), 0.5)
    y = float(legend_style_dict.get("offset", -0.18))
    ncol = legend_style_dict.get("ncol", None)
    if ncol is None:
        ncol = min(4, len(labels))

    ax.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(x, y),
        ncol=ncol,
        frameon=bool(legend_style_dict.get("frameon", False)),
        prop={"family": font_family, "size": legend_style_dict.get("font_size", 9)},
        labelcolor=legend_style_dict.get("font_color", "#374151"),
    )