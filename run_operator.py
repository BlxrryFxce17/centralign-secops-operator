#!/usr/bin/env python3
"""
CentrAlign Autonomous Operator - CLI Runner
Allows command-line execution and live demonstration of the enterprise agent.
"""

import sys
import os
import argparse
import time

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from centralign.runtime.engine import OperatorEngine
from centralign.runtime.state import TaskStatus, StepStatus, TraceEvent, ExecutionContext

console = Console(highlight=False)

def format_event(event: TraceEvent):
    phase_colors = {
        TaskStatus.PENDING: "grey50",
        TaskStatus.UNDERSTANDING: "cyan",
        TaskStatus.PLANNING: "magenta",
        TaskStatus.EXECUTING: "blue",
        TaskStatus.OBSERVING: "green",
        TaskStatus.ADAPTING: "yellow",
        TaskStatus.AWAITING_APPROVAL: "bold red",
        TaskStatus.VERIFYING: "purple",
        TaskStatus.COMPLETED: "bold bright_green",
        TaskStatus.FAILED: "bold bright_red"
    }
    color = phase_colors.get(event.phase, "white")
    timestamp_str = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
    console.print(f"[{color}][{timestamp_str}] [{event.phase.value:<17}][/{color}] {event.message}")

def main():
    parser = argparse.ArgumentParser(description="CentrAlign AI - Autonomous Enterprise Operator")
    parser.add_argument("--scenario", choices=["standard_offboard", "high_risk_offboard", "custom"], default="standard_offboard",
                        help="Pre-configured enterprise scenario to run")
    parser.add_argument("--goal", type=str, default="", help="Custom goal prompt to execute")
    parser.add_argument("--auto-approve", action="store_true", help="Automatically approve Human-in-the-loop requests")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold white]CentrAlign Enterprise Operator Console[/bold white]\n"
        "[dim]Workflow: Understand -> Plan -> Execute -> Observe -> Adapt -> Verify -> Complete[/dim]",
        border_style="blue"
    ))

    if args.scenario == "standard_offboard":
        goal = args.goal or "Execute security offboarding for Ananya Roy (Product Engineer). Revoke all IAM access and SSO sessions."
    elif args.scenario == "high_risk_offboard":
        goal = args.goal or "Execute urgent security offboarding for Vikram Malhotra. Revoke AWS IAM access keys, terminate active Google Workspace sessions, and archive GitHub enterprise repo access."
    else:
        goal = args.goal or "Inspect incoming workspace data and verify security status."

    console.print(f"\n[bold]Target Objective:[/bold] [italic]\"{goal}\"[/italic]\n")

    engine = OperatorEngine(on_trace=lambda ev, ctx: format_event(ev))
    ctx = engine.run_goal(goal, auto_approve=args.auto_approve)

    # Handle Human-in-the-Loop if pending
    if ctx.status == TaskStatus.AWAITING_APPROVAL:
        console.print("\n" + "="*70)
        console.print("[bold red][!] HUMAN-IN-THE-LOOP APPROVAL REQUIRED[/bold red]")
        pending = list(engine.hitl.pending_approvals.values())
        if pending:
            req = pending[0]
            console.print(f"[bold]Request Title:[/bold] {req.title}")
            console.print(f"[bold]Details:[/bold] {req.details}")
            console.print(f"[bold]Payload:[/bold] {req.payload}")
            
            choice = input("\nDo you grant authorization to proceed? (Y/n): ").strip().lower()
            if choice in ["", "y", "yes"]:
                console.print("[green]Authorization granted by Operator. Resuming execution...[/green]\n")
                ctx = engine.resume_approved_task(ctx.task_id, req.request_id, feedback="Approved via CLI console.")
            else:
                console.print("[red]Authorization rejected. Halting task execution safely.[/red]")
                return

    # Print final verification table
    if ctx.verification:
        v_table = Table(title="Independent Verification & Ground Truth Audit", border_style="purple")
        v_table.add_column("Assertion", style="white")
        v_table.add_column("Status", justify="center")

        for d in ctx.verification.details:
            if "[PASS]" in d:
                v_table.add_row(d.replace("[PASS]", "").strip(), "[green]PASSED[/green]")
            else:
                v_table.add_row(d.replace("[FAIL]", "").strip(), "[red]FAILED[/red]")
        console.print("\n", v_table)

    console.print(Panel(
        f"[bold green]STATUS: {ctx.status.value}[/bold green]\n"
        f"[bold]Summary:[/bold] {ctx.final_summary}\n"
        f"[bold]Task ID:[/bold] {ctx.task_id}",
        title="Execution Outcome",
        border_style="green" if ctx.status == TaskStatus.COMPLETED else "red"
    ))

if __name__ == "__main__":
    main()
