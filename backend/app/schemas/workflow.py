from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkflowCreateRequest(BaseModel):
    request_text: str = Field(..., min_length=3, max_length=4000)
    requester: str = Field(default="demo-user", max_length=120)


class ToolCallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tool_name: str
    arguments: Optional[dict] = None
    result: Optional[Any] = None
    success: bool
    latency_ms: float
    error: Optional[str] = None


class RetrievalTraceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query: str
    retrieved_doc_ids: list[str]
    top_score: float
    avg_score: float
    num_results: int
    reranked: bool
    candidates_considered: int


class AgentStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    step_index: int
    node_name: str
    status: str
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    latency_ms: float
    error: Optional[str] = None
    tool_calls: list[ToolCallOut] = []
    retrieval: Optional[RetrievalTraceOut] = None


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reason: str
    risk_level: str
    confidence_at_request: float
    status: str
    reviewer: Optional[str] = None
    decision_notes: Optional[str] = None
    decided_at: Optional[datetime] = None


class WorkflowRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    request_text: str
    requester: str
    status: str
    plan: Optional[list] = None
    final_output: Optional[str] = None
    confidence: Optional[float] = None
    latency_ms: Optional[float] = None
    fallback_count: int
    error: Optional[str] = None
    is_eval: bool
    created_at: datetime
    completed_at: Optional[datetime] = None


class WorkflowRunDetailOut(WorkflowRunOut):
    steps: list[AgentStepOut] = []
    approval: Optional[ApprovalOut] = None


class WorkflowListOut(BaseModel):
    total: int
    items: list[WorkflowRunOut]
