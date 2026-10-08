from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    document_id: str
    source: str
    title: str | None = None
    text: str
    version: str | None = None
    updated_at: str | None = None


class KnowledgeChunk(BaseModel):
    chunk_id: str
    document_id: str
    source: str
    title: str | None = None
    text: str
    version: str | None = None
    updated_at: str | None = None


class RetrievedChunk(KnowledgeChunk):
    score: float


class RagQueryRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)


class RagAnswer(BaseModel):
    answer: str
    sources: list[RetrievedChunk] = Field(default_factory=list)


class KnowledgeBuildResult(BaseModel):
    documents: int
    chunks: int
    index_path: str
