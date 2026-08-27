"""Tests for the agent runner."""

from __future__ import annotations

import pytest

from cao.models import AgentProfile, MessageRole, TerminalStatus
from cao.runner import run_agent
from cao.session import create_session


@pytest.fixture()
def mock_profile():
    return AgentProfile(
        name="test-inventory",
        description="Inventory test agent",
        provider="mock",
        model="claude-sonnet-4-5",
        role="inventory",
        system_prompt="You are an inventory specialist",
    )


@pytest.mark.asyncio
async def test_runner_returns_string(mock_profile):
    session = await create_session()
    terminal = session.create_terminal(mock_profile)
    result = await run_agent(mock_profile, "check order ORD-1001", session, terminal)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_runner_records_messages(mock_profile):
    session = await create_session()
    terminal = session.create_terminal(mock_profile)
    await run_agent(mock_profile, "hello", session, terminal)
    roles = [m.role for m in terminal.messages]
    assert MessageRole.USER in roles
    assert MessageRole.AGENT in roles


@pytest.mark.asyncio
async def test_runner_with_none_profile():
    session = await create_session()
    terminal = session.create_terminal(None)
    result = await run_agent(None, "test message", session, terminal)
    assert "test message" in result
