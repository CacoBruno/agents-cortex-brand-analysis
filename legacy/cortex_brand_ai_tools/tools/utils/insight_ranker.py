from __future__ import annotations

from typing import Any, Dict, List

from tools.utils.insight_quality import score_insight


def rank_insights(output_json: Dict[str, Any]) -> Dict[str, Any]:
    ranked_output: Dict[str, Any] = {}

    for slide_name, content in output_json.items():
        title = content.get("title", "")
        insights = content.get("insights", [])

        scored: List[Dict[str, Any]] = []
        for insight in insights:
            scored.append(
                {
                    "text": insight,
                    "score": score_insight(insight),
                }
            )

        scored_sorted = sorted(scored, key=lambda x: x["score"], reverse=True)

        ranked_output[slide_name] = {
            "title": title,
            "insights": [item["text"] for item in scored_sorted],
            "scores": [item["score"] for item in scored_sorted],
        }

    return ranked_output