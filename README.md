# CentrAlign AI — Autonomous SecOps & Identity Operator

An autonomous enterprise AI employee runtime built from first principles to turn unstructured security objectives into verified outcomes across company tools, APIs, files, and IAM systems.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Pytest](https://img.shields.io/badge/pytest-passing-brightgreen.svg)](https://pytest.org)

---

## 🌟 Executive Summary

CentrAlign AI is pioneering the transition from chat assistants that generate passive text to **autonomous AI employees** that execute complete business workflows, resolve unstated company context, respect governance policies, recover from runtime errors, and independently verify ground truth.

**CentrAlign SecOps Operator** is an implementation of this vision for security operations. It is built around a rigorous 8-stage cognitive execution loop:

$$\text{Goal} \longrightarrow \text{Understand} \longrightarrow \text{Plan} \longrightarrow \text{Execute} \longrightarrow \text{Observe} \longrightarrow \text{Adapt} \longrightarrow \text{Verify} \longrightarrow \text{Complete}$$

---

## 🚀 Key Capabilities Demonstrated

1. **Unstated Company Context & Entity Resolution**:
   - Discovers implicit corporate policies (e.g., security protocols, IAM constraints) from persistent company memory.
   - Resolves colloquial aliases to actual employee IDs and roles (e.g. "Vikram" -> "EMP-SEC-901").

2. **Autonomous Tool Selection & Multi-Modal Execution**:
   - Operates a stateful enterprise SQLite security ledger (Okta, AWS IAM, GitHub, Jamf MDM simulators).
   - Validates multi-factor authentications and revokes access privileges deterministically.

3. **Self-Healing Error Recovery (Adaptation Loop)**:
   - When encountering transient errors (e.g., HTTP 429 rate limit or schema changes), the operator detects the failure, enters the `ADAPTING` phase, computes an alternative path with exponential backoff, and completes the mission.

4. **Human-in-the-Loop (HITL) Governance Gatekeeper**:
   - Security limits are enforced: any CRITICAL tier or AdministratorAccess revocation automatically pauses execution into `AWAITING_APPROVAL`.
   - The operator presents human approvers with the exact reasoning and security rationale, resuming instantly once signed off by a CISO/Admin.

5. **Independent Out-of-Band Outcome Verification**:
   - The operator does not simply believe tool returns. An independent `TaskVerifier` performs out-of-band SQL assertions against the security database to cryptographically verify zero active privileges and immutable audit trail presence.

---

## 🛠️ Quickstart Guide

### 1. Requirements
- Python 3.10+ (Tested on Python 3.12)
- Modern Web Browser (Chrome, Edge, Firefox)

### 2. Setup
Clone the repository and install dependencies using standard pip:

```bash
git clone https://github.com/your-org/centralign-ai.git
cd centralign-ai
pip install -r requirements.txt
```

### 3. Run the Security Dashboard Server
Start the FastAPI orchestration server (which hosts the dashboard UI):

```bash
python server.py --port 8000
```
Then navigate to: http://127.0.0.1:8000/

### 4. Run the Agent (Terminal Mode)
To run headless tasks directly in the terminal without the UI:
```bash
python run_operator.py
```

---

## 🏗️ Repository Structure

- `centralign/runtime/`: The core cognitive engine (`engine.py`), HITL gatekeeper, state manager, and verifier.
- `centralign/tools/`: The capability mesh (SecOps APIs, Memory, etc.).
- `centralign/memory/`: Semantic memory store mapping policies and organization structure.
- `centralign/llm/`: The determinisic engine and provider adapters.
- `web/`: The beautiful glassmorphism React/Vanilla-JS user interface.
- `tests/`: End-to-end Pytest suite verifying execution paths and invariants.

## 🛡️ License

This project is licensed under the MIT License.
