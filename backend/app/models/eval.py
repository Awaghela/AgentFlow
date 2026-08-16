import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


def gen_uuid() -> str:
    return str(uuid.uuid4())


class EvalScenario(TimestampMixin, Base):
    """
    A single reproducible test case in the validation suite, e.g.
    "tool_failure_07: CRM lookup times out mid-plan".
    """

    __tablename__ = "eval_scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text)
    expected_behavior: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    seed_params: Mapped[dict] = mapped_column(JSON, default=dict)


class EvalRun(TimestampMixin, Base):
    """One execution of the full (or partial) scenario suite."""

    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    label: Mapped[str] = mapped_column(String(160), default="scheduled run")
    scenario_count: Mapped[int] = mapped_column(Integer, default=0)
    passed_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column()
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    results: Mapped[list["EvalResult"]] = relationship(
        back_populates="eval_run", cascade="all, delete-orphan"
    )


class EvalResult(TimestampMixin, Base):
    __tablename__ = "eval_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    eval_run_id: Mapped[str] = mapped_column(ForeignKey("eval_runs.id"))
    scenario_id: Mapped[str] = mapped_column(ForeignKey("eval_scenarios.id"))
    workflow_run_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("workflow_runs.id"), nullable=True
    )
    category: Mapped[str] = mapped_column(String(64), index=True)
    passed: Mapped[bool] = mapped_column(default=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assertions: Mapped[list] = mapped_column(JSON, default=list)

    eval_run: Mapped["EvalRun"] = relationship(back_populates="results")
