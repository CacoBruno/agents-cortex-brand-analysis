# Status da migração completa

Fonte funcional: `CacoBruno/cortex-brand-ai-tools`.

## Preservação integral

O repositório novo contém duas formas de preservação:

1. `legacy/cortex_brand_ai_tools/`: snapshot dos 149 arquivos Python do runtime;
2. `legacy/cortex-brand-ai-tools-source`: submodule apontando para o repositório original
   completo, incluindo notebooks, CSVs, imagens e templates PPTX.

O snapshot Python não é a API oficial e não entra no lint do núcleo v2.

## V2 nativo

- Cortex authentication/read adapter;
- news check;
- news ingestion;
- classification review;
- Publicações export;
- Análise de Mídia export;
- RAG seguro;
- analytics allow-listed;
- audit trail;
- communication indexes.

## Compatibilidade allow-listed

Disponível através de `CompatibilityWorkflow`:

- platform tools;
- measurements;
- communication indexes legados;
- coverage context;
- coverage patterns;
- insights orchestration;
- highlights;
- charts / visualization;
- delivery de insights;
- news helpers;
- PPT/template engine.

O bridge não aceita nomes arbitrários de módulos ou funções: apenas tools registradas.

## Entry points preservados

Com o extra `legacy` instalado:

```bash
cortex-brand-legacy-mcp
cortex-brand-legacy-pria
```

Esses entrypoints executam o MCP e o agente PRIA originais a partir da camada
preservada. Eles existem para compatibilidade durante a promoção gradual para v2.

## Componentes dependentes de ML

Clustering, NLP e algumas classificações usam dependências pesadas. Instale o extra:

```bash
pip install -e ".[ai,dev,legacy,legacy-ml]"
```

O core v2 permanece leve e não exige Torch/TensorFlow/Transformers para operações
de plataforma, export, audit ou índices determinísticos.
