import pytest
from centralign.runtime.engine import OperatorEngine
from centralign.runtime.state import TaskStatus, StepStatus
from centralign.tools.secops_systems import reset_security_database

@pytest.fixture(autouse=True)
def clean_db():
    reset_security_database()

def test_hitl_blocks_high_risk_secops():
    engine = OperatorEngine()
    goal = "Revoke access for Vikram Malhotra"
    ctx = engine.run_goal(goal, auto_approve=False)

    # Must pause in AWAITING_APPROVAL because Vikram is CRITICAL tier / AdministratorAccess
    assert ctx.status == TaskStatus.AWAITING_APPROVAL
    assert len(engine.hitl.pending_approvals) == 1

    pending_req = list(engine.hitl.pending_approvals.values())[0]
    assert pending_req.category == "CISO_SECURITY_AUTHORIZATION"

    # Simulate Human CISO granting approval
    ctx_resumed = engine.resume_approved_task(
        task_id=ctx.task_id,
        request_id=pending_req.request_id,
        feedback="Authorized by CISO for emergency containment."
    )

    assert ctx_resumed.status == TaskStatus.COMPLETED
    assert ctx_resumed.verification.verified is True
