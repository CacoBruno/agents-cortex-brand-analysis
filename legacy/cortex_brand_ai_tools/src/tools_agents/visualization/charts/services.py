from __future__ import annotations

from typing import Any

import pandas as pd

from core.dataframe_store import get_dataframe
from services.charts.chart_service import generate_chart

from src.tools_agents.visualization.charts.schemas import (
    GenerateChartInput,
    GenerateChartMeta,
    GenerateChartOutput,
)


def generate_chart_from_store(params: GenerateChartInput) -> GenerateChartOutput:
    """
    Gera um gráfico a partir de um dataframe salvo no DATAFRAME_STORE.
    """
    df = get_dataframe(params.dataframe_id)

    secondary_spec = (
        params.secondary_spec.model_dump(exclude_none=True)
        if params.secondary_spec is not None
        else None
    )

    result = generate_chart(
        df=df,
        chart_type=params.chart_type,
        valor_x=params.valor_x,
        valor_y=params.valor_y,
        valor_z=params.valor_z,
        agrupamento=params.agrupamento,
        colors=params.colors,
        figsize_w=params.figsize_w,
        figsize_h=params.figsize_h,
        transparent_bg=params.transparent_bg,
        background_color=params.background_color,
        title=params.title,
        output_dir=params.output_dir,
        filename=params.filename,
        dpi=params.dpi,
        output_format=params.output_format,
        return_as=params.return_as,
        x_min=params.x_min,
        x_max=params.x_max,
        y_min=params.y_min,
        y_max=params.y_max,
        font_family=params.font_family,
        show_labels=params.show_labels,
        value_label_style=params.value_label_style,
        title_style=params.title_style,
        axis_style=params.axis_style,
        legend_style=params.legend_style,
        grid_style=params.grid_style,
        marker_style=params.marker_style,
        secondary_spec=secondary_spec,
        stack_by=params.stack_by,
        stack_order=params.stack_order,
        stack_colors=params.stack_colors,
        stack_labels=params.stack_labels,
        stack_total_label=params.stack_total_label,
        orientation=params.orientation,
    )

    meta = GenerateChartMeta(
        input_dataframe_id=params.dataframe_id,
        input_rows=len(df),
        input_columns=list(df.columns),
        chart_type=params.chart_type,
        output_format=params.output_format,
        return_as=params.return_as,
        output_path=result if params.return_as == "path" and isinstance(result, str) else None,
    )

    return GenerateChartOutput(
        message="Gráfico gerado com sucesso.",
        result=result,
        meta=meta,
    )