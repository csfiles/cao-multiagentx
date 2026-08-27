# SupportMesh MCP Server

FastMCP server providing customer support tools to CAO agents.

## Tools

| Tool | Description |
|------|-------------|
| `get_customer` | Customer profile by ID |
| `get_customer_tier` | Service tier only (lightweight) |
| `list_customer_orders` | All orders for a customer |
| `get_order` | Full order details |
| `get_order_status` | Order status + tracking |
| `get_order_items` | Line items in an order |
| `calculate_refund_eligibility` | Eligibility + amount |
| `create_refund_request` | Refund proposal (dry-run by default) |
| `search_returns_policy` | Full-text search of returns policy |
| `search_shipping_policy` | Full-text search of shipping policy |
| `search_warranty_policy` | Full-text search of warranty policy |

## Start

```bash
python -m mcp.customer_support_server.server
```

See [../docs/mcp.md](../docs/mcp.md) for full documentation.
