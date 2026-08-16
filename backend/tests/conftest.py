"""
Session-wide test fixtures.

Forces EMBEDDING_BACKEND=tfidf and RERANK_PROVIDER=none as defaults for the
whole test session, so the suite never makes a live network call or
depends on an API key just because one happens to be present in whoever's
running it — regardless of what "auto" would otherwise resolve to.

Explicit values already set in the environment are respected (this only
fills in a default when the variable is absent), which is exactly what
lets tests/test_pgvector_store.py's own `EMBEDDING_BACKEND=local`
requirement (see that file's docstring) keep working correctly.
"""
import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def _isolate_tests_from_live_api_keys():
    defaults = {"EMBEDDING_BACKEND": "tfidf", "RERANK_PROVIDER": "none"}
    previously_unset = [key for key in defaults if key not in os.environ]

    for key, value in defaults.items():
        os.environ.setdefault(key, value)

    from app.core.config import get_settings

    get_settings.cache_clear()

    yield

    for key in previously_unset:
        os.environ.pop(key, None)
    get_settings.cache_clear()
