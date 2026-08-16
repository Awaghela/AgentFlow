from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.persistence import persist_run
from app.models.eval import EvalResult, EvalRun, EvalScenario
from app.orchestration.executor import execute_workflow


@contextmanager
def force_eval_offline_mode():
    """
    The eval suite is a determinism/resilience test, not a live-Cohere
    quality test — running it ALWAYS uses tfidf retrieval and no
    reranking, unconditionally, regardless of what's in the environment.

    This is deliberately NOT overridable via env vars. An earlier version
    only forced this when EMBEDDING_BACKEND was completely absent from the
    environment — which works in a plain shell, but Docker Compose always
    materializes EMBEDDING_BACKEND as a real variable (e.g. "auto" from
    `${EMBEDDING_BACKEND:-auto}`) even when the user never set it
    themselves. That made "is this var present" an unreliable signal for
    "did the user really want this," and the eval suite ended up making
    120 real Cohere calls and hitting a trial-key rate limit despite this
    safeguard supposedly being in place. "120/120, identical every run,
    zero API spend" is a hard guarantee now, not a soft default — if you
    genuinely need to eval against live Cohere, call
    `_run_eval_suite_inner()` directly rather than relying on env vars to
    bypass this.
    """
    original = {
        "EMBEDDING_BACKEND": os.environ.get("EMBEDDING_BACKEND"),
        "RERANK_PROVIDER": os.environ.get("RERANK_PROVIDER"),
    }
    os.environ["EMBEDDING_BACKEND"] = "tfidf"
    os.environ["RERANK_PROVIDER"] = "none"
    get_settings.cache_clear()
    try:
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()


def _check_assertions(scenario: EvalScenario, final_state: dict, total_latency_ms: float) -> tuple[bool, list[str], str | None]:
    expected = scenario.seed_params.get("expected", {})
    assertions: list[str] = []
    all_passed = True

    def check(label: str, condition: bool) -> None:
        nonlocal all_passed
        assertions.append(f"{'PASS' if condition else 'FAIL'}: {label}")
        if not condition:
            all_passed = False

    if "requires_approval" in expected:
        check(
            f"requires_approval == {expected['requires_approval']}",
            bool(final_state.get("requires_approval")) == expected["requires_approval"],
        )

    if "max_confidence" in expected:
        conf = final_state.get("confidence", 1.0)
        check(f"confidence <= {expected['max_confidence']} (got {conf})", conf <= expected["max_confidence"])

    if "status_in" in expected:
        check(
            f"status in {expected['status_in']} (got {final_state.get('status')})",
            final_state.get("status") in expected["status_in"],
        )

    if "fallback_count_min" in expected:
        fc = final_state.get("fallback_count", 0)
        check(f"fallback_count >= {expected['fallback_count_min']} (got {fc})", fc >= expected["fallback_count_min"])

    if "max_top_score" in expected:
        top_score = (final_state.get("retrieval") or {}).get("top_score", 0.0)
        check(f"retrieval.top_score <= {expected['max_top_score']} (got {top_score:.3f})", top_score <= expected["max_top_score"])

    if "blocks_unsafe_text" in expected:
        output = final_state.get("final_output") or ""
        check("unsafe commitment withheld from final_output", "withheld pending human review" in output)

    if "max_total_latency_ms" in expected:
        check(
            f"total_latency_ms <= {expected['max_total_latency_ms']} (got {total_latency_ms:.0f})",
            total_latency_ms <= expected["max_total_latency_ms"],
        )

    if "min_latency_recorded_ms" in expected:
        check(
            f"total_latency_ms >= {expected['min_latency_recorded_ms']:.0f} (got {total_latency_ms:.0f})",
            total_latency_ms >= expected["min_latency_recorded_ms"],
        )

    if "non_empty_output" in expected:
        check("final_output is non-empty", bool((final_state.get("final_output") or "").strip()))

    if not assertions:
        check("workflow completed without raising", True)

    failure_reason = None if all_passed else "; ".join(a for a in assertions if a.startswith("FAIL"))
    return all_passed, assertions, failure_reason


def run_eval_suite(db: Session, scenarios: list[EvalScenario], label: str = "scheduled run") -> EvalRun:
    with force_eval_offline_mode():
        return _run_eval_suite_inner(db, scenarios, label)


def _run_eval_suite_inner(db: Session, scenarios: list[EvalScenario], label: str) -> EvalRun:
    eval_run = EvalRun(
        label=label,
        scenario_count=len(scenarios),
        started_at=datetime.now(timezone.utc),
        config={"scenario_count": len(scenarios)},
    )
    db.add(eval_run)
    db.flush()

    passed_count = 0
    for scenario in scenarios:
        request_text = scenario.seed_params.get("request_text", "")
        forced_fault = scenario.seed_params.get("forced_fault", {})

        try:
            final_state, total_latency_ms = execute_workflow(
                request_text=request_text, requester="eval-harness", forced_fault=forced_fault
            )
            run = persist_run(
                db,
                final_state,
                total_latency_ms,
                is_eval=True,
                eval_scenario_id=scenario.id,
            )
            passed, assertions, failure_reason = _check_assertions(scenario, final_state, total_latency_ms)
            workflow_run_id = run.id
            latency_ms = total_latency_ms
        except Exception as exc:  # noqa: BLE001 - a raised exception is itself a scenario failure
            passed = False
            assertions = [f"FAIL: unhandled exception during execution: {exc}"]
            failure_reason = str(exc)
            workflow_run_id = None
            latency_ms = 0.0

        if passed:
            passed_count += 1

        db.add(
            EvalResult(
                eval_run_id=eval_run.id,
                scenario_id=scenario.id,
                workflow_run_id=workflow_run_id,
                category=scenario.category,
                passed=passed,
                latency_ms=round(latency_ms, 2),
                failure_reason=failure_reason,
                assertions=assertions,
            )
        )

    eval_run.passed_count = passed_count
    eval_run.failed_count = len(scenarios) - passed_count
    eval_run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(eval_run)
    return eval_run
