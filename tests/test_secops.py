import pytest
from centralign.runtime.engine import OperatorEngine
from centralign.runtime.state import TaskStatus, StepStatus
from centralign.memory.store import CompanyMemory
from centralign.tools.secops_systems import reset_security_database, get_security_db_connection
from centralign.runtime.verifier import TaskVerifier

@pytest.fixture(autouse=True)
def clean_db():
    reset_security_database()

def test_secops_engine_initialization():
    engine = OperatorEngine()
    assert "lookup_employee" in engine.tools.tools
    assert "terminate_sso_sessions" in engine.tools.tools
    assert "revoke_cloud_iam" in engine.tools.tools
    assert "revoke_repo_access" in engine.tools.tools
    assert "lock_device_mdm" in engine.tools.tools
    assert "verify_security_state" in engine.tools.tools

def test_critical_offboarding_ciso_escalation_and_approval():
    engine = OperatorEngine()
    goal = "Execute emergency offboarding and privileged access revocation for Vikram Malhotra. Invalidate active SSO sessions across Okta and Google Workspace, revoke AWS production root keys, wipe GitHub repo access, and dispatch MDM remote hardware lock."
    ctx = engine.run_goal(goal, auto_approve=False)

    # 1. Must pause for CISO authorization
    assert ctx.status == TaskStatus.AWAITING_APPROVAL
    assert len(engine.hitl.pending_approvals) == 1

    pending_req = list(engine.hitl.pending_approvals.values())[0]
    assert pending_req.category == "CISO_SECURITY_AUTHORIZATION"
    assert "Vikram Malhotra" in pending_req.title or "Vikram Malhotra" in pending_req.details
    assert pending_req.payload["employee_id"] == "EMP-SEC-901"

    # 2. CISO authorizes emergency access revocation
    ctx_resumed = engine.resume_approved_task(
        task_id=ctx.task_id,
        request_id=pending_req.request_id,
        feedback="Emergency revocation authorized by CISO per SOC2 SEC-POL-04."
    )

    # 3. Assert complete execution and 100% verified invariants
    assert ctx_resumed.status == TaskStatus.COMPLETED
    assert ctx_resumed.verification is not None
    assert ctx_resumed.verification.verified is True
    assert ctx_resumed.verification.assertions_passed >= 5

    # 4. Verify ground truth in enterprise database
    conn = get_security_db_connection()
    c = conn.cursor()
    c.execute("SELECT status FROM employees WHERE employee_id = 'EMP-SEC-901'")
    assert c.fetchone()["status"] in ["SUSPENDED", "OFFBOARDED", "REVOKED"]

    c.execute("SELECT COUNT(*) as cnt FROM cloud_iam_keys WHERE employee_id = 'EMP-SEC-901' AND status = 'ACTIVE'")
    assert c.fetchone()["cnt"] == 0

    c.execute("SELECT COUNT(*) as cnt FROM active_sso_sessions WHERE employee_id = 'EMP-SEC-901' AND status = 'ACTIVE'")
    assert c.fetchone()["cnt"] == 0

    c.execute("SELECT security_status FROM device_inventory WHERE employee_id = 'EMP-SEC-901'")
    assert c.fetchone()["security_status"] in ["LOCKED", "REMOTE_LOCKED"]
    conn.close()

def test_standard_offboarding_soc2_fast_path():
    engine = OperatorEngine()
    # Standard role (Priya Sundaram) follows autonomous fast path
    goal = "Process standard SOC2 access de-provisioning for Priya Sundaram."
    ctx = engine.run_goal(goal, auto_approve=False)

    # Should complete autonomously without pausing
    assert ctx.status == TaskStatus.COMPLETED
    assert ctx.verification is not None
    assert ctx.verification.verified is True
    assert "Priya Sundaram" in ctx.final_summary

def test_siem_gateway_self_healing_backoff():
    engine = OperatorEngine()
    goal = "Execute threat containment for Arjun Mehta following compromised credential telemetry. Query SIEM Threat Intel Gateway with adaptive backoff recovery, revoke cloud IAM keys, and dispatch remote lock."
    ctx = engine.run_goal(goal, auto_approve=True)

    assert ctx.status == TaskStatus.COMPLETED
    # Check that self-healing adaptation was recorded in traces
    adapt_events = [e for e in ctx.trace if e.phase == TaskStatus.ADAPTING]
    assert len(adapt_events) >= 1
    assert ctx.verification.verified is True

def test_zero_hardcoding_dynamic_employee_revocation():
    engine = OperatorEngine()
    # Completely new employee not present in seed database
    goal = "Emergency access revocation and hardware lock for Rohan Gupta across all identity and infrastructure providers."
    ctx = engine.run_goal(goal, auto_approve=True)

    assert ctx.status == TaskStatus.COMPLETED
    assert ctx.verification is not None
    assert ctx.verification.verified is True
    assert "Rohan Gupta" in ctx.final_summary

    # Verify Rohan was dynamically provisioned and subsequently purged in SQLite
    conn = get_security_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE full_name LIKE '%Rohan Gupta%'")
    emp = c.fetchone()
    assert emp is not None
    assert emp["status"] in ["SUSPENDED", "OFFBOARDED", "REVOKED"]
    conn.close()
