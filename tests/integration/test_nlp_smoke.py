from __future__ import annotations

import os

import pytest

from cortex_brand_analysis.domain.nlp import NlpRequest
from cortex_brand_analysis.services.nlp_runtime import NativeNlpRuntime

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_NLP_SMOKE") != "1",
    reason="set RUN_NLP_SMOKE=1 to execute real native NLP models",
)


def test_real_sentiment_smoke():
    result = NativeNlpRuntime().run(
        NlpRequest(
            operation="sentiment",
            data=[
                {
                    "titulo": "Banco anuncia novas condições de crédito",
                    "conteudo": "A instituição reduziu taxas e ampliou opções de financiamento.",
                }
            ],
        )
    )

    assert result.rows == 1
    assert "Sentimento" in result.columns
    assert result.metadata["runtime"] == "native"
    assert result.metadata["model"] == "CortexLexicon"


def test_real_entities_smoke():
    result = NativeNlpRuntime().run(
        NlpRequest(
            operation="entities",
            data=[
                {
                    "titulo": "Banco Central anuncia novas regras",
                    "conteudo": "A Febraban e o Itaú comentaram as medidas.",
                }
            ],
            entity_search={
                "Banco Central": ["Banco Central", "BC", "BCB"],
                "Febraban": ["Febraban", "Federação Brasileira de Bancos"],
                "Itaú": ["Itaú", "Itaú Unibanco"],
            },
        )
    )

    assert result.rows >= 1
    assert "entidade_encontrada" in result.columns
    assert result.metadata["runtime"] == "native"
