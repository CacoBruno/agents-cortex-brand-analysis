from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from cortex_brand_analysis.domain.nlp import NlpRequest
from cortex_brand_analysis.mcp.tools import run_nlp

mcp = FastMCP(
    name="Cortex Brand Analysis",
    instructions=(
        "Use typed Cortex Brand Analysis tools. "
        "Do not infer arbitrary Python, shell, filesystem, or network execution."
    ),
)


@mcp.tool(
    name="nlp_run",
    description=(
        "Run one native Cortex NLP operation: sentiment, protagonism, entities, "
        "themes, or clustering. The request is validated before execution."
    ),
)
def nlp_run(request: NlpRequest) -> dict[str, Any]:
    return run_nlp(request)


def main() -> None:
    """Run the native MCP server over STDIO."""
    mcp.run()


if __name__ == "__main__":
    main()
