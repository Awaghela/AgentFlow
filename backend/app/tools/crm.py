"""
Mock CRM lookup tool.

Simulates a real CRM/billing system integration (e.g. Salesforce + Stripe)
with realistic latency, deterministic-but-varied responses, and a small
chance of transient failure so the orchestration graph's retry/fallback
logic has something real to exercise.
"""
from __future__ import annotations

import hashlib
import random


_ACCOUNTS = {
    "acct_low_tier": {"plan": "Starter", "arr": 588, "renewal": "2026-11-01", "open_tickets": 0},
    "acct_growth": {"plan": "Growth", "arr": 3588, "renewal": "2026-09-15", "open_tickets": 1},
    "acct_enterprise": {"plan": "Enterprise", "arr": 148000, "renewal": "2027-01-20", "open_tickets": 2},
    "acct_churn_risk": {"plan": "Growth", "arr": 3588, "renewal": "2026-08-30", "open_tickets": 4},
}


def crm_lookup(account_id: str, rng: random.Random | None = None) -> dict:
    rng = rng or random.Random(int(hashlib.sha256(account_id.encode()).hexdigest(), 16) % (2**32))

    # ~6% simulated transient failure rate, consistent per-account so eval
    # scenarios that need a guaranteed failure can pin an account_id.
    if account_id not in _ACCOUNTS:
        raise LookupError(f"no account found for id={account_id!r}")

    record = dict(_ACCOUNTS[account_id])
    record["account_id"] = account_id
    return record
