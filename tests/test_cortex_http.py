import gzip
import json
from urllib.parse import parse_qs

import httpx
import pytest

from cortex_brand_analysis.config import Settings
from cortex_brand_analysis.domain.errors import ConfigurationError, DomainError
from cortex_brand_analysis.services.cortex_http import (
    ANALISE_MIDIA_CUBE_ID,
    CHECK_FIELDS,
    CortexAuthenticationError,
    CortexError,
    CortexHTTPGateway,
)

LOGIN_PATH = "/service/integration-authorization-service.login"
DOWNLOAD_PATH = "/service/integration-cube-service.download"


def make_settings(**overrides):
    values = {
        "mcp_api_key": "x" * 16,
        "platform_login": "user",
        "platform_password": "secret",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def make_gateway(handler):
    return CortexHTTPGateway(
        make_settings(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def publications_tsv() -> str:
    row = ["123", "Matéria", "2026-10-07", "Folha", "https://example.com/a", "https://clip/a"]
    return "\t".join(CHECK_FIELDS) + "\n" + "\t".join(row) + "\n"


def cube_handler(body: bytes, content_type: str, seen: list[httpx.Request]):
    def handler(request):
        seen.append(request)
        if request.url.path == LOGIN_PATH:
            return httpx.Response(200, json={"userId": 7, "key": "token"})
        if request.url.path == DOWNLOAD_PATH:
            return httpx.Response(200, content=body, headers={"content-type": content_type})
        raise AssertionError(f"unexpected request {request.url}")

    return handler


@pytest.mark.parametrize("compressed", [False, True])
def test_check_publications_decodes_utf16_cube(compressed):
    body = publications_tsv().encode("utf-16")
    content_type = "text/tab-separated-values"
    if compressed:
        body = gzip.compress(body)
        content_type = "application/gzip"
    seen: list[httpx.Request] = []
    gateway = make_gateway(cube_handler(body, content_type, seen))

    matches = gateway.check_publications(
        "cliente.cortex-intelligence.com",
        ["https://example.com/a"],
        [],
    )

    assert len(matches) == 1
    assert matches[0].cortex_id == "123"
    assert matches[0].title == "Matéria"
    assert matches[0].original_url == "https://example.com/a"

    login, download = seen
    assert login.url.host == "cliente.cortex-intelligence.com"
    assert json.loads(login.content) == {"login": "user", "password": "secret"}
    assert download.headers["x-authorization-token"] == "token"
    form = parse_qs(download.content.decode())
    assert json.loads(form["cube"][0]) == {"name": "Publicações"}
    assert json.loads(form["filters"][0]) == [
        {
            "name": "Link original da publicação",
            "exclude": False,
            "exactMatch": False,
            "value": ["https://example.com/a"],
        }
    ]


def test_empty_cube_returns_no_matches():
    gateway = make_gateway(cube_handler(b"", "text/plain", []))

    assert gateway.check_publications("cliente", ["https://example.com/a"], []) == []


def test_failed_login_raises_authentication_error():
    gateway = make_gateway(lambda request: httpx.Response(401))

    with pytest.raises(CortexAuthenticationError):
        gateway.check_publications("cliente", ["https://example.com/a"], [])


def test_filter_payload_converts_date_ranges():
    date_range = {"name": "Data", "values": ("2026-10-01", "2026-10-07")}

    payload = json.loads(CortexHTTPGateway._filter_payload([date_range]))

    assert payload == [
        {
            "name": "Data",
            "exclude": False,
            "exactMatch": True,
            "rangeStart": 20261001,
            "rangeEnd": 20261007,
        }
    ]


def test_upload_runs_datainput_flow_against_media_analysis_cube():
    seen: list[httpx.Request] = []

    def handler(request):
        seen.append(request)
        path = request.url.path
        if path == LOGIN_PATH:
            return httpx.Response(200, json={"key": "bearer-token"})
        if path == "/datainput":
            return httpx.Response(200, json={"id": "di-1"})
        if path == "/datainput/di-1/execution":
            return httpx.Response(200, json={"executionId": 42})
        if path in ("/execution/42/file", "/execution/42/start"):
            return httpx.Response(200)
        raise AssertionError(f"unexpected request {request.url}")

    gateway = make_gateway(handler)

    result = gateway.upload_classification_changes(
        "cliente.cortex-intelligence.com",
        [{"Chave Análise de Mídia Hash": "abc", "Sentimento": "Negativo"}],
    )

    assert result == ["42"]
    assert [(r.method, r.url.path) for r in seen[1:]] == [
        ("POST", "/datainput"),
        ("POST", "/datainput/di-1/execution"),
        ("POST", "/execution/42/file"),
        ("PUT", "/execution/42/start"),
    ]
    assert json.loads(seen[1].content)["destinationId"] == ANALISE_MIDIA_CUBE_ID
    assert all(r.headers["Authorization"] == "Bearer bearer-token" for r in seen[1:])
    assert b"Negativo" in seen[3].content


def test_upload_with_unexpected_response_raises_cortex_error():
    def handler(request):
        if request.url.path == LOGIN_PATH:
            return httpx.Response(200, json={"key": "bearer-token"})
        return httpx.Response(200, json={"unexpected": True})

    gateway = make_gateway(handler)

    with pytest.raises(CortexError, match="Unexpected datainput response"):
        gateway.upload_classification_changes("cliente", [{"a": 1}])


def test_missing_credentials_is_a_configuration_error():
    with pytest.raises(ConfigurationError):
        CortexHTTPGateway(make_settings(platform_login=None))


def test_client_name_uses_first_host_label():
    assert CortexHTTPGateway.client_name("https://Cliente.cortex-intelligence.com/x") == "cliente"
    assert CortexHTTPGateway.client_name("cliente.cortex-intelligence.com") == "cliente"


def test_client_name_rejects_invalid_url():
    with pytest.raises(DomainError):
        CortexHTTPGateway.client_name("https://")
