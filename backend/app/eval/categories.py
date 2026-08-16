from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryMeta:
    key: str
    label: str
    description: str
    scenario_count: int


CATEGORIES: list[CategoryMeta] = [
    CategoryMeta(
        key="missing_context",
        label="Missing Context",
        description="Requests where the retrieval pipeline has no relevant grounding available.",
        scenario_count=18,
    ),
    CategoryMeta(
        key="failed_tool_calls",
        label="Failed Tool Calls",
        description="A downstream tool (CRM, ticketing, calculator) times out or errors mid-plan.",
        scenario_count=18,
    ),
    CategoryMeta(
        key="incorrect_retrieval",
        label="Incorrect Retrieval",
        description="Retrieved context is weakly relevant; the system must not treat it as authoritative.",
        scenario_count=17,
    ),
    CategoryMeta(
        key="unsafe_outputs",
        label="Unsafe Outputs",
        description="A draft recommendation contains an unapproved commitment and must be blocked.",
        scenario_count=17,
    ),
    CategoryMeta(
        key="latency_issues",
        label="Latency Issues",
        description="A dependency is slow; the pipeline must still complete and flag the budget breach.",
        scenario_count=17,
    ),
    CategoryMeta(
        key="approval_routing",
        label="Approval Routing",
        description="Confidence and risk signals must route to auto-approval or human review correctly.",
        scenario_count=17,
    ),
    CategoryMeta(
        key="fallback_behavior",
        label="Fallback Behavior",
        description="Compound failures must still resolve to a coherent, non-crashing degraded response.",
        scenario_count=16,
    ),
]

CATEGORY_BY_KEY = {c.key: c for c in CATEGORIES}

TOTAL_SCENARIOS = sum(c.scenario_count for c in CATEGORIES)
