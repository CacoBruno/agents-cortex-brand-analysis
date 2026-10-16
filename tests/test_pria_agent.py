from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from cortex_brand_analysis.agents import pria as pria_module
from cortex_brand_analysis.agents.pria import PriaAgent
from cortex_brand_analysis.config import Settings
from cortex_brand_analysis.domain.agent import PriaRequest


class FakeResponses:
    def __init__(self, responses: list[Any]) -> None:
        self.items = responses
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.items.pop(0)


class FakeClient:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = FakeResponses(responses)


def _settings() -> Settings:
    return Settings(MCP_API_KEY="test-api-key-1234567890", OPENAI_API_KEY="test")


def test_pria_returns_direct_answer_without_tool_call():
    response = SimpleNamespace(
        id="resp_1",
        output=[],
        output_text="Olá, sou a PRIA.",
    )
    client = FakeClient([response])

    result = PriaAgent(_settings(), client=client).run(PriaRequest(message="Olá"))

    assert result.answer == "Olá, sou a PRIA."
    assert result.response_id == "resp_1"
    assert result.tool_calls == []


def test_pria_executes_typed_tool_and_continues_response(monkeypatch):
    function_call = SimpleNamespace(
        type="function_call",
        name="analytics_run",
        arguments=json.dumps(
            {
                "operation": "value_counts",
                "data": [{"tema": "Crédito"}],
                "columns": ["tema"],
            }
        ),
        call_id="call_1",
    )
    first = SimpleNamespace(id="resp_1", output=[function_call], output_text="")
    second = SimpleNamespace(
        id="resp_2",
        output=[],
        output_text="Crédito aparece uma vez.",
    )
    client = FakeClient([first, second])

    monkeypatch.setattr(
        pria_module,
        "_dispatch_tool",
        lambda name, arguments: {
            "operation": name,
            "rows": 1,
            "data": [{"tema": "Crédito", "count": 1}],
        },
    )

    result = PriaAgent(_settings(), client=client).run(
        PriaRequest(message="Conte os temas")
    )

    assert result.answer == "Crédito aparece uma vez."
    assert result.response_id == "resp_2"
    assert result.tool_calls == ["analytics_run"]
    continuation = client.responses.calls[1]
    assert continuation["previous_response_id"] == "resp_1"
    assert continuation["input"][0]["type"] == "function_call_output"
