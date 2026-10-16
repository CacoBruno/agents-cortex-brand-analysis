from __future__ import annotations

import json
from typing import Any

from cortex_brand_analysis.config import Settings
from cortex_brand_analysis.domain.agent import PriaRequest, PriaResult
from cortex_brand_analysis.domain.analytics import AnalyticsRequest
from cortex_brand_analysis.domain.communication_indexes import CommunicationIndexRequest
from cortex_brand_analysis.domain.errors import ConfigurationError, UpstreamError
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

PRIA_INSTRUCTIONS = """
Você é PRIA, a inteligência artificial da oferta Brand da Cortex Intelligence.

Atue como consultora e analista de mídia sênior. Ajude o usuário a analisar exposição
de marcas e produtos e a produzir três tipos de entrega:
1. análise de mídia e insights;
2. texto direto para WhatsApp;
3. roteiro para reunião de insights.

Antes de consultar dados Cortex, confirme que existem dados suficientes para montar
um request válido: plataforma, período e ao menos uma empresa ou produto. Filtros e
nomes de empresas/produtos devem corresponder aos valores da plataforma.

Use somente as tools tipadas disponíveis. Nunca invente dados retornados pela Cortex.
Não peça nem execute Python, shell, filesystem ou chamadas de rede arbitrárias.
Para cálculos, prefira analytics_run e communication_index_run.
Para dados de origem, use publications_export ou media_analysis_export.
Use nlp_run somente quando uma operação NLP for necessária.

Ao responder, diferencie claramente evidência dos dados e interpretação analítica.
Se não houver evidência suficiente, diga isso explicitamente.
""".strip()


def _tool(name: str, description: str, model: type[Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": model.model_json_schema(),
    }


PRIA_TOOLS: list[dict[str, Any]] = [
    _tool(
        "nlp_run",
        "Executa NLP nativo: sentiment, protagonism, entities, themes ou clustering.",
        NlpRequest,
    ),
    _tool(
        "analytics_run",
        "Executa analytics seguro: describe, value_counts, groupby, correlation ou timeseries.",
        AnalyticsRequest,
    ),
    _tool(
        "communication_index_run",
        "Calcula índices determinísticos de comunicação.",
        CommunicationIndexRequest,
    ),
    _tool(
        "publications_export",
        "Exporta publicações Cortex com filtros tipados.",
        PublicationExportRequest,
    ),
    _tool(
        "media_analysis_export",
        "Exporta dados de Análise de Mídia Cortex com filtros tipados.",
        MediaAnalysisExportRequest,
    ),
]


def _dispatch_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "nlp_run":
        return run_nlp(NlpRequest.model_validate(arguments))
    if name == "analytics_run":
        return run_analytics(AnalyticsRequest.model_validate(arguments))
    if name == "communication_index_run":
        return run_communication_index(CommunicationIndexRequest.model_validate(arguments))
    if name == "publications_export":
        return export_publications(PublicationExportRequest.model_validate(arguments))
    if name == "media_analysis_export":
        return export_media_analysis(MediaAnalysisExportRequest.model_validate(arguments))
    raise ValueError(f"unsupported PRIA tool: {name}")


class PriaAgent:
    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        if not settings.openai_api_key and client is None:
            raise ConfigurationError("OPENAI_API_KEY is required for PRIA")
        self.settings = settings
        self.client = client or self._build_client()

    def _build_client(self) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ConfigurationError("install the project with the 'ai' extra to enable PRIA") from exc
        return OpenAI(api_key=self.settings.openai_api_key)

    def run(self, request: PriaRequest, max_tool_rounds: int = 6) -> PriaResult:
        kwargs: dict[str, Any] = {
            "model": "gpt-6-luna",
            "instructions": PRIA_INSTRUCTIONS,
            "tools": PRIA_TOOLS,
            "input": request.message,
        }
        if request.previous_response_id:
            kwargs["previous_response_id"] = request.previous_response_id

        try:
            response = self.client.responses.create(**kwargs)

            used_tools: list[str] = []
            rounds = 0

            while rounds < max_tool_rounds:
                calls = [item for item in response.output if item.type == "function_call"]
                if not calls:
                    return PriaResult(
                        answer=response.output_text,
                        response_id=response.id,
                        tool_calls=used_tools,
                    )

                outputs: list[dict[str, str]] = []
                for call in calls:
                    arguments = json.loads(call.arguments)
                    result = _dispatch_tool(call.name, arguments)
                    used_tools.append(call.name)
                    outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": json.dumps(result, ensure_ascii=False),
                        }
                    )

                response = self.client.responses.create(
                    model="gpt-6-luna",
                    instructions=PRIA_INSTRUCTIONS,
                    tools=PRIA_TOOLS,
                    previous_response_id=response.id,
                    input=outputs,
                )
                rounds += 1

        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise UpstreamError("PRIA tool execution failed") from exc
        except Exception as exc:
            raise UpstreamError("PRIA model request failed") from exc

        raise UpstreamError("PRIA exceeded the maximum number of tool rounds")
