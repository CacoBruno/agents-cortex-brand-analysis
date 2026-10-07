from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from cortex_brand_analysis.domain.rag import (
    KnowledgeBuildResult,
    KnowledgeChunk,
    KnowledgeDocument,
    RetrievedChunk,
)


def chunk_text(text: str, size: int = 1200, overlap: int = 200) -> list[str]:
    clean = " ".join(text.split())
    if not clean:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + size)
        chunks.append(clean[start:end])
        if end == len(clean):
            break
        start = max(start + 1, end - overlap)
    return chunks


def make_chunk_id(document_id: str, index: int, text: str) -> str:
    raw = f"{document_id}|{index}|{text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class JsonlKnowledgeIndex:
    """Safe, reproducible local index metadata store.

    No pickle/deserialization is used. Embeddings are stored as JSON arrays.
    """

    def __init__(self, index_path: str | Path) -> None:
        self.index_path = Path(index_path)

    def save(self, chunks: list[KnowledgeChunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with self.index_path.open("w", encoding="utf-8") as handle:
            for chunk, vector in zip(chunks, embeddings, strict=True):
                payload = {
                    "chunk": chunk.model_dump(),
                    "embedding": vector,
                }
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def load(self) -> list[tuple[KnowledgeChunk, list[float]]]:
        if not self.index_path.exists():
            return []
        rows = []
        with self.index_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                rows.append(
                    (
                        KnowledgeChunk.model_validate(payload["chunk"]),
                        [float(value) for value in payload["embedding"]],
                    )
                )
        return rows


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_chunks(documents: list[KnowledgeDocument]) -> list[KnowledgeChunk]:
    result: list[KnowledgeChunk] = []
    for document in documents:
        for index, text in enumerate(chunk_text(document.text)):
            result.append(
                KnowledgeChunk(
                    chunk_id=make_chunk_id(document.document_id, index, text),
                    document_id=document.document_id,
                    source=document.source,
                    title=document.title,
                    text=text,
                    version=document.version,
                    updated_at=document.updated_at,
                )
            )
    return result


def rank_chunks(
    rows: list[tuple[KnowledgeChunk, list[float]]],
    query_embedding: list[float],
    top_k: int,
) -> list[RetrievedChunk]:
    ranked = sorted(
        (
            RetrievedChunk(
                **chunk.model_dump(),
                score=cosine_similarity(vector, query_embedding),
            )
            for chunk, vector in rows
        ),
        key=lambda item: item.score,
        reverse=True,
    )
    return ranked[:top_k]
