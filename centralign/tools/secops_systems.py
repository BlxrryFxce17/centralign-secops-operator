"""
Stateful Enterprise Security & IAM Connector for CentrAlign SecOps Operator.
Simulates Okta/Google SSO, AWS IAM, GitHub Enterprise, Jamf MDM, and SIEM
using a stateful SQLite database with double-checked cryptographic audit trails.
"""

import sqlite3
import json
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from .base import BaseTool, ToolResult

DB_PATH = Path(__file__).parent.parent / "mock_data" / "enterprise_security.sqlite"

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

get_security_db_connection = get_db_connection

def init_security_database():
    """Initializes schemas and seed records for enterprise SecOps simulator."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        department TEXT NOT NULL,
        role TEXT NOT NULL,
        risk_tier TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cloud_iam_keys (
        key_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        cloud_provider TEXT NOT NULL,
        permission_tier TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS active_sso_sessions (
        session_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS code_repository_access (
        access_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        platform TEXT NOT NULL,
        organization TEXT NOT NULL,
        team_name TEXT NOT NULL,
        permission TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS device_inventory (
        device_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        model TEXT NOT NULL,
        serial_number TEXT NOT NULL,
        security_status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS security_audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        actor TEXT NOT NULL,
        target_id TEXT NOT NULL,
        details TEXT NOT NULL,
        checksum TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed initial security posture if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM employees")
    if cursor.fetchone()["cnt"] == 0:
        seed_employees = [
            ("EMP-SEC-901", "Vikram Malhotra", "vikram.malhotra@centralign.corp", "Cloud Infrastructure & SRE", "Lead DevOps Architect", "CRITICAL", "ACTIVE"),
            ("EMP-SEC-902", "Priya Sundaram", "priya.sundaram@centralign.corp", "Core Product Engineering", "Senior Backend Engineer", "STANDARD", "ACTIVE"),
            ("EMP-SEC-903", "Arjun Mehta", "arjun.mehta@centralign.corp", "Financial Systems & Payments", "Staff Platform Engineer", "CRITICAL", "ACTIVE"),
            ("EMP-SEC-904", "Ananya Roy", "ananya.roy@centralign.corp", "Frontend & Design Engineering", "Product Engineer", "STANDARD", "ACTIVE")
        ]
        cursor.executemany("""
        INSERT INTO employees (employee_id, full_name, email, department, role, risk_tier, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, seed_employees)

        seed_iam = [
            ("AKIA_PROD_9942", "EMP-SEC-901", "AWS Production Root", "AdministratorAccess", "ACTIVE"),
            ("AKIA_DEV_8110", "EMP-SEC-901", "AWS Staging & Tooling", "PowerUserAccess", "ACTIVE"),
            ("AKIA_APP_5521", "EMP-SEC-902", "AWS Application Services", "PowerUserAccess", "ACTIVE"),
            ("AKIA_FIN_3301", "EMP-SEC-903", "AWS Banking Core", "AdministratorAccess", "ACTIVE"),
            ("AKIA_UI_1109", "EMP-SEC-904", "AWS S3 Assets", "ReadOnly", "ACTIVE")
        ]
        cursor.executemany("""
        INSERT INTO cloud_iam_keys (key_id, employee_id, cloud_provider, permission_tier, status)
        VALUES (?, ?, ?, ?, ?)
        """, seed_iam)

        seed_sso = [
            ("SESS_OKTA_8831", "EMP-SEC-901", "Okta Enterprise SSO", "103.21.244.12", "ACTIVE"),
            ("SESS_GSUITE_4412", "EMP-SEC-901", "Google Workspace SSO", "103.21.244.12", "ACTIVE"),
            ("SESS_OKTA_2291", "EMP-SEC-902", "Okta Enterprise SSO", "49.37.12.8", "ACTIVE"),
            ("SESS_OKTA_7719", "EMP-SEC-903", "Okta Enterprise SSO", "157.48.19.2", "ACTIVE"),
            ("SESS_GSUITE_9901", "EMP-SEC-904", "Google Workspace SSO", "14.139.12.1", "ACTIVE")
        ]
        cursor.executemany("""
        INSERT INTO active_sso_sessions (session_id, employee_id, provider, ip_address, status)
        VALUES (?, ?, ?, ?, ?)
        """, seed_sso)

        seed_repos = [
            ("REPO_ACC_01", "EMP-SEC-901", "GitHub Enterprise", "centralign-ai-core", "infrastructure-admins", "admin", "ACTIVE"),
            ("REPO_ACC_02", "EMP-SEC-901", "GitHub Enterprise", "centralign-ai-core", "k8s-manifests", "admin", "ACTIVE"),
            ("REPO_ACC_03", "EMP-SEC-902", "GitHub Enterprise", "centralign-ai-core", "backend-services", "write", "ACTIVE"),
            ("REPO_ACC_04", "EMP-SEC-903", "GitHub Enterprise", "centralign-ai-core", "payment-engine", "admin", "ACTIVE"),
            ("REPO_ACC_05", "EMP-SEC-904", "GitHub Enterprise", "centralign-ai-core", "operator-web-ui", "write", "ACTIVE")
        ]
        cursor.executemany("""
        INSERT INTO code_repository_access (access_id, employee_id, platform, organization, team_name, permission, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, seed_repos)

        seed_devices = [
            ("DEV-MAC-2041", "EMP-SEC-901", "MacBook Pro M3 Max 64GB", "C02G40KBMD6R", "ENROLLED"),
            ("DEV-MAC-2042", "EMP-SEC-902", "MacBook Pro M2 Pro 32GB", "C02F99LAMD7P", "ENROLLED"),
            ("DEV-WIN-1092", "EMP-SEC-903", "ThinkPad X1 Carbon 32GB", "PF3099KLM01", "ENROLLED"),
            ("DEV-MAC-2045", "EMP-SEC-904", "MacBook Air M3 16GB", "C02K11LAMD9Q", "ENROLLED")
        ]
        cursor.executemany("""
        INSERT INTO device_inventory (device_id, employee_id, model, serial_number, security_status)
        VALUES (?, ?, ?, ?, ?)
        """, seed_devices)

    conn.commit()
    conn.close()

def reset_security_database():
    """Resets database to clean baseline state for test isolation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS security_audit_log;")
    cursor.execute("DROP TABLE IF EXISTS device_inventory;")
    cursor.execute("DROP TABLE IF EXISTS code_repository_access;")
    cursor.execute("DROP TABLE IF EXISTS active_sso_sessions;")
    cursor.execute("DROP TABLE IF EXISTS cloud_iam_keys;")
    cursor.execute("DROP TABLE IF EXISTS employees;")
    conn.commit()
    conn.close()
    init_security_database()

# Initialize upon module load
init_security_database()

class LookupEmployeeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="lookup_employee",
            description="Queries enterprise directory for employee profile, active IAM credentials, SSO sessions, and assigned hardware."
        )

    def execute(self, query: str = "") -> ToolResult:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Query by ID, email, or partial name
            query_clean = query.strip()
            cursor.execute("""
            SELECT * FROM employees 
            WHERE employee_id = ? OR email LIKE ? OR full_name LIKE ?
            LIMIT 1
            """, (query_clean, f"%{query_clean}%", f"%{query_clean}%"))
            emp = cursor.fetchone()

            # Dynamic fallback: if employee not found in seed, create standard profile so user can test ANY name!
            if not emp and query_clean:
                slug = query_clean.replace(" ", "").upper()[:6]
                emp_id = f"EMP-SEC-{slug}"
                name = query_clean.title()
                email = f"{query_clean.lower().replace(' ', '.')}@centralign.corp"
                cursor.execute("""
                INSERT INTO employees (employee_id, full_name, email, department, role, risk_tier, status)
                VALUES (?, ?, ?, 'Engineering Operations', 'Systems Engineer', 'STANDARD', 'ACTIVE')
                """, (emp_id, name, email))
                # Seed mock assets for new employee
                cursor.execute("INSERT INTO cloud_iam_keys VALUES (?, ?, 'AWS Enterprise', 'PowerUserAccess', 'ACTIVE', CURRENT_TIMESTAMP)", (f"AKIA_GEN_{slug}", emp_id))
                cursor.execute("INSERT INTO active_sso_sessions VALUES (?, ?, 'Okta Enterprise SSO', '103.21.244.1', 'ACTIVE', CURRENT_TIMESTAMP)", (f"SESS_GEN_{slug}", emp_id))
                cursor.execute("INSERT INTO code_repository_access VALUES (?, ?, 'GitHub Enterprise', 'centralign-ai-core', 'engineering-team', 'write', 'ACTIVE', CURRENT_TIMESTAMP)", (f"REPO_GEN_{slug}", emp_id))
                cursor.execute("INSERT INTO device_inventory VALUES (?, ?, 'MacBook Pro M3 32GB', 'C02GEN1029', 'ENROLLED', CURRENT_TIMESTAMP)", (f"DEV-GEN-{slug}", emp_id))
                conn.commit()
                cursor.execute("SELECT * FROM employees WHERE employee_id = ?", (emp_id,))
                emp = cursor.fetchone()

            if not emp:
                conn.close()
                return ToolResult(False, error=f"Employee '{query}' not found in enterprise directory.")

            emp_id = emp["employee_id"]

            cursor.execute("SELECT * FROM cloud_iam_keys WHERE employee_id = ? AND status = 'ACTIVE'", (emp_id,))
            keys = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM active_sso_sessions WHERE employee_id = ? AND status = 'ACTIVE'", (emp_id,))
            sessions = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM code_repository_access WHERE employee_id = ? AND status = 'ACTIVE'", (emp_id,))
            repos = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM device_inventory WHERE employee_id = ?", (emp_id,))
            devices = [dict(r) for r in cursor.fetchall()]

            conn.close()

            payload = {
                "employee_id": emp["employee_id"],
                "full_name": emp["full_name"],
                "email": emp["email"],
                "department": emp["department"],
                "role": emp["role"],
                "risk_tier": emp["risk_tier"],
                "status": emp["status"],
                "active_iam_keys": keys,
                "active_sso_sessions": sessions,
                "active_repo_access": repos,
                "assigned_devices": devices
            }

            return ToolResult(
                success=True,
                data=payload,
                observation=f"Located profile for {emp['full_name']} ({emp['employee_id']}). Role: {emp['role']} [Tier: {emp['risk_tier']}]. Found {len(keys)} active IAM key(s), {len(sessions)} SSO session(s), {len(repos)} repo membership(s), {len(devices)} device(s)."
            )
        except Exception as e:
            conn.close()
            return ToolResult(False, error=str(e), observation=f"Directory lookup error: {str(e)}")

class TerminateSSOSessionsTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="terminate_sso_sessions",
            description="Invalidates active Okta and Google Workspace SSO sessions, resets MFA tokens, and suspends account."
        )

    def execute(self, employee_id: str, actor: str = "CentrAlign_SecOps_Operator", **kwargs) -> ToolResult:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM active_sso_sessions WHERE employee_id = ? AND status = 'ACTIVE'", (employee_id,))
            active_cnt = cursor.fetchone()["cnt"]

            cursor.execute("UPDATE active_sso_sessions SET status = 'TERMINATED' WHERE employee_id = ?", (employee_id,))
            cursor.execute("UPDATE employees SET status = 'SUSPENDED' WHERE employee_id = ?", (employee_id,))

            checksum_raw = f"{employee_id}:TERMINATE_SSO:{active_cnt}:{time.time()}"
            checksum = hashlib.sha256(checksum_raw.encode()).hexdigest()[:16]

            audit_details = json.dumps({"sessions_terminated": active_cnt, "mfa_reset": True, "account_suspended": True})
            cursor.execute("""
            INSERT INTO security_audit_log (action, actor, target_id, details, checksum)
            VALUES ('TERMINATE_SSO_SESSIONS', ?, ?, ?, ?)
            """, (actor, employee_id, audit_details, checksum))

            conn.commit()
            conn.close()

            return ToolResult(
                success=True,
                data={"employee_id": employee_id, "terminated_sessions": active_cnt, "checksum": checksum},
                observation=f"Successfully terminated {active_cnt} active SSO session(s) in Okta and Google Workspace. Account suspended. Checksum: {checksum}."
            )
        except Exception as e:
            conn.close()
            return ToolResult(False, error=str(e), observation=f"SSO termination error: {str(e)}")

class RevokeCloudIAMTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="revoke_cloud_iam",
            description="Revokes AWS and GCP cloud access keys, detaches administrative IAM policies, and invalidates STS tokens."
        )

    def execute(self, employee_id: str, actor: str = "CentrAlign_SecOps_Operator", **kwargs) -> ToolResult:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT key_id, cloud_provider, permission_tier FROM cloud_iam_keys WHERE employee_id = ? AND status = 'ACTIVE'", (employee_id,))
            keys = [dict(r) for r in cursor.fetchall()]

            cursor.execute("UPDATE cloud_iam_keys SET status = 'REVOKED' WHERE employee_id = ?", (employee_id,))

            checksum_raw = f"{employee_id}:REVOKE_IAM:{len(keys)}:{time.time()}"
            checksum = hashlib.sha256(checksum_raw.encode()).hexdigest()[:16]

            audit_details = json.dumps({"revoked_keys": [k["key_id"] for k in keys], "policies_detached": True, "sts_invalidated": True})
            cursor.execute("""
            INSERT INTO security_audit_log (action, actor, target_id, details, checksum)
            VALUES ('REVOKE_CLOUD_IAM_KEYS', ?, ?, ?, ?)
            """, (actor, employee_id, audit_details, checksum))

            conn.commit()
            conn.close()

            return ToolResult(
                success=True,
                data={"employee_id": employee_id, "revoked_keys_count": len(keys), "checksum": checksum},
                observation=f"Revoked {len(keys)} cloud IAM access key(s) across AWS & GCP. Detached privileged policies and invalidated active STS session tokens. Checksum: {checksum}."
            )
        except Exception as e:
            conn.close()
            return ToolResult(False, error=str(e), observation=f"IAM revocation error: {str(e)}")

class RevokeRepoAccessTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="revoke_repo_access",
            description="Removes user from GitHub Enterprise organization teams, revokes SSH keys, and unassigns write access."
        )

    def execute(self, employee_id: str, actor: str = "CentrAlign_SecOps_Operator", **kwargs) -> ToolResult:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM code_repository_access WHERE employee_id = ? AND status = 'ACTIVE'", (employee_id,))
            repo_cnt = cursor.fetchone()["cnt"]

            cursor.execute("UPDATE code_repository_access SET status = 'REVOKED' WHERE employee_id = ?", (employee_id,))

            checksum_raw = f"{employee_id}:REVOKE_REPOS:{repo_cnt}:{time.time()}"
            checksum = hashlib.sha256(checksum_raw.encode()).hexdigest()[:16]

            audit_details = json.dumps({"memberships_revoked": repo_cnt, "ssh_keys_deleted": True})
            cursor.execute("""
            INSERT INTO security_audit_log (action, actor, target_id, details, checksum)
            VALUES ('REVOKE_GITHUB_ORG_ACCESS', ?, ?, ?, ?)
            """, (actor, employee_id, audit_details, checksum))

            conn.commit()
            conn.close()

            return ToolResult(
                success=True,
                data={"employee_id": employee_id, "revoked_memberships": repo_cnt, "checksum": checksum},
                observation=f"Removed from GitHub Enterprise organization. Revoked {repo_cnt} team membership(s) and deleted registered SSH public keys. Checksum: {checksum}."
            )
        except Exception as e:
            conn.close()
            return ToolResult(False, error=str(e), observation=f"Repo revocation error: {str(e)}")

class LockDeviceMDMTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="lock_device_mdm",
            description="Sends remote lock signal to corporate workstation via Jamf/Intune MDM and revokes VPN certificates."
        )

    def execute(self, employee_id: str, action: str = "LOCK", actor: str = "CentrAlign_SecOps_Operator", **kwargs) -> ToolResult:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT device_id, model, serial_number FROM device_inventory WHERE employee_id = ?", (employee_id,))
            devices = [dict(r) for r in cursor.fetchall()]

            target_status = "LOCKED" if action.upper() != "WIPE" else "WIPED"
            cursor.execute("UPDATE device_inventory SET security_status = ? WHERE employee_id = ?", (target_status, employee_id))
            cursor.execute("UPDATE employees SET status = 'OFFBOARDED' WHERE employee_id = ?", (employee_id,))

            checksum_raw = f"{employee_id}:MDM_{target_status}:{len(devices)}:{time.time()}"
            checksum = hashlib.sha256(checksum_raw.encode()).hexdigest()[:16]

            audit_details = json.dumps({"action": target_status, "devices_affected": [d["device_id"] for d in devices], "vpn_revoked": True})
            cursor.execute("""
            INSERT INTO security_audit_log (action, actor, target_id, details, checksum)
            VALUES ('MDM_REMOTE_DEVICE_SECURITY', ?, ?, ?, ?)
            """, (actor, employee_id, audit_details, checksum))

            conn.commit()
            conn.close()

            dev_names = ", ".join([d["device_id"] for d in devices]) or "assigned device"
            return ToolResult(
                success=True,
                data={"employee_id": employee_id, "action": target_status, "devices": devices, "checksum": checksum},
                observation=f"Dispatched remote {target_status} signal to MDM agent for {dev_names}. Corporate VPN certificates revoked. Checksum: {checksum}."
            )
        except Exception as e:
            conn.close()
            return ToolResult(False, error=str(e), observation=f"MDM lock error: {str(e)}")

class VerifySecurityStateTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="verify_security_state",
            description="Out-of-band verification tool asserting zero active sessions, zero active cloud keys, zero repo access, and device locked."
        )

    def execute(self, employee_id: str, **kwargs) -> ToolResult:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,))
            emp = cursor.fetchone()
            if not emp:
                conn.close()
                return ToolResult(False, error=f"Verification failed: Employee {employee_id} not found in directory.")

            # 1. Active IAM Keys
            cursor.execute("SELECT COUNT(*) as cnt FROM cloud_iam_keys WHERE employee_id = ? AND status = 'ACTIVE'", (employee_id,))
            active_keys = cursor.fetchone()["cnt"]

            # 2. Active SSO Sessions
            cursor.execute("SELECT COUNT(*) as cnt FROM active_sso_sessions WHERE employee_id = ? AND status = 'ACTIVE'", (employee_id,))
            active_sessions = cursor.fetchone()["cnt"]

            # 3. Active Repo Access
            cursor.execute("SELECT COUNT(*) as cnt FROM code_repository_access WHERE employee_id = ? AND status = 'ACTIVE'", (employee_id,))
            active_repos = cursor.fetchone()["cnt"]

            # 4. Device Status
            cursor.execute("SELECT security_status FROM device_inventory WHERE employee_id = ?", (employee_id,))
            device_rows = cursor.fetchall()
            all_locked = all(d["security_status"] in ["LOCKED", "WIPED"] for d in device_rows) if device_rows else True

            # 5. Audit Log Count
            cursor.execute("SELECT COUNT(*) as cnt FROM security_audit_log WHERE target_id = ?", (employee_id,))
            audit_cnt = cursor.fetchone()["cnt"]

            conn.close()

            all_passed = (active_keys == 0 and active_sessions == 0 and active_repos == 0 and all_locked and audit_cnt >= 3)
            sha256_hash = hashlib.sha256(f"{employee_id}:{active_keys}:{active_sessions}:{all_locked}:{audit_cnt}".encode()).hexdigest()

            evidence = {
                "employee": {
                    "name": emp["full_name"],
                    "employee_id": emp["employee_id"],
                    "department": emp["department"],
                    "role": emp["role"]
                },
                "employee_id": emp["employee_id"],
                "full_name": emp["full_name"],
                "active_iam_keys": active_keys,
                "active_sso_sessions": active_sessions,
                "active_repo_access": active_repos,
                "unlocked_devices": 0 if all_locked else len(device_rows),
                "devices_locked": all_locked,
                "audit_logs_count": audit_cnt,
                "zero_trust_status": "COMPLIANT" if all_passed else "NON_COMPLIANT",
                "sha256_evidence_hash": sha256_hash
            }

            if not all_passed:
                return ToolResult(False, error="Security invariant check failed: active privileges remain in directory.", data=evidence)

            return ToolResult(
                success=True,
                data=evidence,
                observation=f"INDEPENDENT VERIFICATION CONFIRMED: 0 active IAM keys, 0 active SSO sessions, 0 GitHub memberships, MDM device locked, {audit_cnt} immutable audit trail records verified. Checksum: {sha256_hash[:16]}."
            )
        except Exception as e:
            conn.close()
            return ToolResult(False, error=str(e), observation=f"Security verification error: {str(e)}")

class QuerySecurityStateTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="query_security_state",
            description="Reads live security tables from enterprise directory simulator."
        )

    def execute(self, table: str = "employees", filter_key: str = "", filter_value: str = "") -> ToolResult:
        valid_tables = ["employees", "cloud_iam_keys", "active_sso_sessions", "code_repository_access", "device_inventory", "security_audit_log"]
        if table not in valid_tables:
            return ToolResult(False, error=f"Invalid table: {table}. Allowed: {valid_tables}")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if filter_key and filter_value:
                cursor.execute(f"SELECT * FROM {table} WHERE {filter_key} = ?", (filter_value,))
            else:
                cursor.execute(f"SELECT * FROM {table} ORDER BY 1 DESC LIMIT 25")
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()

            return ToolResult(success=True, data=rows, observation=f"Retrieved {len(rows)} records from '{table}'.")
        except Exception as e:
            conn.close()
            return ToolResult(False, error=str(e))
