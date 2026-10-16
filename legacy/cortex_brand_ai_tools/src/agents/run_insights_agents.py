from datetime import datetime
import os

from src.agents.agent_insights import agent_insights_brand
from langchain_core.messages import HumanMessage


def make_thread_id() -> str:
    """
    Cria um thread_id novo por execução do script.

    Por que isso é importante?
    - Quando uma tool longa é interrompida, o SqliteSaver pode salvar uma AIMessage
      com tool_calls sem a ToolMessage correspondente.
    - Se você reutilizar sempre o mesmo thread_id, o LangGraph tenta continuar a partir
      desse histórico incompleto e gera o erro:
      "Found AIMessages with tool_calls that do not have a corresponding ToolMessage".

    Se quiser retomar uma conversa específica, defina a variável de ambiente THREAD_ID.
    Exemplo PowerShell:
        $env:THREAD_ID="americanas_abril_2026_v2"
        python run_insights_agents.py
    """
    thread_id_env = os.getenv("THREAD_ID")
    if thread_id_env and thread_id_env.strip():
        return thread_id_env.strip()

    return f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


if __name__ == "__main__":

    def print_stream(stream):
        for s in stream:
            message = s["messages"][-1]
            message.pretty_print()

    thread_id = make_thread_id()
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\nSessão iniciada com thread_id: {thread_id}")
    print("Se uma execução longa for interrompida, rode o script novamente para criar um novo thread_id.")
    print("Para forçar um thread_id específico, defina a variável de ambiente THREAD_ID.\n")

    while True:
        entrada_escrita_usuario = input("\nEntrada Usuário (digite 'q' para parar.): ")

        if entrada_escrita_usuario.lower() == "q":
            break

        try:
            print_stream(
                agent_insights_brand.stream(
                    {"messages": [HumanMessage(content=entrada_escrita_usuario)]},
                    config=config,
                    stream_mode="values",
                )
            )
        except KeyboardInterrupt:
            print("\nExecução interrompida pelo usuário.")
            print("Atenção: este thread_id pode ter ficado com checkpoint incompleto.")
            print("Reinicie o script para gerar uma nova sessão segura.")
            break
        except ValueError as e:
            error_text = str(e)
            if "tool_calls" in error_text and "ToolMessage" in error_text:
                print("\nErro de checkpoint incompleto detectado.")
                print("Isso normalmente acontece quando uma tool longa foi interrompida no meio.")
                print("Solução: reinicie o script para gerar um novo thread_id automaticamente.")
                print(f"thread_id atual com problema: {thread_id}")
            else:
                raise
