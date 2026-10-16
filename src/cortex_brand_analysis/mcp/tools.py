from __future__ import annotations

from typing import Any

from cortex_brand_analysis.config import get_settings
from cortex_brand_analysis.domain.analytics import AnalyticsRequest
from cortex_brand_analysis.domain.communication_indexes import CommunicationIndexRequest
from cortex_brand_analysis.domain.exports import (
    MediaAnalysisExportRequest,
    PublicationExportRequest,
)
from cortex_brand_analysis.domain.nlp import NlpRequest
from cortex_brand_analysis.services.cortex_http import CortexHTTPGateway
from cortex_brand_analysis.workflows.analytics import AnalyticsWorkflow
from cortex_brand_analysis.workflows.communication_indexes import CommunicationIndexesWorkflow
from cortex_brand_analysis.workflows.exports import ExportWorkflow
from cortex_brand_analysis.workflows.nlp import NlpWorkflow


def run_nlp(request: NlpRequest, workflow: NlpWorkflow | None = None) -> dict[str, Any]:
    """Execute an allow-listed native NLP operation through the typed v2 workflow."""
    active_workflow = workflow or NlpWorkflow()
    result = active_workflow.run(request)
    return result.model_dump(mode="json")


def run_analytics(
    request: AnalyticsRequest,
    workflow: AnalyticsWorkflow | None = None,
) -> dict[str, Any]:
    """Execute safe allow-listed analytics without arbitrary Python execution."""
    active_workflow = workflow or AnalyticsWorkflow()
    result = active_workflow.run(request)
    return result.model_dump(mode="json")


def run_communication_index(
    request: CommunicationIndexRequest,
    workflow: CommunicationIndexesWorkflow | None = None,
) -> dict[str, Any]:
    """Execute a deterministic communication index through the native workflow."""
    active_workflow = workflow or CommunicationIndexesWorkflow()
    result = active_workflow.run(request)
    return result.model_dump(mode="json")


def _export_workflow() -> ExportWorkflow:
    return ExportWorkflow(CortexHTTPGateway(get_settings()))


def export_publications(
    request: PublicationExportRequest,
    workflow: ExportWorkflow | None = None,
) -> dict[str, Any]:
    """Export Cortex publications using typed filters and the native Cortex gateway."""
    active_workflow = workflow or _export_workflow()
    result = active_workflow.publications(request)
    return result.model_dump(mode="json")


def export_media_analysis(
    request: MediaAnalysisExportRequest,
    workflow: ExportWorkflow | None = None,
) -> dict[str, Any]:
    """Export Cortex media-analysis rows using typed filters."""
    active_workflow = workflow or _export_workflow()
    result = active_workflow.media_analysis(request)
    return result.model_dump(mode="json")
