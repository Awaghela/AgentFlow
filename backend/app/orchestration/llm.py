"""
LLM interface used by the plan and respond nodes.

Two modes, selected by `settings.LLM_MODE`:

  - "simulation" (default): deterministic, template-driven planning and
    response generation. Zero external calls, fully reproducible, and
    what powers the 120-scenario eval suite so results don't drift with
    model updates or API availability.
  - "live": routes through the Anthropic Messages API using
    ANTHROPIC_API_KEY. Same call sites, real completions.

This mirrors how teams actually build these platforms: a simulation/replay
mode for CI and evals, a live mode for production.
"""
from __future__ import annotations

import hashlib
import random
import re

from app.core.config import get_settings

_TOOL_KEYWORDS = {
    "crm_lookup": ["account", "customer", "arr", "plan tier", "renewal", "acct_"],
    "calculate_refund": ["refund", "reimburse", "prorate", "money back"],
    "knowledge_search": ["policy", "sla", "guideline", "how do", "what is", "process"],
    "create_ticket": ["escalate", "open a ticket", "file a ticket", "urgent", "incident"],
}


def _seeded_rng(text: str) -> random.Random:
    digest = hashlib.sha256(text.encode()).hexdigest()
    return random.Random(int(digest, 16) % (2**32))


def simulate_plan(request_text: str, max_steps: int) -> list[dict]:
    """
    Deterministically derive a multi-step plan from the request text by
    matching it against known tool intents, always starting with a
    context-retrieval step (mirrors a real planner's "gather context
    first" bias) and capping at `max_steps`.
    """
    lower = request_text.lower()
    steps: list[dict] = [
        {"step": 1, "action": "retrieve_context", "description": "Retrieve relevant policy/context for the request."}
    ]

    matched_tools = [
        tool
        for tool, keywords in _TOOL_KEYWORDS.items()
        if any(kw in lower for kw in keywords)
    ]
    if not matched_tools:
        matched_tools = ["knowledge_search"]

    for i, tool in enumerate(matched_tools, start=2):
        if len(steps) >= max_steps:
            break
        steps.append(
            {
                "step": i,
                "action": "call_tool",
                "tool": tool,
                "description": f"Call {tool} to gather structured data needed for the recommendation.",
            }
        )

    steps.append(
        {
            "step": len(steps) + 1,
            "action": "synthesize_response",
            "description": "Combine retrieved context and tool outputs into an auditable recommendation.",
        }
    )
    return steps[:max_steps]


def infer_tool_arguments(tool: str, request_text: str, rng: random.Random) -> dict:
    """Best-effort deterministic argument extraction for the simulated planner."""
    if tool == "crm_lookup":
        match = re.search(r"acct_[a-z_]+", request_text.lower())
        account_id = match.group(0) if match else rng.choice(
            ["acct_low_tier", "acct_growth", "acct_enterprise", "acct_churn_risk"]
        )
        return {"account_id": account_id}

    if tool == "calculate_refund":
        # Require the literal $ so this can't grab an unrelated number (e.g.
        # "5 days" if it happens to appear before the price in the sentence).
        price_match = re.search(r"\$(\d+(?:\.\d{1,2})?)", request_text)
        monthly_price = float(price_match.group(1)) if price_match else 299.0
        days_match = re.search(r"(\d{1,2})\s*days?", request_text)
        days_used = int(days_match.group(1)) if days_match else rng.randint(2, 25)
        return {"monthly_price": monthly_price, "days_used": days_used}

    if tool == "knowledge_search":
        return {"query": request_text[:200], "top_k": 3}

    if tool == "create_ticket":
        return {"subject": request_text[:80], "priority": rng.choice(["low", "medium", "high"])}

    return {}


def _truncate_at_word(text: str, max_len: int) -> str:
    """
    Truncate at the last full word before `max_len` instead of slicing
    mid-word, and mark the cut with an ellipsis instead of letting the next
    sentence run straight into it (e.g. "...data processing add See the
    linked trace..." — the exact kind of garbled output a hard character
    slice produces).
    """
    if len(text) <= max_len:
        return text
    truncated = text[:max_len].rsplit(" ", 1)[0]
    return truncated.rstrip(".,;: ") + "…"


def _format_tool_result(tool_name: str, result: object) -> str:
    """
    Turn a raw tool result into a natural-language fragment instead of
    interpolating the dict repr — this is what a person actually reads as
    "the answer" (e.g. "the customer is owed a $119.40 refund"), not
    `{'refund_amount': 119.4, ...}` debug output.
    """
    if tool_name == "calculate_refund" and isinstance(result, dict):
        amount = result.get("refund_amount", 0)
        price = result.get("monthly_price", 0)
        days = result.get("days_used", 0)
        unused_pct = result.get("unused_fraction", 0) * 100
        return (
            f"the customer is owed a ${amount:,.2f} refund "
            f"(${price:,.2f}/month, {days} day(s) used — {unused_pct:.0f}% of the billing period unused)"
        )

    if tool_name == "crm_lookup" and isinstance(result, dict):
        plan = result.get("plan", "unknown")
        arr = result.get("arr", 0)
        renewal = result.get("renewal", "unknown")
        tickets = result.get("open_tickets", 0)
        return (
            f"the account is on the {plan} plan (${arr:,.0f} ARR, renews {renewal}) "
            f"with {tickets} open support ticket(s)"
        )

    if tool_name == "create_ticket" and isinstance(result, dict):
        ticket_id = result.get("ticket_id", "unknown")
        priority = result.get("priority", "unknown")
        return f"opened ticket {ticket_id} at {priority} priority"

    if tool_name == "knowledge_search" and isinstance(result, dict):
        n = result.get("num_results", 0)
        return f"an internal knowledge search returned {n} relevant document(s)"

    # Unknown/future tool — fall back to a compact key=value listing rather
    # than a raw dict repr, so this never regresses to unreadable debug text.
    if isinstance(result, dict):
        return ", ".join(f"{k}={v}" for k, v in result.items())
    return str(result)


def simulate_response(
    request_text: str,
    retrieval_snippets: list[str],
    tool_outputs: list[dict],
    degraded: bool,
) -> str:
    rng = _seeded_rng(request_text)

    lines = []
    if degraded:
        lines.append(
            "Draft recommendation (reduced confidence — one or more inputs were incomplete):"
        )
    else:
        lines.append("Recommendation:")

    successful = [t for t in tool_outputs if t.get("success")]
    failed = [t for t in tool_outputs if not t.get("success")]

    if successful:
        summary_bits = [_format_tool_result(t["tool_name"], t["result"]) for t in successful]
        lines.append("Based on the data gathered, " + "; ".join(summary_bits) + ".")

    if failed:
        # Surface exactly which tool failed and why, instead of silently
        # dropping it — a reviewer reading this shouldn't have to open the
        # trace just to learn the recommendation is incomplete.
        failed_bits = [f"{t['tool_name']} ({t.get('error') or 'call failed'})" for t in failed]
        lines.append(
            "Note: " + "; ".join(failed_bits) + " could not be completed, so this "
            "recommendation is incomplete and should be verified before acting on it."
        )

    if retrieval_snippets:
        lines.append(f"Relevant policy context: {_truncate_at_word(retrieval_snippets[0], 260)}")

    if not tool_outputs and not retrieval_snippets:
        lines.append(
            "No supporting tool output or policy context was available; this recommendation "
            "should be treated as low-confidence and reviewed before acting on it."
        )

    closing = rng.choice(
        [
            "This recommendation is logged with full trace context for audit.",
            "Full reasoning trace and sources are attached to this run for review.",
            "See the linked trace for the retrieval sources and tool calls behind this answer.",
        ]
    )
    lines.append(closing)
    return " ".join(lines)


def live_complete(system: str, user: str) -> str:
    """Route through the real Anthropic API when LLM_MODE=live."""
    settings = get_settings()
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set but LLM_MODE=live")

    from anthropic import Anthropic

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=600,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
