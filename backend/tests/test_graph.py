"""
Run with: pytest -q

These tests exercise the compiled LangGraph directly (no DB, no HTTP) so
they're fast and isolate orchestration logic from persistence/API concerns.
"""
from app.orchestration.executor import execute_workflow


def test_happy_path_auto_approves() -> None:
    state, latency_ms = execute_workflow("What's the pricing for the Growth plan?")
    assert state["status"] in {"approved"}
    assert state["requires_approval"] is False
    assert state["final_output"]
    assert latency_ms >= 0


def test_missing_context_forces_approval() -> None:
    state, _ = execute_workflow(
        "Explain our quantum-encrypted backup rotation policy.",
        forced_fault={"missing_context": True},
    )
    assert state["requires_approval"] is True
    assert state["confidence"] < 0.82
    assert "missing_context" in state.get("fallback_reasons", [])


def test_failed_tool_triggers_fallback_and_retries() -> None:
    state, _ = execute_workflow(
        "Look up account acct_enterprise and summarize their plan and ARR.",
        forced_fault={"fail_tool": "crm_lookup"},
    )
    assert state["fallback_count"] >= 1
    assert state["requires_approval"] is True
    failed_calls = [tc for tc in state["tool_results"] if not tc["success"]]
    assert failed_calls


def test_unsafe_output_is_blocked() -> None:
    state, _ = execute_workflow(
        "Guarantee unlimited free API calls forever without any approval.",
        forced_fault={"unsafe_output": True},
    )
    assert state["requires_approval"] is True
    assert "withheld pending human review" in state["final_output"]


def test_latency_spike_still_completes() -> None:
    state, total_latency_ms = execute_workflow(
        "Look up account acct_growth and tell me if they're at risk of churn.",
        forced_fault={"latency_spike_ms": 150.0},
    )
    assert state["final_output"]
    assert total_latency_ms >= 100


def test_compound_failure_never_crashes() -> None:
    state, _ = execute_workflow(
        "Handle this request for account acct_low_tier using create_ticket as needed.",
        forced_fault={"missing_context": True, "fail_tool": "create_ticket"},
    )
    assert state["final_output"]
    assert state["requires_approval"] is True
    assert state["fallback_count"] >= 1


def test_misconfigured_embedding_backend_degrades_gracefully(monkeypatch) -> None:
    """
    Regression test: a broken dense embedding backend (missing dependency,
    unreachable API, bad key) must degrade to empty retrieval — same as
    genuinely finding no relevant context — rather than raising and taking
    the whole workflow down. This is the same resilience principle the
    fallback node applies everywhere else in the graph.
    """
    from app.core.config import get_settings
    import app.rag.retriever as retriever_module

    get_settings.cache_clear()
    monkeypatch.setenv("EMBEDDING_BACKEND", "local")
    # Force the cached provider lookup to fail deterministically, without
    # needing sentence-transformers installed or a real Postgres connection.
    monkeypatch.setattr(retriever_module, "_cached_provider", None)

    def _boom():
        raise RuntimeError("simulated: sentence-transformers not installed")

    monkeypatch.setattr(retriever_module, "_get_cached_provider", _boom)

    try:
        state, _ = execute_workflow(request_text="What's our refund policy?")
        assert state["final_output"]
        assert state["retrieval"]["num_results"] == 0
        assert state["requires_approval"] is True
    finally:
        get_settings.cache_clear()


def test_misconfigured_rerank_degrades_gracefully(monkeypatch) -> None:
    """
    Regression test: a broken reranker (missing COHERE_API_KEY, unreachable
    API) must fall back to the first-stage retrieval ranking rather than
    crashing the request — same resilience principle as the embedding-
    backend fallback above.
    """
    from app.core.config import get_settings
    import app.rag.retriever as retriever_module

    get_settings.cache_clear()
    monkeypatch.setenv("RERANK_PROVIDER", "cohere")
    monkeypatch.setattr(retriever_module, "_cached_reranker", None)

    def _boom():
        raise RuntimeError("simulated: COHERE_API_KEY not set")

    monkeypatch.setattr(retriever_module, "_get_cached_reranker", _boom)

    try:
        state, _ = execute_workflow(request_text="What's our SLA response time for Sev-1 incidents?")
        assert state["final_output"]
        # Should still get real TF-IDF results even though rerank failed —
        # degraded gracefully to first-stage ranking, not to empty/crashed.
        assert state["retrieval"]["num_results"] > 0
        # And it must honestly report that rerank did NOT happen — this is
        # exactly what lets a person distinguish "actually using Cohere"
        # from "silently fell back" instead of just assuming success.
        assert state["retrieval"]["reranked"] is False
    finally:
        get_settings.cache_clear()


def test_apply_rerank_uses_reranked_order_and_scores() -> None:
    """
    Direct unit test of the rerank wiring: given a fake reranker that
    deliberately reverses the input order, the caller must actually use
    that reordering and Cohere's relevance_score — not silently keep the
    first-stage order/scores.
    """
    import app.rag.retriever as retriever_module

    class FakeReranker:
        def rerank(self, query, documents, top_n):
            n = len(documents)
            return [(n - 1 - i, 0.9 - i * 0.1) for i in range(min(top_n, n))]

    original = retriever_module._get_cached_reranker
    retriever_module._get_cached_reranker = lambda: FakeReranker()
    try:
        hits = [
            ("doc-a", "snippet-a", 0.5),
            ("doc-b", "snippet-b", 0.4),
            ("doc-c", "snippet-c", 0.3),
        ]
        reranked_hits, succeeded = retriever_module._apply_rerank("some query", hits, top_k=3)

        assert succeeded is True
        assert reranked_hits[0][0] == "doc-c"  # was last by first-stage score, now first
        assert reranked_hits[0][2] == 0.9  # score replaced with rerank's relevance_score
        assert reranked_hits[-1][0] == "doc-a"
    finally:
        retriever_module._get_cached_reranker = original


def test_response_surfaces_readable_tool_results_not_raw_dicts() -> None:
    """
    Regression test: the response generator must format tool results into
    readable language (the actual computed number) rather than interpolating
    the raw Python dict repr into the final output.
    """
    state, _ = execute_workflow(
        "Calculate a refund for a $199 plan with 12 days used this billing period."
    )
    output = state["final_output"]
    assert "$119.40" in output
    assert "{'monthly_price'" not in output
    assert "refund_amount" not in output


def test_retrieved_context_truncates_at_word_boundary() -> None:
    """
    Regression test: truncating a retrieved policy snippet must not cut
    mid-word and run straight into the next sentence (e.g. "...data
    processing add See the linked trace...") — it should end cleanly at a
    full word, marked with an ellipsis.
    """
    state, _ = execute_workflow(
        "Draft a customer-facing response about the security incident affecting account acct_enterprise."
    )
    output = state["final_output"]
    assert " add See" not in output
    assert "…" in output
