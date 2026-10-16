# Auditoria metodológica — PRIA e análise de mídia

Status: levantamento inicial, **não** certificação de equivalência.

## Evidência verificada

- Agente legado: `legacy/cortex_brand_ai_tools/src/agents/agent_insights.py`.
- Usa `gpt-4o-mini`, LangGraph `create_react_agent` e `SqliteSaver`.
- Registra três tools: `insights_orchestrator_analysis_media_tool`,
  `insights_orchestrator_with_whatsapp_tool`,
  `insights_orchestrator_with_meeting_insights_tool`.
- O prompt exige plataforma, período, empresa/produto com grafia da plataforma,
  opção de nome de exibição e filtragem de Tier (padrão legado Tier 1 e Tier 2).
- A implementação antiga também solicita periodicidade mensal/semanal,
  `period_label`, `anchor_weekday` e checagem de `Representa empresa`.
- O agente legado **não contém**, neste arquivo, as fórmulas nem o código de
  seleção de evidências dos três orquestradores. Precisamos rastrear as tools
  importadas em `src.tools_agents.insights_tools.tools` antes de declarar
  metodologia recuperada.

## Hipóteses a confirmar na auditoria dos orquestradores

1. Universo: cubo, definição da unidade de análise, duplicatas e filtros efetivos.
2. Indicadores: fórmulas, denominadores, pesos, tratamento de ausentes e status.
3. Seleção de notícias: ranqueamento, amostragem, representatividade e links.
4. Interpretação: regras para mudanças temporais, leitura reputacional e alertas.
5. Outputs: diferenças entre relatório, WhatsApp e reunião.
6. Casos de benchmark: resultados legados congelados e comparação numérica.

## Regras para a migração

- Preservar fórmulas e escolhas metodológicas até haver benchmark e decisão
  documentada para alterar qualquer regra.
- Separar métodos calculados de heurísticas interpretativas e linguagem final.
- Versionar cada método: propósito, campos exigidos, população, fórmula,
  pressupostos, limitações, testes e evidências.
- Nunca alegar que o atual `AnalyticsWorkflow` substitui os orquestradores
  antigos apenas porque já executa `groupby`, `timeseries` e índices.
- O novo `Analytical Methods Registry` começa com métodos legados
  **verificados**, e depois recebe métodos novos propostos e avaliados.

## Próxima inspeção

Localizar e ler `src/tools_agents/insights_tools/tools.py` e suas dependências
no diretório `legacy/cortex_brand_ai_tools`, catalogar operações e criar
testes de paridade com dados sintéticos e casos reais autorizados.
