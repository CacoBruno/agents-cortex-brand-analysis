from __future__ import annotations

import sys
from types import ModuleType

import pandas as pd

from cortex_brand_analysis.domain.nlp import NlpRequest
from cortex_brand_analysis.services.nlp_runtime import NativeNlpRuntime


def _install_module(monkeypatch, name: str, **attrs: object) -> None:
    module = ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    monkeypatch.setitem(sys.modules, name, module)


def test_sentiment_operation_with_stubbed_model(monkeypatch):
    class FakeLexicon:
        def __init__(self, extra_terms):
            self.extra_terms = extra_terms

        def __call__(self, text):
            return (0.1, 0.9)

    _install_module(
        monkeypatch,
        "cortex_brand_analysis.nlp.models.sentiment_analysis.CortexLexicon",
        CortexLexicon=FakeLexicon,
    )
    _install_module(
        monkeypatch,
        "cortex_brand_analysis.nlp.models.text_treatment.text_processing",
        clean_text=lambda text, language, cleaning_tasks: text.lower(),
    )

    result = NativeNlpRuntime().run(
        NlpRequest(
            operation="sentiment",
            data=[{"titulo": "Bom", "conteudo": "Crédito melhor"}],
        )
    )

    assert result.data[0]["Sentimento"] == "Positivo"
    assert result.metadata["model"] == "CortexLexicon"


def test_protagonism_operation_with_stubbed_model(monkeypatch):
    class FakeProtagonism:
        def __init__(self, brands, ignored):
            self.brands = brands

        def run_protagonism(self, primary, title, content):
            return "A"

    _install_module(
        monkeypatch,
        "cortex_brand_analysis.nlp.models.protagonism.Protagonism",
        Protagonism=FakeProtagonism,
    )

    result = NativeNlpRuntime().run(
        NlpRequest(
            operation="protagonism",
            data=[{"titulo": "Itaú anuncia crédito", "conteudo": "Itaú amplia oferta"}],
            brands=["Itaú", "Itaú Unibanco"],
        )
    )

    assert result.data[0]["Nível de Protagonismo final"] == "Protagonismo"
    assert result.metadata["model"] == "CortexProtagonism"


def test_entities_operation_with_stubbed_matcher(monkeypatch):
    def fake_entities(**kwargs):
        out = kwargs["df"].copy()
        out["entidade_encontrada"] = "Itaú"
        return out

    _install_module(
        monkeypatch,
        "cortex_brand_analysis.nlp.models.entities",
        identify_entities_in_dataframe=fake_entities,
    )

    result = NativeNlpRuntime().run(
        NlpRequest(
            operation="entities",
            data=[{"titulo": "Itaú", "conteudo": "Banco"}],
            entity_search={"Itaú": ["Itaú"]},
        )
    )

    assert result.data[0]["entidade_encontrada"] == "Itaú"
    assert result.metadata["model"] == "deterministic_entity_matcher"


def test_clustering_operation_with_stubbed_clusterer(monkeypatch):
    def fake_clusterer(**kwargs):
        out = kwargs["df"].copy()
        out["cluster_id"] = 1
        return out

    _install_module(
        monkeypatch,
        "cortex_brand_analysis.nlp.models.clustering",
        daily_cluster_similaridade_parallel=fake_clusterer,
    )

    result = NativeNlpRuntime().run(
        NlpRequest(
            operation="clustering",
            data=[
                {
                    "data_da_publicacao": "2026-10-15",
                    "titulo": "Crédito",
                    "conteudo": "Notícia sobre crédito",
                }
            ],
        )
    )

    assert result.data[0]["cluster_id"] == 1
    assert result.metadata["model"] == "all-MiniLM-L6-v2"


def test_themes_operation_with_stubbed_classifier(monkeypatch):
    class FakeSchema:
        def __init__(self, **kwargs):
            self.embedding_model_name = kwargs.get("embedding_model_name", "fake-embedding")
            for key, value in kwargs.items():
                setattr(self, key, value)

    class FakeClassifier:
        def __init__(self, macrotemas, rules, config):
            self.config = config

        def predict_dataframe(self, df, **kwargs):
            out = df.copy()
            out["tema"] = "Crédito"
            return out

    _install_module(
        monkeypatch,
        "cortex_brand_analysis.nlp.models.themes.schemas",
        ThemeClassifierConfigSchema=FakeSchema,
        ThemeDefinitionSchema=FakeSchema,
        ThemeRuleSchema=FakeSchema,
    )
    _install_module(
        monkeypatch,
        "cortex_brand_analysis.nlp.models.themes.service",
        ThemeClassifierService=FakeClassifier,
    )

    result = NativeNlpRuntime().run(
        NlpRequest(
            operation="themes",
            data=[{"titulo": "Crédito", "conteudo": "Oferta de crédito"}],
            macrothemes={"Crédito": {"descricao": "Tema de crédito"}},
            theme_rules={"Crédito": {"include": ["crédito"]}},
            theme_config={"embedding_model_name": "fake-embedding"},
        )
    )

    assert result.data[0]["tema"] == "Crédito"
    assert result.metadata["model"] == "fake-embedding"


def test_clustering_rejects_invalid_dates(monkeypatch):
    _install_module(
        monkeypatch,
        "cortex_brand_analysis.nlp.models.clustering",
        daily_cluster_similaridade_parallel=lambda **kwargs: pd.DataFrame(),
    )

    request = NlpRequest(
        operation="clustering",
        data=[{"data_da_publicacao": "not-a-date", "titulo": "x", "conteudo": "y"}],
    )

    try:
        NativeNlpRuntime().run(request)
    except ValueError as exc:
        assert "no valid dates" in str(exc)
    else:
        raise AssertionError("expected ValueError")
