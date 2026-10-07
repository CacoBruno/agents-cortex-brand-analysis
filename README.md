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
