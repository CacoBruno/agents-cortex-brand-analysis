import pytest
from pydantic import ValidationError

from cortex_brand_analysis.domain.nlp import NlpRequest


def test_protagonism_requires_brand():
    with pytest.raises(ValidationError):
        NlpRequest(
            operation="protagonism",
            data=[{"titulo": "x", "conteudo": "y"}],
        )


def test_entities_requires_dictionary():
    with pytest.raises(ValidationError):
        NlpRequest(
            operation="entities",
            data=[{"titulo": "x", "conteudo": "y"}],
        )


def test_themes_requires_definitions():
    with pytest.raises(ValidationError):
        NlpRequest(
            operation="themes",
            data=[{"titulo": "x", "conteudo": "y"}],
        )


def test_sentiment_request_is_native_contract():
    request = NlpRequest(
        operation="sentiment",
        data=[{"titulo": "x", "conteudo": "y"}],
    )
    assert request.operation == "sentiment"
