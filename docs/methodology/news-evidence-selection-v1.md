# NewsEvidenceSelectionV1 — escopo e auditoria

O módulo `workflows/news_evidence_selection.py` é uma migração **parcial**
e deliberadamente determinística de critérios identificados em
`legacy/cortex_brand_ai_tools/services/coverage_pattern/coverage_context.py`.

## Regras implementadas

- Dias: modo legado padrão, com máximos/mínimos de contribuição NPS,
  máximos de alcance promotor/detrator e z-score; união preservando ordem
  de identificação; extras positivos/negativos opcionais.
- Veículos: `Promotores - Detratores`, desempate por Promotores desc e
  Detratores asc, sem fontes nulas e sem duplicatas.
- Assuntos: separar contribuições positivas e negativas; ordenar por
  contribuição, total do assunto e NPS do assunto, conforme sentido.

## Limites explícitos

- Os métodos recebem dataframes **previamente filtrados e autorizados**.
  `top_topics` não aplica o filtro `mes_index=0` nem seleciona empresas.
- Ainda não selecionam ou retornam documentos completos, títulos ou URLs.
  O legado ordena reportagens por alcance desc, prioridade de Tier e
  `doc_score` desc; isso será objeto de implementação e paridade posterior.
- `key_days` reproduz somente o modo legado padrão; o modo parametrizado
  `n_top_*` ainda não foi portado.
- Testes atuais usam dados controlados: **não são teste de paridade executado
  contra as funções legadas nem certificação de metodologia**.
- Uma execução final precisa checar seleção sobre dados reais e consistência
  de universo, múltiplos assuntos por notícia e denominadores.

## Próximas validações

1. CI Ruff + pytest.
2. Extrair fixtures reais/legadas ou executar função original com dados
   sintéticos fixos, comparando saídas JSON e ordenação.
3. Portar agrupamento de reportagens por empresa, dia e assunto preservando
   `document_id`, título, data, fonte, URL e evidências.
4. Integrar com `dataset_id` e `EvidenceResult` auditável.
