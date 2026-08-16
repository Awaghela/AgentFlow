import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


def gen_uuid() -> str:
    return str(uuid.uuid4())


class WorkflowStatus(str, enum.Enum):
    PLANNING = "planning"
    RETRIEVING = "retrieving"
    EXECUTING_TOOLS = "executing_tools"
    VALIDATING = "validating"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    FALLBACK = "fallback"


class WorkflowRun(TimestampMixin, Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    request_text: Mapped[str] = mapped_column(Text)
    requester: Mapped[str] = mapped_column(String(120), default="demo-user")
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus, native_enum=False), default=WorkflowStatus.PLANNING
    )
    plan: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    final_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fallback_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Set when this run was produced by the eval harness rather than a
    # live user request, so demo/seed data is clearly distinguishable.
    is_eval: Mapped[bool] = mapped_column(default=False)
    eval_scenario_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("eval_scenarios.id"), nullable=True
    )

    steps: Mapped[list["AgentStep"]] = relationship(
        back_populates="workflow_run", cascade="all, delete-orphan", order_by="AgentStep.step_index"
    )
    approval: Mapped[Optional["ApprovalRequest"]] = relationship(
        back_populates="workflow_run", uselist=False, cascade="all, delete-orphan"
    )


class AgentStep(TimestampMixin, Base):
    __tablename__ = "agent_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    workflow_run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id"))
    step_index: Mapped[int] = mapped_column(Integer)
    node_name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="success")
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    workflow_run: Mapped["WorkflowRun"] = relationship(back_populates="steps")
    tool_calls: Mapped[list["ToolCall"]] = relationship(
        back_populates="agent_step", cascade="all, delete-orphan"
    )
    retrieval: Mapped[Optional["RetrievalTrace"]] = relationship(
        back_populates="agent_step", uselist=False, cascade="all, delete-orphan"
    )


class ToolCall(TimestampMixin, Base):
    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    agent_step_id: Mapped[str] = mapped_column(ForeignKey("agent_steps.id"))
    tool_name: Mapped[str] = mapped_column(String(64))
    arguments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    result: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    success: Mapped[bool] = mapped_column(default=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    agent_step: Mapped["AgentStep"] = relationship(back_populates="tool_calls")


class RetrievalTrace(TimestampMixin, Base):
    __tablename__ = "retrieval_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    agent_step_id: Mapped[str] = mapped_column(ForeignKey("agent_steps.id"))
    query: Mapped[str] = mapped_column(Text)
    retrieved_doc_ids: Mapped[list] = mapped_column(JSON, default=list)
    top_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    num_results: Mapped[int] = mapped_column(Integer, default=0)
    reranked: Mapped[bool] = mapped_column(default=False)
    candidates_considered: Mapped[int] = mapped_column(Integer, default=0)

    agent_step: Mapped["AgentStep"] = relationship(back_populates="retrieval")
