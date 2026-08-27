"""Claude Code provider — runs claude CLI as a subprocess agent."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from typing import Any

from cao.providers.base import BaseProvider, ProviderConfig, ProviderResponse

logger = logging.getLogger(__name__)

CLAUDE_BINARY = os.environ.get("CAO_CLAUDE_BINARY", "claude")


class ClaudeCodeProvider(BaseProvider):
    """Invokes the `claude` CLI tool to run an agent turn."""

    @classmethod
    def name(cls) -> str:
        return "claude_code"

    async def run_turn(
        self,
        message: str,
        config: ProviderConfig,
        history: list[dict[str, str]] | None = None,
    ) -> ProviderResponse:
        if not shutil.which(CLAUDE_BINARY):
            raise RuntimeError(
                f"'{CLAUDE_BINARY}' binary not found. "
                "Install Claude Code CLI or set CAO_CLAUDE_BINARY."
            )

        mcp_args = _build_mcp_args(config.mcp_servers)
        model_flag = f"--model {config.model}" if config.model else ""

        cmd = [
            CLAUDE_BINARY,
            "--print",  # non-interactive, print output and exit
            "--output-format", "json",
            *(["--model", config.model] if config.model else []),
            *mcp_args,
        ]

        env = {**os.environ, **config.env}
        if config.system_prompt:
            env["CLAUDE_SYSTEM_PROMPT"] = config.system_prompt

        logger.debug("running claude with args: %s", cmd)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        stdout, stderr = await proc.communicate(input=message.encode())

        if proc.returncode != 0:
            raise RuntimeError(
                f"claude exited with code {proc.returncode}: {stderr.decode()[:500]}"
            )

        output = stdout.decode()
        content = _parse_claude_output(output)

        return ProviderResponse(
            content=content,
            provider="claude_code",
            model=config.model,
        )


def _build_mcp_args(mcp_servers: dict[str, Any]) -> list[str]:
    """Convert MCP server config to claude CLI flags."""
    args: list[str] = []
    for name, cfg in mcp_servers.items():
        if isinstance(cfg, dict) and cfg.get("type") == "stdio":
            cmd = cfg.get("command", "")
            server_args = cfg.get("args", [])
            full_cmd = " ".join([cmd, *server_args])
            args.extend(["--mcp-server", f"{name}={full_cmd}"])
    return args


def _parse_claude_output(raw: str) -> str:
    """Parse JSON output from claude --output-format json, fallback to raw text."""
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data.get("result", data.get("content", raw))
    except (json.JSONDecodeError, TypeError):
        pass
    return raw.strip()
