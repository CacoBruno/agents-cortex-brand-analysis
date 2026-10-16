from __future__ import annotations

from typing import Dict, Any

from services.ppt.template_engine.variable_map import TEMPLATE_VARIABLE_MAP


def resolve_named_overrides(
    template_type: str,
    named_overrides: Dict[str, dict],
    allow_fixed_override: bool = False,
) -> Dict[int, dict]:
    """
    Converte overrides semânticos em overrides por índice.

    Exemplo
    -------
    named_overrides = {
        "title": {"text": "Comparativo de performance"},
        "insight_1": {"text": "Texto insight 1"},
        "right_visual": {"image_path": "outputs/grafico_direita.png"},
    }

    ->

    {
        3: {"text": "Comparativo de performance"},
        4: {"text": "Texto insight 1"},
        0: {"image_path": "outputs/grafico_direita.png"},
    }
    """

    if template_type not in TEMPLATE_VARIABLE_MAP:
        raise ValueError(
            f"template_type '{template_type}' não encontrado no TEMPLATE_VARIABLE_MAP. "
            f"Opções disponíveis: {list(TEMPLATE_VARIABLE_MAP.keys())}"
        )

    template_config = TEMPLATE_VARIABLE_MAP[template_type]
    variables_map = template_config.get("variables", {})
    fixed_map = template_config.get("fixed", {})

    resolved: Dict[int, dict] = {}

    for semantic_name, override in named_overrides.items():
        if semantic_name in variables_map:
            element_index = variables_map[semantic_name]

        elif allow_fixed_override and semantic_name in fixed_map:
            element_index = fixed_map[semantic_name]

        else:
            allowed_names = list(variables_map.keys())
            if allow_fixed_override:
                allowed_names += list(fixed_map.keys())

            raise ValueError(
                f"Variável semântica '{semantic_name}' não encontrada "
                f"no template '{template_type}'. "
                f"Opções disponíveis: {allowed_names}"
            )

        if element_index in resolved:
            raise ValueError(
                f"Conflito ao resolver overrides: mais de uma variável "
                f"apontou para o mesmo element_index={element_index}."
            )

        resolved[element_index] = override

    return resolved