# Integração do cortex-brand-ai-tools

## Fonte correta

A fonte funcional principal desta refatoração passa a ser:

`CacoBruno/cortex-brand-ai-tools`

O repositório `mcp-pr-tools-ai` foi usado inicialmente por engano e permanece apenas
como referência histórica de alguns fluxos já migrados.

## Princípio de integração

Não copiar o repositório legado inteiro. Migrar capacidade por capacidade para:

```text
API / Agents
    ↓
Typed contracts
    ↓
Workflows
    ↓
Domain rules
    ↓
Adapters
```

## Mapa inicial

| cortex-brand-ai-tools | arquitetura v2 | decisão |
|---|---|---|
| `src/mcp_server/*` | futura camada `mcp/` | reconstruir sobre workflows tipados |
| `src/agents/*` | futura camada `agents/` | preservar comportamento; trocar acesso direto por requests tipados |
| `src/tools_agents/platform/*` | exports + Cortex adapter | parcialmente migrado |
| `src/tools_agents/measurements/*` | measurements workflow | migrar |
| `src/tools_agents/communication_indexes/*` | communication indexes workflow | migrando agora |
| `src/tools_agents/analysis/coverage_context/*` | coverage workflows | migrar |
| `src/tools_agents/analysis/coverage_pattern/*` | coverage workflows | migrar |
| `src/tools_agents/insights_structural/*` | insights workflows | migrar |
| `src/tools_agents/insights_tools/*` | insights orchestration | migrar após dependências |
| `services/charts/*` | visualization service | preservar e modularizar |
| `services/ppt/*` | presentation service | preservar |
| `services/ia_funtions/*` | AI services | migrar sem estado global |
| `core/dataframe_store.py` | remover | substituir por input explícito / persistência de runs |
| `tools/shared_state.py` | remover | substituir por estado explícito |
| `services/index_function.py` | domain/workflows | portar funções determinísticas |

## Ordem

1. Communication indexes.
2. Measurements.
3. Coverage context / patterns.
4. Charts / visualization.
5. Insights structural.
6. Insights orchestration.
7. Agent PRIA.
8. MCP server sobre o núcleo tipado.
9. PPT / delivery.
