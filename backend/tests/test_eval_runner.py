"""
Regression tests for app.eval.runner's offline-mode guarantee.

test_force_eval_offline_mode_overrides_even_when_explicitly_set_to_auto
reproduces an actual production bug: Docker Compose's
`EMBEDDING_BACKEND: ${EMBEDDING_BACKEND:-auto}` always materializes a real
environment variable inside the container — "auto" by default — even when
the user never set it themselves in their own .env. An earlier version of
force_eval_offline_mode() only forced tfidf when EMBEDDING_BACKEND was
completely *absent*, which made it a no-op in exactly this situation, and
the eval suite ended up making 120 real Cohere calls and hitting a
trial-key rate limit. This test fails if that regresses.
"""
from app.core.config import get_settings
from app.eval.runner import force_eval_offline_mode


def test_force_eval_offline_mode_overrides_even_when_explicitly_set_to_auto(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_BACKEND", "auto")
    monkeypatch.setenv("RERANK_PROVIDER", "auto")
    monkeypatch.setenv("COHERE_API_KEY", "fake-key-simulating-presence")
    get_settings.cache_clear()

    try:
        # Sanity check: prove this scenario really would resolve to cohere
        # without the guard, so the test is actually exercising the bug.
        assert get_settings().resolved_embedding_backend == "cohere"
        assert get_settings().resolved_rerank_provider == "cohere"

        with force_eval_offline_mode():
            settings = get_settings()
            assert settings.resolved_embedding_backend == "tfidf"
            assert settings.resolved_rerank_provider == "none"

        # And the override doesn't leak into code that runs after the
        # eval suite finishes (e.g. demo-data seeding, which should still
        # auto-detect Cohere normally).
        get_settings.cache_clear()
        assert get_settings().resolved_embedding_backend == "cohere"
        assert get_settings().resolved_rerank_provider == "cohere"
    finally:
        get_settings.cache_clear()


def test_force_eval_offline_mode_restores_original_env_on_exception(monkeypatch) -> None:
    """Even if the wrapped code raises, the original environment must be restored."""
    monkeypatch.setenv("EMBEDDING_BACKEND", "cohere")
    get_settings.cache_clear()

    try:
        with force_eval_offline_mode():
            assert get_settings().resolved_embedding_backend == "tfidf"
            raise RuntimeError("simulated failure mid-eval-run")
    except RuntimeError:
        pass
    finally:
        get_settings.cache_clear()
        assert get_settings().EMBEDDING_BACKEND == "cohere"
        get_settings.cache_clear()


def test_run_eval_suite_never_constructs_a_cohere_provider(monkeypatch) -> None:
    """
    End-to-end: with EMBEDDING_BACKEND=auto and a Cohere key present —
    exactly the Docker Compose scenario — actually running the suite must
    never touch the Cohere embedding provider at all. Monkeypatches
    `get_embedding_provider` to explode if called, so this fails loudly
    instead of silently passing if the guard regresses.
    """
    import app.rag.embedding_providers as embedding_providers_module
    from app.db.schema import create_all_tables
    from app.db.session import SessionLocal, engine
    from app.eval.runner import run_eval_suite
    from app.models.eval import EvalScenario

    # Create tables BEFORE flipping to a Cohere-resolving env — table setup
    # for this test only needs the plain tables, and doing it under a
    # "cohere" resolution would try (and fail, on SQLite) to CREATE
    # EXTENSION vector, which is irrelevant to what this test is checking.
    import app.models  # noqa: F401
    create_all_tables(engine)

    monkeypatch.setenv("EMBEDDING_BACKEND", "auto")
    monkeypatch.setenv("COHERE_API_KEY", "fake-key-simulating-presence")
    get_settings.cache_clear()

    def _explode():
        raise AssertionError(
            "get_embedding_provider() was called during the eval suite — "
            "force_eval_offline_mode() failed to prevent a live Cohere call."
        )

    monkeypatch.setattr(embedding_providers_module, "get_embedding_provider", _explode)

    db = SessionLocal()
    try:
        scenario = EvalScenario(
            name="regression_test_scenario",
            category="missing_context",
            description="test",
            expected_behavior="test",
            severity="medium",
            seed_params={
                "request_text": "What's our refund policy?",
                "forced_fault": {},
                "expected": {},
            },
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)

        run = run_eval_suite(db, [scenario], label="regression test")
        assert run.scenario_count == 1
    finally:
        db.close()
        get_settings.cache_clear()
