"""Core CAO data models."""

from __future__ import annotations

import uuid
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Any


class TerminalStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    IDLE = "idle"
    DONE = "done"
    ERROR = "error"


class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class McpServerConfig:
    def __init__(
        self,
        type: str = "stdio",
        command: str = "",
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.type = type
        self.command = command
        self.args = args or []
        self.env = env or {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> McpServerConfig:
        return cls(
            type=data.get("type", "stdio"),
            command=data.get("command", ""),
            args=data.get("args", []),
            env=data.get("env", {}),
        )


class AgentProfile:
    def __init__(
        self,
        name: str,
        description: str = "",
        provider: str = "mock",
        model: str = "claude-sonnet-4-5",
        role: str = "assistant",
        mcp_servers: dict[str, McpServerConfig] | None = None,
        system_prompt: str = "",
        source_path: str | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.provider = provider
        self.model = model
        self.role = role
        self.mcp_servers = mcp_servers or {}
        self.system_prompt = system_prompt
        self.source_path = source_path

    @property
    def display_name(self) -> str:
        return self.name.replace("_", " ").replace("-", " ").title()


class Message:
    def __init__(self, role: MessageRole, content: str) -> None:
        self.role = role
        self.content = content
        self.timestamp = datetime.utcnow()
        self.metadata: dict[str, Any] = {}


class Terminal:
    def __init__(self, terminal_id: str, profile: AgentProfile | None) -> None:
        self.id = terminal_id
        self.profile = profile
        self.status = TerminalStatus.PENDING
        self.messages: list[Message] = []
        self.result: str | None = None
        self.error: str | None = None
        self.caller_id: str | None = None
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None

    def add_message(self, role: MessageRole, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    @property
    def duration_ms(self) -> int | None:
        if self.started_at and self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds() * 1000)
        return None


class Session:
    def __init__(self, session_id: str) -> None:
        self.id = session_id
        self.terminals: dict[str, Terminal] = {}
        self.created_at = datetime.utcnow()
        self.inbox: deque[str] = deque()

    def create_terminal(self, profile: AgentProfile | None) -> Terminal:
        tid = str(uuid.uuid4())[:8]
        terminal = Terminal(tid, profile)
        self.terminals[tid] = terminal
        return terminal

    def get_terminal(self, terminal_id: str) -> Terminal | None:
        return self.terminals.get(terminal_id)

    def deliver_message(self, sender_id: str, content: str) -> None:
        self.inbox.append(f"[from:{sender_id}] {content}")
