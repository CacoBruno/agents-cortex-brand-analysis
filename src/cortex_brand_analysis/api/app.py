from __future__ import annotations

import hmac
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from cortex_brand_analysis.config import get_settings
from cortex_brand_analysis.domain.analytics import AnalyticsRequest, AnalyticsResult
from cortex_brand_analysis.domain.audit import AuditRun, AuditRunList
from cortex_brand_analysis.domain.classification import (
    ClassificationApplyRequest,
    ClassificationApplyResult,
    ClassificationReviewPreview,
    ClassificationReviewRequest,
)
from cortex_brand_analysis.domain.communication_indexes import (
    CommunicationIndexRequest,
    CommunicationIndexResult,
)
from cortex_brand_analysis.domain.compatibility import (
    LegacyCapabilities,
    LegacyToolRequest,
    LegacyToolResult,
)
from cortex_brand_analysis.domain.errors import ConfigurationError, DomainError, UpstreamError
from cortex_brand_analysis.domain.exports import (
    ExportResult,
    MediaAnalysisExportRequest,
    PublicationExportRequest,
)
from cortex_brand_analysis.domain.models import HealthResponse, NewsCheckRequest, NewsCheckResult
from cortex_brand_analysis.domain.news_ingestion import (
    NewsIngestionApplyRequest,
    NewsIngestionApplyResult,
    NewsIngestionPreview,
    NewsIngestionRequest,
)
from cortex_brand_analysis.domain.rag import (
    KnowledgeBuildResult,
    KnowledgeDocument,
    RagAnswer,
    RagQueryRequest,
)
from cortex_brand_analysis.services.audit_store import JsonlAuditStore
from cortex_brand_analysis.services.cortex_http import CortexHTTPGateway
from cortex_brand_analysis.services.knowledge_index import JsonlKnowledgeIndex
from cortex_brand_analysis.services.news_enrichment import OpenAINewsEnricher
from cortex_brand_analysis.services.openai_rag import OpenAIRagService
from cortex_brand_analysis.services.s3_storage import S3NewsStorage
from cortex_brand_analysis.workflows.analytics import AnalyticsWorkflow
from cortex_brand_analysis.workflows.classification_review import ClassificationReviewWorkflow
from cortex_brand_analysis.workflows.communication_indexes import CommunicationIndexesWorkflow
from cortex_brand_analysis.workflows.compatibility import CompatibilityWorkflow
from cortex_brand_analysis.workflows.exports import ExportWorkflow
from cortex_brand_analysis.workflows.news_check import NewsCheckWorkflow
from cortex_brand_analysis.workflows.news_ingestion import NewsIngestionWorkflow
from cortex_brand_analysis.workflows.rag import KnowledgeRagWorkflow

logger = logging.getLogger(__name__)
audit_store = JsonlAuditStore(".data/audit/runs.jsonl")

WRITE_PATHS = {
    "/v1/news/ingestion/apply",
    "/v1/classifications/review/apply",
    "/v1/rag/build",
    "/v1/compat/run",
}

app = FastAPI(
    title="Cortex Brand Analysis",
    version="0.1.0",
    description="Auditable workflows and agents for Cortex brand-analysis operations.",
)


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(ConfigurationError)
async def handle_configuration_error(request: Request, exc: ConfigurationError) -> JSONResponse:
    logger.exception("Service is not configured for %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Service is not configured for this operation"},
    )


@app.exception_handler(UpstreamError)
@app.exception_handler(httpx.HTTPError)
async def handle_upstream_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Upstream operation failed for %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Upstream operation failed"},
    )


@app.middleware("http")
async def audit_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    run_id = str(uuid.uuid4())
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo"))
    started_perf = time.perf_counter()
    operation = f"{request.method} {request.url.path}"
    writes_external_state = request.url.path in WRITE_PATHS

    input_summary: dict[str, object] = {
        "method": request.method,
        "path": request.url.path,
        "query_keys": sorted(request.query_params.keys()),
        "content_length": request.headers.get("content-length"),
    }

    try:
        response = await call_next(request)
    except Exception as exc:
        finished_at = datetime.now(ZoneInfo("America/Sao_Paulo"))
        audit_store.append(
            AuditRun(
                run_id=run_id,
                operation=operation,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=int((time.perf_counter() - started_perf) * 1000),
                status="error",
                writes_external_state=writes_external_state,
                input_summary=input_summary,
                error_type=type(exc).__name__,
                error_message=str(exc)[:1000],
            )
        )
        raise

    response.headers["X-Run-ID"] = run_id
    finished_at = datetime.now(ZoneInfo("America/Sao_Paulo"))
    audit_store.append(
        AuditRun(
            run_id=run_id,
            operation=operation,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=int((time.perf_counter() - started_perf) * 1000),
            status="success" if response.status_code < 400 else "error",
            writes_external_state=writes_external_state,
            input_summary=input_summary,
            result_summary={"http_status": response.status_code},
            error_type=None if response.status_code < 400 else "HTTPError",
            error_message=None
            if response.status_code < 400
            else f"request completed with HTTP {response.status_code}",
        )
    )
    return response


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    expected = get_settings().mcp_api_key
    if not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


def get_gateway() -> CortexHTTPGateway:
    return CortexHTTPGateway(get_settings())


def get_news_workflow() -> NewsCheckWorkflow:
    return NewsCheckWorkflow(get_gateway())


def get_classification_workflow() -> ClassificationReviewWorkflow:
    return ClassificationReviewWorkflow(get_gateway())


def get_analytics_workflow() -> AnalyticsWorkflow:
    return AnalyticsWorkflow()


def get_communication_indexes_workflow() -> CommunicationIndexesWorkflow:
    return CommunicationIndexesWorkflow()


def get_compatibility_workflow() -> CompatibilityWorkflow:
    return CompatibilityWorkflow()


def get_export_workflow() -> ExportWorkflow:
    return ExportWorkflow(get_gateway())


def get_rag_workflow() -> KnowledgeRagWorkflow:
    settings = get_settings()
    return KnowledgeRagWorkflow(
        JsonlKnowledgeIndex(".data/knowledge/product.jsonl"),
        OpenAIRagService(settings),
    )


def get_news_ingestion_workflow() -> NewsIngestionWorkflow:
    settings = get_settings()
    return NewsIngestionWorkflow(
        get_gateway(),
        OpenAINewsEnricher(settings),
        S3NewsStorage(settings),
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post(
    "/v1/news/check",
    response_model=NewsCheckResult,
    dependencies=[Depends(verify_api_key)],
)
def check_news(
    request: NewsCheckRequest,
    workflow: NewsCheckWorkflow = Depends(get_news_workflow),
) -> NewsCheckResult:
    return workflow.run(request)


@app.post(
    "/v1/classifications/review/preview",
    response_model=ClassificationReviewPreview,
    dependencies=[Depends(verify_api_key)],
)
def preview_classification_review(
    request: ClassificationReviewRequest,
    workflow: ClassificationReviewWorkflow = Depends(get_classification_workflow),
) -> ClassificationReviewPreview:
    return workflow.preview(request)


@app.post(
    "/v1/classifications/review/apply",
    response_model=ClassificationApplyResult,
    dependencies=[Depends(verify_api_key)],
)
def apply_classification_review(
    request: ClassificationApplyRequest,
    workflow: ClassificationReviewWorkflow = Depends(get_classification_workflow),
) -> ClassificationApplyResult:
    return workflow.apply(request)


@app.post(
    "/v1/news/ingestion/preview",
    response_model=NewsIngestionPreview,
    dependencies=[Depends(verify_api_key)],
)
def preview_news_ingestion(
    request: NewsIngestionRequest,
    workflow: NewsIngestionWorkflow = Depends(get_news_ingestion_workflow),
) -> NewsIngestionPreview:
    return workflow.preview(request)


@app.post(
    "/v1/news/ingestion/apply",
    response_model=NewsIngestionApplyResult,
    dependencies=[Depends(verify_api_key)],
)
def apply_news_ingestion(
    request: NewsIngestionApplyRequest,
    workflow: NewsIngestionWorkflow = Depends(get_news_ingestion_workflow),
) -> NewsIngestionApplyResult:
    return workflow.apply(request)


@app.post(
    "/v1/exports/publications",
    response_model=ExportResult,
    dependencies=[Depends(verify_api_key)],
)
def export_publications(
    request: PublicationExportRequest,
    workflow: ExportWorkflow = Depends(get_export_workflow),
) -> ExportResult:
    return workflow.publications(request)


@app.post(
    "/v1/exports/media-analysis",
    response_model=ExportResult,
    dependencies=[Depends(verify_api_key)],
)
def export_media_analysis(
    request: MediaAnalysisExportRequest,
    workflow: ExportWorkflow = Depends(get_export_workflow),
) -> ExportResult:
    return workflow.media_analysis(request)


@app.post(
    "/v1/rag/build",
    response_model=KnowledgeBuildResult,
    dependencies=[Depends(verify_api_key)],
)
def build_rag_index(
    documents: list[KnowledgeDocument],
    workflow: KnowledgeRagWorkflow = Depends(get_rag_workflow),
) -> KnowledgeBuildResult:
    return workflow.build(documents)


@app.post(
    "/v1/rag/query",
    response_model=RagAnswer,
    dependencies=[Depends(verify_api_key)],
)
def query_rag(
    request: RagQueryRequest,
    workflow: KnowledgeRagWorkflow = Depends(get_rag_workflow),
) -> RagAnswer:
    return workflow.query(request)


@app.post(
    "/v1/analytics/run",
    response_model=AnalyticsResult,
    dependencies=[Depends(verify_api_key)],
)
def run_analytics(
    request: AnalyticsRequest,
    workflow: AnalyticsWorkflow = Depends(get_analytics_workflow),
) -> AnalyticsResult:
    return workflow.run(request)


@app.get(
    "/v1/audit/runs",
    response_model=AuditRunList,
    dependencies=[Depends(verify_api_key)],
)
def list_audit_runs(limit: int = 100) -> AuditRunList:
    bounded_limit = max(1, min(limit, 500))
    return AuditRunList(runs=audit_store.list_runs(limit=bounded_limit))


@app.post(
    "/v1/indexes/communication",
    response_model=CommunicationIndexResult,
    dependencies=[Depends(verify_api_key)],
)
def run_communication_index(
    request: CommunicationIndexRequest,
    workflow: CommunicationIndexesWorkflow = Depends(
        get_communication_indexes_workflow
    ),
) -> CommunicationIndexResult:
    return workflow.run(request)


@app.get(
    "/v1/compat/capabilities",
    response_model=LegacyCapabilities,
    dependencies=[Depends(verify_api_key)],
)
def list_legacy_capabilities(
    workflow: CompatibilityWorkflow = Depends(get_compatibility_workflow),
) -> LegacyCapabilities:
    return workflow.capabilities()


@app.post(
    "/v1/compat/run",
    response_model=LegacyToolResult,
    dependencies=[Depends(verify_api_key)],
)
def run_legacy_capability(
    request: LegacyToolRequest,
    workflow: CompatibilityWorkflow = Depends(get_compatibility_workflow),
) -> LegacyToolResult:
    return workflow.run(request)
