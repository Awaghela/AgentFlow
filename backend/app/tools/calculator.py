"""Deterministic arithmetic tool used for refund / proration calculations."""
from __future__ import annotations


def calculate_refund(monthly_price: float, days_used: int, billing_period_days: int = 30) -> dict:
    if billing_period_days <= 0:
        raise ValueError("billing_period_days must be positive")

    days_used = max(0, min(days_used, billing_period_days))
    unused_fraction = (billing_period_days - days_used) / billing_period_days
    refund_amount = round(monthly_price * unused_fraction, 2)
    return {
        "monthly_price": monthly_price,
        "days_used": days_used,
        "unused_fraction": round(unused_fraction, 4),
        "refund_amount": refund_amount,
    }
