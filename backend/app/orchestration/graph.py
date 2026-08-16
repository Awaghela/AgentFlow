"""
Builds the AgentFlow LangGraph orchestration graph.

    plan → retrieve ─┬─(context found, no tools needed)──────────► validate
                      ├─(context found, tools needed)──► tools ──┬─► validate
                      └─(context missing)──► fallback ◄──────────┘ (tool failure)
                                                │
                                                ▼
                                             validate → respond → approval → END

`fallback` is a single degradation node reached either when retrieval
comes back empty or when a tool call fails after its retry budget — both
paths converge on "produce a clearly-flagged low-confidence draft and let
`approval` force a human review" rather than hard-failing the request.
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.orchestration.nodes import (
    approval_node,
    fallback_node,
    plan_node,
    respond_node,
    retrieve_node,
    route_after_retrieve,
    route_after_tools,
    tool_node,
    validate_node,
)
from app.orchestration.state import AgentState


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("tools", tool_node)
    graph.add_node("fallback", fallback_node)
    graph.add_node("validate", validate_node)
    graph.add_node("respond", respond_node)
    graph.add_node("approval", approval_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "retrieve")

    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {
            "validate": "validate",
            "tools": "tools",
            "fallback": "fallback",
            "tools_then_fallback_check": "tools",
        },
    )

    graph.add_conditional_edges(
        "tools",
        route_after_tools,
        {"validate": "validate", "fallback": "fallback"},
    )

    graph.add_edge("fallback", "validate")
    graph.add_edge("validate", "respond")
    graph.add_edge("respond", "approval")
    graph.add_edge("approval", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
