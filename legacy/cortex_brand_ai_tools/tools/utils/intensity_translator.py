from __future__ import annotations

from typing import Any, Dict


def classify_intensity(z_score: float | None) -> Dict[str, str]:
    """
    Traduz z-score para linguagem executiva.
    """
    if z_score is None:
        return {
            "level": "neutro",
            "label": "em linha com o comportamento habitual",
        }

    z_abs = abs(z_score)

    if z_abs < 0.5:
        return {
            "level": "neutro",
            "label": "em linha com o comportamento habitual",
        }
    if z_abs < 1.0:
        return {
            "level": "leve",
            "label": "com leve afastamento do comportamento habitual",
        }
    if z_abs < 2.0:
        return {
            "level": "moderado",
            "label": "com desvio perceptível em relação ao padrão recente",
        }
    return {
        "level": "forte",
        "label": "claramente fora do padrão recente",
    }


def direction_label(value: float | None) -> str:
    if value is None:
        return "em linha com"
    if value > 0:
        return "acima de"
    if value < 0:
        return "abaixo de"
    return "em linha com"


def enrich_intensity(analysis: Dict[str, Any]) -> Dict[str, Any]:
    weekly_variation = analysis.get("weekly_variation", {})
    z_scores = analysis.get("z_scores", {})

    intensity: Dict[str, Dict[str, str]] = {}

    for metric, z_value in z_scores.items():
        translated = classify_intensity(z_value)
        direction = direction_label(weekly_variation.get(metric, 0))

        intensity[metric] = {
            "intensity_level": translated["level"],
            "intensity_label": translated["label"],
            "direction": direction,
        }

    analysis["intensity"] = intensity
    return analysis