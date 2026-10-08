import httpx
import pytest

from cortex_brand_analysis.api.app import app, get_news_workflow
from cortex_brand_analysis.services.cortex_http import CortexError

NEWS_CHECK = {
    "platform_url": "cliente.cortex-intelligence.com",
    "original_urls": ["https://example.com/noticia"],
}


class FailingWorkflow:
    def __init__(self, exc):
        self.exc = exc

    def run(self, request):
        raise self.exc


def test_health_returns_run_id(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Run-ID"]


def test_invalid_api_key_is_rejected(api_client):
    response = api_client.post(
        "/v1/news/check",
        json=NEWS_CHECK,
        headers={"X-API-Key": "wrong-key-wrong-key"},
    )

    assert response.status_code == 401


def test_domain_error_returns_422_with_message(api_client):
    response = api_client.post(
        "/v1/analytics/run",
        json={"data": [{"a": 1}], "operation": "correlation", "columns": ["a", "missing"]},
    )

    assert response.status_code == 422
    assert "unknown columns" in response.json()["detail"]


def test_metric_without_aggregation_returns_422(api_client):
    response = api_client.post(
        "/v1/analytics/run",
        json={"data": [{"a": 1}], "operation": "groupby", "group_by": ["a"], "metric": "a"},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "exc",
    [
        CortexError("token expired for user 42"),
        httpx.ConnectError("connection refused"),
    ],
)
def test_upstream_failures_return_502_without_details(api_client, exc):
    app.dependency_overrides[get_news_workflow] = lambda: FailingWorkflow(exc)

    response = api_client.post("/v1/news/check", json=NEWS_CHECK)

    assert response.status_code == 502
    assert response.json() == {"detail": "Upstream operation failed"}


def test_missing_platform_credentials_return_503(api_client):
    response = api_client.post("/v1/news/check", json=NEWS_CHECK)

    assert response.status_code == 503
    assert "PLATFORM_LOGIN" not in response.text


def test_missing_openai_key_returns_503(api_client):
    response = api_client.post("/v1/rag/query", json={"question": "O que é o Cortex PR?"})

    assert response.status_code == 503


def test_requests_are_recorded_in_audit_trail(api_client):
    first = api_client.get("/health")

    runs = api_client.get("/v1/audit/runs").json()["runs"]

    assert runs[0]["run_id"] == first.headers["X-Run-ID"]
    assert runs[0]["operation"] == "GET /health"
    assert runs[0]["status"] == "success"
