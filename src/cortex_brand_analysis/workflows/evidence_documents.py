from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Literal

from cortex_brand_analysis.domain.evidence import (
    EvidenceDocument,
    EvidenceResult,
    EvidenceSelection,
)
from cortex_brand_analysis.domain.errors import DomainError

EvidenceDimension = Literal["day", "source", "topic"]


def _tier_rank(value: str | None) -> int:
    if value is None:
        return 999
    text = value.strip().lower()
    for number in range(1, 5):
        if f"tier {number}" in text or text in (str(number), f"t{number}"):
            return number
    return 999


def _ranking_key(document: EvidenceDocument) -> tuple[float, int, float, str]:
    return (
        -(document.reach or 0),
        _tier_rank(document.tier),
        -(document.document_score or 0),
        document.document_id,
    )


class EvidenceDocumentSelectorV1:
    """Selects auditable original publications from an authorized dataset."""

    def select(
        self,
        *,
        dataset_id: str,
        documents: Sequence[EvidenceDocument],
        dimension: EvidenceDimension,
        values: Sequence[str],
        top_n_per_value: int = 8,
        company: str | None = None,
    ) -> EvidenceResult:
        if not dataset_id.strip():
            raise DomainError("dataset_id is required")
        if not 1 <= top_n_per_value <= 100:
            raise DomainError("top_n_per_value must be between 1 and 100")
        if len(values) > 100 or len(set(values)) != len(values):
            raise DomainError("selection values must be unique and limited to 100")
        if dimension == "day":
            for value in values:
                try:
                    if date.fromisoformat(value).isoformat() != value:
                        raise ValueError("not canonical ISO date")
                except ValueError as exc:
                    raise DomainError("day selection requires ISO dates") from exc
        selections = []
        for value in values:
            eligible = [
                document
                for document in documents
                if (company is None or document.company == company)
                and (
                    (dimension == "day" and document.publication_date.isoformat() == value)
                    or (dimension == "source" and document.source == value)
                    or (dimension == "topic" and document.topic == value)
                )
            ]
            # An analyzed publication should not be duplicated in one selection.
            selected = []
            seen: set[str] = set()
            for document in sorted(eligible, key=_ranking_key):
                if document.document_id not in seen:
                    selected.append(document)
                    seen.add(document.document_id)
                if len(selected) >= top_n_per_value:
                    break
            selections.append(
                EvidenceSelection(
                    method_id="news_evidence_document_ranking",
                    method_version="1.0.0",
                    dataset_id=dataset_id,
                    selection_dimension=dimension,
                    selection_value=value,
                    document_ids=[document.document_id for document in selected],
                    documents=selected,
                    selection_reason=(
                        "Legacy order: reach descending, Tier priority ascending, "
                        "document score descending; document ID breaks final ties."
                    ),
                    eligible_count=len(eligible),
                )
            )
        return EvidenceResult(dataset_id=dataset_id, selections=selections)
