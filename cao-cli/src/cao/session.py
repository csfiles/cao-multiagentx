"""Session management for CAO orchestration runs."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from cao.models import AgentProfile, Session, Terminal, TerminalStatus

logger = logging.getLogger(__name__)

# Global session store (in-process, single server instance)
_sessions: dict[str, Session] = {}
_lock = asyncio.Lock()


async def create_session() -> Session:
    """Create and register a new session."""
    import uuid

    async with _lock:
        session = Session(session_id=str(uuid.uuid4())[:12])
        _sessions[session.id] = session
        logger.info("created session %s", session.id)
        return session


async def get_session(session_id: str) -> Session | None:
    return _sessions.get(session_id)


async def get_or_create_session(session_id: str | None) -> Session:
    if session_id:
        session = await get_session(session_id)
        if session:
            return session
    return await create_session()


async def close_session(session_id: str) -> None:
    async with _lock:
        _sessions.pop(session_id, None)
        logger.info("closed session %s", session_id)


def list_sessions() -> list[Session]:
    return list(_sessions.values())


class AgentRunner:
    """Runs a single agent terminal within a session."""

    def __init__(
        self,
        session: Session,
        terminal: Terminal,
        profile_search_paths: list[Path] | None = None,
    ) -> None:
        self.session = session
        self.terminal = terminal
        self.profile_search_paths = profile_search_paths or [Path("agents")]

    async def run(self, message: str) -> str:
        """Execute the agent and return its final output."""
        from cao.runner import run_agent

        self.terminal.status = TerminalStatus.RUNNING
        try:
            result = await run_agent(
                profile=self.terminal.profile,
                message=message,
                session=self.session,
                terminal=self.terminal,
            )
            self.terminal.result = result
            self.terminal.status = TerminalStatus.DONE
            return result
        except Exception as exc:
            self.terminal.error = str(exc)
            self.terminal.status = TerminalStatus.ERROR
            logger.exception("agent %s failed: %s", self.terminal.id, exc)
            raise
