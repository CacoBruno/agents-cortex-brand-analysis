from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

LegacyGroup = Literal[
    "platform",
    "measurements",
    "index",
    "context",
    "pattern",
    "insights",
    "visualization",
    "highlights",
    "delivery",
    "news",
    "ppt",
]


class LegacyCapability(BaseModel):
    group: LegacyGroup
    tool_name: str
    migrated_native: bool = False
    notes: str | None = None


class LegacyCapabilities(BaseModel):
    capabilities: list[LegacyCapability] = Field(default_factory=list)


class LegacyToolRequest(BaseModel):
    group: LegacyGroup
    tool_name: str
    arguments: dict[str, object] = Field(default_factory=dict)
    data: list[dict] | None = None


class LegacyToolResult(BaseModel):
    group: LegacyGroup
    tool_name: str
    output: object
