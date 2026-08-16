"""
LangGraph node implementations.

Each node is a plain function `(AgentState) -> AgentState` that mutates a
copy of the state and appends one `TraceEvent` describing what it did.
The API layer later flattens `state["trace"]` into `AgentStep` (+ nested
`ToolCall` / `RetrievalTrace`) rows, so every field recorded here shows up
directly in the trace viewer and the audit log.
"""
from __future__ import annotations

import time
from typing import Any

from app.core.config import get_settings
from app.orchestration.llm import infer_tool_arguments, simulate_plan, simulate_response
from app.orchestration.state import AgentState
from app.rag.retriever import retrieve_context
from app.tools.registry import invoke_tool


def _record(
    state: AgentState,
    node_name: str,
    status: str,
    started: float,
    input_data: dict[str, Any],
    output_data: dict[str, Any],
    error: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    retrieval: dict[str, Any] | None = None,
) -> None:
    elapsed_ms = (time.perf_counter() - started) * 1000
    state.setdefault("trace", []).append(
        {
            "node_name": node_name,
            "status": status,
            "input_data": input_data,
            "output_data": output_data,
            "latency_ms": round(elapsed_ms, 2),
            "error": error,
            "tool_calls": tool_calls or [],
            "retrieval": retrieval,
        }
    )


def plan_node(state: AgentState) -> AgentState:
    started = time.perf_counter()
    settings = get_settings()
    request_text = state["request_text"]

    plan = simulate_plan(request_text, settings.MAX_PLAN_STEPS)
    state["plan"] = plan
    state["fallback_count"] = state.get("fallback_count", 0)
    state["fallback_reasons"] = state.get("fallback_reasons", [])
    state["status"] = "planning"

    _record(
        state,
        node_name="plan",
        status="success",
        started=started,
        input_data={"request_text": request_text},
        output_data={"plan": plan},
    )
    return state


def retrieve_node(state: AgentState) -> AgentState:
    started = time.perf_counter()
    fault = state.get("forced_fault", {}) or {}
    state["status"] = "retrieving"

    # Simulate a slow downstream dependency (vector DB, document store) for
    # latency-focused eval scenarios. Capped so the suite stays fast.
    spike_ms = fault.get("latency_spike_ms")
    if spike_ms:
        time.sleep(min(spike_ms, 500) / 1000)

    if fault.get("missing_context"):
        result = {
            "query": state["request_text"],
            "doc_ids": [],
            "snippets": [],
            "top_score": 0.0,
            "avg_score": 0.0,
            "num_results": 0,
            "reranked": False,
            "candidates_considered": 0,
        }
    else:
        r = retrieve_context(state["request_text"])
        result = {
            "query": r.query,
            "doc_ids": r.doc_ids,
            "snippets": r.snippets,
            "top_score": round(r.top_score, 4),
            "avg_score": round(r.avg_score, 4),
            "num_results": r.num_results,
            "reranked": r.reranked,
            "candidates_considered": r.candidates_considered,
        }

    state["retrieval"] = result
    _record(
        state,
        node_name="retrieve",
        status="success" if result["num_results"] > 0 else "empty",
        started=started,
        input_data={"query": state["request_text"]},
        output_data={
            "num_results": result["num_results"],
            "top_score": result["top_score"],
            "reranked": result["reranked"],
            "candidates_considered": result["candidates_considered"],
        },
        retrieval=result,
    )
    return state


def route_after_retrieve(state: AgentState) -> str:
    retrieval = state.get("retrieval") or {}
    plan = state.get("plan") or []
    needs_tools = any(s.get("action") == "call_tool" for s in plan)

    if retrieval.get("num_results", 0) == 0:
        state.setdefault("fallback_reasons", []).append("missing_context")
        return "fallback" if not needs_tools else "tools_then_fallback_check"

    return "tools" if needs_tools else "validate"


def tool_node(state: AgentState) -> AgentState:
    settings = get_settings()
    fault = state.get("forced_fault", {}) or {}
    plan = state.get("plan") or []
    tool_steps = [s for s in plan if s.get("action") == "call_tool"]

    results: list[dict[str, Any]] = []
    step_trace_calls: list[dict[str, Any]] = []
    any_hard_failure = False

    from app.orchestration.llm import _seeded_rng  # local import to avoid cycles

    started = time.perf_counter()
    rng = _seeded_rng(state["request_text"])

    for step in tool_steps:
        tool_name = step["tool"]
        arguments = infer_tool_arguments(tool_name, state["request_text"], rng)

        should_force_fail = fault.get("fail_tool") == tool_name
        attempts = 0
        outcome = None

        while attempts <= settings.FALLBACK_MAX_RETRIES:
            attempts += 1
            if should_force_fail:
                outcome = {
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "success": False,
                    "result": None,
                    "error": "simulated timeout calling downstream service",
                    "latency_ms": settings.TOOL_CALL_TIMEOUT_S * 1000,
                }
            else:
                inv = invoke_tool(tool_name, arguments)
                outcome = {
                    "tool_name": inv.tool_name,
                    "arguments": inv.arguments,
                    "success": inv.success,
                    "result": inv.result,
                    "error": inv.error,
                    "latency_ms": round(inv.latency_ms, 2),
                }

            if outcome["success"]:
                break

        if not outcome["success"]:
            any_hard_failure = True
            state.setdefault("fallback_reasons", []).append(f"tool_failure:{tool_name}")

        results.append(outcome)
        step_trace_calls.append(outcome)

    state["tool_results"] = results
    state["status"] = "executing_tools"

    _record(
        state,
        node_name="tool_call",
        status="failed" if any_hard_failure else "success",
        started=started,
        input_data={"tool_steps": [s["tool"] for s in tool_steps]},
        output_data={"results": results},
        error="one or more tool calls failed after retries" if any_hard_failure else None,
        tool_calls=step_trace_calls,
    )
    return state


def route_after_tools(state: AgentState) -> str:
    results = state.get("tool_results") or []
    if any(not r["success"] for r in results):
        return "fallback"
    # if retrieval had already flagged missing context earlier but we still
    # had tools to run, re-check now that tools succeeded
    if "missing_context" in (state.get("fallback_reasons") or []):
        return "fallback"
    return "validate"


def fallback_node(state: AgentState) -> AgentState:
    started = time.perf_counter()
    state["fallback_count"] = state.get("fallback_count", 0) + 1
    state["status"] = "fallback"
    reasons = state.get("fallback_reasons") or ["unspecified"]

    _record(
        state,
        node_name="fallback",
        status="degraded",
        started=started,
        input_data={"reasons": reasons},
        output_data={
            "strategy": "produce a low-confidence draft and force human approval "
            "instead of failing the request outright"
        },
    )
    return state


def validate_node(state: AgentState) -> AgentState:
    started = time.perf_counter()
    fault = state.get("forced_fault", {}) or {}

    retrieval = state.get("retrieval") or {}
    tool_results = state.get("tool_results") or []
    fallback_count = state.get("fallback_count", 0)

    issues: list[str] = []
    confidence = 0.95

    if retrieval.get("num_results", 0) == 0:
        confidence -= 0.35
        issues.append("no supporting policy context retrieved")

    failed_tools = [r for r in tool_results if not r["success"]]
    if failed_tools:
        confidence -= 0.30
        issues.append(f"{len(failed_tools)} tool call(s) failed")

    if fallback_count > 0:
        confidence -= 0.15 * fallback_count

    if fault.get("force_low_confidence"):
        confidence = min(confidence, 0.4)
        issues.append("low-confidence heuristic triggered")

    unsafe = bool(fault.get("unsafe_output"))
    if unsafe:
        issues.append("draft output contained an unapproved commitment and was blocked")
        confidence = min(confidence, 0.3)

    confidence = max(0.0, min(1.0, round(confidence, 3)))

    risk_level = "low"
    text_lower = state["request_text"].lower()
    if fault.get("force_high_risk") or any(
        kw in text_lower for kw in ["security", "breach", "legal", "contract exception", "lawsuit"]
    ):
        risk_level = "high"
    elif "refund" in text_lower or failed_tools:
        risk_level = "medium"

    state["validation"] = {"issues": issues, "confidence": confidence, "unsafe": unsafe}
    state["confidence"] = confidence
    state["risk_level"] = risk_level
    state["status"] = "validating"

    _record(
        state,
        node_name="validate",
        status="flagged" if issues else "success",
        started=started,
        input_data={"retrieval_hits": retrieval.get("num_results", 0), "failed_tools": len(failed_tools)},
        output_data={"confidence": confidence, "risk_level": risk_level, "issues": issues},
    )
    return state


def respond_node(state: AgentState) -> AgentState:
    started = time.perf_counter()
    retrieval = state.get("retrieval") or {}
    tool_results = state.get("tool_results") or []
    degraded = state.get("fallback_count", 0) > 0 or bool(state.get("validation", {}).get("issues"))

    if state.get("validation", {}).get("unsafe"):
        output = (
            "This request could not be auto-completed: the draft recommendation included an "
            "unapproved commitment and has been withheld pending human review."
        )
    else:
        output = simulate_response(
            state["request_text"],
            retrieval.get("snippets", []),
            tool_results,
            degraded=degraded,
        )

    state["final_output"] = output
    _record(
        state,
        node_name="respond",
        status="success",
        started=started,
        input_data={"degraded": degraded},
        output_data={"final_output": output},
    )
    return state


def approval_node(state: AgentState) -> AgentState:
    started = time.perf_counter()
    settings = get_settings()
    confidence = state.get("confidence", 0.0)
    risk_level = state.get("risk_level", "low")
    unsafe = state.get("validation", {}).get("unsafe", False)

    high_stakes = risk_level == "high" or unsafe
    needs_approval = (
        unsafe
        or confidence < settings.AUTO_APPROVE_CONFIDENCE
        or high_stakes
    )

    state["requires_approval"] = needs_approval
    if needs_approval:
        reasons = []
        if unsafe:
            reasons.append("unsafe/unapproved output blocked")
        if confidence < settings.AUTO_APPROVE_CONFIDENCE:
            reasons.append(f"confidence {confidence:.2f} below auto-approve threshold")
        if high_stakes:
            reasons.append(f"risk level={risk_level}")
        state["approval_reason"] = "; ".join(reasons)
        state["status"] = "pending_approval"
    else:
        state["approval_reason"] = None
        state["status"] = "approved"

    _record(
        state,
        node_name="approval",
        status="pending_approval" if needs_approval else "auto_approved",
        started=started,
        input_data={"confidence": confidence, "risk_level": risk_level},
        output_data={"requires_approval": needs_approval, "reason": state.get("approval_reason")},
    )
    return state
