from __future__ import annotations

from copy import deepcopy
from typing import Dict, Optional

from services.ppt.template_engine.template_map import get_slide_number_from_template_type
from services.ppt.template_engine.overrides import apply_element_override


def build_slide_from_template(
    template_data: dict,
    template_type: str | None = None,
    slide_number: int | None = None,
    element_overrides: Optional[Dict[int, dict]] = None,
    template_map: dict | None = None,
) -> dict:
    """
    Cria um novo slide a partir de um slide-template existente.

    Params
    ------
    template_data:
        JSON carregado do arquivo template.
    template_type:
        Nome do tipo de template, ex: 'cover', 'transition', etc.
    slide_number:
        Número do slide-template. Se informado, tem prioridade.
    element_overrides:
        Dict no formato:
        {
            0: {"text": "Novo título"},
            2: {"image_path": "outputs/chart.png"}
        }
    """

    slides = template_data.get("slides", [])

    if slide_number is None:
        if template_type is None:
            raise ValueError("Informe slide_number ou template_type.")
        slide_number = get_slide_number_from_template_type(template_type)

    base_slide = None
    for slide in slides:
        if slide["slide_number"] == slide_number:
            base_slide = deepcopy(slide)
            break

    if base_slide is None:
        raise ValueError(f"Slide template {slide_number} não encontrado.")

    overrides = element_overrides or {}

    for element_idx, override in overrides.items():
        if element_idx >= len(base_slide["elements"]):
            raise IndexError(
                f"element_idx {element_idx} fora do range. "
                f"Esse slide tem {len(base_slide['elements'])} elementos."
            )

        base_slide["elements"][element_idx] = apply_element_override(
            base_slide["elements"][element_idx],
            override,
        )

    return base_slide