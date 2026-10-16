from services.output_configs.output_configs_insight_tools import OUTPUT_CONFIG


def _safe_get(d: dict, path: list, default=None):
    current = d
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def _first_available(result: dict, paths: list):
    for path in paths:
        value = _safe_get(result, path)
        if value is not None:
            return value
    return None


def _extract_client_answer(final_answer):
    """
    Extrai o conteúdo que deve ser mostrado ao cliente.
    Evita devolver prompt, meta e estruturas internas.
    """

    if not isinstance(final_answer, dict):
        return final_answer

    # Caso meeting_script:
    # final_answer = {"meta": ..., "prompt": ..., "llm_output": {...}}
    if final_answer.get("llm_output") is not None:
        return final_answer["llm_output"]

    # Caso insights:
    # final_answer = {"status": ..., "message": ..., "data": {...}}
    if final_answer.get("data") is not None:
        return final_answer["data"]

    # Caso WhatsApp:
    # pode vir como {"output": {"final_text": "..."}}
    whatsapp_text = _safe_get(final_answer, ["output", "final_text"])
    if whatsapp_text is not None:
        return whatsapp_text

    return final_answer


def format_orchestrator_output(
    result: dict,
    output_type: str,
    return_debug: bool = False,
) -> dict:
    config = OUTPUT_CONFIG.get(output_type, {})

    raw_final_answer = _first_available(
        result,
        config.get("final_paths", [["insights"]])
    )

    final_answer = _extract_client_answer(raw_final_answer)

    files = _first_available(
        result,
        config.get("file_paths", [])
    )

    output = {
        "status": "success",
        "output_type": output_type,

        # isso é o que o agente deve mostrar ao usuário
        "final_answer": final_answer,

        "files": files,
        "metadata": {
            "has_final_answer": final_answer is not None,
            "has_files": files is not None,
            "available_keys": list(result.keys()),
        }
    }

    if return_debug:
        output["debug"] = {
            "raw_final_answer_type": type(raw_final_answer).__name__,
            "raw_final_answer_keys": list(raw_final_answer.keys())
            if isinstance(raw_final_answer, dict)
            else None,
        }

    return output