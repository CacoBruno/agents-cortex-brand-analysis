from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


ChartType = Literal[
    "linha",
    "barra",
    "barra_empilhada",
    "dispersao",
    "pizza",
    "area",
    "bolha",
]


OrientationType = Literal["vertical", "horizontal"]

OutputFormatType = Literal["png", "svg", "pdf", "jpg", "jpeg", "webp"]

ReturnAsType = Literal["path", "bytes", "buffer", "base64", "figure"]


class SecondarySpecInput(BaseModel):
    chart_type: Literal["linha", "barra"] = Field(
        default="linha",
        description="Tipo do gráfico secundário."
    )
    valor_y: str = Field(..., description="Coluna usada no eixo secundário.")
    agrupamento: Optional[str] = Field(
        default=None,
        description="Coluna de agrupamento do gráfico secundário."
    )
    colors: Optional[Union[Dict[str, Any], List[Any]]] = Field(
        default=None,
        description="Cores do gráfico secundário."
    )
    y_min: Optional[float] = Field(default=None)
    y_max: Optional[float] = Field(default=None)
    ylabel: Optional[str] = Field(default=None)
    axis_style: Optional[Dict[str, Any]] = Field(default=None)
    value_label_style: Optional[Dict[str, Any]] = Field(default=None)
    marker_style: Optional[Dict[str, Any]] = Field(default=None)
    alpha: float = Field(default=0.9)


class GenerateChartInput(BaseModel):
    dataframe_id: str = Field(..., description="ID do dataframe salvo no DATAFRAME_STORE.")
    chart_type: ChartType = Field(..., description="Tipo do gráfico.")
    valor_x: str = Field(..., description="Coluna do eixo X.")
    valor_y: Optional[str] = Field(default=None, description="Coluna do eixo Y.")
    valor_z: Optional[str] = Field(default=None, description="Coluna do tamanho da bolha.")
    agrupamento: Optional[str] = Field(default=None, description="Coluna de agrupamento.")
    colors: Optional[Union[Dict[str, Any], List[Any]]] = Field(
        default=None,
        description="Mapa/lista de cores."
    )

    figsize_w: float = Field(default=12.0, description="Largura da figura.")
    figsize_h: float = Field(default=6.0, description="Altura da figura.")
    transparent_bg: bool = Field(default=True, description="Fundo transparente.")
    background_color: Optional[str] = Field(default=None, description="Cor de fundo.")
    title: Optional[str] = Field(default=None, description="Título do gráfico.")

    output_dir: str = Field(default="charts", description="Pasta de saída.")
    filename: Optional[str] = Field(default=None, description="Nome do arquivo.")
    dpi: int = Field(default=200, description="DPI do arquivo raster.")
    output_format: OutputFormatType = Field(default="png", description="Formato do arquivo.")
    return_as: ReturnAsType = Field(default="path", description="Tipo de retorno.")

    x_min: Optional[float] = Field(default=None)
    x_max: Optional[float] = Field(default=None)
    y_min: Optional[float] = Field(default=None)
    y_max: Optional[float] = Field(default=None)

    font_family: str = Field(default="Arial")
    show_labels: bool = Field(default=True)

    value_label_style: Optional[Dict[str, Any]] = Field(default=None)
    title_style: Optional[Dict[str, Any]] = Field(default=None)
    axis_style: Optional[Dict[str, Any]] = Field(default=None)
    legend_style: Optional[Dict[str, Any]] = Field(default=None)
    grid_style: Optional[Dict[str, Any]] = Field(default=None)
    marker_style: Optional[Dict[str, Any]] = Field(default=None)

    secondary_spec: Optional[SecondarySpecInput] = Field(default=None)

    stack_by: Optional[str] = Field(default=None, description="Coluna para barra empilhada.")
    stack_order: Optional[List[Any]] = Field(default=None, description="Ordem das pilhas.")
    stack_colors: Optional[Union[Dict[str, Any], List[Any]]] = Field(default=None)
    stack_labels: bool = Field(default=True)
    stack_total_label: bool = Field(default=False)
    orientation: OrientationType = Field(default="vertical")


class GenerateChartMeta(BaseModel):
    input_dataframe_id: str = Field(..., description="ID do dataframe de entrada.")
    input_rows: int = Field(..., description="Número de linhas do dataframe de entrada.")
    input_columns: List[str] = Field(..., description="Colunas do dataframe de entrada.")
    chart_type: str = Field(..., description="Tipo do gráfico gerado.")
    output_format: str = Field(..., description="Formato de saída.")
    return_as: str = Field(..., description="Tipo de retorno.")
    output_path: Optional[str] = Field(default=None, description="Caminho do arquivo, quando return_as=path.")


class GenerateChartOutput(BaseModel):
    status: str = Field(default="success")
    message: str = Field(..., description="Mensagem de sucesso.")
    result: Optional[Any] = Field(default=None, description="Resultado do gráfico.")
    meta: GenerateChartMeta


class ToolErrorOutput(BaseModel):
    status: str = Field(default="error")
    message: str = Field(..., description="Mensagem de erro.")
    error_type: str = Field(..., description="Tipo da exceção.")
    details: str = Field(..., description="Detalhes do erro.")