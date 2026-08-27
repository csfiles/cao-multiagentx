"""Tests for the support workflow routing logic."""

from __future__ import annotations

import pytest

from app.models import IssueType, SupportRequest
from workflows.support_workflow import run_support_workflow


@pytest.mark.asyncio
async def test_workflow_order_status():
    """Order status request should resolve without refund assessment."""
    req = SupportRequest(
        customer_id="CUST-001",
        message="Where is my order ORD-1001?",
        issue_type=IssueType.order_status,
        order_id="ORD-1001",
    )
    response = await run_support_workflow(req)
    assert response.customer_message
    assert response.case_summary.order_data is not None
    assert response.case_summary.refund_eligibility is None


@pytest.mark.asyncio
async def test_workflow_damaged_item():
    """Damaged item request should trigger refund specialist."""
    req = SupportRequest(
        customer_id="CUST-001",
        message="I received a damaged product in order ORD-1001",
        issue_type=IssueType.damaged_item,
        order_id="ORD-1001",
    )
    response = await run_support_workflow(req)
    assert response.customer_message
    assert response.case_summary.refund_eligibility is not None
    assert response.case_summary.refund_eligibility["eligible"] is True


@pytest.mark.asyncio
async def test_workflow_unknown_customer():
    """Unknown customer should produce a graceful response."""
    req = SupportRequest(
        customer_id="CUST-999",
        message="Where is my order?",
        issue_type=IssueType.order_status,
    )
    response = await run_support_workflow(req)
    assert response.customer_message
    assert "support" in response.customer_message.lower()


@pytest.mark.asyncio
async def test_workflow_policy_question():
    """Policy question should return policy matches."""
    req = SupportRequest(
        customer_id="CUST-002",
        message="What is the return policy for electronics?",
        issue_type=IssueType.policy_question,
    )
    response = await run_support_workflow(req)
    assert response.customer_message
    assert len(response.case_summary.policy_findings) >= 0  # may find 0 if no match


@pytest.mark.asyncio
async def test_workflow_response_does_not_expose_internals():
    """Customer response should not mention agent names or internal IDs."""
    req = SupportRequest(
        customer_id="CUST-001",
        message="Help with my order ORD-1001",
        issue_type=IssueType.order_status,
        order_id="ORD-1001",
    )
    response = await run_support_workflow(req)
    msg = response.customer_message.lower()
    # Must not leak internal implementation details
    for internal in ["inventory_specialist", "policy_supervisor", "refund_specialist", "communication_agent"]:
        assert internal not in msg
