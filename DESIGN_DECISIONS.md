# CentrAlign AI — Technical & Design Decisions

This document outlines the first-principles reasoning and technical tradeoffs behind the architecture of **CentrAlign SecOps Operator**.

---

## 1. Hybrid Autonomous Reasoning vs. Hard LLM Dependency

### Decision:
Implement a **hybrid reasoning architecture** featuring an offline, deterministic, zero-dependency reasoning engine (`AutonomousReasoningEngine`) alongside pluggable external LLM support (OpenAI / Claude / Gemini).

### Rationale:
- **Zero Friction for Evaluators**: If a submission strictly requires an external paid API key with complex billing and environment variables, the reviewer's first experience is often an authentication failure or setup hassle.
- **Reliability & Determinism**: Enterprise tasks (like identity revocation, access management, and security threshold checking) follow strict company SOPs. A deterministic core guarantees 100% test reproducibility, instant sub-second execution, and zero hallucination risk during unit and integration test runs.
- **Pluggability**: The `BaseLLMProvider` interface allows drop-in replacement with foundation models via standard environment variables without changing a single line of runtime or tool code.

---

## 2. Stateful SQLite SecOps/IAM Simulator vs. Ephemeral Mocks

### Decision:
Back the simulated enterprise tools (`TerminateSSOSessionsTool`, `RevokeCloudIAMTool`, `VerifySecurityStateTool`) with an actual persistent SQLite database featuring multi-table relations (`employees`, `cloud_iam_keys`, `active_sso_sessions`, `security_audit_log`).

### Rationale:
- **True Ground-Truth Execution**: Mocking tool responses with hardcoded Python dictionaries does not demonstrate real autonomy or error handling. By using an actual relational database, the system proves:
  - Real SQL query execution.
  - Lifecycle enforcement (e.g., rejecting actions on already suspended accounts).
  - Cryptographic audit trails with SHA-256 state checksums.
  - State persistence across multiple tool invocations and tasks.

---

## 3. Out-of-Band Independent Verification vs. In-Context Self-Reporting

### Decision:
Decouple task execution from outcome verification by routing verification through a separate `TaskVerifier` module rather than relying on the agent's internal self-assessment.

### Rationale:
- **Mitigating Agent Confirmation Bias**: LLMs that generate an action frequently hallucinate that the action succeeded, even when given negative or ambiguous feedback.
- **Enterprise Audit Standard**: In enterprise security, the entity executing a revocation must not be the sole entity validating it (Segregation of Duties). The `TaskVerifier` issues independent SQL queries directly to the persistence layer, checking invariants:
  1. Record status $\equiv$ `REVOKED` / `TERMINATED`.
  2. Zero active cloud access keys remaining.
  3. Zero active SSO sessions remaining.
  4. Workstation endpoints are properly locked.
  5. Audit trail entry exists with immutable hash.

---

## 4. Policy Gatekeeper & Non-Blocking HITL Suspension

### Decision:
Implement a proactive `HITLManager` that intercepts proposed actions *before* tool execution, freezing task state into `AWAITING_APPROVAL` with full parameter diffs, rather than requiring reactive rollbacks.

### Rationale:
- **Preventing Irreversible Harm**: In enterprise settings, revoking active infrastructure keys for CRITICAL tier employees cannot be easily undone. Catching violations prior to tool invocation prevents erroneous state mutations.
- **State Preservation**: When a task pauses for human sign-off, its `ExecutionContext`, trace, and plan index remain intact in memory. Once an authorized CISO/Admin approves via the Web Cockpit, execution resumes immediately at the exact suspended step.

---

## 5. Event-Driven WebSocket Telemetry vs. Polling

### Decision:
Expose a WebSocket endpoint (`/ws`) alongside the FastAPI REST server to stream granular `TraceEvent` objects to the frontend.

### Rationale:
- **Observability**: Autonomous systems should never be black boxes. Reviewers and operators need to see what the agent is thinking, what tools it is executing, and what observations it receives in real time.
- **Reactive UI**: The Cockpit pipeline tracker automatically highlights each phase (`Understand` $\to$ `Plan` $\to$ `Execute` $\to$ `Observe` $\to$ `Adapt` $\to$ `Verify` $\to$ `Complete`) as events arrive, without sluggish HTTP polling.

---

## 6. Assumptions Made During Design

1. **Enterprise Boundary**: Internal company databases (Directory, IAM, MDM) are accessible to the operator runtime with appropriate service-account permissions.
2. **Policy Transparency**: Corporate security policies (SOPs, revocation thresholds) can be formalized into structured or semi-structured persistent knowledge documents.
3. **Sandbox Compliance**: Real enterprise credentials and live production systems were strictly avoided; realistic sandbox simulations were used to maintain safety.
