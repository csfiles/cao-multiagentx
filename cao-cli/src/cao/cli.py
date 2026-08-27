"""CAO CLI — main command-line interface."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cao import __version__

console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(__version__, prog_name="cao")
@click.option("--log-level", default=None, help="Log level (DEBUG/INFO/WARNING)")
def main(log_level: str | None) -> None:
    """CAO — CLI Agent Orchestrator.

    Multi-agent orchestration via Markdown profiles and MCP tools.
    """
    level = log_level or os.environ.get("CAO_LOG_LEVEL", "WARNING")
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        stream=sys.stderr,
    )


@main.command()
@click.argument("profile_path")
@click.option("--input", "-i", "input_text", required=True, help="Message to send to the agent")
@click.option("--session", "-s", default=None, help="Session ID to join")
@click.option("--provider", default=None, help="Override provider (e.g. mock)")
def run(profile_path: str, input_text: str, session: str | None, provider: str | None) -> None:
    """Run an agent profile with a given input message.

    Example:
        cao run agents/inventory_specialist.md --input "Check order ORD-1001"
    """
    from cao.profile import load_profile
    from cao.runner import run_agent
    from cao.session import create_session

    path = Path(profile_path)
    if not path.exists():
        console.print(f"[red]Profile not found: {profile_path}[/red]")
        sys.exit(1)

    profile = load_profile(path)
    if provider:
        profile.provider = provider

    async def _run() -> None:
        s = await create_session()
        terminal = s.create_terminal(profile)
        result = await run_agent(profile, input_text, s, terminal)
        console.print(Panel(result, title=f"[bold blue]{profile.display_name}[/bold blue]"))

    asyncio.run(_run())


@main.command()
@click.argument("profile_names", nargs=-1)
@click.option("--input", "-i", "input_text", required=True, help="Initial message")
@click.option("--provider", default=None, help="Override provider for all agents")
def launch(profile_names: tuple[str, ...], input_text: str, provider: str | None) -> None:
    """Launch a supervisor agent (and optionally additional agents).

    Example:
        cao launch customer_support_supervisor --input "My order is damaged"
    """
    from cao.profile import discover_profiles
    from cao.runner import run_agent
    from cao.session import create_session

    search_paths = [
        Path(p) for p in os.environ.get("CAO_AGENT_PATHS", "agents:.").split(":")
    ]
    profiles = discover_profiles(search_paths)

    names = profile_names if profile_names else list(profiles.keys())[:1]

    async def _run() -> None:
        session = await create_session()
        console.print(f"[dim]Session: {session.id}[/dim]")
        for name in names:
            profile = profiles.get(name)
            if profile is None:
                console.print(f"[yellow]Agent not found: {name}[/yellow]")
                continue
            if provider:
                profile.provider = provider
            terminal = session.create_terminal(profile)
            console.print(f"[bold]Running:[/bold] {profile.display_name}")
            result = await run_agent(profile, input_text, session, terminal)
            console.print(Panel(result, title=profile.display_name))

    asyncio.run(_run())


@main.command()
@click.argument("profile_name")
def install(profile_name: str) -> None:
    """Install a built-in agent profile to the local agents/ directory.

    Example:
        cao install customer_support_supervisor
    """
    # In a full implementation this would download from the CAO profile registry.
    # Here we inform the user where to find profiles.
    console.print(
        Panel(
            f"[yellow]'{profile_name}' is not a built-in profile.[/yellow]\n\n"
            "Create agent profiles as Markdown files with YAML frontmatter.\n"
            "See: [link]https://github.com/awslabs/cli-agent-orchestrator[/link]",
            title="cao install",
        )
    )


@main.command()
def agents() -> None:
    """List available agent profiles in the current directory."""
    from cao.profile import discover_profiles

    search_paths = [
        Path(p) for p in os.environ.get("CAO_AGENT_PATHS", "agents:.").split(":")
    ]
    profiles = discover_profiles(search_paths)

    if not profiles:
        console.print("[yellow]No agent profiles found.[/yellow]")
        console.print(f"Searched: {[str(p) for p in search_paths]}")
        return

    table = Table(title="Available Agents", show_header=True)
    table.add_column("Name", style="bold blue")
    table.add_column("Role", style="cyan")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("Description")

    for profile in profiles.values():
        table.add_row(
            profile.name,
            profile.role,
            profile.provider,
            profile.model,
            profile.description[:60] + ("..." if len(profile.description) > 60 else ""),
        )

    console.print(table)


@main.command()
def update() -> None:
    """Update CAO CLI to the latest version."""
    console.print(
        "[yellow]To update CAO CLI, run:[/yellow]\n"
        "  uv tool install git+https://github.com/awslabs/cli-agent-orchestrator.git@main --upgrade\n"
        "  [dim]or[/dim]\n"
        "  uv pip install -e . --upgrade"
    )


@main.command()
def version() -> None:
    """Show CAO CLI version."""
    console.print(f"CAO CLI v{__version__}")


if __name__ == "__main__":
    main()
