from __future__ import annotations

import gzip
import io
import json
from urllib.parse import urlparse

import httpx
import pandas as pd

from cortex_brand_analysis.config import Settings
from cortex_brand_analysis.domain.classification import (
    ClassificationRecord,
    ClassificationSelector,
)
from cortex_brand_analysis.domain.models import PublicationMatch

CHECK_FIELDS = [
    "ID Cortex",
    "Título",
    "Data",
    "Fonte",
    "Link original da publicação",
    "Link",
]

CHECK_FIELDS_PR_DATA = [
    "titulo_da_publicacao",
    "nome_fonte_normalizado",
    "Fornecedor",
    "data_da_publicacao",
    "cliente",
    "original_link",
    "clipadora_link",
    "nome_fornecedor",
]

REVISION_FIELDS = [
    "Chave Análise de Mídia Hash",
    "Título",
    "Fonte",
    "Link original da publicação",
    "Link",
    "Empresa analisada",
    "Produto analisado",
    "Alcance total",
    "Tier",
    "Sentimento",
    "Nível de Protagonismo",
    "Tópicos",
    "Assunto específico",
    "Ação",
    "Origem da menção",
    "Jornalista",
    "Temas",
    "Tipo da ação",
]

ANALISE_MIDIA_CUBE_ID = "01f6057b711545708703eec79e5426fd"


class CortexError(RuntimeError):
    pass


class CortexAuthenticationError(CortexError):
    pass


class CortexHTTPGateway:
    """Adapter for Cortex cube read/write operations."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        if not settings.platform_login or not settings.platform_password:
            raise CortexAuthenticationError(
                "PLATFORM_LOGIN and PLATFORM_PASSWORD are required for Cortex operations"
            )
        self.settings = settings
        self.client = client or httpx.Client(timeout=settings.http_timeout_seconds)

    @staticmethod
    def client_name(platform_url: str) -> str:
        candidate = platform_url if "://" in platform_url else f"https://{platform_url}"
        host = urlparse(candidate).hostname
        if not host:
            raise ValueError(f"Invalid platform URL: {platform_url}")
        return host.split(".")[0].lower()

    def _authenticate(self, client_name: str) -> dict[str, str]:
        response = self.client.post(
            f"https://{client_name}.cortex-intelligence.com/"
            "service/integration-authorization-service.login",
            json={
                "login": self.settings.platform_login,
                "password": self.settings.platform_password,
            },
        )
        if response.status_code != 200:
            raise CortexAuthenticationError(
                f"Cortex authentication failed with status {response.status_code}"
            )
        payload = response.json()
        try:
            return {
                "x-authorization-user-id": str(payload["userId"]),
                "x-authorization-token": str(payload["key"]),
            }
        except KeyError as exc:
            raise CortexAuthenticationError("Unexpected authentication response") from exc

    def _bearer_headers(self, client_name: str) -> dict[str, str]:
        response = self.client.post(
            f"https://{client_name}.cortex-intelligence.com/"
            "service/integration-authorization-service.login",
            json={
                "login": self.settings.platform_login,
                "password": self.settings.platform_password,
            },
        )
        response.raise_for_status()
        payload = response.json()
        key = payload.get("key")
        if not key:
            raise CortexAuthenticationError("Missing bearer token in authentication response")
        return {"Authorization": f"Bearer {key}"}

    @staticmethod
    def _filter_payload(filters: list[dict]) -> str:
        normalized: list[dict] = []
        for item in filters:
            values = item["values"]
            payload: dict = {
                "name": item["name"],
                "exclude": item.get("exclude", False),
                "exactMatch": item.get("exact_match", True),
            }
            if isinstance(values, tuple):
                start, end = values
                payload["rangeStart"] = int(str(start).replace("-", ""))
                payload["rangeEnd"] = int(str(end).replace("-", ""))
            elif isinstance(values, list):
                payload["value"] = [str(value) for value in values]
            else:
                raise TypeError("filter values must be a list or tuple")
            normalized.append(payload)
        return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _headers_payload(fields: list[str]) -> str:
        return json.dumps([{"name": field} for field in fields], ensure_ascii=False)

    def _download_cube(
        self,
        client_name: str,
        cube_name: str,
        fields: list[str],
        filters: list[dict],
    ) -> pd.DataFrame:
        headers = self._authenticate(client_name)
        response = self.client.post(
            f"https://{client_name}.cortex-intelligence.com/"
            "service/integration-cube-service.download?",
            headers=headers,
            data={
                "cube": json.dumps({"name": cube_name}, ensure_ascii=False),
                "charset": "UTF-16",
                "delimiter": "\t",
                "quote": '"',
                "escape": '"',
                "headers": self._headers_payload(fields),
                "filters": self._filter_payload(filters),
            },
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        raw = gzip.decompress(response.content) if "gzip" in content_type else response.content
        text = raw.decode("utf-16", "surrogateescape")
        if not text.strip():
            return pd.DataFrame(columns=fields)
        return pd.read_csv(io.StringIO(text), delimiter="\t")

    def check_publications(
        self,
        platform_url: str,
        original_urls: list[str],
        clipping_urls: list[str],
    ) -> list[PublicationMatch]:
        client_name = self.client_name(platform_url)
        frames: list[pd.DataFrame] = []

        if original_urls:
            frames.append(
                self._download_cube(
                    client_name,
                    "Publicações",
                    CHECK_FIELDS,
                    [{
                        "name": "Link original da publicação",
                        "exact_match": False,
                        "values": original_urls,
                    }],
                )
            )

        if clipping_urls:
            frames.append(
                self._download_cube(
                    client_name,
                    "Publicações",
                    CHECK_FIELDS,
                    [{
                        "name": "Link",
                        "exact_match": False,
                        "values": clipping_urls,
                    }],
                )
            )

        if not frames:
            return []

        data = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["ID Cortex"])
        return [
            PublicationMatch(
                cortex_id=_as_optional_str(row.get("ID Cortex")),
                title=_as_optional_str(row.get("Título")),
                source=_as_optional_str(row.get("Fonte")),
                date=_as_optional_str(row.get("Data")),
                original_url=_as_optional_str(row.get("Link original da publicação")),
                clipping_url=_as_optional_str(row.get("Link")),
            )
            for row in data.to_dict(orient="records")
        ]

    def check_pr_data(self, original_urls: list[str], client: str) -> list[dict]:
        if not original_urls:
            return []

        frame = self._download_cube(
            "prdata",
            "[Data Delivery] Publicações",
            CHECK_FIELDS_PR_DATA,
            [{
                "name": "original_link",
                "exact_match": False,
                "values": original_urls,
            }],
        )
        if "cliente" in frame.columns:
            frame = frame[frame["cliente"].astype(str) == client]
        return frame.drop_duplicates().to_dict(orient="records")

    def find_classifications(
        self,
        platform_url: str,
        selectors: list[ClassificationSelector],
    ) -> list[ClassificationRecord]:
        client_name = self.client_name(platform_url)
        frames: list[pd.DataFrame] = []

        for selector in selectors:
            if selector.media_analysis_id:
                filters = [{
                    "name": "Chave Análise de Mídia Hash",
                    "exact_match": False,
                    "values": [selector.media_analysis_id],
                }]
            else:
                filters = []
                if selector.original_url:
                    filters.append({
                        "name": "Link original da publicação",
                        "exact_match": False,
                        "values": [selector.original_url],
                    })
                elif selector.clipping_url:
                    filters.append({
                        "name": "Link",
                        "exact_match": False,
                        "values": [selector.clipping_url],
                    })
                elif selector.title:
                    filters.append({
                        "name": "Título",
                        "exact_match": False,
                        "values": [selector.title],
                    })

                if selector.company:
                    filters.append({
                        "name": "Empresa analisada",
                        "exact_match": False,
                        "values": [selector.company],
                    })
                if selector.product:
                    filters.append({
                        "name": "Produto analisado",
                        "exact_match": False,
                        "values": [selector.product],
                    })

            if filters:
                frames.append(
                    self._download_cube(
                        client_name,
                        "Análise de Mídia",
                        REVISION_FIELDS,
                        filters,
                    )
                )

        if not frames:
            return []

        data = (
            pd.concat(frames, ignore_index=True)
            .drop_duplicates(subset=["Chave Análise de Mídia Hash"])
        )

        value_fields = [
            "Alcance total",
            "Tier",
            "Sentimento",
            "Nível de Protagonismo",
            "Tópicos",
            "Assunto específico",
            "Ação",
            "Origem da menção",
            "Jornalista",
            "Temas",
            "Tipo da ação",
        ]

        records: list[ClassificationRecord] = []
        for row in data.to_dict(orient="records"):
            media_id = _as_optional_str(row.get("Chave Análise de Mídia Hash"))
            if not media_id:
                continue
            records.append(
                ClassificationRecord(
                    media_analysis_id=media_id,
                    title=_as_optional_str(row.get("Título")),
                    source=_as_optional_str(row.get("Fonte")),
                    original_url=_as_optional_str(row.get("Link original da publicação")),
                    clipping_url=_as_optional_str(row.get("Link")),
                    company=_as_optional_str(row.get("Empresa analisada")),
                    product=_as_optional_str(row.get("Produto analisado")),
                    values={field: _clean_value(row.get(field)) for field in value_fields},
                )
            )
        return records

    def upload_classification_changes(
        self,
        platform_url: str,
        rows: list[dict],
    ) -> list[str]:
        if not rows:
            return []

        client_name = self.client_name(platform_url)
        headers = self._bearer_headers(client_name)
        dataframe = pd.DataFrame(rows)
        csv_buffer = io.StringIO()
        dataframe.to_csv(csv_buffer, index=False, sep="\t", quotechar='"')
        csv_buffer.seek(0)

        base_url = "https://api.cortex-intelligence.com"
        content = {
            "destinationId": ANALISE_MIDIA_CUBE_ID,
            "fileProcessingTimeout": 3600,
            "executionTimeout": 3600,
        }

        datainput = self.client.post(
            f"{base_url}/datainput",
            headers=headers,
            json=content,
        )
        datainput.raise_for_status()
        data_input_id = datainput.json()["id"]

        execution = self.client.post(
            f"{base_url}/datainput/{data_input_id}/execution",
            headers=headers,
            json=content,
        )
        execution.raise_for_status()
        execution_id = str(execution.json()["executionId"])

        upload = self.client.post(
            f"{base_url}/execution/{execution_id}/file",
            headers=headers,
            data={
                "charset": "UTF-8",
                "quote": '"',
                "escape": "\\",
                "delimiter": "\t",
                "fileType": "CSV",
                "encode": "UTF-8",
            },
            files={
                "file": (
                    "classification-review.tsv",
                    csv_buffer.getvalue(),
                    "text/tab-separated-values",
                )
            },
        )
        upload.raise_for_status()

        start = self.client.put(
            f"{base_url}/execution/{execution_id}/start",
            headers=headers,
        )
        start.raise_for_status()
        return [execution_id]


def _as_optional_str(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    return str(value)


def _clean_value(value: object) -> object | None:
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value
