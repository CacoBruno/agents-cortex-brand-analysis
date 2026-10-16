# Analysis Workflow v1 — Arquitetura e contrato de implementação

Status: ADR proposto (sem mudanças no runtime). Branch: `integration/cortex-brand-ai-tools`.

## Decisão

Manter a PRIA como agente conversacional OpenAI Responses API + function calling sem
LangChain ou LangGraph. Criar uma operação `analysis_run` com plano tipado,
validação determinística, referência a datasets e histórico auditável. A PRIA não
recebe linhas brutas, nem executa operações arbitrárias.

## Diagnóstico atual (verificado no código)

- `PriaAgent.run`: loop de function calls, até 6 rodadas, com
  `previous_response_id` para histórico conversacional.
- `media_analysis_export` e `publications_export` exportam linhas da Cortex;
  `_compact_export` reduz o retorno para o modelo.
- `AnalyticsRequest.data` e `CommunicationIndexRequest.data` exigem linhas
  em cada chamada; não existe vínculo com um dataset exportado anteriormente.
- `DateRange` preenche datas ausentes e os contratos de export preenchem
  `tiers` e `classification_status` com defaults; para análises amplas, essas
  decisões precisam ser explícitas.
- O adapter usa `exact_match=False` para filtros textuais de export.
- Nenhum estado analítico persistente próprio foi observado nesses caminhos.

## Nova arquitetura

```text
CLI / API / MCP
       |
PRIA (interpretação, perguntas, síntese)
       |
analysis_run(AnalysisIntent / AnalysisPlan)
       |
AnalysisPlanner (planos permitidos; sem Python gerado)
       |
AnalysisValidator (escopo, filtros, limites, autorização)
       |
AnalysisWorkflow (estado e etapas determinísticas)
       |-- CortexExportGateway
       |-- DatasetRepository (dados persistentes, segregados e versionados)
       |-- AnalyticsWorkflow (operações allow-list)
       |-- CommunicationIndexesWorkflow
       |-- Evidence / Result Repository
       |
AnalysisResult (resumo, valores, fontes, avisos, ids)
       |
PRIA (insights + explicação)
```

## Contratos-alvo

```python
class AnalysisIntent(BaseModel):
    analysis_type: Literal["brand_exposure", "theme", "comparison"]
    platform_url: str
    start_date: date
    end_date: date
    companies: list[str]
    products: list[str]
    dimensions: list[Literal[
        "volume", "timeseries", "sentiment",
        "protagonism", "themes", "sources", "reach"
    ]]
    session_id: str | None = None

class AnalysisStep(BaseModel):
    step_id: str
    operation: Literal[
        "export", "profile", "timeseries", "value_counts",
        "groupby", "communication_index"
    ]
    depends_on: list[str]
    parameters: dict[str, object]

class AnalysisPlan(BaseModel):
    plan_id: str
    intent: AnalysisIntent
    steps: list[AnalysisStep]

class AnalysisState(BaseModel):
    session_id: str
    tenant_id: str
    platform_url: str
    dataset_ids: list[str]
    active_dataset_id: str | None
    plan_id: str | None
    executed_steps: list[str]
    result_ids: list[str]
    status: Literal["draft", "validated", "running", "complete", "failed"]
```

Os modelos acima são exemplos de contrato, não código implementado. O contrato
real não deve usar `dict[str, object]` para ações livres sem validação
discriminada: cada tipo de passo terá seu próprio modelo Pydantic.

## Planejamento

1. O LLM identifica intenção e dimensões desejadas.
2. O planner cria um DAG a partir de templates allow-list. A execução ordena
   dependências e rejeita ciclos, operações desconhecidas e planos excessivos.
3. O validator faz preflight sem acessar Cortex.
4. A consulta produz um dataset persistente referenciado por `dataset_id`.
5. Métricas e índices acessam esse dataset dentro do backend, sem payload
   de linhas na chamada de function calling.
6. Cada etapa salva input, output, status, duração, erros e proveniência.
7. O agente recebe apenas resultados estruturados e evidências amostradas.

## Estado persistente

Separar histórico conversacional (`previous_response_id`) de estado analítico
(`analysis_session_id`). Persistir sessões e metadados em armazenamento
transacional, e datasets em storage gerenciado com TTL, checksum, schema,
timestamp, tenant e escopo de autorização. Não usar estado global em memória
como solução definitiva, nem path controlado pelo LLM.

Modelo de referência: `DatasetRef` contendo `dataset_id`, `tenant_id`,
`platform_id`, `scope_hash`, `schema_version`, `row_count`,
`created_at`, `expires_at`, `content_hash`. Os valores de credenciais nunca
são persistidos nesses artefatos.

## Barreira determinística

- Validar identidade/tenant, plataforma permitida e permissões antes do acesso.
- Exigir datas explícitas e ao menos um nome de empresa/produto.
- Validar `start <= end`, janela máxima configurável, limite de passos e de
  tamanho/volume estimado; registrar filtros efetivos.
- Resolver empresa/produto com catálogo de valores da plataforma quando
  disponível; sem isso, sinalizar correspondência não confirmada.
- Diferenciar ausência de filtro de exclusão intencional; evitar defaults
  metodológicos ocultos para `tiers` e `classification_status`.
- Validar colunas e compatibilidade de índice antes da operação.
- Diferenciar registros de publicações dos de análise de mídia e documentar
  denominadores, nulos, classificações pendentes e duplicidades.
- Impor autorização em *cada leitura* de dataset_id, com segregação por tenant.
- Não executar Python gerado, shell, SQL arbitrário, eval ou ferramentas de rede
  escolhidas diretamente pelo LLM.
- Limitar tamanho do retorno à OpenAI independentemente do tamanho da consulta.
- Falhas com códigos estruturados (missing_scope, unknown_filter,
  unauthorized_dataset, too_large, stale_dataset, unsupported_operation).

## Sequência de entrega

### Fase A — fundação
- Criar `domain/analysis.py` com intent, plan, step, state e result tipados.
- Criar `AnalysisValidator` com testes para filtros, datas, dependências e limites.
- Criar `AnalysisPlanner` determinístico com templates de exposição geral.
- Testar tudo sem conexão com Cortex.

### Fase B — armazenamento e orquestração
- Criar `DatasetRepository` e `AnalysisSessionRepository`, interfaces e
  adapters persistentes seguros.
- Implementar `AnalysisWorkflow` carregando dados por `dataset_id`.
- Acionar `AnalyticsWorkflow` e `CommunicationIndexesWorkflow`
  internamente, sem enviar arrays de linhas ao modelo.
- Testes com fake gateway, persistência, replay e idempotência.

### Fase C — integração
- Expor `analysis_run` na API, MCP e PRIA; migrar gradualmente de export
  bruto para referência a dataset.
- Medir tokens, tamanho de função, duração, auditoria, precisão dos filtros
  e consistência de denominadores.
- Validar cenário real Itaú 2026-10-01 a 2026-10-16.
- Reaproveitar `AnalysisResult` nos outputs WhatsApp e roteiro de reunião.

## Critérios de aceite

1. Duas perguntas sobre o mesmo escopo reutilizam `dataset_id` sem export
   duplicado, quando não expirado.
2. Nenhum function_call_output contém base inteira.
3. Falta de escopo impede acesso à Cortex.
4. Análise negativa usa como denominador o universo válido, não apenas
   matérias previamente filtradas como negativas.
5. Os resultados listam filtros, universo, contagens, versão, fontes e avisos.
6. Dataset de outro tenant e IDs expirados são rejeitados.
7. Um teste de integração prova sequência export → análise → follow-up.
8. CI verde nos Python suportados antes da disponibilização operacional.
