"""
FastAPI Server & WebSocket Bridge for CentrAlign Operator Cockpit.
Provides real-time telemetry streaming, task dispatch, HITL approval resolution,
and ERP database inspection.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from centralign.runtime.engine import OperatorEngine
from centralign.runtime.state import TaskStatus, TraceEvent, ExecutionContext

from centralign.tools.secops_systems import get_security_db_connection, reset_security_database
from centralign.memory.store import CompanyMemory

app = FastAPI(title="CentrAlign Sentinel — Autonomous SecOps Operator", version="2.0.0")

# Mount web static directory
web_dir = Path(__file__).parent / "web"
app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

# Global active connections
active_websockets: List[WebSocket] = []
current_engine = OperatorEngine()
main_loop = None

async def broadcast(event_type: str, payload: Any):
    msg = json.dumps({"type": event_type, "data": payload})
    for ws in list(active_websockets):
        try:
            await ws.send_text(msg)
        except Exception:
            if ws in active_websockets:
                active_websockets.remove(ws)

def handle_engine_trace(event: TraceEvent, context: ExecutionContext):
    global main_loop
    payload = {
        "event": event.model_dump(),
        "task_status": context.status.value,
        "current_step": context.current_step_index,
        "plan": [s.model_dump() for s in (context.plan or [])],
        "task_id": context.task_id
    }
    if main_loop and main_loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(broadcast("TRACE_EVENT", payload), main_loop)
        except Exception as e:
            print(f"[Trace Error] {e}")

# Initialize engine with callback
current_engine.on_trace = handle_engine_trace

class RunTaskRequest(BaseModel):
    goal: str
    auto_approve: bool = False

class ApproveTaskRequest(BaseModel):
    task_id: str
    request_id: str
    feedback: str = "Approved by dashboard operator"

@app.get("/")
def get_dashboard():
    index_file = web_dir / "index.html"
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global main_loop
    main_loop = asyncio.get_running_loop()
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        # Send initial state
        await websocket.send_text(json.dumps({
            "type": "INIT_STATE",
            "data": {
                "company": current_engine.memory.get_company_info(),
                "tools": current_engine.tools.list_tools()
            }
        }))
        while True:
            # Keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)

@app.post("/api/run")
async def run_task(req: RunTaskRequest):
    global main_loop
    main_loop = asyncio.get_running_loop()
    loop = main_loop
    ctx = await loop.run_in_executor(None, current_engine.run_goal, req.goal, req.auto_approve)
    
    pending_approvals = [
        r.model_dump() for r in current_engine.hitl.pending_approvals.values()
    ]

    return {
        "task_id": ctx.task_id,
        "status": ctx.status.value,
        "summary": ctx.final_summary,
        "pending_approvals": pending_approvals,
        "verification": ctx.verification.model_dump() if ctx.verification else None,
        "plan": [s.model_dump() for s in (ctx.plan or [])]
    }

@app.post("/api/approve")
async def approve_task(req: ApproveTaskRequest):
    loop = asyncio.get_event_loop()
    try:
        ctx = await loop.run_in_executor(
            None, current_engine.resume_approved_task, req.task_id, req.request_id, req.feedback
        )
        return {
            "task_id": ctx.task_id,
            "status": ctx.status.value,
            "summary": ctx.final_summary,
            "verification": ctx.verification.model_dump() if ctx.verification else None,
            "plan": [s.model_dump() for s in (ctx.plan or [])]
        }
    except ValueError as e:
        return JSONResponse(
            status_code=404,
            content={"error": str(e), "message": "Task context expired. Please re-run the workflow."}
        )


@app.get("/api/secops/data")
def get_secops_data():
    conn = get_security_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM employees ORDER BY employee_id ASC")
    employees = [dict(r) for r in c.fetchall()]

    c.execute("SELECT * FROM cloud_iam_keys ORDER BY key_id ASC")
    cloud_keys = [dict(r) for r in c.fetchall()]

    c.execute("SELECT * FROM active_sso_sessions ORDER BY session_id ASC")
    sso_sessions = [dict(r) for r in c.fetchall()]

    c.execute("SELECT * FROM code_repository_access ORDER BY access_id ASC")
    repo_access = [dict(r) for r in c.fetchall()]

    c.execute("SELECT * FROM device_inventory ORDER BY device_id ASC")
    devices = [dict(r) for r in c.fetchall()]

    c.execute("SELECT * FROM security_audit_log ORDER BY log_id DESC LIMIT 30")
    audit_log = [dict(r) for r in c.fetchall()]
    conn.close()

    total_active_keys = sum(1 for k in cloud_keys if k.get("status") == "ACTIVE")
    total_active_sso = sum(1 for s in sso_sessions if s.get("status") == "ACTIVE")
    total_unlocked_dev = sum(1 for d in devices if d.get("security_status") != "REMOTE_LOCKED")

    return {
        "employees": employees,
        "cloud_keys": cloud_keys,
        "sso_sessions": sso_sessions,
        "repo_access": repo_access,
        "devices": devices,
        "audit_log": audit_log,
        "summary": {
            "total_employees": len(employees),
            "active_iam_keys": total_active_keys,
            "active_sso_sessions": total_active_sso,
            "unlocked_devices": total_unlocked_dev,
            "total_audit_events": len(audit_log)
        }
    }

@app.post("/api/secops/reset")
def reset_secops_db():
    reset_security_database()
    return {"status": "Enterprise Security database successfully reset to seed state."}


@app.get("/api/memory")
def get_memory():
    return {
        "company": current_engine.memory.get_company_info(),
        "memory": current_engine.memory.memory,
        "episodic_history": current_engine.memory.get_learnings()
    }

if __name__ == "__main__":
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser(description="CentrAlign Operator Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind server (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    args = parser.parse_args()

    uvicorn.run("server:app", host=args.host, port=args.port, reload=False)
