from __future__ import annotations

import ipaddress
import json
import socket
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup

from cortex_brand_analysis.config import Settings
from cortex_brand_analysis.domain.errors import ConfigurationError, NewsEnrichmentError
from cortex_brand_analysis.domain.news_ingestion import EnrichedNews, news_idempotency_key

__all__ = ["NewsEnrichmentError", "OpenAINewsEnricher"]

MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
USER_AGENT = "Mozilla/5.0 CortexBrandAnalysis/1.0"


def _ensure_public_url(url: str) -> None:
    """Reject URLs that are not http(s) or that resolve to non-public addresses.

    Known limitation: the host is resolved again when httpx connects, so a DNS
    rebinding attack between this check and the connection is still possible.
    """
    parts = urlparse(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise NewsEnrichmentError("URL blocked: only http and https URLs are allowed")

    try:
        port = parts.port or (443 if parts.scheme == "https" else 80)
        infos = socket.getaddrinfo(parts.hostname, port, type=socket.SOCK_STREAM)
    except (OSError, UnicodeError, ValueError) as exc:
        raise NewsEnrichmentError("could not resolve the URL host") from exc

    for info in infos:
        address = ipaddress.ip_address(str(info[4][0]).split("%", 1)[0])
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        if not address.is_global or address.is_multicast:
            raise NewsEnrichmentError("URL blocked: host resolves to a non-public address")


class OpenAINewsEnricher:
    """Fetch a news page and use OpenAI structured output to extract metadata.

    Every failure is raised as NewsEnrichmentError with a message that is safe
    to return to API clients; upstream details stay in the exception chain.
    """

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        if not settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for news enrichment")
        self.settings = settings
        self.client = client or httpx.Client(
            timeout=settings.http_timeout_seconds,
            follow_redirects=False,
        )

    def _fetch(self, url: str) -> tuple[str, bytes, str | None]:
        """Download a page following redirects manually, validating every hop."""
        current = url
        for _ in range(MAX_REDIRECTS + 1):
            _ensure_public_url(current)
            try:
                with self.client.stream(
                    "GET",
                    current,
                    headers={"User-Agent": USER_AGENT},
                    follow_redirects=False,
                ) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise NewsEnrichmentError("redirect without a Location header")
                        current = str(response.url.join(location))
                        continue

                    response.raise_for_status()
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_RESPONSE_BYTES:
                            raise NewsEnrichmentError("page is larger than the allowed limit")
                    return str(response.url), bytes(body), response.charset_encoding
            except httpx.HTTPStatusError as exc:
                raise NewsEnrichmentError(
                    f"page responded with HTTP {exc.response.status_code}"
                ) from exc
            except httpx.TimeoutException as exc:
                raise NewsEnrichmentError("timed out while downloading the page") from exc
            except httpx.HTTPError as exc:
                raise NewsEnrichmentError("connection error while downloading the page") from exc

        raise NewsEnrichmentError("too many redirects")

    def enrich(self, url: str, client_name: str) -> EnrichedNews:
        final_url, body, charset = self._fetch(url)

        soup = BeautifulSoup(body, "html.parser", from_encoding=charset)
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(soup.stripped_strings)
        if not text:
            raise NewsEnrichmentError("page did not contain readable text")

        try:
            from openai import OpenAI, OpenAIError
        except ImportError as exc:
            raise ConfigurationError(
                "install the project with the 'ai' extra to enable enrichment"
            ) from exc

        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "outlet": {"type": "string"},
                "city": {"type": ["string", "null"]},
                "state": {"type": ["string", "null"]},
                "author": {"type": ["string", "null"]},
                "content": {"type": "string"},
                "publication_date": {"type": ["string", "null"]},
            },
            "required": [
                "title",
                "outlet",
                "city",
                "state",
                "author",
                "content",
                "publication_date",
            ],
            "additionalProperties": False,
        }

        ai = OpenAI(api_key=self.settings.openai_api_key)
        try:
            result = ai.responses.create(
                model="gpt-6-luna",
                input=[
                    {
                        "role": "system",
                        "content": (
                            "Extraia os metadados da publicação jornalística. "
                            "Preserve o conteúdo factual e não invente informações."
                        ),
                    },
                    {"role": "user", "content": text[:120000]},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "news_metadata",
                        "strict": True,
                        "schema": schema,
                    }
                },
            )
        except OpenAIError as exc:
            raise NewsEnrichmentError("metadata extraction with the model failed") from exc

        try:
            data = json.loads(result.output_text)
            captured_at = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
            domain = urlparse(final_url).hostname or urlparse(url).hostname or ""

            return EnrichedNews(
                idempotency_key=news_idempotency_key(client_name, url),
                url=url,
                title=data["title"],
                outlet=data["outlet"],
                domain=domain.removeprefix("www."),
                city=data["city"],
                state=data["state"],
                author=data["author"],
                content=data["content"],
                publication_date=data["publication_date"],
                captured_at=captured_at,
            )
        except (ValueError, KeyError, TypeError) as exc:
            raise NewsEnrichmentError("model returned metadata in an unexpected format") from exc
