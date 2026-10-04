"""
Core execution state, data contracts, and trace representations
for CentrAlign Autonomous Operator runtime.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import time
import uuid

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    OBSERVING = "OBSERVING"
    ADAPTING = "ADAPTING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"

class ActionStep(BaseModel):
    step_id: str = Field(default_factory=lambda: f"step_{uuid.uuid4().hex[:6]}")
    description: str
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_outcome: str = ""
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    observation: Optional[str] = None
    error: Optional[str] = None
    retries_attempted: int = 0
    max_retries: int = 2
    requires_approval: bool = False
    approval_reason: Optional[str] = None
    approved_by: Optional[str] = None
    duration_ms: float = 0.0

class TraceEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    timestamp: float = Field(default_factory=time.time)
    phase: TaskStatus
    message: str
    data: Optional[Dict[str, Any]] = None

class VerificationResult(BaseModel):
    verified: bool = False
    assertions_checked: int = 0
    assertions_passed: int = 0
    details: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)

class ExecutionContext(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    user_goal: str
    interpreted_intent: str = ""
    relevant_policies: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    plan: Optional[List[ActionStep]] = None
    current_step_index: int = 0
    trace: List[TraceEvent] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    verification: Optional[VerificationResult] = None
    final_summary: str = ""
    error_message: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None

    def add_trace(self, phase: TaskStatus, message: str, data: Optional[Dict[str, Any]] = None):
        event = TraceEvent(phase=phase, message=message, data=data)
        self.trace.append(event)
        return event
