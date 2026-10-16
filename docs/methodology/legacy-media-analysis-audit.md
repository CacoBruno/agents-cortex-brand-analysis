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


## Segunda inspeção — ferramentas, grafo, estado e nodes (16/10/2026)

Arquivos inspecionados:
- `legacy/cortex_brand_ai_tools/src/tools_agents/insights_tools/tools.py`
- `legacy/cortex_brand_ai_tools/src/tools_agents/insights_tools/graph.py`
- `legacy/cortex_brand_ai_tools/src/tools_agents/insights_tools/services.py`
- `legacy/cortex_brand_ai_tools/src/tools_agents/insights_tools/nodes.py`

### DAG original confirmado

```text
captura_dados
  ├─ padrao_exposicao
  │    ├─ highlights ──────┐
  │    └─ contexto_exposicao├─ insights ── [WhatsApp | reunião | fim]
  └─ contexto_negocios ────┘
```

### Distinção histórica crítica

`build_initial_coverage_state()` define `start_date=end_date-1 ano` e
`analysis_start_date` separadamente. O histórico alimenta views, métricas
e comparações, enquanto a janela focal é aplicada no contexto de notícias.
Uma análise v2 que exporte apenas a janela focal **não é metodologicamente
equivalente**. Introduzir `reference_start_date`, `analysis_start_date`
e `analysis_end_date` com semântica formal, e testar denominadores.

### Defaults metodológicos legados observados

- `status_classificacao=["Classificado"]`
- `tipos_de_impactos=["Promotores","Detratores","Inócuos"]`
- `representa_empresa="Sim"`
- `tier=["Tier 1","Tier 2"]`
- `focus_analysis="Empresa analisada"`
- `return_metric="merged"`
- `topic_col="Assunto específico"`
- `filter_values=[0]`, selecionando período índice zero
- limites de ranking configuráveis para notícias, veículos, assuntos e dias.
Essas regras descrevem a **metodologia legada**, não precisam ser adotadas
sem revisão em toda nova análise; registrar versão e recorte efetivo.

### Ferramentas analíticas chamadas pelo padrão de exposição

- `build_media_metrics_view_tool`
- `build_last_period_statistics_tool`
- `build_company_big_number_dict_tool`
- `build_media_metrics_view_by_source_tool`
- `build_sources_last_period_multi_company_dict_enriched_tool`
- `build_topic_contrib_df_tool` (diário e por período)
- `build_topic_contrib_llm_dict_tool`
- `build_daily_metrics_enriched_tool`
- `build_daily_pattern_dict_tool`

### Ferramentas de seleção de evidências e contexto

- `extrair_contexto_noticias_tool` com conteúdo, título, fonte,
  sentimento, protagonismo, impacto, assunto e URL originais
- `build_main_days_coverage_tool` prioriza dias com contribuição
  reputacional e z-score de alcance
- `build_top_vehicles_coverage_tool`
- `build_specific_topics_reports_tool`
- `build_coverage_summary_tool`

O fluxo também utiliza `generate_company_context_tool`,
`generate_highlights_tool` e `generate_coverage_insights_tool`.
A geração de WhatsApp e reunião consome o estado e os insights anteriores.

### Conclusões de implementação

1. O núcleo a migrar é `coverage_pattern` + `coverage_context`,
   não apenas as três ferramentas de saída.
2. Criar `ExposureMethodV1`, `NewsEvidenceSelectionV1` e
   `ReputationInterpretationV1` com testes e versões independentes.
3. Os indicadores `nps_contrib_dia`, `z-score_alcance` e a view
   `return_metric="merged"` exigem auditoria de fórmulas e benchmarks
   antes de equivalência numérica.
4. Comparar filtros das views antigas com os atuais exports Cortex,
   incluindo `Representa empresa` e o período histórico.
5. Evitar mover os prompts legados sem antes documentar os inputs e
   os resultados esperados de cada gerador.

### Próximos arquivos a ler

- `src/tools_agents/analysis/coverage_pattern/tools.py` e módulos usados
- `src/tools_agents/analysis/coverage_context/tools.py` e módulos usados
- `src/tools_agents/highlights/tools.py`
- `src/tools_agents/insights_structural/tools.py`
- `src/tools_agents/communication_indexes/tools.py`
