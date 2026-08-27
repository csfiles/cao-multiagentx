"""
SupportMesh MCP Server.

Run with:
    python -m mcp.customer_support_server.server

Or via the package entry point:
    supportmesh-mcp-server
"""

from __future__ import annotations

import logging
import os
from mcp.server.fastmcp import FastMCP

from . import tools

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log_level = os.getenv("SUPPORTMESH_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("supportmesh.mcp")

# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="supportmesh-customer-support",
    instructions=(
        "You are the SupportMesh customer support MCP server. "
        "Provide accurate customer, order, refund, and policy data. "
        "All refund operations are dry-run by default unless SUPPORTMESH_ALLOW_MUTATIONS=true."
    ),
)


# ---------------------------------------------------------------------------
# Customer tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_customer(customer_id: str) -> dict:
    """Retrieve a customer profile by customer ID.

    Args:
        customer_id: Customer identifier (e.g., CUST-001)
    """
    return await tools.get_customer(customer_id)


@mcp.tool()
async def get_customer_tier(customer_id: str) -> dict:
    """Get the service tier for a customer (standard / premium / enterprise).

    Args:
        customer_id: Customer identifier
    """
    return await tools.get_customer_tier(customer_id)


@mcp.tool()
async def list_customer_orders(customer_id: str) -> dict:
    """List all orders associated with a customer.

    Args:
        customer_id: Customer identifier
    """
    return await tools.list_customer_orders(customer_id)


# ---------------------------------------------------------------------------
# Order tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_order(order_id: str) -> dict:
    """Retrieve full order details including items, totals, and shipping info.

    Args:
        order_id: Order identifier (e.g., ORD-1001)
    """
    return await tools.get_order(order_id)


@mcp.tool()
async def get_order_status(order_id: str) -> dict:
    """Get the current status and tracking information for an order.

    Args:
        order_id: Order identifier
    """
    return await tools.get_order_status(order_id)


@mcp.tool()
async def get_order_items(order_id: str) -> dict:
    """Get the list of line items in an order.

    Args:
        order_id: Order identifier
    """
    return await tools.get_order_items(order_id)


# ---------------------------------------------------------------------------
# Refund tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def calculate_refund_eligibility(order_id: str, reason: str) -> dict:
    """Calculate whether a refund is eligible for an order and what amount.

    Eligibility depends on order status (must be delivered), days since delivery
    vs. customer tier's return window, and refund reason.

    Args:
        order_id: Order identifier
        reason: Reason for refund (damaged / wrong_item / not_satisfied / defective / not_received)
    """
    return await tools.calculate_refund_eligibility(order_id, reason)


@mcp.tool()
async def create_refund_request(order_id: str, reason: str, dry_run: bool = True) -> dict:
    """Create a refund request for an order.

    By default this is a dry-run — it returns a proposal without writing anything.
    Writing only occurs if SUPPORTMESH_ALLOW_MUTATIONS=true AND dry_run=False.

    IMPORTANT: Always use dry_run=True unless you have explicit authorization.

    Args:
        order_id: Order identifier
        reason: Reason for the refund
        dry_run: If True (default), return proposal only. Set False only with authorization.
    """
    return await tools.create_refund_request(order_id, reason, dry_run)


# ---------------------------------------------------------------------------
# Policy tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_returns_policy(query: str) -> dict:
    """Search the returns policy document for relevant information.

    Args:
        query: Natural language search query (e.g., "return window for electronics")
    """
    return await tools.search_returns_policy(query)


@mcp.tool()
async def search_shipping_policy(query: str) -> dict:
    """Search the shipping policy document for relevant information.

    Args:
        query: Natural language search query (e.g., "express delivery cutoff time")
    """
    return await tools.search_shipping_policy(query)


@mcp.tool()
async def search_warranty_policy(query: str) -> dict:
    """Search the warranty policy document for relevant information.

    Args:
        query: Natural language search query (e.g., "electronics warranty period")
    """
    return await tools.search_warranty_policy(query)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the SupportMesh MCP server."""
    logger.info(
        "SupportMesh MCP server starting (mutations_allowed=%s)",
        os.getenv("SUPPORTMESH_ALLOW_MUTATIONS", "false"),
    )
    mcp.run()


if __name__ == "__main__":
    main()
