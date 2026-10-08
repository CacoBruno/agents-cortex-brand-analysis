from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

Tier = Literal["Tier 1", "Tier 2", "Tier 3", "Outros"]
Sentiment = Literal["Positivo", "Negativo", "Neutro"]
MentionOrigin = Literal["Espontânea", "Indeterminado", "Proativo", "Trabalhada"]


class ClassificationSelector(BaseModel):
    media_analysis_id: str | None = Field(default=None, min_length=1)
    original_url: str | None = None
    clipping_url: str | None = None
    title: str | None = None
    company: str | None = None
    product: str | None = None

    @model_validator(mode="after")
    def validate_selector(self) -> ClassificationSelector:
        if self.media_analysis_id:
            return self

        locator = self.original_url or self.clipping_url or self.title
        brand = self.company or self.product
        if not locator or not brand:
            raise ValueError(
                "selector requires media_analysis_id, or a locator "
                "(original_url/clipping_url/title) plus company/product"
            )
        return self


class ClassificationPatch(BaseModel):
    total_reach: int | None = Field(default=None, ge=0)
    tier: Tier | None = None
    sentiment: Sentiment | None = None
    protagonism: str | None = None
    topic: str | None = None
    specific_subject: str | None = None
    communication_action: str | None = None
    mention_origin: MentionOrigin | None = None
    journalist: str | None = None
    themes: str | None = None
    action_type: str | None = None

    @model_validator(mode="after")
    def require_change(self) -> ClassificationPatch:
        if not self.model_dump(exclude_none=True):
            raise ValueError("at least one classification field must be changed")
        return self


class ClassificationChange(BaseModel):
    selector: ClassificationSelector
    patch: ClassificationPatch


class ClassificationReviewRequest(BaseModel):
    platform_url: str
    changes: list[ClassificationChange] = Field(min_length=1)


class ClassificationRecord(BaseModel):
    media_analysis_id: str
    title: str | None = None
    source: str | None = None
    original_url: str | None = None
    clipping_url: str | None = None
    company: str | None = None
    product: str | None = None
    values: dict[str, object | None] = Field(default_factory=dict)


class ClassificationReviewItem(BaseModel):
    media_analysis_id: str
    title: str | None = None
    selector: ClassificationSelector
    before: dict[str, object | None]
    after: dict[str, object | None]
    changed_fields: list[str]


class ClassificationReviewPreview(BaseModel):
    matched: int
    unmatched_selectors: list[ClassificationSelector] = Field(default_factory=list)
    changes: list[ClassificationReviewItem] = Field(default_factory=list)


class ClassificationApplyRequest(ClassificationReviewRequest):
    confirm: Literal[True]


class ClassificationApplyResult(BaseModel):
    updated: int
    execution_ids: list[str] = Field(default_factory=list)
    preview: ClassificationReviewPreview
