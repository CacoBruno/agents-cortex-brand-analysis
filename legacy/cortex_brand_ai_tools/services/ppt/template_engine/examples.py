from __future__ import annotations

from services.ppt.template_engine.loader import load_template_file
from services.ppt.template_engine.build_slide_from_named_overrides import (
    build_slide_from_named_overrides,
)



def build_example_slides(template_path: str = "template_cortex.json") -> dict:
    """
    Gera exemplos de uso para todos os tipos de slide do template,
    já no formato final esperado pelo construtor de PPT.
    """

    template_data = load_template_file(template_path)

    # =========================
    # SLIDES
    # =========================

    slide_cover = build_slide_from_named_overrides(
        template_data=template_data,
        template_type="cover",
        target_slide_number=1,
        named_overrides={
            "title": {"text": "Relatório de Reputação"},
            "subtitle": {"text": "Análise de mídia • Março 2026"},
        },
    )

    slide_transition = build_slide_from_named_overrides(
        template_data=template_data,
        template_type="transition",
        target_slide_number=2,
        named_overrides={
            "transition_title": {"text": "Panorama Geral"},
        },
    )

    slide_big_numbers = build_slide_from_named_overrides(
        template_data=template_data,
        template_type="content_chart_big_numbers",
        target_slide_number=3,
        named_overrides={
            "main_chart": {"image_path": "outputs/chart_nps.png"},
            "title": {"text": "Desempenho reputacional no período"},
            "insight_1": {"text": "Crescimento de menções positivas."},
            "insight_2": {"text": "Detratores concentrados em poucos picos."},
            "big_numbers_title": {"text": "Big Numbers"},
            "big_numbers_table": {
                "cell_updates": [
                    {"row": 0, "col": 0, "text": "54,1%"},
                    {"row": 0, "col": 1, "text": "72%"},
                ]
            },
        },
    )

    slide_dual = build_slide_from_named_overrides(
        template_data=template_data,
        template_type="content_dual_visual",
        target_slide_number=4,
        named_overrides={
            "right_visual": {"image_path": "outputs/grafico_direita.png"},
            "left_visual": {"image_path": "outputs/grafico_esquerda.png"},
            "title": {"text": "Comparativo de performance"},
            "insight_1": {"text": "Concentração temática no lado esquerdo."},
            "insight_2": {"text": "Evolução temporal no lado direito."},
        },
    )

    slide_highlight = build_slide_from_named_overrides(
        template_data=template_data,
        template_type="content_chart_with_highlight_panel_right",
        target_slide_number=5,
        named_overrides={
            "main_chart": {"image_path": "outputs/chart.png"},
            "title": {"text": "Evolução do volume"},
            "highlight_1": {"text": "Pico impulsionado por crise reputacional."},
        },
    )

    slide_large_visual = build_slide_from_named_overrides(
        template_data=template_data,
        template_type="content_chart_with_large_side_image",
        target_slide_number=6,
        named_overrides={
            "main_chart": {"image_path": "outputs/chart_crise.png"},
            "right_side_image": {"image_path": "outputs/imagem.png"},
            "title": {"text": "Impacto da crise"},
        },
    )

    slide_insights = build_slide_from_named_overrides(
        template_data=template_data,
        template_type="content_insights",
        target_slide_number=7,
        named_overrides={
            "title": {"text": "Insights"},
            "subtitle": {"text": "Aprendizados e recomendações"},
            "insight_1": {"text": "Concentração de eventos críticos."},
            "insight_2": {"text": "Cobertura positiva institucional."},
            "insight_3": {"text": "Alto impacto em poucos temas."},
            "recommendation_1": {"text": "Reforçar mensagens-chave."},
            "recommendation_2": {"text": "Preparar gestão de crise."},
            "recommendation_3": {"text": "Explorar oportunidades."},
        },
    )

    slide_closing = build_slide_from_named_overrides(
        template_data=template_data,
        template_type="closing",
        target_slide_number=8,
        named_overrides={
            "logo": {"image_path": "outputs/logo_cliente.png"},
            "signature_block": {"text": "Relatório desenvolvido pela Cortex"},
            "website": {"text": "www.cortex-intelligence.com"},
        },
    )

    # =========================
    # ORDENAÇÃO FINAL
    # =========================

    slides = [
        slide_cover,
        slide_transition,
        slide_big_numbers,
        slide_dual,
        slide_highlight,
        slide_large_visual,
        slide_insights,
        slide_closing,
    ]

    # 🔥 IMPORTANTE: ordenar por slide_number
    slides = sorted(slides, key=lambda x: x["slide_number"])

    # =========================
    # OUTPUT FINAL
    # =========================

    return {
        "slide_width": 14630400,
        "slide_height": 8229600,
        "slides": slides,
    }


if __name__ == "__main__":
    presentation = build_example_slides("template_cortex.json")

    print("Estrutura final pronta para builder:")
    print(f"Slides: {len(presentation['slides'])}")