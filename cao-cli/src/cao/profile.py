"""Agent profile loading and validation.

Profiles are Markdown files with YAML frontmatter:

    ---
    name: my-agent
    description: Does something useful
    provider: claude_code
    model: sonnet
    role: developer
    mcpServers:
      cao-mcp-server:
        type: stdio
        command: cao-mcp-server
        args: []
    ---

    # Agent system prompt...
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from cao.models import AgentProfile, McpServerConfig

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

REQUIRED_FIELDS = {"name", "description", "provider", "model"}
VALID_PROVIDERS = {"claude_code", "kiro_cli", "codex", "mock", "openai"}
VALID_ROLES = {"supervisor", "developer", "reviewer", "specialist", "worker", "agent"}


def load_profile(path: Path) -> AgentProfile:
    """Load and validate an agent profile from a Markdown file."""
    raw = path.read_text(encoding="utf-8")
    return parse_profile(raw, source_path=path)


def parse_profile(content: str, source_path: Path | None = None) -> AgentProfile:
    """Parse agent profile from raw Markdown+YAML content."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        raise ValueError(
            f"Agent profile is missing YAML frontmatter. "
            f"Expected '---' block at the start of the file. "
            f"Source: {source_path}"
        )

    front = yaml.safe_load(match.group(1))
    if not isinstance(front, dict):
        raise ValueError(f"Frontmatter must be a YAML mapping. Source: {source_path}")

    _validate_frontmatter(front, source_path)

    mcp_servers: dict[str, McpServerConfig] = {}
    for server_name, server_cfg in front.get("mcpServers", {}).items():
        mcp_servers[server_name] = McpServerConfig.from_dict(server_cfg)

    system_prompt = content[match.end():].strip()

    return AgentProfile(
        name=front["name"],
        description=front["description"],
        provider=front["provider"],
        model=front["model"],
        role=front.get("role", "agent"),
        mcp_servers=mcp_servers,
        system_prompt=system_prompt,
        source_path=source_path,
    )


def _validate_frontmatter(front: dict[str, Any], source_path: Path | None) -> None:
    missing = REQUIRED_FIELDS - set(front.keys())
    if missing:
        raise ValueError(
            f"Agent profile missing required fields: {missing}. "
            f"Source: {source_path}"
        )


def discover_profiles(search_paths: list[Path]) -> dict[str, AgentProfile]:
    """Discover all .md agent profiles in the given directories."""
    profiles: dict[str, AgentProfile] = {}
    for directory in search_paths:
        if not directory.is_dir():
            continue
        for md_file in directory.glob("*.md"):
            try:
                profile = load_profile(md_file)
                profiles[profile.name] = profile
            except (ValueError, yaml.YAMLError):
                pass  # skip malformed files during discovery
    return profiles
