from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class GenDataviewsInput(BaseModel):
    dataframe_id: str = Field(
        ...,
        description=(
            "ID de um DataFrame previamente armazenado no dataframe_store. "
            "Esse ID deve vir de tools de download ou de transformação."
        )
    )
    data_ancora_semana: Optional[str] = Field(
        default=None,
        description=(
            "Data âncora para início da semana, no formato YYYY-MM-DD. "
            "Se não informada, a função usa o comportamento padrão."
        )
    )

    @field_validator("data_ancora_semana")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("data_ancora_semana deve estar no formato YYYY-MM-DD")
        return v

    def to_service_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True)


class GenDataviewsMeta(BaseModel):
    source_dataframe_id: str
    result_rows: int
    result_columns_count: int
    result_columns: List[str]
    operation: str
    filters_applied: Dict[str, Any]


class GenDataviewsOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: GenDataviewsMeta
    preview: List[Dict[str, Any]]


class ToolErrorOutput(BaseModel):
    status: str = "error"
    message: str
    error_type: str
    details: Optional[str] = None


class CalcNPSScoreInput(BaseModel):
    dataframe_id: str = Field(
        ...,
        description="ID de um DataFrame previamente armazenado no dataframe_store."
    )
    value_col: str = Field(
        default="alcance",
        description="Nome da coluna usada como valor principal no cálculo."
    )
    impacto_col: str = Field(
        default="Tipos de impactos",
        description="Nome da coluna que contém os tipos de impacto."
    )
    group_cols: Union[str, List[str]] = Field(
        default=["Data", "Empresa analisada"],
        description="Coluna ou lista de colunas para agrupamento."
    )
    sum_cols: Union[str, List[str]] = Field(
        default=["alcance", "valoracao", "count"],
        description="Coluna ou lista de colunas a serem somadas."
    )
    dedupe_columns: bool = Field(
        default=True,
        description="Se True, remove colunas duplicadas no resultado."
    )

    @field_validator("value_col", "impacto_col")
    @classmethod
    def validate_required_str(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("O valor deve ser uma string não vazia.")
        return v.strip()

    @field_validator("group_cols", "sum_cols", mode="before")
    @classmethod
    def normalize_str_or_list(cls, v):
        if isinstance(v, tuple):
            v = list(v)

        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("O valor não pode ser string vazia.")
            return v

        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                item = str(item).strip()
                if item:
                    cleaned.append(item)
            if not cleaned:
                raise ValueError("A lista deve conter pelo menos um valor válido.")
            return cleaned

        raise ValueError("O valor deve ser string ou lista de strings.")

    def to_service_kwargs(self) -> dict:
        data = self.model_dump(exclude_none=True)
        data.pop("dataframe_id", None)
        return data


class CalcNPSScoreMeta(BaseModel):
    source_dataframe_id: str
    result_rows: int
    result_columns_count: int
    result_columns: List[str]
    operation: str
    filters_applied: Dict[str, Any]


class CalcNPSScoreOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: CalcNPSScoreMeta
    preview: List[Dict[str, Any]]

class NPSTotalAndContribInput(BaseModel):
    dataframe_id: str = Field(
        ...,
        description="ID de um DataFrame previamente armazenado no dataframe_store."
    )
    dim_col: str = Field(
        ...,
        description='Dimensão de análise. Exemplo: "Temas".'
    )
    value_col: str = Field(
        default="alcance",
        description="Nome da coluna de valor usada no cálculo."
    )
    impacto_col: str = Field(
        default="Tipos de impactos",
        description="Nome da coluna com os tipos de impacto."
    )
    group_cols: Union[str, List[str]] = Field(
        default=["Data", "Empresa analisada"],
        description="Coluna ou lista de colunas para agrupamento."
    )
    impacts: List[str] = Field(
        default=["Promotores", "Detratores", "Inócuos"],
        description="Lista com os labels de impacto considerados no cálculo."
    )
    contr_type: str = Field(
        default="Total",
        description='Tipo de contribuição: "Total" ou "Promotor".'
    )
    round_total: int = Field(
        default=2,
        description="Número de casas decimais para o nps_score."
    )
    round_contrib: int = Field(
        default=4,
        description="Número de casas decimais para a contribuição."
    )

    @field_validator("dim_col", "value_col", "impacto_col", "contr_type")
    @classmethod
    def validate_non_empty_str(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("O valor deve ser uma string não vazia.")
        return v.strip()

    @field_validator("group_cols", mode="before")
    @classmethod
    def normalize_group_cols(cls, v):
        if isinstance(v, tuple):
            v = list(v)

        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("group_cols não pode ser vazio.")
            return v

        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                item = str(item).strip()
                if item:
                    cleaned.append(item)
            if not cleaned:
                raise ValueError("group_cols deve conter ao menos uma coluna válida.")
            return cleaned

        raise ValueError("group_cols deve ser string ou lista de strings.")

    @field_validator("impacts", mode="before")
    @classmethod
    def normalize_impacts(cls, v):
        if isinstance(v, tuple):
            v = list(v)

        if isinstance(v, str):
            v = [v]

        if not isinstance(v, list):
            raise ValueError("impacts deve ser uma lista de strings.")

        cleaned = []
        for item in v:
            if item is None:
                continue
            item = str(item).strip()
            if item:
                cleaned.append(item)

        if not cleaned:
            raise ValueError("impacts deve conter ao menos um valor válido.")

        return cleaned

    @field_validator("contr_type")
    @classmethod
    def validate_contr_type(cls, v: str) -> str:
        allowed = {"Total", "Promotor"}
        if v not in allowed:
            raise ValueError('contr_type deve ser "Total" ou "Promotor".')
        return v

    @field_validator("round_total", "round_contrib")
    @classmethod
    def validate_rounding(cls, v: int) -> int:
        if not isinstance(v, int) or v < 0:
            raise ValueError("O valor deve ser um inteiro maior ou igual a 0.")
        return v

    def to_service_kwargs(self) -> dict:
        data = self.model_dump(exclude_none=True)
        data.pop("dataframe_id", None)
        return data


class NPSTotalAndContribMeta(BaseModel):
    source_dataframe_id: str
    result_rows: int
    result_columns_count: int
    result_columns: List[str]
    operation: str
    filters_applied: Dict[str, Any]


class NPSTotalAndContribOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: NPSTotalAndContribMeta
    preview: List[Dict[str, Any]]


class ProtagonismScoreInput(BaseModel):
    dataframe_id: str = Field(
        ...,
        description="ID de um DataFrame previamente armazenado no dataframe_store."
    )
    value_col: str = Field(
        default="alcance",
        description="Nome da coluna de valor usada no cálculo."
    )
    impacto_col: str = Field(
        default="Nível de Protagonismo final",
        description="Nome da coluna com os níveis de protagonismo."
    )
    group_cols: Union[str, List[str]] = Field(
        default=["Data", "Empresa analisada"],
        description="Coluna ou lista de colunas para agrupamento."
    )
    filter_column: Optional[str] = Field(
        default=None,
        description="Nome da coluna para filtro opcional antes do cálculo."
    )
    filter_value: Optional[Any] = Field(
        default=None,
        description="Valor usado no filtro opcional."
    )

    @field_validator("value_col", "impacto_col")
    @classmethod
    def validate_non_empty_str(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("O valor deve ser uma string não vazia.")
        return v.strip()

    @field_validator("filter_column")
    @classmethod
    def validate_optional_filter_column(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not isinstance(v, str) or not v.strip():
            raise ValueError("filter_column deve ser uma string não vazia.")
        return v.strip()

    @field_validator("group_cols", mode="before")
    @classmethod
    def normalize_group_cols(cls, v):
        if isinstance(v, tuple):
            v = list(v)

        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("group_cols não pode ser vazio.")
            return v

        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                item = str(item).strip()
                if item:
                    cleaned.append(item)
            if not cleaned:
                raise ValueError("group_cols deve conter ao menos uma coluna válida.")
            return cleaned

        raise ValueError("group_cols deve ser string ou lista de strings.")

    def to_service_kwargs(self) -> dict:
        data = self.model_dump(exclude_none=True)
        data.pop("dataframe_id", None)
        return data


class ProtagonismScoreMeta(BaseModel):
    source_dataframe_id: str
    result_rows: int
    result_columns_count: int
    result_columns: List[str]
    operation: str
    filters_applied: Dict[str, Any]


class ProtagonismScoreOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: ProtagonismScoreMeta
    preview: List[Dict[str, Any]]


class FreqScoreInput(BaseModel):
    dataframe_id: str = Field(
        ...,
        description="ID de um DataFrame previamente armazenado no dataframe_store."
    )
    value_col: str = Field(
        default="count",
        description="Nome da coluna de valor usada no cálculo da frequência."
    )
    impacto_col: str = Field(
        default="Tipos de impactos",
        description="Nome da coluna com os tipos de impacto."
    )
    group_cols: Union[str, List[str]] = Field(
        default=["Data", "Empresa analisada"],
        description="Coluna ou lista de colunas para agrupamento."
    )

    @field_validator("value_col", "impacto_col")
    @classmethod
    def validate_non_empty_str(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("O valor deve ser uma string não vazia.")
        return v.strip()

    @field_validator("group_cols", mode="before")
    @classmethod
    def normalize_group_cols(cls, v):
        if isinstance(v, tuple):
            v = list(v)

        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("group_cols não pode ser vazio.")
            return v

        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                item = str(item).strip()
                if item:
                    cleaned.append(item)
            if not cleaned:
                raise ValueError("group_cols deve conter ao menos uma coluna válida.")
            return cleaned

        raise ValueError("group_cols deve ser string ou lista de strings.")

    def to_service_kwargs(self) -> dict:
        data = self.model_dump(exclude_none=True)
        data.pop("dataframe_id", None)
        return data


class FreqScoreMeta(BaseModel):
    source_dataframe_id: str
    result_rows: int
    result_columns_count: int
    result_columns: List[str]
    operation: str
    filters_applied: Dict[str, Any]


class FreqScoreOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: FreqScoreMeta
    preview: List[Dict[str, Any]]


class ValorationScoreInput(BaseModel):
    dataframe_id: str = Field(
        ...,
        description="ID de um DataFrame previamente armazenado no dataframe_store."
    )
    value_col: str = Field(
        default="valoracao",
        description="Nome da coluna de valoração usada no cálculo."
    )
    group_cols: Union[str, List[str]] = Field(
        default=["Data", "Empresa analisada"],
        description="Coluna ou lista de colunas para agrupamento."
    )

    @field_validator("value_col")
    @classmethod
    def validate_non_empty_str(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("value_col deve ser uma string não vazia.")
        return v.strip()

    @field_validator("group_cols", mode="before")
    @classmethod
    def normalize_group_cols(cls, v):
        if isinstance(v, tuple):
            v = list(v)

        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("group_cols não pode ser vazio.")
            return v

        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                item = str(item).strip()
                if item:
                    cleaned.append(item)
            if not cleaned:
                raise ValueError("group_cols deve conter ao menos uma coluna válida.")
            return cleaned

        raise ValueError("group_cols deve ser string ou lista de strings.")

    def to_service_kwargs(self) -> dict:
        data = self.model_dump(exclude_none=True)
        data.pop("dataframe_id", None)
        return data


class ValorationScoreMeta(BaseModel):
    source_dataframe_id: str
    result_rows: int
    result_columns_count: int
    result_columns: List[str]
    operation: str
    filters_applied: Dict[str, Any]


class ValorationScoreOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: ValorationScoreMeta
    preview: List[Dict[str, Any]]


class JornalistaScoreInput(BaseModel):
    dataframe_id: str = Field(
        ...,
        description="ID de um DataFrame previamente armazenado no dataframe_store."
    )
    value_cols: Union[str, List[str]] = Field(
        default=["jornalista_count", "count"],
        description="Coluna ou lista de colunas de valor a serem somadas."
    )
    group_cols: Union[str, List[str]] = Field(
        default=["Data", "Empresa analisada"],
        description="Coluna ou lista de colunas para agrupamento."
    )

    @field_validator("value_cols", "group_cols", mode="before")
    @classmethod
    def normalize_str_or_list(cls, v):
        if isinstance(v, tuple):
            v = list(v)

        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("O valor não pode ser string vazia.")
            return v

        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                item = str(item).strip()
                if item:
                    cleaned.append(item)
            if not cleaned:
                raise ValueError("A lista deve conter ao menos um valor válido.")
            return cleaned

        raise ValueError("O valor deve ser string ou lista de strings.")

    def to_service_kwargs(self) -> dict:
        data = self.model_dump(exclude_none=True)
        data.pop("dataframe_id", None)
        return data


class JornalistaScoreMeta(BaseModel):
    source_dataframe_id: str
    result_rows: int
    result_columns_count: int
    result_columns: List[str]
    operation: str
    filters_applied: Dict[str, Any]


class JornalistaScoreOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: JornalistaScoreMeta
    preview: List[Dict[str, Any]]

class ActionScoreInput(BaseModel):
    dataframe_id: str = Field(
        ...,
        description="ID de um DataFrame previamente armazenado no dataframe_store."
    )
    value_cols: Union[str, List[str]] = Field(
        default=["acao_count", "count"],
        description="Coluna ou lista de colunas de valor a serem somadas."
    )
    group_cols: Union[str, List[str]] = Field(
        default=["Data", "Empresa analisada"],
        description="Coluna ou lista de colunas para agrupamento."
    )

    @field_validator("value_cols", "group_cols", mode="before")
    @classmethod
    def normalize_str_or_list(cls, v):
        if isinstance(v, tuple):
            v = list(v)

        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("O valor não pode ser string vazia.")
            return v

        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                item = str(item).strip()
                if item:
                    cleaned.append(item)
            if not cleaned:
                raise ValueError("A lista deve conter ao menos um valor válido.")
            return cleaned

        raise ValueError("O valor deve ser string ou lista de strings.")

    def to_service_kwargs(self) -> dict:
        data = self.model_dump(exclude_none=True)
        data.pop("dataframe_id", None)
        return data


class ActionScoreMeta(BaseModel):
    source_dataframe_id: str
    result_rows: int
    result_columns_count: int
    result_columns: List[str]
    operation: str
    filters_applied: Dict[str, Any]


class ActionScoreOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: ActionScoreMeta
    preview: List[Dict[str, Any]]
