"""Base provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderConfig:
    """Configuration for a provider invocation."""

    model: str
    system_prompt: str
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    temperature: float = 0.1
    max_tokens: int = 8192
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class ProviderResponse:
    """Response from a provider turn."""

    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tokens_used: int = 0
    provider: str = ""
    model: str = ""


class BaseProvider(ABC):
    """Abstract base for agent execution providers."""

    @abstractmethod
    async def run_turn(
        self,
        message: str,
        config: ProviderConfig,
        history: list[dict[str, str]] | None = None,
    ) -> ProviderResponse:
        """Execute a single agent turn and return the response."""
        ...

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Return the provider identifier string."""
        ...
