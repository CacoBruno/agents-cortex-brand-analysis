# Architecture v2

## Goal

Refactor the original `mcp-pr-tools-ai` project into a testable, auditable automation service for Cortex brand-analysis operations.

The old repository remains a functional reference. New development happens here.

## Design rule

Dependencies point inward:

```text
API / Agents
    |
    v
Workflows
    |
    v
Domain + service contracts
    ^
    |
External adapters (Cortex, OpenAI, S3, news extraction)
```

A workflow must be runnable in tests without network access or an LLM.

## Layers

### `domain/`

Typed request/result models and deterministic business rules. No FastAPI, LangChain, OpenAI, HTTP or AWS imports.

### `workflows/`

Coordinates operations. A workflow receives service contracts through dependency injection.

Example:

```text
NewsCheckWorkflow
  -> check Cortex Publicações
  -> identify missing URLs
  -> check PR Data
  -> return structured result
```

### `services/`

Protocols and adapters for external systems. Network timeouts and upstream-specific errors belong here.

### `api/`

FastAPI transport only. It validates authentication, maps HTTP requests to workflows and converts internal/upstream failures into safe HTTP responses.

### Future `agents/`

LLMs parse natural-language intent into typed domain requests. Agents must not directly perform Cortex/S3 mutations.

## Security decisions

The refactor intentionally removes these patterns from the original architecture:

- no fallback API key such as `changeme`;
- no `eval()` for LLM or external output;
- no global DataFrame state;
- no traceback returned to clients;
- no `allow_dangerous_code=True`;
- no unsafe pickle loading in request paths;
- all HTTP clients use explicit timeouts.

## Migration map

| Original | Destination |
|---|---|
| `mcp_server.py` | `api/` |
| `agents_tools/*.py` | `agents/` + thin API/tool wrappers |
| `src/cortex_actions/*` | `workflows/` |
| `src/structural_functions/cortex_platform.py` | `services/cortex_http.py` |
| `src/structural_functions/news.py` | `services/news_*.py` |
| `src/structural_functions/similarweb.py` | `services/reach.py` |
| generic helpers in `structural.py` | domain/util modules by responsibility |
| `tools/shared_state.py` | removed; explicit run/session storage |
| vector DB files committed to Git | versioned knowledge source + reproducible index build |

## Migration sequence

1. Foundation + Cortex read operations + CI.
2. Classification review workflow.
3. News enrichment and controlled upload workflow.
4. Export/query workflows.
5. RAG with source metadata and safe index loading.
6. Analytics agent in a sandboxed/allow-listed execution model.
7. Audit trail, idempotency keys and persistent run state.
