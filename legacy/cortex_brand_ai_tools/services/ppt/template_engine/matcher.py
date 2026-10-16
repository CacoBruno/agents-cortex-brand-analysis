from __future__ import annotations

from typing import Dict


DEFAULT_TEMPLATE_MAP: Dict[str, int] = {
    "cover": 1,
    "content_chart_big_numbers": 2,
    "content_dual_visual": 3,
    "content_chart_left_highlights_right": 4,
    "content_chart_right_highlights_left": 5,
    "content_large_visual_right": 6,
    "content_insights": 7,
    "transition": 8,
    "closing": 9,
}


def get_slide_number_from_template_type(
    template_type: str,
    template_map: Dict[str, int] | None = None,
) -> int:
    mapping = template_map or DEFAULT_TEMPLATE_MAP

    if template_type not in mapping:
        raise ValueError(
            f"template_type '{template_type}' não encontrado. "
            f"Opções: {list(mapping.keys())}"
        )

    return mapping[template_type]