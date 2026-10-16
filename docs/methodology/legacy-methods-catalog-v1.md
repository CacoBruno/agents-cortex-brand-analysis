# Catálogo metodológico legado v1 — evidência de código

Status: auditoria de comportamento, **não** certificação de paridade.
Fontes:
- `legacy/cortex_brand_ai_tools/services/coverage_pattern/pattern_and_statistic.py`
- `legacy/cortex_brand_ai_tools/services/coverage_pattern/coverage_context.py`
- `legacy/cortex_brand_ai_tools/src/tools_agents/analysis/coverage_pattern/services.py`
- `legacy/cortex_brand_ai_tools/src/tools_agents/analysis/coverage_context/services.py`

## Separação das camadas

A fachada `MediaPatternService` repassa chamadas a funções em
`pattern_and_statistic.py`. A maior parte das regras metodológicas
está **neste módulo de implementação**, não na fachada.

O serviço `coverage_context/services.py` implementa recorte por datas e
orquestra funções em `coverage_pattern/coverage_context.py`.
A extração textual delega a `services/texts_treatments`, ainda pendente
de auditoria de seleção por texto e busca.

## Regras determinísticas recuperadas — primeira amostra

### MP-001 — Faixa de NPS

Função `classify_nps_band(nps_percent)`:
- `x <= -80`: crise
- `-80 < x < 0`: atenção
- `0 <= x < 35`: regular
- `35 <= x < 50`: bom
- `50 <= x < 80`: ótimo
- `x >= 80`: excelente

A função chama `_to_float` antes de classificar.
Verificar separadamente a definição e unidade da métrica NPS que produz
`nps_percent`; a régua acima **não é a fórmula do índice**.

### MP-002 — Posição histórica pelo z-score

Função `classify_historical_position(z_score)`:
- `z >= 2`: muito acima
- `1 <= z < 2`: acima
- `-1 < z < 1`: dentro do padrão
- `-2 < z <= -1`: abaixo
- `z <= -2`: muito abaixo

Nota: as condições reais tornam exatamente `-1` "abaixo",
e exatamente `-2` "muito abaixo".

### MP-003 — Variação em pontos percentuais

`classify_variation(value, "p.p.")`:
- `x >= 5`: melhora relevante
- `1 <= x < 5`: melhora leve
- `-1 < x < 1`: estabilidade
- `-5 < x <= -1`: piora leve
- `x <= -5`: piora relevante
- valor ausente: sem base comparativa

### MP-004 — Variação percentual

`classify_variation(value, "%")`:
- `x >= 20`: alta relevante
- `5 <= x < 20`: leve alta
- `-5 < x < 5`: estabilidade
- `-20 < x <= -5`: leve queda
- `x <= -20`: queda relevante

### MP-005 — Estabilidade histórica

`classify_stability(cv)`:
- `cv <= 15`: muito estável
- `15 < cv <= 30`: estável
- `30 < cv <= 60`: volátil
- `cv > 60`: muito volátil
- ausente: indefinido

### MP-006 — Protagonismo

`classify_protagonism_level(protagonism_percent, z_score)`:
- `x >= 70`: muito alto
- `40 <= x < 70`: moderado
- `x < 40`: baixo
- inclui leitura histórica por MP-002.
A alegação de "chance de lembrança" é interpretação do legado;
não deve ser apresentada como probabilidade estatística calibrada.

### EV-001 — Seleção de dias

`select_key_days_from_daily_nps_contrib` exige Data, contribuição,
Promotores, Detratores e z-score. Combina critérios de maiores
contribuições positivas/negativas, promotores, detratores e z-score.
É preciso auditar todas as regras de desempate e união de seleções
antes de portar e declarar paridade.

### EV-002 — Seleção de veículos

`build_top_vehicles_coverage_from_dict` calcula
`composite_score = Promotores - Detratores`; ordena pelo score
descendente, depois Promotores descendente e Detratores ascendente,
remove fontes ausentes e duplicadas e seleciona `top_n`.
Esse ranking não representa necessariamente os veículos de maior volume,
alcance ou negatividade. Não rotulá-lo genericamente como "top veículos".

## Política de equivalência

Para cada método: (1) fixar versão e fonte; (2) congelar casos de borda;
(3) gerar fixtures com a execução legada; (4) reimplementar no domínio
nativo, sem imports do legado; (5) comparar resultados e metadados;
(6) só então certificar e habilitar na PRIA.

Ainda pendentes: fórmulas de NPS e contribuição, composição de métricas,
janelas de referência, tratamento de datas e NA, seleção textual,
composição de evidências e prompts analíticos.
