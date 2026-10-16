# src/mcp_server/server.py

import traceback
from fastmcp import FastMCP

from src.mcp_server.adapters import build_mcp_tool_from_langchain
from src.mcp_server.registry import get_langchain_tools


mcp = FastMCP("brand-cortex-tools")


def register_tools(groups: list[str] | None = None):
    try:
        tools = get_langchain_tools(groups=groups)

        print(f">>> Total de tools carregadas: {len(tools)}")

        for tool in tools:
            try:
                print(f">>> Registrando tool: {tool.name}")

                mcp_tool = build_mcp_tool_from_langchain(tool)
                mcp.tool()(mcp_tool)

                print(f">>> OK: {tool.name}")

            except Exception:
                print(f">>> ERRO AO REGISTRAR TOOL: {getattr(tool, 'name', None)}")
                traceback.print_exc()

    except Exception:
        print(">>> ERRO AO CARREGAR TOOLS")
        traceback.print_exc()
        raise


def main():
    print(">>> Iniciando MCP Server")

    register_tools(groups=['platform', 'insights'] ) # ['platform'] 

    print(">>> Subindo servidor em http://0.0.0.0:8000/mcp")

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        path="/mcp",
    )


if __name__ == "__main__":
    main()