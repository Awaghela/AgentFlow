from __future__ import annotations

import time

from app.orchestration.graph import get_graph
from app.orchestration.state import AgentState, ForcedFault


def execute_workflow(
    request_text: str,
    requester: str = "demo-user",
    forced_fault: ForcedFault | None = None,
) -> tuple[AgentState, float]:
    """Runs the full LangGraph pipeline once and returns (final_state, total_latency_ms)."""
    graph = get_graph()

    initial_state: AgentState = {
        "request_text": request_text,
        "requester": requester,
        "forced_fault": forced_fault or {},
        "trace": [],
        "fallback_count": 0,
        "fallback_reasons": [],
    }

    started = time.perf_counter()
    final_state = graph.invoke(initial_state)
    total_latency_ms = (time.perf_counter() - started) * 1000

    return final_state, total_latency_ms
