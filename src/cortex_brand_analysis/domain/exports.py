from __future__ import annotations

from datetime import date, timedelta

from pydantic import BaseModel, Field, model_validator


class DateRange(BaseModel):
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def normalize_dates(self) -> DateRange:
        today = date.today()
        if self.start_date is None:
            self.start_date = today - timedelta(days=7)
        if self.end_date is None:
            self.end_date = today
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date")
        return self


class PublicationExportRequest(DateRange):
    platform_url: str
    companies: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    media: list[str] = Field(default_factory=list)
    tiers: list[str] = Field(default_factory=lambda: ["Tier 1", "Tier 2", "Outros"])
    states: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_brand(self) -> PublicationExportRequest:
        if not self.companies and not self.products:
            raise ValueError("at least one company or product is required")
        return self


class MediaAnalysisExportRequest(DateRange):
    platform_url: str
    companies: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    media: list[str] = Field(default_factory=list)
    tiers: list[str] = Field(default_factory=lambda: ["Tier 1", "Tier 2", "Outros"])
    states: list[str] = Field(default_factory=list)
    impact_types: list[str] = Field(default_factory=list)
    sentiments: list[str] = Field(default_factory=list)
    protagonism: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    specific_subjects: list[str] = Field(default_factory=list)
    communication_actions: list[str] = Field(default_factory=list)
    mention_origins: list[str] = Field(default_factory=list)
    journalists: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    macro_subjects: list[str] = Field(default_factory=list)
    classification_status: list[str] = Field(
        default_factory=lambda: ["Classificado", "Pendente"]
    )

    @model_validator(mode="after")
    def require_brand(self) -> MediaAnalysisExportRequest:
        if not self.companies and not self.products:
            raise ValueError("at least one company or product is required")
        return self


class ExportResult(BaseModel):
    rows: int
    columns: list[str]
    data: list[dict]
