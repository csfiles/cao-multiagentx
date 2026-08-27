"""
Rich-based terminal formatting for SupportMesh CLI output.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


def print_banner() -> None:
    console.print(
        Panel(
            "[bold cyan]SupportMesh[/bold cyan]  [dim]multi-agent customer support[/dim]",
            border_style="cyan",
            expand=False,
        )
    )


def print_request(customer_id: str, message: str) -> None:
    console.print(
        Panel(
            f"[bold]Customer:[/bold] {customer_id}\n\n{message}",
            title="[bold yellow]Incoming Request[/bold yellow]",
            border_style="yellow",
        )
    )


def print_agent_step(agent_name: str, status: str, detail: str = "") -> None:
    color = {"running": "blue", "done": "green", "error": "red"}.get(status, "white")
    icon = {"running": "⟳", "done": "✓", "error": "✗"}.get(status, "·")
    line = f"[{color}]{icon} {agent_name}[/{color}]"
    if detail:
        line += f"  [dim]{detail}[/dim]"
    console.print(line)


def print_case_summary(summary: dict[str, Any]) -> None:
    table = Table(title="Case Summary", box=box.SIMPLE_HEAD, show_header=True)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    customer = summary.get("customer_data") or {}
    order = summary.get("order_data") or {}
    refund = summary.get("refund_eligibility") or {}

    if customer:
        table.add_row("Customer", f"{customer.get('name', '?')} ({customer.get('tier', '?')} tier)")
    if order:
        table.add_row("Order", f"{order.get('id', '?')} — {order.get('status', '?')}")
        table.add_row("Total", f"${order.get('total', 0):.2f} {order.get('currency', 'USD')}")
    if refund:
        eligible = "Yes" if refund.get("eligible") else "No"
        amount = refund.get("eligible_amount", 0)
        table.add_row("Refund Eligible", f"{eligible} (${amount:.2f})")
    table.add_row(
        "Confidence",
        f"{summary.get('overall_confidence', 1.0):.0%}",
    )
    console.print(table)


def print_customer_response(message: str) -> None:
    console.print(
        Panel(
            message,
            title="[bold green]Customer Response[/bold green]",
            border_style="green",
        )
    )


def print_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str) -> None:
    console.print(f"[bold green]✓[/bold green] {message}")


def print_warning(message: str) -> None:
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")
