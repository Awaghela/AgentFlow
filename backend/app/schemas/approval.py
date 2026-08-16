from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApprovalDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    reviewer: str = Field(default="reviewer@agentflow.dev", max_length=120)
    notes: Optional[str] = Field(default=None, max_length=2000)


class ApprovalRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    request_text: str
    requester: str
    status: str
    confidence: Optional[float] = None
    latency_ms: Optional[float] = None


class ApprovalWithRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reason: str
    risk_level: str
    confidence_at_request: float
    status: str
    reviewer: Optional[str] = None
    decision_notes: Optional[str] = None
    decided_at: Optional[datetime] = None
    workflow_run: ApprovalRunSummary
