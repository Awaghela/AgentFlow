"""
Central tool registry.

Every tool the agent can call is registered here with a name, callable,
and a JSON-schema-ish argument spec (used both for LLM tool-use prompting
in live mode and for validating simulated tool calls in the eval harness).
`invoke_tool` wraps every call with timing and uniform error handling so
`AgentStep`/`ToolCall` trace records look the same regardless of which
tool ran.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from app.tools.calculator import calculate_refund
from app.tools.crm import crm_lookup
from app.tools.knowledge_search import knowledge_search
from app.tools.ticketing import create_ticket


@dataclass
class ToolSpec:
    name: str
    description: str
    fn: Callable[..., dict]


REGISTRY: dict[str, ToolSpec] = {
    "crm_lookup": ToolSpec(
        name="crm_lookup",
        description="Look up account plan, ARR, renewal date, and open tickets by account_id.",
        fn=crm_lookup,
    ),
    "calculate_refund": ToolSpec(
        name="calculate_refund",
        description="Compute a prorated refund given monthly price and days used.",
        fn=calculate_refund,
    ),
    "knowledge_search": ToolSpec(
        name="knowledge_search",
        description="Search internal policy and product docs for relevant context.",
        fn=knowledge_search,
    ),
    "create_ticket": ToolSpec(
        name="create_ticket",
        description="Open a support ticket with a given priority.",
        fn=create_ticket,
    ),
}


@dataclass
class ToolInvocationResult:
    tool_name: str
    arguments: dict[str, Any]
    success: bool
    result: Any = None
    error: str | None = None
    latency_ms: float = 0.0


def invoke_tool(tool_name: str, arguments: dict[str, Any]) -> ToolInvocationResult:
    started = time.perf_counter()
    spec = REGISTRY.get(tool_name)

    if spec is None:
        elapsed = (time.perf_counter() - started) * 1000
        return ToolInvocationResult(
            tool_name=tool_name,
            arguments=arguments,
            success=False,
            error=f"unknown tool '{tool_name}'",
            latency_ms=elapsed,
        )

    try:
        result = spec.fn(**arguments)
        elapsed = (time.perf_counter() - started) * 1000
        return ToolInvocationResult(
            tool_name=tool_name, arguments=arguments, success=True, result=result, latency_ms=elapsed
        )
    except Exception as exc:  # noqa: BLE001 - deliberately broad, this is a trace boundary
        elapsed = (time.perf_counter() - started) * 1000
        return ToolInvocationResult(
            tool_name=tool_name,
            arguments=arguments,
            success=False,
            error=str(exc),
            latency_ms=elapsed,
        )
