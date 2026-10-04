"""
Company Memory Store for CentrAlign Autonomous Operator.
Maintains persistent company knowledge: SOPs, compliance policies,
financial thresholds, entity alias mappings, and episodic memory.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

class CompanyMemory:
    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            data_path = str(Path(__file__).parent.parent / "mock_data" / "security_sop.json")
        self.data_path = Path(data_path)
        self.memory: Dict[str, Any] = {}
        self.episodic_history: List[Dict[str, Any]] = []
        self.load()

    def load(self):
        if self.data_path.exists():
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.memory = json.load(f)
        # Also try loading legacy company_sop for backward compatibility
        legacy_path = self.data_path.parent / "company_sop.json"
        if legacy_path.exists() and "vendor_aliases" not in self.memory:
            try:
                with open(legacy_path, "r", encoding="utf-8") as f:
                    legacy_data = json.load(f)
                    for k, v in legacy_data.items():
                        if k not in self.memory:
                            self.memory[k] = v
            except Exception:
                pass

    def get_company_info(self) -> Dict[str, Any]:
        return {
            "name": self.memory.get("organization_name") or self.memory.get("company_name", "CentrAlign Corp"),
            "security_framework": self.memory.get("security_framework", "SOC2 Type II & ISO 27001"),
            "policies": self.memory.get("security_policies", {})
        }

    def resolve_employee_target(self, query: str) -> Optional[Dict[str, Any]]:
        """Resolves natural language employee references to official directory record."""
        query_clean = query.strip().lower()
        directory = self.memory.get("employee_directory", {})
        for emp_id, profile in directory.items():
            if (emp_id.lower() in query_clean or 
                query_clean in emp_id.lower() or 
                profile.get("full_name", "").lower() in query_clean or 
                query_clean in profile.get("full_name", "").lower() or
                query_clean in profile.get("email", "").lower()):
                res = dict(profile)
                res["employee_id"] = emp_id
                return res
        return None

    def resolve_vendor_alias(self, alias: str) -> Optional[Dict[str, Any]]:
        """Resolves colloquial or unstated vendor names to official corporate entity."""
        alias_clean = alias.strip().lower()
        aliases = self.memory.get("vendor_aliases", {})
        for key, val in aliases.items():
            if key in alias_clean or alias_clean in key or alias_clean in val.get("official_name", "").lower():
                return val
        return None

    def query_relevant_policies(self, context_keywords: List[str]) -> List[Dict[str, Any]]:
        """Returns relevant corporate and security governance policies."""
        relevant = []
        keywords_lower = [k.lower() for k in context_keywords]

        # SecOps / Zero Trust / Offboarding policies
        if any(k in ["offboard", "terminate", "revoke", "iam", "sso", "security", "access", "lock", "breach", "credential"] for k in keywords_lower):
            sec = self.memory.get("security_policies", {})
            relevant.append({
                "type": "SECOPS_ZERO_TRUST_POLICY",
                "rules": sec,
                "summary": f"SOC2 Rule: Revoke credentials within 15 min. CISO Approval required for CRITICAL roles ({sec.get('escalation_thresholds', {}).get('require_ciso_approval_roles')}) or AdministratorAccess."
            })

        # Financial / Invoice policies (legacy support)
        if any(k in ["invoice", "payment", "bill", "vendor", "po", "purchase", "amount"] for k in keywords_lower):
            fin = self.memory.get("financial_policies", {})
            relevant.append({
                "type": "FINANCIAL_POLICY",
                "rules": fin,
                "summary": f"Expenditure threshold: Auto < ₹50,000, CFO approval required above ₹1,50,000."
            })

        # Relevant SOPs
        sops = self.memory.get("standard_operating_procedures", {})
        for sop_name, steps in sops.items():
            sop_name_words = sop_name.lower().split("_")
            if any(w in keywords_lower for w in sop_name_words):
                relevant.append({
                    "type": "STANDARD_OPERATING_PROCEDURE",
                    "procedure_name": sop_name,
                    "steps": steps
                })

        return relevant

    def record_learning(self, task_id: str, insight: str, outcome: str):
        """Persists episodic memory from execution outcomes to continuously adapt."""
        entry = {
            "task_id": task_id,
            "insight": insight,
            "outcome": outcome
        }
        self.episodic_history.append(entry)

    def get_learnings(self) -> List[Dict[str, Any]]:
        return self.episodic_history
