from __future__ import annotations

import uuid


_VALID_PRIORITIES = {"low", "medium", "high", "urgent"}


def create_ticket(subject: str, priority: str = "medium", account_id: str | None = None) -> dict:
    if priority not in _VALID_PRIORITIES:
        raise ValueError(f"invalid priority {priority!r}, expected one of {_VALID_PRIORITIES}")

    return {
        "ticket_id": f"tkt_{uuid.uuid4().hex[:8]}",
        "subject": subject,
        "priority": priority,
        "account_id": account_id,
        "status": "open",
    }
