from langgraph.graph import StateGraph, END

from src.tools_agents.insights_tools.state import CoverageGraphState
from src.tools_agents.insights_tools.nodes import (
    node_captura_dados,
    node_padrao_exposicao,
    node_contexto_exposicao,
    node_contexto_negocios,
    node_highlights,
    node_insights,
    node_whatsapp,
    node_meeting_insights,

)


def build_coverage_orchestrator_graph():
    builder = StateGraph(CoverageGraphState)

    builder.add_node("node_captura_dados", node_captura_dados)
    builder.add_node("node_padrao_exposicao", node_padrao_exposicao)
    builder.add_node("node_contexto_negocios", node_contexto_negocios)
    builder.add_node("node_highlights", node_highlights)
    builder.add_node("node_contexto_exposicao", node_contexto_exposicao)
    builder.add_node("node_insights", node_insights)

    builder.set_entry_point("node_captura_dados")

    builder.add_edge("node_captura_dados", "node_padrao_exposicao")
    builder.add_edge("node_captura_dados", "node_contexto_negocios")

    builder.add_edge("node_padrao_exposicao", "node_highlights")
    builder.add_edge("node_padrao_exposicao", "node_contexto_exposicao")

    builder.add_edge(
        [
            "node_highlights",
            "node_contexto_exposicao",
            "node_contexto_negocios",
        ],
        "node_insights",
    )

    builder.add_edge("node_insights", END)

    return builder.compile()



def build_coverage_orchestrator_graph_with_whatsapp():
    builder = StateGraph(CoverageGraphState)

    builder.add_node("node_captura_dados", node_captura_dados)
    builder.add_node("node_padrao_exposicao", node_padrao_exposicao)
    builder.add_node("node_contexto_exposicao", node_contexto_exposicao)
    builder.add_node("node_contexto_negocios", node_contexto_negocios)
    builder.add_node("node_highlights", node_highlights)
    builder.add_node("node_insights", node_insights)
    builder.add_node("node_whatsapp", node_whatsapp) 

    builder.set_entry_point("node_captura_dados")

    # início
    builder.add_edge("node_captura_dados", "node_padrao_exposicao")
    builder.add_edge("node_captura_dados", "node_contexto_negocios")

    # paralelos
    builder.add_edge("node_padrao_exposicao", "node_highlights")
    builder.add_edge("node_padrao_exposicao", "node_contexto_exposicao")

    # join → insights
    builder.add_edge(
        [
            "node_highlights",
            "node_contexto_exposicao",
            "node_contexto_negocios",
        ],
        "node_insights",
    )

    # 👇 novo fluxo
    builder.add_edge("node_insights", "node_whatsapp")

    builder.add_edge("node_whatsapp", END)

    return builder.compile()


def build_coverage_orchestrator_graph_with_meeting_insights():
    builder = StateGraph(CoverageGraphState)

    builder.add_node("node_captura_dados", node_captura_dados)
    builder.add_node("node_padrao_exposicao", node_padrao_exposicao)
    builder.add_node("node_contexto_exposicao", node_contexto_exposicao)
    builder.add_node("node_contexto_negocios", node_contexto_negocios)
    builder.add_node("node_highlights", node_highlights)
    builder.add_node("node_insights", node_insights)
    builder.add_node("node_meeting_insights", node_meeting_insights)
    
    builder.set_entry_point("node_captura_dados")

    builder.add_edge("node_captura_dados", "node_padrao_exposicao")
    builder.add_edge("node_captura_dados", "node_contexto_negocios")

    builder.add_edge("node_padrao_exposicao", "node_highlights")
    builder.add_edge("node_padrao_exposicao", "node_contexto_exposicao")

    builder.add_edge(
        [
            "node_highlights",
            "node_contexto_exposicao",
            "node_contexto_negocios",
        ],
        "node_insights",
    )

    builder.add_edge("node_insights", "node_meeting_insights")
    builder.add_edge("node_meeting_insights", END)

    return builder.compile()