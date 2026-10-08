import socket

import httpx
import pytest

from cortex_brand_analysis.config import Settings
from cortex_brand_analysis.domain.errors import ConfigurationError, NewsEnrichmentError
from cortex_brand_analysis.services import news_enrichment
from cortex_brand_analysis.services.news_enrichment import OpenAINewsEnricher

DNS = {
    "news.example.com": "93.184.216.34",
    "other.example.com": "93.184.216.35",
    "intranet.example.com": "10.0.0.5",
    "localhost": "127.0.0.1",
    "metadata.example.com": "169.254.169.254",
}


@pytest.fixture(autouse=True)
def fake_dns(monkeypatch):
    def getaddrinfo(host, port, *args, **kwargs):
        try:
            ip = DNS[host]
        except KeyError:
            ip = host  # literal IPs resolve to themselves
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))]

    monkeypatch.setattr(news_enrichment.socket, "getaddrinfo", getaddrinfo)


def make_enricher(handler):
    settings = Settings(_env_file=None, mcp_api_key="x" * 16, openai_api_key="test-key")
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenAINewsEnricher(settings, client=client)


def unreachable(request):
    raise AssertionError(f"request should have been blocked: {request.url}")


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.example.com/",
        "http://intranet.example.com/admin",
        "http://localhost:8000/",
        "http://[::1]/",
    ],
)
def test_internal_destinations_are_blocked(url):
    enricher = make_enricher(unreachable)

    with pytest.raises(NewsEnrichmentError, match="non-public address"):
        enricher.enrich(url, "cliente")


@pytest.mark.parametrize("url", ["ftp://news.example.com/file", "file:///etc/passwd"])
def test_non_http_schemes_are_blocked(url):
    enricher = make_enricher(unreachable)

    with pytest.raises(NewsEnrichmentError, match="only http and https"):
        enricher.enrich(url, "cliente")


def test_redirect_to_internal_address_is_blocked():
    requested = []

    def handler(request):
        requested.append(str(request.url))
        return httpx.Response(302, headers={"Location": "http://intranet.example.com/secret"})

    enricher = make_enricher(handler)

    with pytest.raises(NewsEnrichmentError, match="non-public address"):
        enricher.enrich("https://news.example.com/a", "cliente")
    assert requested == ["https://news.example.com/a"]


def test_public_redirects_are_followed():
    def handler(request):
        if request.url.host == "news.example.com":
            return httpx.Response(301, headers={"Location": "https://other.example.com/b"})
        return httpx.Response(200, html="<p>conteúdo</p>")

    enricher = make_enricher(handler)

    final_url, body, _ = enricher._fetch("https://news.example.com/a")

    assert final_url == "https://other.example.com/b"
    assert "conteúdo".encode() in body


def test_redirect_loop_is_limited():
    enricher = make_enricher(
        lambda request: httpx.Response(302, headers={"Location": "https://news.example.com/a"})
    )

    with pytest.raises(NewsEnrichmentError, match="too many redirects"):
        enricher.enrich("https://news.example.com/a", "cliente")


def test_http_error_message_is_safe():
    enricher = make_enricher(lambda request: httpx.Response(404))

    with pytest.raises(NewsEnrichmentError) as exc_info:
        enricher.enrich("https://news.example.com/a", "cliente")

    assert str(exc_info.value) == "page responded with HTTP 404"


def test_oversized_page_is_rejected(monkeypatch):
    monkeypatch.setattr(news_enrichment, "MAX_RESPONSE_BYTES", 10)
    enricher = make_enricher(lambda request: httpx.Response(200, content=b"x" * 11))

    with pytest.raises(NewsEnrichmentError, match="larger than the allowed limit"):
        enricher.enrich("https://news.example.com/a", "cliente")


def test_missing_openai_key_is_a_configuration_error():
    settings = Settings(_env_file=None, mcp_api_key="x" * 16, openai_api_key=None)

    with pytest.raises(ConfigurationError):
        OpenAINewsEnricher(settings)
