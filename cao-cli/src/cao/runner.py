"""Agent runner — executes a single agent turn using the configured provider."""

from __future__ import annotations

import logging
from typing import Any

from cao.models import AgentProfile, Message, MessageRole, Session, Terminal
from cao.providers import get_provider
from cao.providers.base import ProviderConfig

logger = logging.getLogger(__name__)


async def run_agent(
    profile: AgentProfile | None,
    message: str,
    session: Session,
    terminal: Terminal,
) -> str:
    """Run a single agent turn and return the text result."""
    if profile is None:
        return f"[no profile — echo] {message}"

    provider_cls = get_provider(profile.provider)
    provider = provider_cls()

    mcp_config: dict[str, Any] = {
        name: {
            "type": cfg.type,
            "command": cfg.command,
            "args": cfg.args,
            "env": cfg.env,
        }
        for name, cfg in profile.mcp_servers.items()
    }

    config = ProviderConfig(
        model=profile.model,
        system_prompt=profile.system_prompt,
        mcp_servers=mcp_config,
    )

    history = [
        {"role": m.role.value, "content": m.content}
        for m in terminal.messages
    ]

    logger.info(
        "running agent %s (provider=%s model=%s)",
        profile.name,
        profile.provider,
        profile.model,
    )

    terminal.add_message(MessageRole.USER, message)
    response = await provider.run_turn(message, config, history)
    terminal.add_message(MessageRole.AGENT, response.content)

    logger.info(
        "agent %s completed (%d chars)",
        profile.name,
        len(response.content),
    )

    return response.content
