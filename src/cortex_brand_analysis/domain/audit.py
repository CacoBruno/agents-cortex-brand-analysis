from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RunStatus = Literal["running", "success", "error"]


class AuditRun(BaseModel):
    run_id: str
    operation: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    status: RunStatus = "running"
    writes_external_state: bool = False
    input_summary: dict[str, object] = Field(default_factory=dict)
    result_summary: dict[str, object] = Field(default_factory=dict)
    error_type: str | None = None
    error_message: str | None = None


class AuditRunList(BaseModel):
    runs: list[AuditRun] = Field(default_factory=list)
