from __future__ import annotations

import json
from typing import Dict, Any, Tuple, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

EXPECTED_KEYS = [
    "o_que_os_dados_nos_dizem",
    "recomendacoes_de_atuacao",
    "oportunidades_observadas",
    "riscos_observados",
]


def _extract_json_from_text(text: str) -> str:
    """
    Tenta extrair o JSON de uma resposta textual da LLM.
    Suporta:
    - JSON puro
    - JSON dentro de ```json ... ```
    - texto com JSON embutido
    """
    if not text:
        raise ValueError("Resposta vazia da LLM.")

    cleaned = text.strip()

    # Caso venha em bloco markdown
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    # Tentativa 1: texto inteiro já é JSON
    try:
        json.loads(cleaned)
        return cleaned
    except Exception:
        pass

    # Tentativa 2: pegar do primeiro { até o último }
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start:end + 1]
        json.loads(candidate)  # valida aqui
        return candidate

    raise ValueError("Não foi possível extrair um JSON válido da resposta da LLM.")


def _normalize_output_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza pequenas variações de chave que a LLM possa devolver.
    """
    key_map = {
        "o que os dados nos dizem": "o_que_os_dados_nos_dizem",
        "o_que_os_dados_nos_dizem": "o_que_os_dados_nos_dizem",
        "recomendações de atuação": "recomendacoes_de_atuacao",
        "recomendacoes_de_atuacao": "recomendacoes_de_atuacao",
        "oportunidades observadas": "oportunidades_observadas",
        "oportunidades_observadas": "oportunidades_observadas",
        "riscos observados": "riscos_observados",
        "riscos_observados": "riscos_observados",
    }

    normalized = {}
    for k, v in data.items():
        k_norm = key_map.get(str(k).strip().lower(), k)
        normalized[k_norm] = v

    return normalized


def _validate_output_dict(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Valida se o dicionário final contém todas as chaves esperadas
    e se os valores são strings não vazias.
    """
    errors = []

    if not isinstance(data, dict):
        return False, ["Saída não é um dicionário."]

    for key in EXPECTED_KEYS:
        if key not in data:
            errors.append(f"Chave ausente: '{key}'")
        else:
            if not isinstance(data[key], str):
                errors.append(f"Valor da chave '{key}' deve ser string.")
            elif not data[key].strip():
                errors.append(f"Valor da chave '{key}' está vazio.")

    extra_keys = [k for k in data.keys() if k not in EXPECTED_KEYS]
    if extra_keys:
        # não invalida, só registra
        errors.append(f"Chaves extras encontradas: {extra_keys}")

    hard_errors = [e for e in errors if not e.startswith("Chaves extras")]
    return len(hard_errors) == 0, errors


def _build_prompts(
    company_name: str,
    period_label: str,
    big_number: Dict[str, Any],
    highlight_infos: Dict[str, Any],
    coverage_context_result: Dict[str, Any],
    contexto_negocios: Dict[str, Any],
    previous_error: str | None = None,
) -> Tuple[str, str]:
    """
    Monta o system prompt e user prompt.
    """

    stats_text = highlight_infos.get("stats_layer", {}).get("final_text", "")
    daily_text = highlight_infos.get("daily_layer", {}).get("final_text", "")
    topics_text = highlight_infos.get("topics_layer", {}).get("final_text", "")
    sources_text = highlight_infos.get("sources_layer", {}).get("final_text", "")

    final_synthesis = (
        coverage_context_result.get("outputs", {})
        .get("final_synthesis", {})
        .get("final_synthesis", {})
    )

    day_summary = (
        coverage_context_result.get("outputs", {})
        .get("day_analysis", {})
        .get("resumo_geral", "")
    )

    day_details = (
        coverage_context_result.get("outputs", {})
        .get("day_analysis", {})
        .get("analise_por_dia", [])
    )

    topic_summary = (
        coverage_context_result.get("outputs", {})
        .get("topic_analysis", {})
        .get("resumo_geral", "")
    )

    topic_promoters = (
        coverage_context_result.get("outputs", {})
        .get("topic_analysis", {})
        .get("analise_assuntos_promotores", [])
    )

    topic_detractors = (
        coverage_context_result.get("outputs", {})
        .get("topic_analysis", {})
        .get("analise_assuntos_detratores", [])
    )

    vehicle_summary = (
        coverage_context_result.get("outputs", {})
        .get("vehicle_analysis", {})
        .get("resumo_geral", "")
    )

    vehicle_details = (
        coverage_context_result.get("outputs", {})
        .get("vehicle_analysis", {})
        .get("analise_por_veiculo", [])
    )

    business_context = contexto_negocios.get("contexto", {}).get("content", "")

    retry_instruction = ""
    if previous_error:
        retry_instruction = f"""
ATENÇÃO: na tentativa anterior, sua resposta falhou nesta validação:
{previous_error}

Agora responda corretamente.
"""

    system_prompt = f"""
Você é um analista sênior de reputação e mídia, especializado em transformar dados de cobertura em insights estratégicos para reuniões com clientes.

Sua tarefa é cruzar:
- highlights quantitativos
- contexto qualitativo da cobertura
- leitura editorial da exposição
- contexto de negócios da empresa

Regras obrigatórias:
1. Não invente fatos.
2. Não repita apenas os dados; interprete-os.
3. Sempre explique dinâmica reputacional, vetores de sustentação e vetores de risco.
4. O contexto de negócios deve calibrar a interpretação, mas não dominar a análise.
5. Seja executivo, claro e acionável.
6. Responda APENAS em JSON válido.
7. Não use markdown.
8. Não use comentários.
9. Todas as chaves e valores devem estar em português.
10. Todas as 4 chaves obrigatórias devem existir e seus valores devem ser strings.

JSON obrigatório:
{{
  "o_que_os_dados_nos_dizem": "...",
  "recomendacoes_de_atuacao": "...",
  "oportunidades_observadas": "...",
  "riscos_observados": "..."
}}
"""

    user_prompt = f"""
{retry_instruction}

EMPRESA: {company_name}
PERÍODO: {period_label}

NÚMEROS DO PERÍODO:
{json.dumps(big_number, ensure_ascii=False, indent=2, default=str)}

HIGHLIGHTS DE STATS:
{stats_text}

HIGHLIGHTS DE DAILY:
{daily_text}

HIGHLIGHTS DE TOPICS:
{topics_text}

HIGHLIGHTS DE SOURCES:
{sources_text}

SÍNTESE FINAL DA COBERTURA:
{json.dumps(final_synthesis, ensure_ascii=False, indent=2, default=str)}

RESUMO DIÁRIO:
{day_summary}

DETALHE POR DIA:
{json.dumps(day_details, ensure_ascii=False, indent=2, default=str)}

RESUMO DE ASSUNTOS:
{topic_summary}

ASSUNTOS PROMOTORES:
{json.dumps(topic_promoters, ensure_ascii=False, indent=2, default=str)}

ASSUNTOS DETRATORES:
{json.dumps(topic_detractors, ensure_ascii=False, indent=2, default=str)}

RESUMO DOS VEÍCULOS:
{vehicle_summary}

DETALHE POR VEÍCULO:
{json.dumps(vehicle_details, ensure_ascii=False, indent=2, default=str)}

CONTEXTO DE NEGÓCIOS:
{business_context}

INSTRUÇÕES DE ANÁLISE:
1. Compare os highlights com o contexto da cobertura.
2. Identifique consistências, tensões e padrões recorrentes.
3. Distinga o que é:
   - sustentação de imagem
   - pressão reputacional
   - escala sem ganho real de percepção
4. Em "o_que_os_dados_nos_dizem", faça uma síntese executiva da dinâmica de exposição da marca no período.
5. Em "recomendacoes_de_atuacao", proponha ações práticas de comunicação.
6. Em "oportunidades_observadas", destaque alavancas positivas que podem ser ampliadas.
7. Em "riscos_observados", destaque temas, veículos, enquadramentos ou padrões que podem deteriorar a imagem.

LEMBRETE CRÍTICO:
Responda APENAS com JSON válido, sem explicações fora do JSON.
"""

    return system_prompt, user_prompt


def generate_coverage_insights_llm(
    company_name: str,
    period_label: str,
    big_number: Dict[str, Any],
    highlight_infos: Dict[str, Any],
    coverage_context_result: Dict[str, Any],
    contexto_negocios: Dict[str, Any],
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    max_retries: int = 3,
) -> Dict[str, str]:
    """
    Gera insights executivos em JSON validado.

    Retorno:
    {
        "o_que_os_dados_nos_dizem": str,
        "recomendacoes_de_atuacao": str,
        "oportunidades_observadas": str,
        "riscos_observados": str
    }

    Lança ValueError se não conseguir obter uma saída válida após os retries.
    """

    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
    )

    last_error = None

    for attempt in range(1, max_retries + 1):
        system_prompt, user_prompt = _build_prompts(
            company_name=company_name,
            period_label=period_label,
            big_number=big_number,
            highlight_infos=highlight_infos,
            coverage_context_result=coverage_context_result,
            contexto_negocios=contexto_negocios,
            previous_error=last_error,
        )

        try:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])

            raw_text = response.content if hasattr(response, "content") else str(response)

            json_text = _extract_json_from_text(raw_text)
            parsed = json.loads(json_text)
            parsed = _normalize_output_keys(parsed)

            is_valid, errors = _validate_output_dict(parsed)
            if is_valid:
                # Mantém apenas as chaves esperadas, na ordem desejada
                return {k: parsed[k] for k in EXPECTED_KEYS}

            last_error = "; ".join(errors)

        except Exception as e:
            last_error = f"Tentativa {attempt}: {type(e).__name__}: {str(e)}"

    raise ValueError(
        "Falha ao gerar JSON válido para os insights após "
        f"{max_retries} tentativas. Último erro: {last_error}"
    )