# Contratos matemáticos da análise de mídia — legado

Status: fórmulas inspecionadas no código; certificação de paridade ainda pendente.

Fonte: `legacy/cortex_brand_ai_tools/services/index_function.py`
e `legacy/cortex_brand_ai_tools/services/coverage_pattern/pattern_and_statistic.py`.

## MP-007 — NPS de mídia ponderado por alcance

`calc_nps_score`: agrupa por dimensão/tempo, soma `alcance` por
`Tipos de impactos` e calcula:

```text
NPS = (alcance_promotor - alcance_detrator)
      / (alcance_promotor + alcance_detrator + alcance_inocuo)
```

Retorna proporção em [-1, 1], com quatro casas decimais; denominador zero
retorna zero. **Não confundir com NPS convencional de pesquisa nem com
porcentagem de matérias negativas**. A interpretação em escala de -100 a +100
exige multiplicação explícita por 100. `calc_nps_score` também soma
`alcance`, `valoracao` e `frequencia` auxiliares.

## MP-008 — Contribuição por dimensão

`nps_total_and_contrib`, `contr_type="Total"`:

```text
contrib_dim = (alcance_promotor_dim - alcance_detrator_dim)
              / alcance_total_de_todos_os_impactos_no_grupo
```

`contr_type="Promotor"`: só alcance promotor da dimensão no numerador.
A função calcula NPS do grupo arredondado a duas casas decimais e
contribuição por dimensão a quatro casas decimais. A soma de contribuições
de dimensões **mutuamente exclusivas e exaustivas** deve reproduzir o NPS
do grupo até diferenças de arredondamento. Se uma matéria possui múltiplos
temas, a soma pode ultrapassar o NPS; isso exige política de alocação.

## MP-009 — Contribuição por assunto específico

`build_nps_contrib_by_specific_topic`:

```text
contrib_assunto = NPS_assunto * (frequencia_assunto / frequencia_periodo)
```

**Diferença crítica:** este caminho usa `freq_score` (coluna
`frequencia`) para pesos de tema, enquanto `calc_nps_score`
usa `alcance` para calcular NPS. Portanto a soma de contribuições
de tema não é automaticamente igual ao NPS ponderado por alcance.
Não substituir esta regra pela fórmula MP-008 sem decisão metodológica
explícita e benchmark.

## MP-010 — Protagonismo ponderado por alcance

```text
protagonism_score = (alcance_Protagonismo +
                     alcance_Referencia_contextual_Setor)
                    / soma_alcance_cinco_categorias
```

Categorias: Citação relevante; Figurante; Referência contextual / Setor;
Protagonismo; Referência em matéria de concorrente.
Retorna proporção a quatro casas; denominador zero retorna zero.

## EV-003 — Evidências e denominadores

O ranking `build_daily_media_pattern_dict` usa valor absoluto da
contribuição diária de NPS, enquanto `select_key_days_from_daily_nps_contrib`
pode selecionar dias por contribuição positiva, negativa, promotores,
detratores e z-score. São políticas distintas. Os índices `mes_index=0`
e históricos devem ser validados conforme data âncora e calendário.

## Testes de referência necessários

1. NPS por alcance com 100 promotor, 50 detrator, 50 inócuo = 0.25.
2. Contribuição MP-008 de duas dimensões exaustivas soma 0.25.
3. Contagem de matérias diferente do peso por alcance, para impedir
   regressão que confunda métricas.
4. Tema MP-009 com pesos de frequência: demonstrar quando diverge do
   NPS total ponderado por alcance.
5. Denominador zero, nulos e categorias desconhecidas.
6. Múltiplos temas, registros duplicados e diferenciação publicação
   versus classificação por empresa.
7. Verificar output nativo frente ao legado com dados reais congelados.

Nenhuma função de produção foi substituída nesta auditoria.
