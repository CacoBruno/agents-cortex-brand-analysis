from __future__ import annotations

import json
from collections import Counter
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
from cortex_brand_analysis.domain.model_policy import ModelPolicy
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
Atue como consultora e analista de mídia sênior, com três entregas:
(1) análise de mídia e insights; (2) texto para WhatsApp;
(3) roteiro para reunião de insights.

ESCOPO E LIMITES
- Utilize somente tools tipadas disponíveis. Nunca invente dados, filtros
  cadastrados na plataforma, resultados ou ferramentas.
- Não execute Python, shell, filesystem, rede arbitrária ou acesso direto
  à infraestrutura. Não use o código legado.
- Diferencie evidências de interpretação e explique limitações dos dados.

ETAPA 1 — ENTENDER O PEDIDO ANTES DE CONSULTAR
- Identifique o objetivo: exposição geral de marca/produto, recorte temático,
  comparação, reputação, impacto, desempenho de ações ou outro recorte.
- Para consultas Cortex, obtenha plataforma, datas inicial e final explícitas
  e ao menos uma empresa ou produto identificado.
- Não execute exports se faltar qualquer um desses elementos. Faça perguntas
  objetivas somente sobre informações essenciais ainda ausentes.
- Não substitua datas ausentes por defaults do contrato: confirme com o usuário
  o período desejado. Não presuma que a plataforma é a mesma de outro cliente.
- Se o nome indicado for ambíguo, peça desambiguação. Nomes de empresas e
  produtos precisam corresponder aos valores usados pela plataforma. Se não
  houver recurso para consultar o catálogo de valores, não afirme que houve
  validação do cadastro. Informe a limitação quando ela afetar o resultado.

ETAPA 2 — DEFINIR FILTROS CONFORME A INTENÇÃO
- Filtros de escopo: platform_url, start_date, end_date, companies/products.
  Eles estabelecem o universo da consulta e não podem ser omitidos.
- Filtros opcionais disponíveis para análise de mídia: media, tiers, states,
  impact_types, sentiments, protagonism, topics, specific_subjects,
  communication_actions, mention_origins, journalists, themes,
  macro_subjects e classification_status.
- Use filtros opcionais apenas quando explicitamente solicitados ou
  inequivocamente necessários ao objetivo. Nunca invente seus valores.
- Exposição geral: mantenha mídias, sentimentos, protagonismo, temas e
  assuntos sem restrição para preservar o universo. Não transforme
  "analisar negatividade" em filtro de notícias negativas, pois isso
  impediria calcular a proporção de negatividade na cobertura total.
- Para comparações, preserve denominadores e explique quais subconjuntos
  são comparados. Evite filtros que eliminem o grupo de referência.
- Trate status de classificação como parte do escopo metodológico:
  se incluir registros pendentes, não interprete ausências de classificação
  como categorias substantivas. Declare a cobertura de classificados.
- Nunca trate correspondência textual parcial como confirmação de uma
  entidade exata: o adapter atual utiliza exact_match=False.

ETAPA 3 — EXECUÇÃO E RESPOSTA
- Use media_analysis_export para dados classificados e publications_export
  para publicações de origem. Não confunda os universos das duas bases.
- Antes de exportar, verifique todos os campos obrigatórios da chamada.
  Evite exportações exploratórias sem recorte explícito.
- Para métricas, prefira analytics_run e communication_index_run quando
  seus contratos e fontes forem adequados. Não alegue que essas operações
  analisaram o export se não houver vínculo real entre os dados.
- Exports retornam ao modelo um perfil agregado da base consultada,
  sem o texto integral de todas as matérias.
- Reporte o universo analisado, filtros efetivos, datas, total de registros,
  limitações de classificação e distinção entre resultados e hipóteses.
- Se a consulta vier vazia ou excessivamente ampla por ambiguidade,
  não invente conclusão; peça apenas a revisão necessária do escopo.
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


def _compact_export(result: dict[str, Any], sample_size: int = 8) -> dict[str, Any]:
    """Convert a potentially huge Cortex export into a bounded analytical profile.

    The full export is used to calculate the profile, but raw article content is never
    sent back to the model. This keeps function_call_output safely below API limits.
    """
    rows = result.get("data", [])
    if not isinstance(rows, list):
        return result

    categorical_candidates = [
        "Mídia",
        "Fonte",
        "Tier",
        "Sentimento",
        "Nível de Protagonismo",
        "Nível de Protagonismo final",
        "Empresa analisada",
        "Produto analisado",
        "Macro assunto",
        "Tópicos",
        "Assunto específico",
        "Ação",
        "Tipo da ação",
        "Temas",
        "Origem da menção",
        "Tipos de impactos",
        "Status classificação",
    ]
    numeric_candidates = ["Alcance orgânico", "Alcance total"]
    date_candidates = ["Data", "data_da_publicacao"]

    profile: dict[str, Any] = {
        "rows": result.get("rows", len(rows)),
        "columns": result.get("columns", []),
        "top_values": {},
        "numeric_summary": {},
        "date_range": {},
    }

    for column in categorical_candidates:
        values: list[str] = []
        for row in rows:
            value = row.get(column)
            if value is None or value == "":
                continue
            if isinstance(value, list):
                values.extend(str(item) for item in value if item not in (None, ""))
            else:
                values.append(str(value))
        if values:
            profile["top_values"][column] = [
                {"value": value, "count": count}
                for value, count in Counter(values).most_common(10)
            ]

    for column in numeric_candidates:
        values: list[float] = []
        for row in rows:
            value = row.get(column)
            try:
                if value is not None:
                    values.append(float(value))
            except (TypeError, ValueError):
                continue
        if values:
            profile["numeric_summary"][column] = {
                "sum": round(sum(values), 2),
                "mean": round(sum(values) / len(values), 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "non_null": len(values),
            }

    for column in date_candidates:
        values = sorted(
            str(row[column])
            for row in rows
            if row.get(column) not in (None, "")
        )
        if values:
            profile["date_range"][column] = {
                "min": values[0],
                "max": values[-1],
            }

    excluded = {"Conteúdo", "conteudo", "text", "Texto"}
    sample: list[dict[str, Any]] = []
    for row in rows[:sample_size]:
        sample.append(
            {
                key: value
                for key, value in row.items()
                if key not in excluded
            }
        )

    profile["sample"] = sample
    profile["note"] = (
        "Perfil calculado deterministicamente sobre a exportação completa. "
        "O conteúdo integral das matérias foi omitido do retorno ao modelo."
    )
    return profile


def _dispatch_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "nlp_run":
        return run_nlp(NlpRequest.model_validate(arguments))
    if name == "analytics_run":
        return run_analytics(AnalyticsRequest.model_validate(arguments))
    if name == "communication_index_run":
        return run_communication_index(CommunicationIndexRequest.model_validate(arguments))
    if name == "publications_export":
        result = export_publications(PublicationExportRequest.model_validate(arguments))
        return _compact_export(result)
    if name == "media_analysis_export":
        result = export_media_analysis(MediaAnalysisExportRequest.model_validate(arguments))
        return _compact_export(result)
    raise ValueError(f"unsupported PRIA tool: {name}")


class PriaAgent:
    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        if not settings.openai_api_key and client is None:
            raise ConfigurationError("OPENAI_API_KEY is required for PRIA")
        self.settings = settings
        self.model_policy = ModelPolicy.from_settings(settings)
        self.client = client or self._build_client()

    def _build_client(self) -> Any:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ConfigurationError(
                "install the project with the 'ai' extra to enable PRIA"
            ) from exc
        return OpenAI(api_key=self.settings.openai_api_key)

    def run(self, request: PriaRequest, max_tool_rounds: int = 6) -> PriaResult:
        kwargs: dict[str, Any] = {
            "model": self.model_policy.for_role("conversation").model,
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
                    model=self.model_policy.for_role("conversation").model,
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
