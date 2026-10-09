from __future__ import annotations

from cortex_brand_analysis.domain.nlp import NlpRequest, NlpResult
from cortex_brand_analysis.services.nlp_runtime import NativeNlpRuntime


class NlpWorkflow:
    def __init__(self, runtime: NativeNlpRuntime | None = None) -> None:
        self.runtime = runtime or NativeNlpRuntime()

    def run(self, request: NlpRequest) -> NlpResult:
        return self.runtime.run(request)
