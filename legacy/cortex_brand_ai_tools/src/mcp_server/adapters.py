# src/mcp_server/adapters.py

# src/mcp_server/adapters.py

import traceback
import json


def build_mcp_tool_from_langchain(tool):

    def wrapper(input_data: dict):
        try:
            print(f"[MCP] Executando tool: {tool.name}")
            print(f"[MCP] Input recebido: {json.dumps(input_data, ensure_ascii=False)[:2000]}")

            result = tool.invoke(input_data)

            print(f"[MCP] Tool finalizada: {tool.name}")
            return result

        except Exception as e:
            print(f"[MCP][ERRO] Tool falhou: {tool.name}")
            traceback.print_exc()

            return {
                "status": "error",
                "tool": getattr(tool, "name", None),
                "error_type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
            }

    wrapper.__name__ = tool.name or tool.__name__
    wrapper.__doc__ = tool.description or tool.__doc__

    return wrapper