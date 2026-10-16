from __future__ import annotations

import re
from typing import Any, Dict


GENERIC_TERMS = [
    "alto",
    "alta",
    "baixo",
    "baixa",
    "relevante",
    "forte",
    "impactante",
    "importante",
    "significativo",
    "crescimento",
    "queda",
    "oscilação",
    "movimento",
]

CAUSALITY_TERMS = [
    "porque",
    "devido",
    "puxado",
    "impulsionado",
    "pressionado",
    "explicado",
    "provocado",
    "em função",
    "por conta",
]

TIME_TERMS = [
    "dia",
    "semana",
    "mês",
    "período",
    "segunda",
    "terça",
    "quarta",
    "quinta",
    "sexta",
    "sábado",
    "domingo",
]

CONTEXT_TERMS = [
    "tema",
    "cobertura",
    "notícia",
    "notícias",
    "veículo",
    "veículos",
    "fonte",
    "fontes",
    "matéria",
    "matérias",
    "abordagem",
]


def has_number(text: str) -> bool:
    return bool(re.search(r"\d", text or ""))


def has_percentage(text: str) -> bool:
    return "%" in (text or "")


def has_causality(text: str) -> bool:
    text_lower = (text or "").lower()
    return any(term in text_lower for term in CAUSALITY_TERMS)


def has_time_reference(text: str) -> bool:
    text_lower = (text or "").lower()
    return any(term in text_lower for term in TIME_TERMS)


def has_context(text: str) -> bool:
    text_lower = (text or "").lower()
    return any(term in text_lower for term in CONTEXT_TERMS)


def generic_penalty(text: str) -> float:
    text_lower = (text or "").lower()
    count = sum(1 for term in GENERIC_TERMS if term in text_lower)
    return min(count * 0.05, 0.30)


def score_insight(text: str) -> float:
    score = 0.0

    if has_number(text) or has_percentage(text):
        score += 0.25

    if has_causality(text):
        score += 0.25

    if has_time_reference(text):
        score += 0.20

    if has_context(text):
        score += 0.20

    penalty = generic_penalty(text)
    final_score = max(score - penalty, 0.0)

    return round(min(final_score, 1.0), 2)


def evaluate_output(output_json: Dict[str, Any]) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    for slide_name, content in output_json.items():
        if not isinstance(content, dict):
            continue

        insights = content.get("insights", [])
        scores = [score_insight(insight) for insight in insights]

        results[slide_name] = {
            "scores": scores,
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        }

    return results