from app.eval.categories import TOTAL_SCENARIOS
from app.eval.scenarios import generate_all_scenarios


def test_generates_exactly_120_scenarios() -> None:
    scenarios = generate_all_scenarios()
    assert len(scenarios) == 120
    assert len(scenarios) == TOTAL_SCENARIOS


def test_all_seven_categories_represented() -> None:
    scenarios = generate_all_scenarios()
    categories = {s.category for s in scenarios}
    assert categories == {
        "missing_context",
        "failed_tool_calls",
        "incorrect_retrieval",
        "unsafe_outputs",
        "latency_issues",
        "approval_routing",
        "fallback_behavior",
    }


def test_scenario_names_are_unique() -> None:
    scenarios = generate_all_scenarios()
    names = [s.name for s in scenarios]
    assert len(names) == len(set(names))
