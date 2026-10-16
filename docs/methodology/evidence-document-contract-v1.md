# EvidenceResult v1 — rastreabilidade documental

Status: implementação inicial, sem certificação de paridade/integração PRIA.

## Contratos

`domain/evidence.py`: `EvidenceDocument` (ID, data, título, fonte,
URL, alcance, Tier, doc_score, empresa, assunto);
`EvidenceSelection` (metodologia, versão, dataset, critério, elegíveis,
ordem dos IDs, documentos e racional); `EvidenceResult` (seleções e alertas).

`workflows/evidence_documents.py`: seleciona matérias por dia, fonte
ou assunto, permitindo filtro por empresa.

## Critério de priorização

A lógica do legado em `services/coverage_pattern/coverage_context.py`
ordena matérias por alcance descendente, prioridade de Tier e doc_score
descendente. A implementação nativa mantém esses três critérios.
Adiciona desempate por `document_id` para estabilidade entre execuções;
essa é uma **diferença consciente** a testar contra o legado.

A seleção desduplica `document_id` dentro de cada categoria. A contagem
`eligible_count` indica registros antes dessa desduplicação.

## Limites

- Por ora, `topic` é escalar; base com multitemas exige normalização
  documentada ou explosão controlada antes de selecionar.
- O seletor recebe somente dados já autorizados, não aplica controle de
  acesso nem recupera `dataset_id` do repositório.
- Um documento com fonte e assunto permanece elegível em múltiplas
  seleções; deduplicação ocorre dentro de cada grupo apenas.
- Não foi incorporada a extração de passagens textuais/evidência por
  notícia nem verificação editorial de representatividade.
- A paridade deverá validar também filtros, ranqueamento original,
  notícias recuperadas, URLs e ausência de duplicatas.

## Próxima fase

Integrar ao `DatasetRepository` e `AnalysisWorkflow` com checagem
de tenant e escopo e comparar resultados nativos com as tools legadas.
