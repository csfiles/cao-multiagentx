"""
Application-level models for the CLI and workflow layer.

These are distinct from the MCP server's models — they represent the
higher-level state managed by the support workflow.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IssueType(str, Enum):
    order_status = "order_status"
    refund_request = "refund_request"
    policy_question = "policy_question"
    damaged_item = "damaged_item"
    wrong_item = "wrong_item"
    shipping_delay = "shipping_delay"
    general = "general"


class SupportRequest(BaseModel):
    """Incoming customer support request."""

    customer_id: str
    message: str
    issue_type: IssueType = IssueType.general
    severity: IssueSeverity = IssueSeverity.medium
    order_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    """Result from a single agent in the workflow."""

    agent_name: str
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class CaseSummary(BaseModel):
    """Internal case summary assembled by the support workflow."""

    request: SupportRequest
    customer_data: dict[str, Any] | None = None
    order_data: dict[str, Any] | None = None
    policy_findings: list[dict[str, Any]] = Field(default_factory=list)
    refund_eligibility: dict[str, Any] | None = None
    refund_proposal: dict[str, Any] | None = None
    agent_results: list[AgentResult] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class SupportResponse(BaseModel):
    """Final customer-facing response."""

    request: SupportRequest
    case_summary: CaseSummary
    customer_message: str
    resolved: bool = False
    follow_up_required: bool = False
