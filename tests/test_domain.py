import pytest
from pydantic import ValidationError

from cortex_brand_analysis.domain.models import NewsCheckRequest


def test_platform_url_is_normalized() -> None:
    request = NewsCheckRequest(
        platform_url="cliente.cortex-intelligence.com/",
        original_urls=[" https://example.com/a ", "https://example.com/a"],
    )
    assert request.platform_url == "https://cliente.cortex-intelligence.com"
    assert request.original_urls == ["https://example.com/a"]


def test_empty_platform_url_is_rejected() -> None:
    with pytest.raises(ValidationError):
        NewsCheckRequest(platform_url="   ")
