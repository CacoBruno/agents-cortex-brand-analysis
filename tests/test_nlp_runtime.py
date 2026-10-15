from __future__ import annotations

from typing import Any

import pandas as pd

from cortex_brand_analysis.domain.nlp import NlpRequest
from cortex_brand_analysis.services.nlp_runtime import NativeNlpRuntime


def test_native_runtime_dispatches_and_serializes(monkeypatch):
    runtime = NativeNlpRuntime()

    def fake_sentiment(
        df: pd.DataFrame, request: NlpRequest
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        out = df.copy()
        out["score"] = 1.0
        return out, {"model": "fake-sentiment"}

    monkeypatch.setattr(runtime, "_run_sentiment", fake_sentiment)

    result = runtime.run(
        NlpRequest(
            operation="sentiment",
            data=[{"titulo": "Teste", "conteudo": "Conteúdo"}],
        )
    )

    assert result.operation == "sentiment"
    assert result.rows == 1
    assert "score" in result.columns
    assert result.data[0]["score"] == 1.0
    assert result.metadata == {"runtime": "native", "model": "fake-sentiment"}


def test_native_runtime_records_are_json_safe(monkeypatch):
    runtime = NativeNlpRuntime()

    def fake_sentiment(
        df: pd.DataFrame, request: NlpRequest
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        out = pd.DataFrame(
            [
                {
                    "titulo": "Teste",
                    "missing": None,
                    "date": pd.Timestamp("2026-10-15"),
                }
            ]
        )
        return out, {"model": "fake-sentiment"}

    monkeypatch.setattr(runtime, "_run_sentiment", fake_sentiment)

    result = runtime.run(
        NlpRequest(
            operation="sentiment",
            data=[{"titulo": "Teste", "conteudo": "Conteúdo"}],
        )
    )

    row: dict[str, Any] = result.data[0]
    assert row["missing"] is None
    assert isinstance(row["date"], str)
