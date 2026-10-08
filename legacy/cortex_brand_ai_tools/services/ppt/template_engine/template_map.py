from __future__ import annotations

from services.ppt.template_engine.variable_map import TEMPLATE_VARIABLE_MAP


TEMPLATE_MAP = {
    template_name: config["slide_number"]
    for template_name, config in TEMPLATE_VARIABLE_MAP.items()
}


def get_slide_number_from_template_type(template_type: str) -> int:
    if template_type not in TEMPLATE_MAP:
        raise ValueError(
            f"template_type '{template_type}' não encontrado. "
            f"Opções disponíveis: {list(TEMPLATE_MAP.keys())}"
        )
    return TEMPLATE_MAP[template_type]