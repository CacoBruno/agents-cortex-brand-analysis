import pytest
from fastapi.testclient import TestClient

from cortex_brand_analysis.api import app as app_module
from cortex_brand_analysis.config import get_settings
from cortex_brand_analysis.services.audit_store import JsonlAuditStore

API_KEY = "test-api-key-1234567890"


@pytest.fixture
def api_client(monkeypatch, tmp_path):
    """TestClient isolated from the developer's .env, credentials and .data/ directory."""
    monkeypatch.chdir(tmp_path)
    for name in ("PLATFORM_LOGIN", "PLATFORM_PASSWORD", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("MCP_API_KEY", API_KEY)
    get_settings.cache_clear()
    monkeypatch.setattr(app_module, "audit_store", JsonlAuditStore(tmp_path / "runs.jsonl"))

    with TestClient(app_module.app, raise_server_exceptions=False) as client:
        client.headers["X-API-Key"] = API_KEY
        yield client

    app_module.app.dependency_overrides.clear()
    get_settings.cache_clear()
