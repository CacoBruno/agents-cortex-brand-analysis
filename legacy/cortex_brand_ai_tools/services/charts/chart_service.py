from __future__ import annotations

import pandas as pd

from services.charts.build_figure import build_chart_figure
from services.charts.exporters import export_figure
from services.charts.utils import _norm_type, _norm_orientation, _safe_filename


def generate_chart(
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
    output_dir: str = "charts",
    filename: str | None = None,
    dpi: int = 200,
    output_format: str = "png",
    return_as: str = "path",
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
    fig, ax, ax2 = build_chart_figure(
        df=df,
        chart_type=chart_type,
        valor_x=valor_x,
        valor_y=valor_y,
        valor_z=valor_z,
        agrupamento=agrupamento,
        colors=colors,
        figsize_w=figsize_w,
        figsize_h=figsize_h,
        transparent_bg=transparent_bg,
        background_color=background_color,
        title=title,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        font_family=font_family,
        show_labels=show_labels,
        value_label_style=value_label_style,
        title_style=title_style,
        axis_style=axis_style,
        legend_style=legend_style,
        grid_style=grid_style,
        marker_style=marker_style,
        secondary_spec=secondary_spec,
        stack_by=stack_by,
        stack_order=stack_order,
        stack_colors=stack_colors,
        stack_labels=stack_labels,
        stack_total_label=stack_total_label,
        orientation=orientation,
    )

    if filename is None:
        parts = [_norm_type(chart_type), valor_x]
        if valor_y:
            parts.append(valor_y)
        if valor_z:
            parts.append(valor_z)
        if agrupamento:
            parts.append(f"by_{agrupamento}")
        if _norm_type(chart_type) == "barra_empilhada" and stack_by:
            parts.append(f"stack_{stack_by}")
        parts.append("h" if _norm_orientation(orientation) == "horizontal" else "v")
        if secondary_spec and secondary_spec.get("valor_y"):
            parts.append(f"sec_{secondary_spec['valor_y']}")
        filename = f"{_safe_filename('__'.join(parts))}.{output_format.lower()}"

    return export_figure(
        fig=fig,
        output_format=output_format,
        return_as=return_as,
        output_dir=output_dir,
        filename=filename,
        dpi=dpi,
        transparent_bg=transparent_bg,
        close_figure=True,
    )