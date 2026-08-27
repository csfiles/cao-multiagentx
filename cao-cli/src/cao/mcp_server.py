"""CAO MCP Server — exposes assign/handoff/send_message orchestration tools.

This server is what agents declare as 'cao-mcp-server' in their mcpServers
frontmatter. It enables inter-agent communication patterns:

  assign(agent, message)      -> non-blocking, returns terminal_id
  handoff(agent, message)     -> blocking, returns agent result
  send_message(msg, recv_id)  -> delivers a message to a terminal/session inbox
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from cao.models import AgentProfile, TerminalStatus
from cao.profile import discover_profiles, load_profile
from cao.session import create_session, get_or_create_session

logger = logging.getLogger(__name__)

mcp = FastMCP("cao-mcp-server", version="1.0.0")

# Profile search paths — can be overridden by env
_PROFILE_PATHS = [
    Path(p) for p in os.environ.get("CAO_AGENT_PATHS", "agents:.").split(":")
]

_PROFILE_CACHE: dict[str, AgentProfile] = {}


def _get_profile(agent_name: str) -> AgentProfile:
    if agent_name not in _PROFILE_CACHE:
        profiles = discover_profiles(_PROFILE_PATHS)
        _PROFILE_CACHE.update(profiles)
    profile = _PROFILE_CACHE.get(agent_name)
    if profile is None:
        raise ValueError(
            f"Agent profile '{agent_name}' not found. "
            f"Searched: {[str(p) for p in _PROFILE_PATHS]}"
        )
    return profile


@mcp.tool()
async def assign(
    agent_name: str,
    message: str,
    session_id: str | None = None,
    caller_terminal_id: str | None = None,
) -> dict:
    """Non-blocking agent launch.

    Launches an agent in the background and returns immediately with the
    terminal_id. Use send_message to receive the result when the agent finishes.

    Args:
        agent_name: Name of the agent profile to launch.
        message: The task/message to send to the agent.
        session_id: CAO session ID (auto-created if not provided).
        caller_terminal_id: Terminal ID of the caller (for result routing).

    Returns:
        dict with terminal_id and session_id.
    """
    import asyncio

    profile = _get_profile(agent_name)
    session = await get_or_create_session(session_id)
    terminal = session.create_terminal(profile)
    terminal.caller_id = caller_terminal_id

    logger.info("assign: launching %s (terminal=%s)", agent_name, terminal.id)

    # Launch without awaiting
    asyncio.create_task(_run_and_deliver(session, terminal, message))

    return {
        "terminal_id": terminal.id,
        "session_id": session.id,
        "agent": agent_name,
        "status": "launched",
    }


@mcp.tool()
async def handoff(
    agent_name: str,
    message: str,
    session_id: str | None = None,
) -> dict:
    """Blocking agent execution.

    Launches an agent and waits for it to complete, then returns the result.
    Use this for sequential dependencies where you need the result before
    proceeding.

    Args:
        agent_name: Name of the agent profile to launch.
        message: The task/message to send to the agent.
        session_id: CAO session ID (auto-created if not provided).

    Returns:
        dict with agent result and metadata.
    """
    from datetime import datetime

    profile = _get_profile(agent_name)
    session = await get_or_create_session(session_id)
    terminal = session.create_terminal(profile)

    logger.info("handoff: running %s (terminal=%s)", agent_name, terminal.id)

    terminal.started_at = datetime.utcnow()
    from cao.runner import run_agent

    try:
        result = await run_agent(
            profile=profile,
            message=message,
            session=session,
            terminal=terminal,
        )
        terminal.finished_at = datetime.utcnow()
        return {
            "terminal_id": terminal.id,
            "session_id": session.id,
            "agent": agent_name,
            "status": "done",
            "result": result,
            "duration_ms": terminal.duration_ms,
        }
    except Exception as exc:
        terminal.finished_at = datetime.utcnow()
        return {
            "terminal_id": terminal.id,
            "session_id": session.id,
            "agent": agent_name,
            "status": "error",
            "error": str(exc),
        }


@mcp.tool()
async def send_message(
    message: str,
    receiver_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Deliver a message to a terminal or session inbox.

    Workers call this to return results to their caller. If receiver_id is
    omitted, the message is delivered to the session inbox (supervisor inbox).

    Args:
        message: The message content to deliver.
        receiver_id: Terminal ID of the recipient, or None for session inbox.
        session_id: CAO session ID.

    Returns:
        dict with delivery confirmation.
    """
    if not session_id:
        return {"status": "error", "error": "session_id required for send_message"}

    from cao.session import get_session

    session = await get_session(session_id)
    if session is None:
        return {"status": "error", "error": f"session {session_id} not found"}

    if receiver_id:
        terminal = session.get_terminal(receiver_id)
        if terminal is None:
            return {"status": "error", "error": f"terminal {receiver_id} not found"}
        from cao.models import MessageRole
        terminal.add_message(MessageRole.USER, message)
        logger.info("send_message: delivered to terminal %s", receiver_id)
    else:
        session.deliver_message("worker", message)
        logger.info("send_message: delivered to session inbox %s", session_id)

    return {"status": "delivered", "receiver_id": receiver_id or "inbox"}


@mcp.tool()
async def list_agents(search_path: str | None = None) -> dict:
    """List available agent profiles.

    Args:
        search_path: Directory to search (defaults to CAO_AGENT_PATHS).

    Returns:
        dict with list of agent names and descriptions.
    """
    paths = [Path(search_path)] if search_path else _PROFILE_PATHS
    profiles = discover_profiles(paths)
    return {
        "agents": [
            {"name": p.name, "description": p.description, "role": p.role}
            for p in profiles.values()
        ]
    }


async def _run_and_deliver(session, terminal, message: str) -> None:
    """Background task: run agent, deliver result to session inbox."""
    from datetime import datetime

    terminal.started_at = datetime.utcnow()
    from cao.runner import run_agent

    try:
        result = await run_agent(
            profile=terminal.profile,
            message=message,
            session=session,
            terminal=terminal,
        )
        terminal.finished_at = datetime.utcnow()
        session.deliver_message(
            terminal.id,
            f"[CAO Result from {terminal.profile.name if terminal.profile else 'agent'}] {result}",
        )
    except Exception as exc:
        terminal.finished_at = datetime.utcnow()
        session.deliver_message(terminal.id, f"[CAO Error from agent] {exc}")


def run_server() -> None:
    """Entry point for the cao-mcp-server command."""
    import logging

    logging.basicConfig(
        level=os.environ.get("CAO_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    logger.info("CAO MCP Server starting (agent paths: %s)", _PROFILE_PATHS)
    mcp.run()
