"""Tests for session and terminal management."""

from __future__ import annotations

import asyncio

import pytest

from cao.models import AgentProfile, MessageRole, TerminalStatus
from cao.session import close_session, create_session, get_session


@pytest.fixture()
def profile():
    return AgentProfile(
        name="test-agent",
        description="Test",
        provider="mock",
        model="claude-sonnet-4-5",
        role="tester",
    )


@pytest.mark.asyncio
async def test_create_session_returns_unique_ids():
    s1 = await create_session()
    s2 = await create_session()
    assert s1.id != s2.id


@pytest.mark.asyncio
async def test_get_session_returns_same_object():
    session = await create_session()
    fetched = await get_session(session.id)
    assert fetched is session


@pytest.mark.asyncio
async def test_get_session_unknown_returns_none():
    result = await get_session("no-such-id")
    assert result is None


@pytest.mark.asyncio
async def test_create_terminal(profile):
    session = await create_session()
    terminal = session.create_terminal(profile)
    assert terminal.id in session.terminals
    assert terminal.profile is profile
    assert terminal.status == TerminalStatus.PENDING


@pytest.mark.asyncio
async def test_add_message_to_terminal(profile):
    session = await create_session()
    terminal = session.create_terminal(profile)
    terminal.add_message(MessageRole.USER, "hello")
    assert len(terminal.messages) == 1
    assert terminal.messages[0].content == "hello"
    assert terminal.messages[0].role == MessageRole.USER


@pytest.mark.asyncio
async def test_deliver_message_to_inbox():
    session = await create_session()
    session.deliver_message("t1", "task complete")
    assert len(session.inbox) == 1
    assert "task complete" in session.inbox[0]


@pytest.mark.asyncio
async def test_close_session(profile):
    session = await create_session()
    sid = session.id
    await close_session(sid)
    assert await get_session(sid) is None
