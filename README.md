# Agents Cortex Brand Analysis

Refatoração do projeto `mcp-pr-tools-ai` para uma arquitetura segura, testável e auditável de automações e agentes para análise de marca da Cortex.

## Status

A arquitetura v2 já cobre os fluxos abaixo, todos expostos pela API:

```text
API (FastAPI)
 -> Workflows (news check, ingestão, revisão de classificação, exports, RAG, analytics)
 -> Adapters (Cortex HTTP, OpenAI, S3, índice JSONL)
```

O repositório antigo permanece como referência funcional durante a migração.
Os agentes LLM (`agents/`) ainda não foram implementados; veja
[docs/architecture.md](docs/architecture.md).

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

Python 3.11 ou 3.12:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate

pip install -e ".[ai,dev]"
```

Crie um arquivo `.env` na raiz do projeto (ele é ignorado pelo git) com as variáveis
abaixo, no formato `NOME=valor`, uma por linha:

| Variável | Obrigatória | Padrão | Uso |
|---|---|---|---|
| `MCP_API_KEY` | sim (mín. 16 caracteres) | – | chave exigida no header `X-API-Key` |
| `PLATFORM_LOGIN` | para rotas Cortex | – | login da plataforma Cortex |
| `PLATFORM_PASSWORD` | para rotas Cortex | – | senha da plataforma Cortex |
| `OPENAI_API_KEY` | para ingestão e RAG | – | enriquecimento de notícias e RAG |
| `AWS_REGION` | não | `sa-east-1` | região do S3 |
| `LOG_LEVEL` | não | `INFO` | reservado; o logging ainda não é configurado pela aplicação |
| `HTTP_TIMEOUT_SECONDS` | não | `20` | timeout das chamadas HTTP (máx. 120) |

As credenciais AWS **não** são lidas do `.env`: o boto3 usa a cadeia padrão
(variáveis de ambiente do processo, `~/.aws/credentials` ou role da instância).

Checagens (as mesmas do CI):

```bash
ruff check .
ruff format --check .
mypy src
pytest --cov=src/cortex_brand_analysis
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

## Códigos de erro da API

| Status | Quando |
|---|---|
| `401` | `X-API-Key` inválida |
| `422` | request inválido ou regra de negócio violada (ex.: coluna inexistente no analytics); a mensagem é retornada |
| `502` | falha em serviço externo (Cortex, OpenAI, S3); detalhes ficam apenas no log |
| `503` | credencial ou dependência opcional ausente para a operação (ex.: `PLATFORM_LOGIN`, `OPENAI_API_KEY`) |

## Migrações concluídas

1. checagem de notícias (Publicações + PR Data);
2. revisão de classificação com preview/apply;
3. enriquecimento e upload controlado de notícias;
4. exportação de Publicações e Análise de Mídia;
5. RAG de produto com fontes e build reproduzível;
6. analytics seguro com operações allow-listed;
7. audit trail, idempotência e persistência de runs.


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

URLs que falham aparecem em `failed` com uma mensagem segura (ex.: `page responded
with HTTP 404`). Por proteção contra SSRF, só são aceitas URLs `http`/`https` cujo
host resolva para IPs públicos; redirecionamentos são validados a cada salto e a
página é limitada a 5 MB.

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


## Audit trail e run IDs

Todas as requisições HTTP recebem um identificador único no header:

```text
X-Run-ID: <uuid>
```

Cada execução é persistida em:

```text
.data/audit/runs.jsonl
```

O registro contém:
- `run_id`;
- operação HTTP;
- `started_at` e `finished_at`;
- duração em milissegundos;
- status (`success` / `error`);
- indicador `writes_external_state`;
- resumo seguro do input;
- resumo do resultado;
- tipo e mensagem de erro quando aplicável.

Por segurança, o middleware não persiste o corpo completo das requisições nem
credenciais. O resumo registra apenas metadados como método, rota, nomes de query
parameters e tamanho do conteúdo.

As operações atualmente marcadas como escrita externa são:
- `POST /v1/news/ingestion/apply`;
- `POST /v1/classifications/review/apply`;
- `POST /v1/rag/build`.

### Consultar execuções

```text
GET /v1/audit/runs?limit=100
```

A rota é protegida pela mesma API key e retorna primeiro as execuções mais recentes.
O limite máximo é 500 registros.
