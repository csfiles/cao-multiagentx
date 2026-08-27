"""Tests for MCP server tool functions."""

from __future__ import annotations

import pytest

from mcp.customer_support_server import tools


# ---------------------------------------------------------------------------
# Customer tools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_customer_found():
    result = await tools.get_customer("CUST-001")
    assert result["id"] == "CUST-001"
    assert result["name"] == "Alice Johnson"
    assert result["tier"] == "premium"


@pytest.mark.asyncio
async def test_get_customer_not_found():
    result = await tools.get_customer("CUST-999")
    assert result["error"] == "not_found"
    assert result["customer_id"] == "CUST-999"


@pytest.mark.asyncio
async def test_get_customer_tier():
    result = await tools.get_customer_tier("CUST-001")
    assert result["tier"] == "premium"


@pytest.mark.asyncio
async def test_list_customer_orders():
    result = await tools.list_customer_orders("CUST-001")
    assert result["count"] >= 1
    order_ids = [o["id"] for o in result["orders"]]
    assert "ORD-1001" in order_ids


# ---------------------------------------------------------------------------
# Order tools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_order_found():
    result = await tools.get_order("ORD-1001")
    assert result["id"] == "ORD-1001"
    assert result["status"] == "delivered"
    assert result["total"] == pytest.approx(289.97)


@pytest.mark.asyncio
async def test_get_order_not_found():
    result = await tools.get_order("ORD-9999")
    assert result["error"] == "not_found"


@pytest.mark.asyncio
async def test_get_order_status():
    result = await tools.get_order_status("ORD-1001")
    assert result["status"] == "delivered"
    assert result["tracking_number"] is not None


@pytest.mark.asyncio
async def test_get_order_items():
    result = await tools.get_order_items("ORD-1001")
    assert result["item_count"] == 2
    names = [i["name"] for i in result["items"]]
    assert "Wireless Noise-Cancelling Headphones" in names


# ---------------------------------------------------------------------------
# Policy tools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_returns_policy():
    result = await tools.search_returns_policy("return window premium")
    assert result["policy_type"] == "returns"
    assert isinstance(result["matches"], list)
    assert result["confidence"] >= 0.0


@pytest.mark.asyncio
async def test_search_shipping_policy():
    result = await tools.search_shipping_policy("express delivery cutoff")
    assert result["policy_type"] == "shipping"
    assert isinstance(result["matches"], list)


@pytest.mark.asyncio
async def test_search_warranty_policy():
    result = await tools.search_warranty_policy("electronics warranty period")
    assert result["policy_type"] == "warranty"
    assert isinstance(result["matches"], list)
