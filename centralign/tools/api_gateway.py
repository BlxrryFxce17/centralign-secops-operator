"""
Enterprise API Gateway & Compliance Connector for CentrAlign Operator.
Provides simulated external APIs, AML/Sanctions checks, webhooks,
and demonstrates self-healing error recovery (e.g. 429 rate limit backoff).
"""

import time
from typing import Any, Dict, Optional
from .base import BaseTool, ToolResult

class APIGatewayTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="call_api",
            description="Calls internal or external microservices (e.g. AML Sanctions database, KYC scoring, notification webhooks)."
        )
        self.call_counts = {}

    def execute(self, endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None,
                simulate_transient_error: bool = False) -> ToolResult:
        endpoint_clean = endpoint.strip().lower()
        self.call_counts[endpoint_clean] = self.call_counts.get(endpoint_clean, 0) + 1

        # Demonstrate real self-healing: if first call to sanctions API and simulate_transient_error is True, fail with 429, then succeed on retry!
        if simulate_transient_error and self.call_counts[endpoint_clean] == 1:
            return ToolResult(
                success=False,
                error="HTTP 429 Too Many Requests: Rate limit exceeded on compliance API gateway. Try after backoff.",
                observation="HTTP 429 Rate Limit encountered. Agent should back off and retry."
            )

        # 1. Sanctions / AML Check
        if "sanctions" in endpoint_clean or "kyc" in endpoint_clean:
            entity_name = payload.get("entity_name", "") if payload else ""
            country = payload.get("country", "") if payload else ""

            # Check if jurisdiction is restricted
            is_high_risk = "sanctioned" in country.lower() or "alpha" in country.lower() or "restricted" in country.lower()
            risk_score = 85.0 if is_high_risk else 12.5

            return ToolResult(
                success=True,
                data={
                    "entity_name": entity_name,
                    "country": country,
                    "risk_score": risk_score,
                    "aml_status": "FLAGGED_HIGH_RISK" if is_high_risk else "CLEAR",
                    "matched_watchlist": is_high_risk,
                    "regulatory_notes": "Entity located in jurisdiction subject to enhanced due diligence under Company SOP Section 4." if is_high_risk else "No sanctions or adverse media matches found."
                },
                observation=f"Sanctions API response for '{entity_name}': Risk Score = {risk_score} (Threshold: 65). Status: {'FLAGGED_HIGH_RISK' if is_high_risk else 'CLEAR'}."
            )

        # 2. Slack / Teams / Webhook notification
        elif "notify" in endpoint_clean or "webhook" in endpoint_clean:
            channel = payload.get("channel", "#enterprise-ops") if payload else "#enterprise-ops"
            msg = payload.get("message", "Task completed") if payload else "Task completed"
            return ToolResult(
                success=True,
                data={"channel": channel, "delivered": True, "timestamp": time.time()},
                observation=f"Delivered audit notification to {channel}: '{msg}'."
            )

        else:
            return ToolResult(
                success=True,
                data={"endpoint": endpoint, "status": "200 OK", "response": "Mock API completed successfully."},
                observation=f"API call to {endpoint} returned status 200 OK."
            )
