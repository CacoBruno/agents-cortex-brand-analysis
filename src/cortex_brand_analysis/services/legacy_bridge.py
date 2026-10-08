from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

import pandas as pd


class LegacyRuntimeUnavailable(RuntimeError):
    pass


LEGACY_GROUP_TOOLS: dict[str, set[str]] = {
    "platform": {
        "get_dataframe",
        "get_brand_info",
        "export_publications_database",
        "export_media_analysis_database",
        "export_action_database",
        "get_prdata_dataframe",
        "get_prdata_opensource",
        "get_mss_dataframe",
    },
    "measurements": {
        "sentiment_classification",
        "protagonism_classification",
        "clustering_to_classification",
        "identify_entities_in_dataframe",
        "thems_classification",
    },
    "index": {
        "gen_dataviews",
        "calc_nps_score",
        "nps_total_and_contrib",
        "protagonism_score",
        "freq_score",
        "valoration_score",
        "jornalista_score",
        "action_score",
    },
    "context": {
        "extrair_contexto_noticias",
        "build_main_days_coverage",
        "build_top_vehicles_coverage",
        "build_specific_topics_reports",
        "build_coverage_summary",
    },
    "pattern": {
        "build_media_metrics_view",
        "build_media_metrics_view_by_source",
        "build_topic_contrib_df",
        "build_topic_contrib_llm_dict",
        "build_last_period_statistics",
        "build_company_big_number_dict",
        "build_sources_last_period_multi_company_dict_enriched",
        "build_daily_metrics_enriched",
        "build_daily_pattern_dict",
    },
    "insights": {
        "insights_orchestrator_analysis_media",
        "insights_orchestrator_with_whatsapp",
        "generate_company_context",
        "generate_coverage_insights",
    },
    "visualization": {"generate_chart"},
    "highlights": {"generate_highlights_tool"},
}


def legacy_root() -> Path:
    root = Path(__file__).resolve().parents[3] / "legacy" / "cortex_brand_ai_tools"
    if not root.exists():
        raise LegacyRuntimeUnavailable(
            "legacy/cortex_brand_ai_tools is not available in this checkout"
        )
    return root


def ensure_legacy_on_path() -> Path:
    root = legacy_root()
    value = str(root)
    if value not in sys.path:
        sys.path.insert(0, value)
    return root


def save_input_dataframe(data: list[dict]) -> str:
    ensure_legacy_on_path()
    module = importlib.import_module("core.dataframe_store")
    frame = pd.DataFrame(data)
    return module.save_dataframe(
        frame,
        source="v2_compat_request",
        filters={"origin": "compatibility_bridge"},
    )


def _registry_tools(group: str) -> list[Any]:
    ensure_legacy_on_path()
    registry = importlib.import_module("src.mcp_server.registry")
    return registry.get_langchain_tools(groups=[group])


def _special_tools(group: str) -> list[Any]:
    ensure_legacy_on_path()
    if group == "visualization":
        module = importlib.import_module("src.tools_agents.visualization.charts.tools")
        return [module.generate_chart_tool]
    if group == "highlights":
        module = importlib.import_module("src.tools_agents.highlights.tools")
        return [module.generate_highlights_tool]
    return []


def load_tool(group: str, tool_name: str) -> Any:
    allowed = LEGACY_GROUP_TOOLS.get(group, set())
    if tool_name not in allowed:
        raise ValueError(f"tool not allowed for group '{group}': {tool_name}")

    tools = (
        _special_tools(group)
        if group in {"visualization", "highlights"}
        else _registry_tools(group)
    )
    for tool in tools:
        if getattr(tool, "name", None) == tool_name:
            return tool
        if getattr(tool, "__name__", None) == tool_name:
            return tool

    available = sorted(
        {
            getattr(tool, "name", getattr(tool, "__name__", "unknown"))
            for tool in tools
        }
    )
    raise LegacyRuntimeUnavailable(
        f"tool '{tool_name}' was not loaded; available tools: {available}"
    )


def invoke_tool(
    group: str,
    tool_name: str,
    arguments: dict[str, object],
    data: list[dict] | None = None,
) -> Any:
    args = dict(arguments)
    if data is not None and "dataframe_id" not in args:
        args["dataframe_id"] = save_input_dataframe(data)

    tool = load_tool(group, tool_name)
    if hasattr(tool, "invoke"):
        return tool.invoke(args)
    return tool(**args)
