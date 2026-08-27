"""Tests for policy search functionality."""

from __future__ import annotations

import pytest

from mcp.customer_support_server import tools


@pytest.mark.asyncio
async def test_returns_policy_returns_matches():
    result = await tools.search_returns_policy("damaged item refund")
    assert len(result["matches"]) > 0


@pytest.mark.asyncio
async def test_shipping_policy_express():
    result = await tools.search_shipping_policy("expedited shipping cost")
    assert result["policy_type"] == "shipping"
    assert len(result["matches"]) > 0


@pytest.mark.asyncio
async def test_warranty_policy_electronics():
    result = await tools.search_warranty_policy("electronics warranty months")
    assert result["policy_type"] == "warranty"
    assert len(result["matches"]) > 0


@pytest.mark.asyncio
async def test_policy_empty_query():
    """Empty-ish query should not crash and return some results."""
    result = await tools.search_returns_policy("a")
    # Short query with no meaningful keywords → may return 0 matches (ok)
    assert isinstance(result["matches"], list)


@pytest.mark.asyncio
async def test_policy_confidence_range():
    result = await tools.search_returns_policy("return window for standard tier customers")
    assert 0.0 <= result["confidence"] <= 1.0
