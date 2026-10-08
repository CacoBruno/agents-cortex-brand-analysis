from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re


def _safe_get(data: dict, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _format_impact_millions(value: Any, decimals: int = 1) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "N/D"

    millions = num / 1_000_000
    text = f"{millions:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} M"


def _format_int_ptbr(value: Any) -> str:
    try:
        num = int(round(float(value)))
    except (TypeError, ValueError):
        return "N/D"

    return f"{num:,}".replace(",", ".")


def _normalize_percent_str(value: Any) -> str:
    if value is None:
        return "N/D"

    if isinstance(value, str):
        text = value.strip().replace(" ", "")
        if text.endswith("%"):
            raw = text[:-1].replace(",", ".")
            try:
                num = float(raw)
            except ValueError:
                return value.strip().replace(".", ",")
            return f"{num:.2f}".replace(".", ",") + "%"

        try:
            num = float(text.replace(",", "."))
        except ValueError:
            return value
    else:
        try:
            num = float(value)
        except (TypeError, ValueError):
            return "N/D"

    if abs(num) <= 1:
        num *= 100

    return f"{num:.2f}".replace(".", ",") + "%"


def _build_big_numbers_block(big_number: dict) -> dict[str, str]:
    return {
        "NPS": _normalize_percent_str(big_number.get("NPS")),
        "Protagonismo": _normalize_percent_str(big_number.get("Protagonismo")),
        "Impacto Promotor": _format_impact_millions(big_number.get("Impacto Promotor")),
        "Impacto Inócuo": _format_impact_millions(big_number.get("Impacto Inócuo")),
        "Impacto Detrator": _format_impact_millions(big_number.get("Impacto Detrator")),
        "Impacto Total": _format_impact_millions(big_number.get("Impacto Total")),
        "Publicações Promotoras": _format_int_ptbr(big_number.get("Publicações Promotoras")),
        "Publicações Inócuas": _format_int_ptbr(big_number.get("Publicações Inócuas")),
        "Publicações Detratoras": _format_int_ptbr(big_number.get("Publicações Detratoras")),
        "Publicações Totais": _format_int_ptbr(big_number.get("Publicações Totais")),
    }


def _infer_meeting_tone(
    big_number: dict,
    insights: dict | None = None,
    coverage_context_result: dict | None = None,
) -> str:
    def parse_percent(v: Any) -> float:
        if v is None:
            return 0.0

        if isinstance(v, str):
            t = v.strip().replace("%", "").replace(",", ".")
            try:
                x = float(t)
            except ValueError:
                return 0.0
        else:
            try:
                x = float(v)
            except (TypeError, ValueError):
                return 0.0

        if abs(x) <= 1:
            x *= 100

        return x

    nps = parse_percent(big_number.get("NPS", 0))
    prot = parse_percent(big_number.get("Protagonismo", 0))

    riscos = []
    if isinstance(insights, dict):
        riscos = insights.get("riscos_observados") or insights.get("riscos") or []

    pressao = _safe_get(
        coverage_context_result or {},
        ["outputs", "final_synthesis", "final_synthesis", "vetores_que_pressionaram"],
        [],
    )

    risk_count = len(riscos) if isinstance(riscos, list) else (1 if riscos else 0)
    pressure_count = len(pressao) if isinstance(pressao, list) else (1 if pressao else 0)

    if nps < 0:
        return "crise"
    if nps < 35 or risk_count >= 4 or pressure_count >= 4:
        return "cautela"
    if nps < 50 or prot < 50 or risk_count >= 2 or pressure_count >= 2:
        return "atenção"

    return "otimista"


def _clean_markdown_text(text: Any) -> str:
    if text is None:
        return ""

    text = str(text).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def build_meeting_script_prompt(
    company_name: str,
    analysis_period: str,
    big_number: dict,
    highlight_infos: dict,
    coverage_context_result: dict,
    insights: dict,
    contexto_negocios: dict,
) -> str:
    big_numbers_fmt = _build_big_numbers_block(big_number)

    tone = _infer_meeting_tone(
        big_number=big_number,
        insights=insights,
        coverage_context_result=coverage_context_result,
    )

    highlight_synthesis = _safe_get(
        highlight_infos,
        ["final_synthesis", "synthesis_text"],
        "",
    )

    coverage_final = _safe_get(
        coverage_context_result,
        ["outputs", "final_synthesis", "final_synthesis"],
        {},
    ) or {}

    business_context = _safe_get(
        contexto_negocios,
        ["contexto", "content"],
        "",
    )

    payload = {
        "empresa": company_name,
        "periodo_analise": analysis_period,
        "tom_sugerido_para_reuniao": tone,
        "big_numbers_formatados": big_numbers_fmt,
        "sintese_highlights": highlight_synthesis,
        "contexto_cobertura": coverage_final,
        "insights": insights,
        "contexto_negocios": business_context,
    }

    system_prompt = """
Você é um analista sênior de comunicação e reputação, especializado em conduzir reuniões executivas de insights com clientes.

Sua tarefa é transformar dados de exposição de marca na mídia em um SCRIPT DE REUNIÃO.

Retorne um JSON válido com as chaves exatamente abaixo:

{
  "tom_da_reuniao": "string",
  "mensagem_central_para_o_cliente": "string",
  "script_reuniao": {
    "abertura": "string",
    "big_numbers": "string",
    "leitura_dos_highlights": "string",
    "leitura_do_contexto_da_cobertura": "string",
    "o_que_os_dados_nos_dizem": "string",
    "recomendacoes_de_atuacao": "string",
    "oportunidades_observadas": "string",
    "riscos_observados": "string",
    "conexao_com_contexto_de_negocio": "string",
    "fechamento": "string"
  },
  "pontos_narrativos": [
    "string 1",
    "string 2",
    "string 3"
  ]
}

Regras:
- Escreva em português do Brasil.
- Não invente fatos.
- Use apenas as evidências fornecidas.
- Priorize NPS e Protagonismo.
- Diferencie o que sustentou imagem, o que pressionou imagem e o que só deu escala.
- Escreva como roteiro falado para uma reunião executiva.
- Não use bullets dentro das strings.
""".strip()

    user_prompt = (
        "DADOS PARA GERAR O SCRIPT DE REUNIÃO:\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )

    return system_prompt + "\n\n" + user_prompt


def generate_meeting_script_with_llm(
    company_name: str,
    analysis_period: str,
    big_number: dict,
    highlight_infos: dict,
    coverage_context_result: dict,
    insights: dict,
    contexto_negocios: dict,
    *,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
) -> dict:
    from langchain_openai import ChatOpenAI

    prompt = build_meeting_script_prompt(
        company_name=company_name,
        analysis_period=analysis_period,
        big_number=big_number,
        highlight_infos=highlight_infos,
        coverage_context_result=coverage_context_result,
        insights=insights,
        contexto_negocios=contexto_negocios,
    )

    llm = ChatOpenAI(model=model, temperature=temperature)
    response = llm.invoke(prompt)

    content = response.content if hasattr(response, "content") else str(response)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {
            "raw_output": content,
            "parse_error": "A resposta do LLM não veio em JSON válido.",
        }

    return {
        "meta": {
            "company_name": company_name,
            "analysis_period": analysis_period,
            "model": model,
            "temperature": temperature,
        },
        "prompt": prompt,
        "llm_output": parsed,
        "raw_text": content,
    }


def render_meeting_script_markdown(script_result: dict) -> str:
    llm_output = script_result.get("llm_output", {})

    tom = llm_output.get("tom_da_reuniao", "")
    msg_central = llm_output.get("mensagem_central_para_o_cliente", "")
    script = llm_output.get("script_reuniao", {}) or {}
    pontos = llm_output.get("pontos_narrativos", []) or []
    meta = script_result.get("meta", {}) or {}

    md = f"""# Script de Reunião de Insights

**Empresa:** {meta.get("company_name", "")}  
**Período:** {meta.get("analysis_period", "")}  
**Tom sugerido da reunião:** {tom}

## Mensagem central para o cliente
{_clean_markdown_text(msg_central)}

## 1. Abertura
{_clean_markdown_text(script.get("abertura", ""))}

## 2. Big Numbers
{_clean_markdown_text(script.get("big_numbers", ""))}

## 3. Leitura dos Highlights
{_clean_markdown_text(script.get("leitura_dos_highlights", ""))}

## 4. Leitura do Contexto da Cobertura
{_clean_markdown_text(script.get("leitura_do_contexto_da_cobertura", ""))}

## 5. O que os dados nos dizem
{_clean_markdown_text(script.get("o_que_os_dados_nos_dizem", ""))}

## 6. Recomendações de atuação
{_clean_markdown_text(script.get("recomendacoes_de_atuacao", ""))}

## 7. Oportunidades observadas
{_clean_markdown_text(script.get("oportunidades_observadas", ""))}

## 8. Riscos observados
{_clean_markdown_text(script.get("riscos_observados", ""))}

## 9. Conexão com o contexto de negócio
{_clean_markdown_text(script.get("conexao_com_contexto_de_negocio", ""))}

## 10. Fechamento
{_clean_markdown_text(script.get("fechamento", ""))}

## Pontos narrativos de apoio
"""

    for item in pontos:
        md += f"- {item}\n"

    return md.strip() + "\n"


def save_meeting_script_files(
    script_result: dict,
    output_dir: str | Path = ".",
    base_filename: str = "script_reuniao_insights",
) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"{base_filename}.json"
    md_path = output_dir / f"{base_filename}.md"

    json_path.write_text(
        json.dumps(script_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_path.write_text(
        render_meeting_script_markdown(script_result),
        encoding="utf-8",
    )

    return {
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }