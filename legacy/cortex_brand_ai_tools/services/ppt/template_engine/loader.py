from __future__ import annotations

import json
from copy import deepcopy
from json import JSONDecoder
import json
from json import JSONDecoder
from typing import Any, Union, List
from pathlib import Path
from typing import Dict, Any, List


def load_template_file(filepath: str, *, allow_multiple: bool = True) -> Union[Any, List[Any]]:
    """
    Lê um arquivo JSON.
    - Caso o arquivo contenha múltiplos objetos JSON concatenados (ex: '}{'),
      e allow_multiple=True, retorna uma LISTA com todos os objetos encontrados.
    - Caso contrário, retorna o objeto único (dict/list).

    Levanta ValueError com mensagem amigável em caso de erro.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        # Se não for "extra data", é JSON realmente inválido
        if (not allow_multiple) or (e.msg != "Extra data"):
            raise ValueError(f"Erro ao decodificar JSON em '{filepath}': {e}") from e

        # Fallback: arquivo tem mais de um JSON concatenado
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = f.read()

            dec = JSONDecoder()
            i = 0
            n = len(raw)
            objs: List[Any] = []

            while True:
                # pula espaços/brancos entre objetos
                while i < n and raw[i].isspace():
                    i += 1
                if i >= n:
                    break

                obj, end = dec.raw_decode(raw, i)
                objs.append(obj)
                i = end

            if not objs:
                raise ValueError("Arquivo vazio ou sem JSON válido.")
            return objs

        except Exception as e2:
            raise ValueError(
                f"Falha ao ler múltiplos JSONs concatenados em '{filepath}': {e2}"
            ) from e2



def build_slide_index(template_data: dict) -> Dict[int, dict]:
    slides = template_data.get("slides", [])
    return {
        slide["slide_number"]: deepcopy(slide)
        for slide in slides
    }