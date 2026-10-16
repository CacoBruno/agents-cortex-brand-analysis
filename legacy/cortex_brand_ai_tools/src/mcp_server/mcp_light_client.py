# mcp_light_client.py

import json
import requests
from typing import Any


class MCPLightClient:
    def __init__(self, url: str = "http://localhost:8000/mcp", timeout: int = 120):
        self.url = url
        self.timeout = timeout
        self.session_id = None

        self.base_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

    def _headers(self) -> dict:
        headers = dict(self.base_headers)

        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        return headers

    def _parse_sse_response(self, resp: requests.Response) -> list[dict]:
        """
        Lê resposta SSE do FastMCP:
        linhas no formato:
        data: {...}
        """
        messages = []

        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue

            # debug opcional
            # print("RAW:", line)

            if line.startswith("data: "):
                data_str = line[6:]

                if data_str == "[DONE]":
                    break

                try:
                    msg = json.loads(data_str)
                    messages.append(msg)
                except json.JSONDecodeError:
                    messages.append({
                        "raw": data_str,
                        "parse_error": True,
                    })

        return messages

    def _request(self, payload: dict) -> dict:
        resp = requests.post(
            self.url,
            headers=self._headers(),
            json=payload,
            stream=True,
            timeout=self.timeout,
        )

        if resp.status_code >= 400:
            raise RuntimeError(
                f"Erro HTTP {resp.status_code}: {resp.text}"
            )

        # captura session id se vier no header
        new_session_id = resp.headers.get("mcp-session-id")
        if new_session_id:
            self.session_id = new_session_id

        messages = self._parse_sse_response(resp)

        if not messages:
            return {}

        # procura resposta JSON-RPC principal
        for msg in messages:
            if "result" in msg or "error" in msg:
                return msg

        return messages[-1]

    def initialize(self) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "python-mcp-light-client",
                    "version": "1.0.0",
                },
            },
        }

        result = self._request(payload)

        # Alguns servidores esperam initialized depois do initialize
        self.initialized_notification()

        return result

    def initialized_notification(self) -> None:
        payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }

        requests.post(
            self.url,
            headers=self._headers(),
            json=payload,
            stream=True,
            timeout=self.timeout,
        )

    def list_tools(self) -> list[dict]:
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        msg = self._request(payload)

        if "error" in msg:
            raise RuntimeError(msg["error"])

        return msg.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """
        Chama uma tool MCP.

        Como seu adapter cria wrapper(input_data: dict),
        o argumento precisa ir dentro de input_data.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": {
                    "input_data": arguments
                },
            },
        }

        msg = self._request(payload)

        if "error" in msg:
            raise RuntimeError(msg["error"])

        return msg.get("result")