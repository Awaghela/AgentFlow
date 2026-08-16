"""
Shared state passed between LangGraph nodes.

`ForcedFault` lets the eval harness deterministically inject the exact
failure modes it needs to test (a tool timing out, retrieval coming back
empty, an unsafe draft slipping through, latency spikes) without any
special-casing in the nodes themselves — every node just checks
`state["forced_fault"]` the same way it would check a real failure signal.
"""
from __future__ import annotations

from typing import Any, Optional, TypedDict


class ForcedFault(TypedDict, total=False):
    missing_context: bool
    fail_tool: Optional[str]  # tool_name that should raise/timeout
    unsafe_output: bool
    latency_spike_ms: float
    force_low_confidence: bool
    force_high_risk: bool


class TraceEvent(TypedDict):
    node_name: str
    status: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    latency_ms: float
    error: Optional[str]
    tool_calls: list[dict[str, Any]]
    retrieval: Optional[dict[str, Any]]


class AgentState(TypedDict, total=False):
    # inputs
    request_text: str
    requester: str
    forced_fault: ForcedFault

    # working state
    plan: list[dict[str, Any]]
    retrieval: Optional[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    validation: dict[str, Any]
    confidence: float
    risk_level: str
    requires_approval: bool
    approval_reason: Optional[str]
    final_output: Optional[str]
    status: str
    fallback_count: int
    fallback_reasons: list[str]
    error: Optional[str]

    # trace accumulation (consumed by the API layer to persist AgentStep rows)
    trace: list[TraceEvent]
