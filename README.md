# Agents Cortex Brand Analysis

Refatoração do projeto `mcp-pr-tools-ai` para uma arquitetura segura, testável e auditável de automações e agentes para análise de marca da Cortex.

## Status

Esta branch inicia a arquitetura v2 e migra o primeiro fluxo real:

```text
API
 -> NewsCheckWorkflow
 -> CortexHTTPGateway
 -> Cortex Publicações / PR Data
```

O repositório antigo permanece como referência funcional durante a migração.

## Princípios

- regras determinísticas ficam fora do LLM;
- LLMs transformam linguagem natural em requests tipados, não executam infraestrutura diretamente;
- integrações externas ficam atrás de adapters;
- workflows podem ser testados sem rede;
- sem `eval()`, estado global ou execução arbitrária de Python;
- erros internos não são expostos pela API;
- chamadas HTTP usam timeout explícito;
- mudanças serão migradas incrementalmente, sem reescrever tudo de uma vez.

## Estrutura

```text
src/cortex_brand_analysis/
├── api/          # FastAPI / transporte
├── domain/       # modelos e regras determinísticas
├── services/     # Cortex, OpenAI, S3 e demais adapters
└── workflows/    # orquestração dos casos de uso

tests/
docs/
.github/workflows/
```

Veja [docs/architecture.md](docs/architecture.md) para o desenho completo e o mapa de migração.

## Desenvolvimento

Python 3.11:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate

pip install -e ".[dev]"
copy .env.example .env
pytest
ruff check .
```

Para subir a API:

```bash
uvicorn cortex_brand_analysis.main:app --reload
```

Health check:

```text
GET /health
```

Checagem de notícias:

```text
POST /v1/news/check
X-API-Key: <MCP_API_KEY>
```

Exemplo:

```json
{
  "platform_url": "cliente.cortex-intelligence.com",
  "original_urls": [
    "https://example.com/noticia"
  ],
  "clipping_urls": []
}
```

## Próximas migrações

1. revisão de classificação;
2. enriquecimento e upload controlado de notícias;
3. exportação de Publicações e Análise de Mídia;
4. RAG de produto com fontes e build reproduzível;
5. analytics agent seguro;
6. audit trail, idempotência e persistência de runs.


## Ingestão de notícias

A ingestão nova separa enriquecimento e escrita.

### Preview

```text
POST /v1/news/ingestion/preview
```

O workflow:
1. checa Publicações;
2. checa PR Data;
3. enriquece apenas URLs realmente ausentes;
4. gera `idempotency_key` determinística por cliente + URL;
5. retorna o payload sem gravar no Data Lake.

### Apply

```text
POST /v1/news/ingestion/apply
```

Requer `confirm: true`. Cada item é salvo no S3 usando:

```text
pr/cortex-staging/oraculo/<idempotency_key>.json
```

Como a chave é determinística, repetir a mesma operação não cria um novo objeto com outra identidade.

Para habilitar o enriquecimento com OpenAI:

```bash
pip install -e ".[ai,dev]"
```


## Exportações

### Publicações

```text
POST /v1/exports/publications
```

Filtros tipados:
- empresa/produto;
- período;
- mídia;
- tier;
- estado.

### Análise de Mídia

```text
POST /v1/exports/media-analysis
```

Além dos filtros acima, aceita sentimento, protagonismo, tópico, assunto específico,
ação, origem da menção, jornalista, temas, macro assunto, tipos de impacto e status
de classificação.

As duas rotas retornam:

```json
{
  "rows": 1,
  "columns": ["..."],
  "data": [{"...": "..."}]
}
```

O LLM não monta filtros Cortex diretamente; ele deverá produzir um desses requests
tipados e o workflow determinístico executa a consulta.


## RAG seguro e reproduzível

O RAG antigo foi substituído por um índice que não usa pickle nem
`allow_dangerous_deserialization=True`.

### Construção do índice

```text
POST /v1/rag/build
```

Recebe documentos com:
- `document_id`;
- `source`;
- `title`;
- `text`;
- `version`;
- `updated_at`.

O workflow quebra os documentos em chunks, gera embeddings e persiste o índice em:

```text
.data/knowledge/product.jsonl
```

Cada linha contém metadados do chunk + vetor numérico em JSON. O índice pode ser
apagado e reconstruído a partir dos documentos-fonte.

### Consulta

```text
POST /v1/rag/query
```

A resposta inclui:
- resposta textual;
- chunks recuperados;
- `document_id`;
- `source`;
- score de similaridade.

Se a base ainda não tiver sido construída, a API informa isso explicitamente em vez
de tentar carregar artefatos serializados inseguros.


## Analytics seguro

O agente Pandas antigo foi substituído por um executor com operações allow-listed.

```text
POST /v1/analytics/run
```

Operações permitidas:
- `describe`;
- `value_counts`;
- `groupby`;
- `correlation`;
- `timeseries`.

Também são permitidos filtros explícitos com operadores:
- `eq`;
- `ne`;
- `in`;
- `contains`;
- `gte`;
- `lte`.

O executor não possui acesso a:
- `eval` / `exec`;
- Python REPL;
- filesystem;
- shell;
- rede;
- requests arbitrários.

A camada de LLM futura deverá apenas converter linguagem natural em `AnalyticsRequest`.
O cálculo continuará sendo executado pelo workflow determinístico.
