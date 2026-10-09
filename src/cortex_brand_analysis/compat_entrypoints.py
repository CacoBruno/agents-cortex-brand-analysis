from __future__ import annotations

import importlib
import runpy

from cortex_brand_analysis.services.legacy_bridge import ensure_legacy_on_path


def run_legacy_mcp() -> None:
    ensure_legacy_on_path()
    module = importlib.import_module("src.mcp_server.server")
    module.main()


def run_legacy_pria() -> None:
    ensure_legacy_on_path()
    runpy.run_module("src.agents.run_insights_agents", run_name="__main__")
