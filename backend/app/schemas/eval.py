from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EvalScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    description: str
    expected_behavior: str
    severity: str


class EvalResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scenario_id: str
    workflow_run_id: Optional[str]
    category: str
    passed: bool
    latency_ms: float
    failure_reason: Optional[str] = None
    assertions: list[str] = []


class EvalRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    scenario_count: int
    passed_count: int
    failed_count: int
    started_at: datetime
    completed_at: Optional[datetime] = None


class EvalRunDetailOut(EvalRunOut):
    results: list[EvalResultOut] = []


class TriggerEvalRunRequest(BaseModel):
    label: str = "manual run"
    scenario_limit: Optional[int] = None
