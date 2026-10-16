from __future__ import annotations

from cortex_brand_analysis.domain.nlp import NlpRequest, NlpResult
from cortex_brand_analysis.mcp.tools import run_nlp


class FakeWorkflow:
    def run(self, request: NlpRequest) -> NlpResult:
        return NlpResult(
            operation=request.operation,
            rows=1,
            columns=["sentiment"],
            data=[{"sentiment": "Positivo"}],
            metadata={"runtime": "native", "model": "fake"},
        )


def test_native_mcp_nlp_tool_calls_typed_workflow():
    payload = run_nlp(
        NlpRequest(
            operation="sentiment",
            data=[{"titulo": "Teste", "conteudo": "Crédito melhor"}],
        ),
        workflow=FakeWorkflow(),
    )

    assert payload["operation"] == "sentiment"
    assert payload["metadata"]["runtime"] == "native"
    assert payload["data"][0]["sentiment"] == "Positivo"
