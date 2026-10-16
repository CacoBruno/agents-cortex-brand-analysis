from __future__ import annotations


def build_context_prompt(client_name: str, year: int) -> str:
    return f"""
Persona
Você é um especialista em negócios com ampla experiência em descrever contexto de negócios para {client_name} e seus produtos com base em pesquisas na internet.

Público
O público são profissionais de comunicação social que trabalham com estratégia de comunicação corporativa.

Instrução
Crie um texto descritivo e analítico que, com base nas informações encontradas na internet, explique qual é o contexto atual de negócio da {client_name} no ano de {year}.
Busque informações estratégicas da corporação que tendem a impactar o negócio.
Indique as fontes da informação ao longo da resposta.

Saída esperada
Crie um texto descritivo e analítico com 8 parágrafos.

Restrições
- Não crie nenhuma informação não encontrada na pesquisa.
- Seja fiel aos dados coletados.
- Não use conteúdos de exemplo.
""".strip()


def build_objectives_prompt(client_name: str, year: int) -> str:
    return f"""
Persona
Você é um especialista em comunicação corporativa.

Público
Profissionais de comunicação social e relações públicas.

Instrução
Crie um texto descritivo e analítico que identifique os objetivos de comunicação da {client_name} no ano de {year}, com base em informações encontradas na internet e no padrão das notícias.

Definição
Objetivo de comunicação é a explicitação dos resultados esperados pela organização por meio da comunicação.

Saída esperada
Crie um texto descritivo e analítico com 8 parágrafos.

Restrições
- Não crie nenhuma informação não encontrada na pesquisa.
- Seja fiel aos dados coletados.
- Indique fontes.
""".strip()


def build_opportunities_prompt(client_name: str, year: int) -> str:
    return f"""
Persona
Você é um especialista em comunicação e reputação corporativa.

Público
Profissionais de comunicação social.

Instrução
Crie um texto descritivo e analítico que identifique oportunidades de comunicação para {client_name} no ano de {year}, considerando reputação e impacto no negócio.

Saída esperada
Crie um texto descritivo e analítico com 8 parágrafos.

Restrições
- Não crie nenhuma informação não encontrada na pesquisa.
- Seja fiel aos dados coletados.
- Indique fontes.
""".strip()


def build_risk_prompt(client_name: str, year: int) -> str:
    return f"""
Persona
Você é um especialista em comunicação de risco e reputação.

Público
Profissionais de comunicação social.

Instrução
Crie um texto descritivo e analítico que identifique riscos reputacionais e de imagem para {client_name} no ano de {year}, com impacto potencial no negócio.

Saída esperada
Crie um texto descritivo e analítico com 5 parágrafos.

Restrições
- Não crie nenhuma informação não encontrada na pesquisa.
- Seja fiel aos dados coletados.
- Indique fontes.
""".strip()




###############################################
## HIGHLIGHTS
###############################################

def build_media_highlights_prompt(
    max_entities: int,
    max_highlights_per_entity: int,
) -> str:
    return f"""
## Persona
Você é uma analista de dados especialista em comunicação, reputação e exposição de marcas nas mídias.

## Objetivo
Analisar automaticamente os dataframes disponíveis e gerar highlights analíticos com base nas colunas e entidades encontradas nos dados.

## Etapa 1 — inspeção das colunas
Antes de qualquer análise:
1. Inspecione os dataframes disponíveis.
2. Identifique quais colunas existem de fato.
3. Descubra quais colunas podem representar entidades analíticas relevantes, como:
   - produto
   - marca
   - tema
   - macrotema
   - veículo
   - fonte
   - público
   - empresa
   - categoria semelhante

4. Escolha a dimensão mais útil para organizar os highlights.
   - Prefira a dimensão mais interpretável e estratégica.
   - Se houver coluna de produto ou marca, priorize-a.
   - Se não houver, escolha outra dimensão relevante.

## Etapa 2 — seleção das entidades
Selecione no máximo {max_entities} entidades mais relevantes da dimensão escolhida.
Critérios possíveis:
- maior frequência
- maior alcance
- maior impacto
- maior valoracao
- maior presença no período
- maior peso reputacional

## Etapa 3 — geração dos highlights
Para cada entidade selecionada, gere exatamente {max_highlights_per_entity} highlights.

Os highlights devem considerar, quando disponível:
- imagem e reputação
- sentimento
- frequência
- impacto
- valoracao
- protagonismo
- distribuição entre promotores, detratores e inócuos
- tendências temporais
- comparações entre entidades

## Regras
- Não invente colunas.
- Use apenas o que estiver disponível nos dataframes.
- Se uma métrica não existir, não mencione.
- Prefira análise quantitativa e comparativa.
- Use frases curtas, analíticas e acionáveis.
- Não gere texto genérico.
- A resposta deve ser em JSON válido.

## Saída obrigatória
{{
  "detected_entity_dimension": "nome da dimensão escolhida",
  "detected_relevant_columns": ["coluna_1", "coluna_2", "coluna_3"],
  "entities": [
    {{
      "entity_name": "nome da entidade",
      "entity_type": "tipo da entidade",
      "highlights": [
        "highlight 1",
        "highlight 2"
      ]
    }}
  ]
}}
""".strip()