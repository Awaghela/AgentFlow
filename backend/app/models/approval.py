import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


def gen_uuid() -> str:
    return str(uuid.uuid4())


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    APPROVED = "approved"
    REJECTED = "rejected"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ApprovalRequest(TimestampMixin, Base):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    workflow_run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id"), unique=True)
    reason: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, native_enum=False))
    confidence_at_request: Mapped[float] = mapped_column(Float)
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, native_enum=False), default=ApprovalStatus.PENDING
    )
    reviewer: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    decision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    workflow_run: Mapped["WorkflowRun"] = relationship(back_populates="approval")
