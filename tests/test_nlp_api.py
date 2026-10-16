from cortex_brand_analysis.api.app import app, get_nlp_workflow
from cortex_brand_analysis.domain.nlp import NlpResult


class FakeNlpWorkflow:
    def run(self, request):
        return NlpResult(
            operation=request.operation,
            rows=1,
            columns=["titulo", "sentiment"],
            data=[{"titulo": "Teste", "sentiment": "Positivo"}],
            metadata={"runtime": "native", "model": "fake"},
        )


def test_nlp_endpoint_uses_native_contract(api_client):
    app.dependency_overrides[get_nlp_workflow] = lambda: FakeNlpWorkflow()

    response = api_client.post(
        "/v1/nlp/run",
        json={
            "operation": "sentiment",
            "data": [{"titulo": "Teste", "conteudo": "Conteúdo"}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["operation"] == "sentiment"
    assert body["metadata"]["runtime"] == "native"
    assert body["data"][0]["sentiment"] == "Positivo"
    assert response.headers["X-Run-ID"]
