"""
Human-in-the-Loop (HITL) Governance and Policy Gatekeeper.
Evaluates high-risk actions against enterprise limits and manages
approval state transitions.
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
import uuid
import time

class ApprovalRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:6]}")
    task_id: str
    step_id: str
    title: str
    category: str # "FINANCIAL_THRESHOLD", "COMPLIANCE_RISK", "IRREVERSIBLE_ACTION"
    details: str
    payload: Dict[str, Any]
    status: str = "PENDING" # "PENDING", "APPROVED", "REJECTED"
    requested_at: float = Field(default_factory=time.time)
    resolved_at: Optional[float] = None
    resolver: Optional[str] = None
    feedback_notes: Optional[str] = None

class HITLManager:
    def __init__(self, auto_approve_all: bool = False):
        self.auto_approve_all = auto_approve_all
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalRequest] = []
        self.approved_step_ids: set[str] = set()

    def evaluate_action(self, task_id: str, step_id: str, tool_name: str, parameters: Dict[str, Any],
                        policies: Dict[str, Any]) -> Optional[ApprovalRequest]:
        """Checks if an action violates risk thresholds and requires human authorization."""
        if self.auto_approve_all or step_id in self.approved_step_ids:
            return None

        # 1. SecOps & CISO Emergency Access Revocation Authorization Check
        emp_name = parameters.get("employee_name") or parameters.get("name") or "Employee"
        emp_id = parameters.get("employee_id") or "EMP-ID"
        risk_tier = str(parameters.get("risk_tier", "")).upper()
        perm_tier = parameters.get("permission_tier") or parameters.get("role") or "PrivilegedAccess"

        if tool_name in ["revoke_cloud_iam", "lock_device_mdm"] or risk_tier == "CRITICAL" or "admin" in str(perm_tier).lower():
            if risk_tier == "CRITICAL" or "admin" in str(perm_tier).lower() or emp_id in ["EMP-2024-001", "EMP-2024-003"]:
                req = ApprovalRequest(
                    task_id=task_id,
                    step_id=step_id,
                    title=f"CISO Authorization Required: Critical Revocation for {emp_name}",
                    category="CISO_SECURITY_AUTHORIZATION",
                    details=f"Target employee '{emp_name}' ({emp_id}) holds {perm_tier} across Production Cloud Infrastructure. Emergency remote lock and key invalidation requires mandatory CISO sign-off per SOC2 Control CC6.1 / SEC-POL-04.",
                    payload=parameters
                )
                self.pending_approvals[req.request_id] = req
                return req

        # 2. Financial threshold check (e.g. invoice posting > ₹1,50,000)
        if tool_name == "post_invoice_erp":
            amount = float(parameters.get("amount", 0.0))
            threshold = 150000.0
            if amount > threshold:
                req = ApprovalRequest(
                    task_id=task_id,
                    step_id=step_id,
                    title=f"CFO Authorization Required: Ledger Posting of ₹{amount:,.2f} INR",
                    category="FINANCIAL_THRESHOLD",
                    details=f"Invoice {parameters.get('invoice_number')} for '{parameters.get('vendor_name')}' exceeds the autonomous limit of ₹{threshold:,.2f}. Manual CFO sign-off is mandatory per Corporate Financial Policy Section 2.",
                    payload=parameters
                )
                self.pending_approvals[req.request_id] = req
                return req

        # 3. High-Risk Compliance / Sanctions check
        if tool_name == "call_api" and "onboard" in str(parameters):
            risk_score = float(parameters.get("risk_score", 0.0))
            if risk_score > 65.0:
                req = ApprovalRequest(
                    task_id=task_id,
                    step_id=step_id,
                    title=f"Compliance Officer Review: High Risk Entity (Score {risk_score}/100)",
                    category="COMPLIANCE_RISK",
                    details="Vendor registration flagged with AML risk above threshold. Enhanced due diligence required.",
                    payload=parameters
                )
                self.pending_approvals[req.request_id] = req
                return req

        return None

    def approve(self, request_id: str, resolver: str = "Authorized_Manager", feedback: str = "Approved by human operator.") -> bool:
        if request_id in self.pending_approvals:
            req = self.pending_approvals.pop(request_id)
            req.status = "APPROVED"
            req.resolved_at = time.time()
            req.resolver = resolver
            req.feedback_notes = feedback
            self.approved_step_ids.add(req.step_id)
            self.approval_history.append(req)
            return True
        return False

    def reject(self, request_id: str, resolver: str = "Authorized_Manager", feedback: str = "Rejected by human operator.") -> bool:
        if request_id in self.pending_approvals:
            req = self.pending_approvals.pop(request_id)
            req.status = "REJECTED"
            req.resolved_at = time.time()
            req.resolver = resolver
            req.feedback_notes = feedback
            self.approval_history.append(req)
            return True
        return False
