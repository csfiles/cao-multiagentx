"""
SupportMesh CLI entry point.

Usage:
    supportmesh ask --customer CUST-001 "Where is my order?"
    supportmesh health
    supportmesh demo
"""

from __future__ import annotations

import asyncio
import json
import sys

import click
from rich.console import Console

from .config import config
from .formatting import (
    console,
    print_banner,
    print_case_summary,
    print_customer_response,
    print_error,
    print_request,
    print_success,
    print_warning,
)
from .models import IssueType, SupportRequest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _detect_issue_type(message: str) -> IssueType:
    msg = message.lower()
    if any(w in msg for w in ["refund", "money back", "charge"]):
        return IssueType.refund_request
    if any(w in msg for w in ["damaged", "broken", "cracked", "defective"]):
        return IssueType.damaged_item
    if any(w in msg for w in ["wrong item", "wrong product", "incorrect"]):
        return IssueType.wrong_item
    if any(w in msg for w in ["where is", "status", "tracking", "shipped", "delivery"]):
        return IssueType.order_status
    if any(w in msg for w in ["policy", "return", "warranty", "guarantee"]):
        return IssueType.policy_question
    if any(w in msg for w in ["delayed", "late", "shipping"]):
        return IssueType.shipping_delay
    return IssueType.general


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(version="0.1.0", prog_name="supportmesh")
def main() -> None:
    """SupportMesh — multi-agent customer support powered by CAO + MCP."""


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@main.command()
@click.option("--customer", "-c", required=True, help="Customer ID (e.g. CUST-001)")
@click.option("--order", "-o", default=None, help="Order ID if known (e.g. ORD-1001)")
@click.option("--json-output", is_flag=True, help="Output result as JSON")
@click.argument("message")
def ask(customer: str, order: str | None, message: str, json_output: bool) -> None:
    """Submit a customer support request and get a response.

    \b
    Examples:
        supportmesh ask --customer CUST-001 "Where is my order ORD-1001?"
        supportmesh ask -c CUST-002 -o ORD-1002 "I received a damaged item"
    """
    if not json_output:
        print_banner()
        print_request(customer, message)

    request = SupportRequest(
        customer_id=customer,
        message=message,
        issue_type=_detect_issue_type(message),
        order_id=order,
    )

    try:
        from workflows.support_workflow import run_support_workflow

        result = asyncio.run(run_support_workflow(request))

        if json_output:
            click.echo(json.dumps(result.model_dump(), indent=2))
        else:
            print_case_summary(result.case_summary.model_dump())
            print_customer_response(result.customer_message)
            if result.follow_up_required:
                print_warning("This case requires human follow-up.")

    except Exception as exc:
        if json_output:
            click.echo(json.dumps({"error": str(exc)}), err=True)
        else:
            print_error(f"Workflow failed: {exc}")
        sys.exit(1)


@main.command()
def health() -> None:
    """Check that the MCP server and data files are accessible."""
    print_banner()

    import asyncio
    from mcp.customer_support_server.tools import get_default_store

    store = get_default_store()
    store._load()

    customers = len(store._customers)
    orders = len(store._orders)

    if customers > 0 and orders > 0:
        print_success(f"Data loaded: {customers} customers, {orders} orders")
    else:
        print_warning(f"Data: {customers} customers, {orders} orders (check data/ directory)")

    for policy in ("returns", "shipping", "warranty"):
        content = store._load_policy(policy)
        if content:
            print_success(f"Policy '{policy}': {len(content)} chars loaded")
        else:
            print_warning(f"Policy '{policy}': not found")

    if config.allow_mutations:
        print_warning("SUPPORTMESH_ALLOW_MUTATIONS=true — refund writes are ENABLED")
    else:
        print_success("SUPPORTMESH_ALLOW_MUTATIONS=false — refund writes are safely disabled")


@main.command()
def demo() -> None:
    """Run a quick demo with sample customer data.

    Uses CUST-001 and ORD-1001 from the local data files.
    """
    print_banner()
    console.print("[dim]Running demo with customer CUST-001...[/dim]\n")

    customer_id = config.demo_customer_id
    message = "I received a damaged item in my order ORD-1001. Can I get a refund?"
    order_id = "ORD-1001"

    request = SupportRequest(
        customer_id=customer_id,
        message=message,
        issue_type=IssueType.damaged_item,
        order_id=order_id,
    )

    print_request(customer_id, message)

    try:
        from workflows.support_workflow import run_support_workflow

        result = asyncio.run(run_support_workflow(request))
        print_case_summary(result.case_summary.model_dump())
        print_customer_response(result.customer_message)

    except Exception as exc:
        print_error(f"Demo failed: {exc}")
        console.print(
            "\n[dim]Tip: run 'make health' to check that data files are present.[/dim]"
        )
        sys.exit(1)


@main.command("mcp-server")
def mcp_server() -> None:
    """Start the SupportMesh MCP server."""
    from mcp.customer_support_server.server import main as server_main

    server_main()
