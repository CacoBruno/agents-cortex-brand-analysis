from __future__ import annotations

from typing import Dict, Optional

from services.ppt.template_engine.builder import build_slide_from_template
from services.ppt.template_engine.resolve_named_overrides import resolve_named_overrides


def build_slide_from_named_overrides(
    template_data: dict,
    template_type: str,
    named_overrides: Dict[str, dict],
    target_slide_number: Optional[int] = None,  # 👈 NOVO
    allow_fixed_override: bool = False,
) -> dict:
    """
    Cria um slide a partir de um template usando nomes semânticos,
    permitindo definir o slide_number final (ordem narrativa).

    Params
    ------
    template_type:
        Tipo de template (layout)
    target_slide_number:
        Número final do slide na apresentação (storytelling)
    """

    # 🔹 converte semantic → index
    element_overrides = resolve_named_overrides(
        template_type=template_type,
        named_overrides=named_overrides,
        allow_fixed_override=allow_fixed_override,
    )

    # 🔹 monta slide base
    slide_dict = build_slide_from_template(
        template_data=template_data,
        template_type=template_type,
        element_overrides=element_overrides,
    )

    # 🔥 AQUI está a mudança importante
    if target_slide_number is not None:
        slide_dict["slide_number"] = target_slide_number

    return slide_dict