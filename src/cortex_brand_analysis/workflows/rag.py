from __future__ import annotations

from cortex_brand_analysis.domain.rag import (
    KnowledgeBuildResult,
    KnowledgeDocument,
    RagAnswer,
    RagQueryRequest,
)
from cortex_brand_analysis.services.knowledge_index import (
    JsonlKnowledgeIndex,
    build_chunks,
    rank_chunks,
)


class RagServiceProtocol:
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def answer(self, question: str, sources): ...


class KnowledgeRagWorkflow:
    def __init__(
        self,
        index: JsonlKnowledgeIndex,
        rag_service: RagServiceProtocol,
    ) -> None:
        self.index = index
        self.rag_service = rag_service

    def build(self, documents: list[KnowledgeDocument]) -> KnowledgeBuildResult:
        chunks = build_chunks(documents)
        embeddings = self.rag_service.embed([chunk.text for chunk in chunks])
        self.index.save(chunks, embeddings)
        return KnowledgeBuildResult(
            documents=len(documents),
            chunks=len(chunks),
            index_path=str(self.index.index_path),
        )

    def query(self, request: RagQueryRequest) -> RagAnswer:
        rows = self.index.load()
        if not rows:
            return RagAnswer(
                answer="A base de conhecimento ainda não foi construída.",
                sources=[],
            )
        query_embedding = self.rag_service.embed([request.question])[0]
        sources = rank_chunks(rows, query_embedding, request.top_k)
        return self.rag_service.answer(request.question, sources)
