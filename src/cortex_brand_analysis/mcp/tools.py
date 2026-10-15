from __future__ import annotations

from typing import Any

from cortex_brand_analysis.domain.nlp import NlpRequest
from cortex_brand_analysis.workflows.nlp import NlpWorkflow


def run_nlp(request: NlpRequest, workflow: NlpWorkflow | None = None) -> dict[str, Any]:
    """Execute an allow-listed native NLP operation through the typed v2 workflow."""
    active_workflow = workflow or NlpWorkflow()
    result = active_workflow.run(request)
    return result.model_dump(mode="json")
