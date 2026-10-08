from __future__ import annotations

from cortex_brand_analysis.domain.classification import (
    ClassificationApplyRequest,
    ClassificationApplyResult,
    ClassificationChange,
    ClassificationRecord,
    ClassificationReviewItem,
    ClassificationReviewPreview,
    ClassificationReviewRequest,
)
from cortex_brand_analysis.services.protocols import CortexGateway

PATCH_TO_CORTEX = {
    "total_reach": "Alcance total",
    "tier": "Tier",
    "sentiment": "Sentimento",
    "protagonism": "Nível de Protagonismo",
    "topic": "Tópicos",
    "specific_subject": "Assunto específico",
    "communication_action": "Ação",
    "mention_origin": "Origem da menção",
    "journalist": "Jornalista",
    "themes": "Temas",
    "action_type": "Tipo da ação",
}


def _matches(record: ClassificationRecord, change: ClassificationChange) -> bool:
    selector = change.selector
    if selector.media_analysis_id:
        return record.media_analysis_id == selector.media_analysis_id

    checks = [
        (selector.original_url, record.original_url),
        (selector.clipping_url, record.clipping_url),
        (selector.title, record.title),
        (selector.company, record.company),
        (selector.product, record.product),
    ]
    return all(expected is None or expected == actual for expected, actual in checks)


def _build_after(
    record: ClassificationRecord,
    change: ClassificationChange,
) -> tuple[dict[str, object | None], list[str]]:
    before = dict(record.values)
    after = dict(before)
    changed: list[str] = []

    for patch_name, value in change.patch.model_dump(exclude_none=True).items():
        cortex_name = PATCH_TO_CORTEX[patch_name]
        if after.get(cortex_name) != value:
            after[cortex_name] = value
            changed.append(cortex_name)

    return after, changed


class ClassificationReviewWorkflow:
    def __init__(self, cortex: CortexGateway) -> None:
        self.cortex = cortex

    def preview(self, request: ClassificationReviewRequest) -> ClassificationReviewPreview:
        selectors = [change.selector for change in request.changes]
        records = self.cortex.find_classifications(request.platform_url, selectors)

        items: list[ClassificationReviewItem] = []
        unmatched = []

        for change in request.changes:
            matched_records = [record for record in records if _matches(record, change)]
            if not matched_records:
                unmatched.append(change.selector)
                continue

            for record in matched_records:
                after, changed_fields = _build_after(record, change)
                if not changed_fields:
                    continue
                items.append(
                    ClassificationReviewItem(
                        media_analysis_id=record.media_analysis_id,
                        title=record.title,
                        selector=change.selector,
                        before=dict(record.values),
                        after=after,
                        changed_fields=changed_fields,
                    )
                )

        return ClassificationReviewPreview(
            matched=len(items),
            unmatched_selectors=unmatched,
            changes=items,
        )

    def apply(self, request: ClassificationApplyRequest) -> ClassificationApplyResult:
        preview = self.preview(request)
        if not preview.changes:
            return ClassificationApplyResult(updated=0, preview=preview)

        rows = [
            {"Chave Análise de Mídia Hash": item.media_analysis_id, **item.after}
            for item in preview.changes
        ]
        execution_ids = self.cortex.upload_classification_changes(
            request.platform_url,
            rows,
        )
        return ClassificationApplyResult(
            updated=len(rows),
            execution_ids=execution_ids,
            preview=preview,
        )
