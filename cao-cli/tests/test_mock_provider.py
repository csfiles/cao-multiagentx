"""Tests for the mock provider."""

from __future__ import annotations

import asyncio

import pytest

from cao.providers.mock import MockProvider
from cao.providers.base import ProviderConfig


@pytest.fixture()
def provider():
    return MockProvider()


@pytest.fixture()
def config():
    return ProviderConfig(
        model="claude-sonnet-4-5",
        system_prompt="",
        mcp_servers={},
    )


@pytest.mark.asyncio
async def test_mock_provider_name():
    assert MockProvider.name() == "mock"


@pytest.mark.asyncio
async def test_inventory_response(provider, config):
    config.system_prompt = "You are an inventory and order lookup specialist"
    resp = await provider.run_turn("Check order ORD-9999", config, [])
    assert "ORD" in resp.content
    assert resp.provider == "mock"


@pytest.mark.asyncio
async def test_returns_policy_response(provider, config):
    config.system_prompt = "You are a returns policy expert"
    resp = await provider.run_turn("What is the returns window?", config, [])
    assert "return" in resp.content.lower()


@pytest.mark.asyncio
async def test_refund_response_dry_run(provider, config):
    config.system_prompt = "You are a refund specialist"
    resp = await provider.run_turn("Process refund for damaged item", config, [])
    assert "DRY RUN" in resp.content or "refund" in resp.content.lower()


@pytest.mark.asyncio
async def test_communication_response(provider, config):
    config.system_prompt = "You are a customer communication and response drafting agent"
    resp = await provider.run_turn("Draft a response", config, [])
    assert len(resp.content) > 50


@pytest.mark.asyncio
async def test_fallback_response(provider, config):
    config.system_prompt = "You are a generic agent"
    resp = await provider.run_turn("Do something", config, [])
    assert resp.content  # non-empty
    assert resp.tokens_used >= 0
