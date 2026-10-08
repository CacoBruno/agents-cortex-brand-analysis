from pathlib import Path

from cortex_brand_analysis.domain.rag import KnowledgeDocument, RagQueryRequest
from cortex_brand_analysis.services.knowledge_index import JsonlKnowledgeIndex
from cortex_brand_analysis.workflows.rag import KnowledgeRagWorkflow


class FakeRagService:
    def embed(self, texts):
        vectors = []
        for text in texts:
            vectors.append(
                [
                    float("reputação" in text.lower()),
                    float("alcance" in text.lower()),
                    float(len(text) % 7),
                ]
            )
        return vectors

    def answer(self, question, sources):
        from cortex_brand_analysis.domain.rag import RagAnswer

        return RagAnswer(answer=f"Resposta: {question}", sources=sources)


def test_build_and_query_use_safe_jsonl_index(tmp_path: Path):
    index = JsonlKnowledgeIndex(tmp_path / "knowledge.jsonl")
    workflow = KnowledgeRagWorkflow(index, FakeRagService())

    build = workflow.build(
        [
            KnowledgeDocument(
                document_id="metodologia-1",
                source="manual.md",
                title="Metodologia",
                text="O cálculo de reputação combina indicadores definidos pela metodologia.",
            )
        ]
    )

    assert build.documents == 1
    assert build.chunks == 1
    assert index.index_path.read_text(encoding="utf-8").startswith("{")

    answer = workflow.query(RagQueryRequest(question="Como funciona reputação?"))
    assert answer.sources
    assert answer.sources[0].document_id == "metodologia-1"
    assert answer.sources[0].source == "manual.md"
