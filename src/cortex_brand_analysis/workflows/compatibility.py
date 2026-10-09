from __future__ import annotations

from cortex_brand_analysis.domain.compatibility import (
    LegacyCapabilities,
    LegacyCapability,
    LegacyToolRequest,
    LegacyToolResult,
)
from cortex_brand_analysis.services import legacy_bridge


NATIVE_TOOLS = {
    ("platform", "export_publications_database"),
    ("platform", "export_media_analysis_database"),
    ("index", "calc_nps_score"),
    ("index", "nps_total_and_contrib"),
    ("index", "protagonism_score"),
    ("index", "freq_score"),
    ("index", "valoration_score"),
    ("index", "jornalista_score"),
    ("index", "action_score"),
}


class CompatibilityWorkflow:
    def capabilities(self) -> LegacyCapabilities:
        rows = []
        for group, tools in legacy_bridge.LEGACY_GROUP_TOOLS.items():
            for tool_name in sorted(tools):
                native = (group, tool_name) in NATIVE_TOOLS
                rows.append(
                    LegacyCapability(
                        group=group,
                        tool_name=tool_name,
                        migrated_native=native,
                        notes=(
                            "Prefer native v2 endpoint"
                            if native
                            else "Available through compatibility runtime"
                        ),
                    )
                )
        return LegacyCapabilities(capabilities=rows)

    def run(self, request: LegacyToolRequest) -> LegacyToolResult:
        output = legacy_bridge.invoke_tool(
            request.group,
            request.tool_name,
            request.arguments,
            request.data,
        )
        return LegacyToolResult(
            group=request.group,
            tool_name=request.tool_name,
            output=output,
        )
