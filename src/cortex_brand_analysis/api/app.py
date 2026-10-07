from __future__ import annotations

import hmac
import logging
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status

from cortex_brand_analysis.config import get_settings
from cortex_brand_analysis.domain.analytics import AnalyticsRequest, AnalyticsResult
from cortex_brand_analysis.domain.audit import AuditRun, AuditRunList
from cortex_brand_analysis.domain.classification import (
    ClassificationApplyRequest,
    ClassificationApplyResult,
    ClassificationReviewPreview,
    ClassificationReviewRequest,
)
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
from cortex_brand_analysis.services.cortex_http import CortexError, CortexHTTPGateway
from cortex_brand_analysis.services.knowledge_index import JsonlKnowledgeIndex
from cortex_brand_analysis.services.news_enrichment import OpenAINewsEnricher
from cortex_brand_analysis.services.openai_rag import OpenAIRagService
from cortex_brand_analysis.services.s3_storage import S3NewsStorage
from cortex_brand_analysis.workflows.analytics import AnalyticsWorkflow
from cortex_brand_analysis.workflows.classification_review import ClassificationReviewWorkflow
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
}

app = FastAPI(
    title="Cortex Brand Analysis",
    version="0.1.0",
    description="Auditable workflows and agents for Cortex brand-analysis operations.",
)


@app.middleware("http")
async def audit_requests(request: Request, call_next):
    run_id = str(uuid.uuid4())
    started_at = datetime.now(ZoneInfo("America/Sao_Paulo"))
    started_perf = time.perf_counter()
    operation = f"{request.method} {request.url.path}"
    writes_external_state = request.url.path in WRITE_PATHS

    input_summary = {
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
    try:
        return workflow.run(request)
    except CortexError as exc:
        logger.exception("Cortex operation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cortex upstream operation failed",
        ) from exc


@app.post(
    "/v1/classifications/review/preview",
    response_model=ClassificationReviewPreview,
    dependencies=[Depends(verify_api_key)],
)
def preview_classification_review(
    request: ClassificationReviewRequest,
    workflow: ClassificationReviewWorkflow = Depends(get_classification_workflow),
) -> ClassificationReviewPreview:
    try:
        return workflow.preview(request)
    except CortexError as exc:
        logger.exception("Cortex classification preview failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cortex upstream operation failed",
        ) from exc


@app.post(
    "/v1/classifications/review/apply",
    response_model=ClassificationApplyResult,
    dependencies=[Depends(verify_api_key)],
)
def apply_classification_review(
    request: ClassificationApplyRequest,
    workflow: ClassificationReviewWorkflow = Depends(get_classification_workflow),
) -> ClassificationApplyResult:
    try:
        return workflow.apply(request)
    except CortexError as exc:
        logger.exception("Cortex classification apply failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cortex upstream operation failed",
        ) from exc


@app.post(
    "/v1/news/ingestion/preview",
    response_model=NewsIngestionPreview,
    dependencies=[Depends(verify_api_key)],
)
def preview_news_ingestion(
    request: NewsIngestionRequest,
    workflow: NewsIngestionWorkflow = Depends(get_news_ingestion_workflow),
) -> NewsIngestionPreview:
    try:
        return workflow.preview(request)
    except CortexError as exc:
        logger.exception("Cortex news ingestion preview failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cortex upstream operation failed",
        ) from exc


@app.post(
    "/v1/news/ingestion/apply",
    response_model=NewsIngestionApplyResult,
    dependencies=[Depends(verify_api_key)],
)
def apply_news_ingestion(
    request: NewsIngestionApplyRequest,
    workflow: NewsIngestionWorkflow = Depends(get_news_ingestion_workflow),
) -> NewsIngestionApplyResult:
    try:
        return workflow.apply(request)
    except CortexError as exc:
        logger.exception("Cortex news ingestion apply failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cortex upstream operation failed",
        ) from exc


@app.post(
    "/v1/exports/publications",
    response_model=ExportResult,
    dependencies=[Depends(verify_api_key)],
)
def export_publications(
    request: PublicationExportRequest,
    workflow: ExportWorkflow = Depends(get_export_workflow),
) -> ExportResult:
    try:
        return workflow.publications(request)
    except CortexError as exc:
        logger.exception("Cortex publications export failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cortex upstream operation failed",
        ) from exc


@app.post(
    "/v1/exports/media-analysis",
    response_model=ExportResult,
    dependencies=[Depends(verify_api_key)],
)
def export_media_analysis(
    request: MediaAnalysisExportRequest,
    workflow: ExportWorkflow = Depends(get_export_workflow),
) -> ExportResult:
    try:
        return workflow.media_analysis(request)
    except CortexError as exc:
        logger.exception("Cortex media-analysis export failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cortex upstream operation failed",
        ) from exc


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
