"""Tests for refund eligibility and safety."""

from __future__ import annotations

import os

import pytest

from mcp.customer_support_server import tools


@pytest.mark.asyncio
async def test_refund_eligible_damaged():
    """Delivered order within return window should be eligible for 100% refund."""
    result = await tools.calculate_refund_eligibility("ORD-1001", "damaged")
    assert result["eligible"] is True
    assert result["eligible_amount"] == pytest.approx(289.97)


@pytest.mark.asyncio
async def test_refund_not_satisfied_half():
    """not_satisfied reason gets 50% refund."""
    result = await tools.calculate_refund_eligibility("ORD-1001", "not_satisfied")
    assert result["eligible"] is True
    assert result["eligible_amount"] == pytest.approx(289.97 * 0.5, abs=0.01)


@pytest.mark.asyncio
async def test_refund_not_delivered():
    """Shipped but not yet delivered order should not be eligible."""
    result = await tools.calculate_refund_eligibility("ORD-1002", "damaged")
    assert result["eligible"] is False
    assert "shipped" in result["reason_text"].lower() or "delivered" in result["reason_text"].lower()


@pytest.mark.asyncio
async def test_refund_order_not_found():
    result = await tools.calculate_refund_eligibility("ORD-9999", "damaged")
    assert result["eligible"] is False
    assert "not found" in result["reason_text"].lower()


@pytest.mark.asyncio
async def test_create_refund_dry_run_default(monkeypatch):
    """create_refund_request should always return dry_run=True by default."""
    monkeypatch.setenv("SUPPORTMESH_ALLOW_MUTATIONS", "false")
    result = await tools.create_refund_request("ORD-1001", "damaged")
    assert result["dry_run"] is True
    assert result["status"] == "proposed"


@pytest.mark.asyncio
async def test_create_refund_mutations_blocked(monkeypatch):
    """Even with dry_run=False, mutations must be blocked if env var is false."""
    monkeypatch.setenv("SUPPORTMESH_ALLOW_MUTATIONS", "false")
    monkeypatch.setenv("SUPPORTMESH_DRY_RUN", "false")
    result = await tools.create_refund_request("ORD-1001", "damaged", dry_run=False)
    assert result["dry_run"] is True
    assert result["status"] == "proposed"


@pytest.mark.asyncio
async def test_refund_high_value_requires_approval():
    """High-value orders (>$500) should set requires_approval=True."""
    result = await tools.calculate_refund_eligibility("ORD-1004", "damaged")
    assert result["eligible"] is True
    assert result["requires_approval"] is True
