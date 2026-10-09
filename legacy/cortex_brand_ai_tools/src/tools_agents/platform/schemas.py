from __future__ import annotations

from typing import List, Optional, Union, Any, Dict
from pydantic import BaseModel, Field, field_validator


StrOrList = Optional[Union[str, List[str]]]


class ExportDatabaseMAInput(BaseModel):
    url_platform: str = Field(
        ...,
        description="URL da plataforma Cortex, por exemplo: https://americanas.cortex-intelligence.com/"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Data inicial no formato YYYY-MM-DD"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Data final no formato YYYY-MM-DD"
    )

    empresa_analisada: StrOrList = Field(
        default=None,
        description="Empresa ou lista de empresas analisadas"
    )
    produto_analisado: StrOrList = Field(
        default=None,
        description="Produto ou lista de produtos analisados"
    )
    midia: StrOrList = Field(
        default=None,
        description="Mídia ou lista de mídias, que são exatamente: Bluesky, Facebook, Impresso, Instagram. Newsletter, Online, Podcast, Rádio, Redes Sociais, Threads, TikTok, Tumblr - Tags, TV, X, YouTube"
    )
    tier: StrOrList = Field(
        default=None,
        description="Tier ou lista de tiers que são exatamete: 'Tier 1, 'Tier 2', 'Outros'"
    )
    estado: StrOrList = Field(
        default=None,
        description="Estado ou lista de estados, exemplos: Bahia, São Paulo"
    )
    tipos_de_impactos: StrOrList = Field(
        default=None,
        description="Tipos de impacto exatamente: Promotores, Detratores, Inócuos"
    )
    sentimento: StrOrList = Field(
        default=None,
        description="Sentimento ou lista de sentimentos exatamente: Positivo, Negativo e Neutro"
    )
    protagonismo: StrOrList = Field(
        default=None,
        description="Protagonismo ou lista de protagonismos: "
    )
    topico: StrOrList = Field(
        default=None,
        description="Tópico ou lista de tópicos"
    )
    assuntos_especifico: StrOrList = Field(
        default=None,
        description="Assunto específico ou lista de assuntos específicos"
    )
    acao_comunicacao: StrOrList = Field(
        default=None,
        description="Ação de comunicação ou lista de ações de comunicação"
    )
    origem_mencao: StrOrList = Field(
        default=None,
        description="Origem da menção ou lista de origens"
    )
    jornalista: StrOrList = Field(
        default=None,
        description="Jornalista ou lista de jornalistas"
    )
    temas: StrOrList = Field(
        default=None,
        description="Tema ou lista de temas"
    )
    macro_assunto: StrOrList = Field(
        default=None,
        description="Macro assunto ou lista de macro assuntos"
    )
    representa_empresa: Optional[str] = Field(
        default=None,
        description="Se a menção representa a empresa. Normalmente 'Sim' ou 'Não'"
    )
    status_classificacao: StrOrList = Field(
        default=None,
        description="Status da classificação ou lista de status"
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # validação simples para YYYY-MM-DD
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("A data deve estar no formato YYYY-MM-DD")
        return v

    @field_validator(
        "empresa_analisada",
        "produto_analisado",
        "midia",
        "tier",
        "estado",
        "tipos_de_impactos",
        "sentimento",
        "protagonismo",
        "topico",
        "assuntos_especifico",
        "acao_comunicacao",
        "origem_mencao",
        "jornalista",
        "temas",
        "macro_assunto",
        "status_classificacao",
        mode="before",
    )
    @classmethod
    def normalize_str_or_list(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                if not isinstance(item, str):
                    item = str(item)
                item = item.strip()
                if item:
                    cleaned.append(item)
            return cleaned or None
        return v


    def to_service_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True)
    

class ExportDatabaseMAMeta(BaseModel):
    rows: int
    columns_count: int
    columns: List[str]
    filters_applied: Dict[str, Any]


class ExportDatabaseMAOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str   # chave principal
    meta: ExportDatabaseMAMeta
    preview: List[Dict[str, Any]]


class ToolErrorOutput(BaseModel):
    status: str = "error"
    message: str
    error_type: str
    details: Optional[str] = None


# =============================
# BASE DE PUBLICAÇÕES
# =============================

class ExportDatabasePublInput(BaseModel):
    url_platform: str = Field(
        ...,
        description="URL da plataforma Cortex."
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Data inicial no formato YYYY-MM-DD."
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Data final no formato YYYY-MM-DD."
    )

    empresa_citada: StrOrList = Field(
        default=None,
        description="Empresa citada ou lista de empresas citadas."
    )
    produto_citado: StrOrList = Field(
        default=None,
        description="Produto citado ou lista de produtos citados."
    )
    midia: StrOrList = Field(
        default=None,
        description="Mídia ou lista de mídias."
    )
    tier: StrOrList = Field(
        default=None,
        description="Tier ou lista de tiers."
    )
    estado: StrOrList = Field(
        default=None,
        description="Estado ou lista de estados."
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("A data deve estar no formato YYYY-MM-DD")
        return v

    @field_validator(
        "empresa_citada",
        "produto_citado",
        "midia",
        "tier",
        "estado",
        mode="before",
    )
    @classmethod
    def normalize_str_or_list(cls, v):
        if v is None:
            return None

        if isinstance(v, str):
            v = v.strip()
            return v if v else None

        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                if not isinstance(item, str):
                    item = str(item)
                item = item.strip()
                if item:
                    cleaned.append(item)
            return cleaned or None

        return v

    def to_service_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True)


class ExportDatabasePublMeta(BaseModel):
    rows: int
    columns_count: int
    columns: List[str]
    filters_applied: Dict[str, Any]


class ExportDatabasePublOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: ExportDatabasePublMeta
    preview: List[Dict[str, Any]]

# =========================
# BASE DE AÇÕES
# =========================    

class ExportActionDatabaseInput(BaseModel):
    url_platform: str = Field(
        ...,
        description="URL da plataforma Cortex, por exemplo: https://americanas.cortex-intelligence.com/"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Data inicial no formato YYYY-MM-DD."
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Data final no formato YYYY-MM-DD."
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("A data deve estar no formato YYYY-MM-DD")
        return v

    def to_service_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True)


class ExportActionDatabaseMeta(BaseModel):
    rows: int
    columns_count: int
    columns: List[str]
    filters_applied: Dict[str, Any]


class ExportActionDatabaseOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: ExportActionDatabaseMeta
    preview: List[Dict[str, Any]]


# =========================
# GET INFOS BRAND
# =========================    



class GetInfosBrandInput(BaseModel):
    url_platform: str = Field(
        ...,
        description="URL da plataforma Cortex."
    )

    def to_service_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True)


class GetInfosBrandMeta(BaseModel):
    rows: int
    columns_count: int
    columns: List[str]
    filters_applied: Dict[str, Any]


class GetInfosBrandOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: GetInfosBrandMeta
    preview: List[Dict[str, Any]]


# =========================
# PR DATA
# =========================    

class GetPRDataDataFrameInput(BaseModel):
    start_date: str = Field(
        ...,
        description="Data inicial no formato YYYY-MM-DD."
    )
    end_date: str = Field(
        ...,
        description="Data final no formato YYYY-MM-DD."
    )
    therms_values: List[str] = Field(
        ...,
        description="Lista de termos para busca no PRData."
    )
    media_outlets: StrOrList = Field(
        default=None,
        description="Veículo ou lista de veículos de mídia."
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("A data deve estar no formato YYYY-MM-DD")
        return v

    @field_validator("therms_values", mode="before")
    @classmethod
    def validate_therms_values(cls, v):
        if v is None:
            raise ValueError("therms_values é obrigatório")

        if isinstance(v, str):
            v = [v]

        if not isinstance(v, list):
            raise ValueError("therms_values deve ser uma lista de strings")

        cleaned = []
        for item in v:
            if item is None:
                continue
            if not isinstance(item, str):
                item = str(item)
            item = item.strip()
            if item:
                cleaned.append(item)

        if not cleaned:
            raise ValueError("therms_values deve conter ao menos um termo válido")

        return cleaned

    @field_validator("media_outlets", mode="before")
    @classmethod
    def normalize_media_outlets(cls, v):
        if v is None:
            return None

        if isinstance(v, str):
            v = v.strip()
            return v if v else None

        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                if not isinstance(item, str):
                    item = str(item)
                item = item.strip()
                if item:
                    cleaned.append(item)
            return cleaned or None

        return v

    def to_service_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True)


class GetPRDataDataFrameMeta(BaseModel):
    rows: int
    columns_count: int
    columns: List[str]
    filters_applied: Dict[str, Any]


class GetPRDataDataFrameOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: GetPRDataDataFrameMeta
    preview: List[Dict[str, Any]]


### OpenSource

MIDIAS_PUBLICADAS_VALIDAS = {
    "Online",
    "X",
    "Instagram",
    "Facebook",
    "YouTube",
    "Bluesky",
}


class GetPRDataOpenSourceDataFrameInput(BaseModel):
    start_date: str = Field(
        ...,
        description="Data inicial no formato YYYY-MM-DD."
    )
    end_date: str = Field(
        ...,
        description="Data final no formato YYYY-MM-DD."
    )
    therms_values: List[str] = Field(
        ...,
        description="Lista de termos para busca no PRData."
    )
    media_outlets: StrOrList = Field(
        default=None,
        description="Veículo ou lista de veículos de mídia."
    )
    midia_publicada: StrOrList = Field(
        default=None,
        description=(
            "Mídia publicada ou lista de mídias publicadas. "
            "Valores aceitos: Online, X, Instagram, Facebook, YouTube, Bluesky."
        )
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("A data deve estar no formato YYYY-MM-DD")
        return v

    @field_validator("therms_values", mode="before")
    @classmethod
    def validate_therms_values(cls, v):
        if v is None:
            raise ValueError("therms_values é obrigatório")

        if isinstance(v, str):
            v = [v]

        if not isinstance(v, list):
            raise ValueError("therms_values deve ser uma lista de strings")

        cleaned = []
        for item in v:
            if item is None:
                continue
            if not isinstance(item, str):
                item = str(item)
            item = item.strip()
            if item:
                cleaned.append(item)

        if not cleaned:
            raise ValueError("therms_values deve conter ao menos um termo válido")

        return cleaned

    @field_validator("media_outlets", mode="before")
    @classmethod
    def normalize_media_outlets(cls, v):
        if v is None:
            return None

        if isinstance(v, str):
            v = v.strip()
            return v if v else None

        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                if not isinstance(item, str):
                    item = str(item)
                item = item.strip()
                if item:
                    cleaned.append(item)
            return cleaned or None

        return v

    @field_validator("midia_publicada", mode="before")
    @classmethod
    def normalize_midia_publicada(cls, v):
        if v is None:
            return None

        if isinstance(v, str):
            v = v.strip()
            if not v:
                return None
            if v not in MIDIAS_PUBLICADAS_VALIDAS:
                raise ValueError(
                    f"midia_publicada inválida: '{v}'. "
                    f"Valores aceitos: {sorted(MIDIAS_PUBLICADAS_VALIDAS)}"
                )
            return v

        if isinstance(v, list):
            cleaned = []
            invalids = []

            for item in v:
                if item is None:
                    continue
                if not isinstance(item, str):
                    item = str(item)

                item = item.strip()
                if not item:
                    continue

                if item not in MIDIAS_PUBLICADAS_VALIDAS:
                    invalids.append(item)
                else:
                    cleaned.append(item)

            if invalids:
                raise ValueError(
                    f"Valores inválidos em midia_publicada: {invalids}. "
                    f"Valores aceitos: {sorted(MIDIAS_PUBLICADAS_VALIDAS)}"
                )

            return cleaned or None

        raise ValueError("midia_publicada deve ser string ou lista de strings")

    def to_service_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True)


### 


class GetMSSDataFrameInput(BaseModel):
    veiculos_mss: StrOrList = Field(
        default=None,
        description="Veículo MSS ou lista de veículos MSS."
    )
    veiculos_fornecedor: StrOrList = Field(
        default=None,
        description="Veículo do fornecedor ou lista de veículos do fornecedor."
    )
    fornecedores: StrOrList = Field(
        default=None,
        description="Fornecedor ou lista de fornecedores."
    )
    tier: StrOrList = Field(
        default=None,
        description="Tier ou lista de tiers."
    )
    tipo_publico: StrOrList = Field(
        default=None,
        description="Tipo de público ou lista de tipos de público."
    )
    estados: StrOrList = Field(
        default=None,
        description="Estado ou lista de estados."
    )
    cidades: StrOrList = Field(
        default=None,
        description="Cidade ou lista de cidades."
    )
    pais: StrOrList = Field(
        default=None,
        description="País ou lista de países."
    )

    @field_validator(
        "veiculos_mss",
        "veiculos_fornecedor",
        "fornecedores",
        "tier",
        "tipo_publico",
        "estados",
        "cidades",
        "pais",
        mode="before",
    )
    @classmethod
    def normalize_str_or_list(cls, v):
        if v is None:
            return None

        if isinstance(v, str):
            v = v.strip()
            return v if v else None

        if isinstance(v, list):
            cleaned = []
            for item in v:
                if item is None:
                    continue
                if not isinstance(item, str):
                    item = str(item)
                item = item.strip()
                if item:
                    cleaned.append(item)
            return cleaned or None

        return v

    def to_service_kwargs(self) -> dict:
        return self.model_dump(exclude_none=True)


class GetMSSDataFrameMeta(BaseModel):
    rows: int
    columns_count: int
    columns: List[str]
    filters_applied: Dict[str, Any]


class GetMSSDataFrameOutput(BaseModel):
    status: str = "success"
    message: str
    dataframe_id: str
    meta: GetMSSDataFrameMeta
    preview: List[Dict[str, Any]]