import pytest
from centralign.runtime.engine import OperatorEngine
from centralign.runtime.state import TaskStatus, StepStatus
from centralign.memory.store import CompanyMemory
from centralign.tools.secops_systems import reset_security_database

@pytest.fixture(autouse=True)
def clean_db():
    reset_security_database()

def test_engine_initialization():
    engine = OperatorEngine()
    assert engine.memory is not None
    assert engine.tools is not None
    assert engine.hitl is not None
    assert engine.verifier is not None

def test_secops_workflow():
    engine = OperatorEngine()
    goal = "Revoke access for Rahul Sharma"
    ctx = engine.run_goal(goal, auto_approve=True)
    assert ctx.status == TaskStatus.COMPLETED
    assert ctx.verification is not None
    assert ctx.verification.verified is True
