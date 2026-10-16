from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, HttpUrl, model_validator


class EvidenceDocument(BaseModel):
    document_id: str = Field(min_length=1)
    publication_date: date
    title: str = Field(min_length=1)
    source: str = Field(min_length=1)
    url: HttpUrl
    reach: float | None = Field(default=None, ge=0)
    tier: str | None = None
    document_score: float | None = None
    company: str | None = None
    topic: str | None = None


class EvidenceSelection(BaseModel):
    method_id: str
    method_version: str
    dataset_id: str = Field(min_length=1)
    selection_dimension: str
    selection_value: str
    document_ids: list[str] = Field(default_factory=list)
    documents: list[EvidenceDocument] = Field(default_factory=list)
    selection_reason: str
    eligible_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_document_ids(self) -> EvidenceSelection:
        actual_ids = [document.document_id for document in self.documents]
        if self.document_ids != actual_ids:
            raise ValueError("document_ids must match the ordered documents")
        if len(actual_ids) != len(set(actual_ids)):
            raise ValueError("duplicate document IDs in evidence selection")
        if self.eligible_count < len(actual_ids):
            raise ValueError("eligible_count cannot be less than selected documents")
        return self


class EvidenceResult(BaseModel):
    dataset_id: str
    method_version: str = "1.0.0"
    selections: list[EvidenceSelection] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
