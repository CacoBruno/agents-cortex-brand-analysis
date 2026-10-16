from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from cortex_brand_analysis.domain.analytics import AnalyticsRequest
from cortex_brand_analysis.domain.communication_indexes import CommunicationIndexRequest
from cortex_brand_analysis.domain.exports import (
    MediaAnalysisExportRequest,
    PublicationExportRequest,
)
from cortex_brand_analysis.domain.nlp import NlpRequest
from cortex_brand_analysis.mcp.tools import (
    export_media_analysis,
    export_publications,
    run_analytics,
    run_communication_index,
    run_nlp,
)

mcp = FastMCP(
    name="Cortex Brand Analysis",
    instructions="Use only typed Cortex Brand Analysis workflows.",
)


@mcp.tool(name="nlp_run")
def nlp_run(request: NlpRequest) -> dict[str, Any]:
    return run_nlp(request)


@mcp.tool(name="analytics_run")
def analytics_run(request: AnalyticsRequest) -> dict[str, Any]:
    return run_analytics(request)


@mcp.tool(name="communication_index_run")
def communication_index_run(
    request: CommunicationIndexRequest,
) -> dict[str, Any]:
    return run_communication_index(request)


@mcp.tool(name="publications_export")
def publications_export(
    request: PublicationExportRequest,
) -> dict[str, Any]:
    return export_publications(request)


@mcp.tool(name="media_analysis_export")
def media_analysis_export(
    request: MediaAnalysisExportRequest,
) -> dict[str, Any]:
    return export_media_analysis(request)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
