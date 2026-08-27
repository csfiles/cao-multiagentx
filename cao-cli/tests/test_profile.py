"""Tests for agent profile parsing."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from cao.profile import parse_profile


def _profile(frontmatter: str, body: str = "") -> str:
    return f"---\n{textwrap.dedent(frontmatter).strip()}\n---\n{body}"


def test_parse_basic_profile():
    raw = _profile(
        """
        name: inventory-specialist
        description: Looks up order and inventory data
        provider: mock
        model: claude-sonnet-4-5
        role: inventory
        """,
        "You are an inventory specialist.",
    )
    profile = parse_profile(raw)
    assert profile.name == "inventory-specialist"
    assert profile.description == "Looks up order and inventory data"
    assert profile.provider == "mock"
    assert profile.model == "claude-sonnet-4-5"
    assert profile.role == "inventory"
    assert "inventory specialist" in profile.system_prompt


def test_parse_mcp_servers():
    raw = _profile(
        """
        name: test-agent
        description: Agent with MCP
        provider: claude_code
        model: sonnet
        role: worker
        mcpServers:
          cao-mcp-server:
            type: stdio
            command: cao-mcp-server
            args: []
        """
    )
    profile = parse_profile(raw)
    assert "cao-mcp-server" in profile.mcp_servers
    srv = profile.mcp_servers["cao-mcp-server"]
    assert srv.type == "stdio"
    assert srv.command == "cao-mcp-server"
    assert srv.args == []


def test_parse_missing_name_raises():
    raw = "---\nprovider: mock\n---\n"
    with pytest.raises(ValueError, match="name"):
        parse_profile(raw)


def test_parse_no_frontmatter_raises():
    with pytest.raises(ValueError, match="frontmatter"):
        parse_profile("Just plain text, no YAML.")


def test_display_name():
    raw = _profile("name: inventory_specialist\ndescription: x\nprovider: mock\nmodel: x\nrole: y")
    profile = parse_profile(raw)
    assert profile.display_name == "Inventory Specialist"


def test_profile_defaults():
    raw = _profile("name: minimal-agent\ndescription: minimal\nprovider: mock\nmodel: claude-3\nrole: assistant")
    profile = parse_profile(raw)
    assert profile.mcp_servers == {}
    assert profile.system_prompt == ""
