from __future__ import annotations

import hmac
import logging

from fastapi import Depends, FastAPI, Header, HTTPException, status

from cortex_brand_analysis.config import get_settings
from cortex_brand_analysis.domain.models import HealthResponse, NewsCheckRequest, NewsCheckResult
from cortex_brand_analysis.services.cortex_http import CortexError, CortexHTTPGateway
from cortex_brand_analysis.workflows.news_check import NewsCheckWorkflow

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cortex Brand Analysis",
    version="0.1.0",
    description="Auditable workflows and agents for Cortex brand-analysis operations.",
)


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    expected = get_settings().mcp_api_key
    if not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


def get_news_workflow() -> NewsCheckWorkflow:
    return NewsCheckWorkflow(CortexHTTPGateway(get_settings()))


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
