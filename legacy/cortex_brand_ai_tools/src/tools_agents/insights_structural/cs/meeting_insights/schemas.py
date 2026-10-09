from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MeetingScriptToolInput(BaseModel):
    company_name: str = Field(...)
    analysis_period: str = Field(...)

    big_number: Dict[str, Any] = Field(default_factory=dict)
    highlight_infos: Dict[str, Any] = Field(default_factory=dict)
    coverage_context_result: Dict[str, Any] = Field(default_factory=dict)
    insights: Dict[str, Any] = Field(default_factory=dict)
    contexto_negocios: Dict[str, Any] = Field(default_factory=dict)

    model: str = "gpt-4.1-mini"
    temperature: float = 0.2
    max_retries: int = 3


class SaveMeetingScriptToolInput(MeetingScriptToolInput):
    output_dir: str = "."
    base_filename: str = "script_reuniao_insights"


class ToolErrorOutput(BaseModel):
    status: str = "error"
    message: str
    error_type: Optional[str] = None
    details: Optional[str] = None