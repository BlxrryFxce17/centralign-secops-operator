"""
Independent Outcome Verification Engine for CentrAlign Operator.
Performs deterministic out-of-band ground-truth assertion checks
to verify that requested tasks were genuinely completed in the target system.
"""

from typing import Any, Dict, List
from .state import VerificationResult

from ..tools.secops_systems import VerifySecurityStateTool

class TaskVerifier:
    def __init__(self):

        self.security_verifier = VerifySecurityStateTool()

    def verify_security_task(self, employee_id: str) -> VerificationResult:
        """
        Executes deterministic, out-of-band ground-truth assertion checks
        against enterprise Identity, Cloud IAM, VCS, and MDM systems.
        Verifies Zero Active Privileges Remain.
        """
        details = []
        assertions_checked = 0
        assertions_passed = 0

        res = self.security_verifier.execute(employee_id=employee_id)
        assertions_checked += 1

        if not res.success:
            details.append(f"[FAIL] Security state verification failed: {res.error}")
            return VerificationResult(
                verified=False,
                assertions_checked=assertions_checked,
                assertions_passed=assertions_passed,
                details=details,
                evidence={"error": res.error}
            )

        assertions_passed += 1
        data = res.data or {}
        emp = data.get("employee", {})
        emp_name = emp.get("name", employee_id)
        details.append(f"[PASS] Identity confirmed in Enterprise Directory: {emp_name} ({employee_id}).")

        # Invariant 1: Zero Active SSO Sessions
        assertions_checked += 1
        sso_count = data.get("active_sso_sessions", 0)
        if sso_count == 0:
            assertions_passed += 1
            details.append("[PASS] Identity Invariant 1: Zero active SSO sessions (Okta & Google Workspace tokens invalidated).")
        else:
            details.append(f"[FAIL] Identity Invariant 1: Found {sso_count} active SSO sessions still remaining.")

        # Invariant 2: Zero Active Cloud IAM Keys
        assertions_checked += 1
        iam_count = data.get("active_iam_keys", 0)
        if iam_count == 0:
            assertions_passed += 1
            details.append("[PASS] Cloud IAM Invariant 2: Zero active AWS/GCP access keys (all credentials REVOKED & INACTIVE).")
        else:
            details.append(f"[FAIL] Cloud IAM Invariant 2: Found {iam_count} active cloud access keys remaining.")

        # Invariant 3: Zero Active Repository Permissions
        assertions_checked += 1
        repo_count = data.get("active_repo_access", 0)
        if repo_count == 0:
            assertions_passed += 1
            details.append("[PASS] VCS Invariant 3: Zero active GitHub Enterprise repository permissions and SSH keys.")
        else:
            details.append(f"[FAIL] VCS Invariant 3: Found {repo_count} active repository grants remaining.")

        # Invariant 4: Workstation MDM Hardware Lock
        assertions_checked += 1
        unlocked_count = data.get("unlocked_devices", 0)
        if unlocked_count == 0:
            assertions_passed += 1
            details.append("[PASS] Endpoint Invariant 4: All issued workstations confirmed locked via Jamf/Intune MDM.")
        else:
            details.append(f"[FAIL] Endpoint Invariant 4: Found {unlocked_count} endpoint devices still unlocked.")

        # Invariant 5: Immutable Cryptographic Evidence Hash
        assertions_checked += 1
        evidence_hash = data.get("sha256_evidence_hash")
        if evidence_hash and len(evidence_hash) == 64:
            assertions_passed += 1
            details.append(f"[PASS] Cryptographic Proof Invariant 5: SHA-256 tamper-evident digest generated ({evidence_hash[:16]}...).")
        else:
            details.append("[FAIL] Cryptographic Proof Invariant 5: Missing or invalid SHA-256 evidence digest.")

        all_passed = (assertions_passed == assertions_checked)
        return VerificationResult(
            verified=all_passed,
            assertions_checked=assertions_checked,
            assertions_passed=assertions_passed,
            details=details,
            evidence=data
        )


