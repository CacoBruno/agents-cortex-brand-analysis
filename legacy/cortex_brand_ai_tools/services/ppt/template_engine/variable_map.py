from __future__ import annotations

TEMPLATE_VARIABLE_MAP = {
    "cover": {
        "slide_number": 1,
        "variables": {
            "title": 0,
            "subtitle": 1,
            "logo": 2,
        },
        "fixed": {},
    },

    "content_chart_big_numbers": {
        "slide_number": 2,
        "variables": {
            "main_chart": 0,
            "title": 3,
            "insight_1": 4,
            "insight_2": 5,
            "big_numbers_table": 8,
            "nps_scale": 9,
            "logo": 10,
            "big_numbers_title": 11,
        },
        "fixed": {
            "divider": 1,
            "top_header_shape": 2,
            "right_insight_tag": 6,
            "left_insight_tag": 7,
        },
    },

    "content_dual_visual": {
        "slide_number": 3,
        "variables": {
            "right_visual": 0,
            "title": 3,
            "insight_1": 4,
            "insight_2": 5,
            "logo": 8,
            "left_visual": 9,
        },
        "fixed": {
            "divider": 1,
            "top_header_shape": 2,
            "right_insight_tag": 6,
            "left_insight_tag": 7,
        },
    },

    "content_chart_with_highlight_panel_right": {
        "slide_number": 4,
        "variables": {
            "main_chart": 1,
            "title": 3,
            "chart_description": 4,
            "highlight_1": 5,
            "logo": 6,
        },
        "fixed": {
            "right_panel_background": 0,
            "top_header_shape": 2,
        },
    },

    "content_chart_with_highlight_panel_left": {
        "slide_number": 5,
        "variables": {
            "main_chart": 1,
            "title": 2,
            "chart_description": 3,
            "highlight_1": 4,
            "logo": 5,
        },
        "fixed": {
            "left_panel_background": 0,
        },
    },

    "content_chart_with_large_side_image": {
        "slide_number": 6,
        "variables": {
            "right_side_image": 1,
            "chart_description": 2,
            "main_chart": 3,
            "title": 4,
            "subtitle_or_section_label": 5,
            # Ajuste estes nomes/índices finais depois de inspecionar o restante do slide 6
            # no JSON completo, porque o trecho aberto veio truncado.
        },
        "fixed": {
            "right_panel_background": 0,
        },
    },

"content_insights": {
    "slide_number": 7,
    "variables": {
        "title": 0,
        "subtitle": 1,
        "header_note": 2,
        "logo": 3,

        "insight_1": 4,
        "insight_2": 5,
        "insight_3": 7,

        "recommendation_1": 8,
        "recommendation_2": 6,
        "recommendation_3": 9,
    },
    "fixed": {
        "divider_1": 10,
        "divider_2": 11,
        "divider_3": 12,

        "recommendation_icon_1": 13,
        "recommendation_icon_2": 14,
        "recommendation_icon_3": 15,

        "insight_icon_1": 16,
        "insight_icon_2": 17,
        "insight_icon_3": 18,
    },
},

    "transition": {
        "slide_number": 8,
        "variables": {
            "transition_title": 1,
        },
        "fixed": {
            "background_visual": 0,
        },
    },

    "closing": {
        "slide_number": 9,
        "variables": {
            "logo": 0,
            "signature_block": 1,
            "website": 2,
        },
        "fixed": {},
    },
}